"""
Map Generator Service

This module contains all map poster generation logic, extracted from the original
create_map_poster.py script. It provides functions for fetching map data from OSM,
loading themes, and rendering map posters.

All functions use the app's logging system for consistent logging.
"""

import os
import json
import time
import logging
from datetime import datetime
from functools import lru_cache
from typing import Dict, Tuple, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import osmnx as ox
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for thread safety
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim

# Configure logger for this module
logger = logging.getLogger(__name__)

# Directory paths
THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"


def load_fonts():
    """
    Load Roboto fonts from the fonts directory.
    Returns dict with font paths for different weights.
    """
    fonts = {
        'bold': os.path.join(FONTS_DIR, 'Roboto-Bold.ttf'),
        'regular': os.path.join(FONTS_DIR, 'Roboto-Regular.ttf'),
        'light': os.path.join(FONTS_DIR, 'Roboto-Light.ttf')
    }
    
    # Verify fonts exist
    for weight, path in fonts.items():
        if not os.path.exists(path):
            logger.warning(f"Font not found: {path}")
            return None
    
    return fonts


FONTS = load_fonts()


def generate_output_filename(city: str, theme_name: str) -> str:
    """
    Generate unique output filename with city, theme, and datetime.
    
    Args:
        city: City name
        theme_name: Theme name
        
    Returns:
        Full path to output file
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_{theme_name}_{timestamp}.png"
    return os.path.join(POSTERS_DIR, filename)


def get_available_themes() -> List[str]:
    """
    Scans the themes directory and returns a list of available theme names.
    
    Returns:
        List of theme names (without .json extension)
    """
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)
        return []
    
    themes = []
    for file in sorted(os.listdir(THEMES_DIR)):
        if file.endswith('.json'):
            theme_name = file[:-5]  # Remove .json extension
            themes.append(theme_name)
    return themes


@lru_cache(maxsize=32)
def load_theme(theme_name: str = "feature_based") -> Dict:
    """
    Load theme from JSON file in themes directory.
    Results are cached to improve performance.
    
    Args:
        theme_name: Name of the theme to load
        
    Returns:
        Dictionary containing theme configuration
    """
    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")
    
    if not os.path.exists(theme_file):
        logger.warning(f"Theme file '{theme_file}' not found. Using default feature_based theme.")
        # Fallback to embedded default theme
        return {
            "name": "Feature-Based Shading",
            "bg": "#FFFFFF",
            "text": "#000000",
            "gradient_color": "#FFFFFF",
            "water": "#C0C0C0",
            "parks": "#F0F0F0",
            "road_motorway": "#0A0A0A",
            "road_primary": "#1A1A1A",
            "road_secondary": "#2A2A2A",
            "road_tertiary": "#3A3A3A",
            "road_residential": "#4A4A4A",
            "road_default": "#3A3A3A"
        }
    
    with open(theme_file, 'r') as f:
        theme = json.load(f)
        logger.info(f"Loaded theme: {theme.get('name', theme_name)}")
        if 'description' in theme:
            logger.debug(f"Theme description: {theme['description']}")
        return theme


def create_gradient_fade(ax, color: str, location: str = 'bottom', zorder: int = 10):
    """
    Creates a fade effect at the top or bottom of the map.
    
    Args:
        ax: Matplotlib axes object
        color: Color for the gradient
        location: 'bottom' or 'top'
        zorder: Z-order for layering
    """
    vals = np.linspace(0, 1, 256).reshape(-1, 1)
    gradient = np.hstack((vals, vals))
    
    rgb = mcolors.to_rgb(color)
    my_colors = np.zeros((256, 4))
    my_colors[:, 0] = rgb[0]
    my_colors[:, 1] = rgb[1]
    my_colors[:, 2] = rgb[2]
    
    if location == 'bottom':
        my_colors[:, 3] = np.linspace(1, 0, 256)
        extent_y_start = 0
        extent_y_end = 0.25
    else:
        my_colors[:, 3] = np.linspace(0, 1, 256)
        extent_y_start = 0.75
        extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(my_colors)
    
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    
    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end
    
    ax.imshow(gradient, extent=[xlim[0], xlim[1], y_bottom, y_top], 
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')


def get_edge_attributes_by_type(G, theme: Dict) -> Tuple[List[str], List[float]]:
    """
    Assigns colors and widths to edges based on road type hierarchy.
    Returns tuple of (edge_colors, edge_widths) lists corresponding to each edge.
    This combines color and width assignment in a single iteration for efficiency.
    
    Args:
        G: OSMnx graph
        theme: Theme dictionary with road color definitions
        
    Returns:
        Tuple of (edge_colors, edge_widths)
    """
    edge_colors = []
    edge_widths = []
    
    for u, v, data in G.edges(data=True):
        # Get the highway type (can be a list or string)
        highway = data.get('highway', 'unclassified')
        
        # Handle list of highway types (take the first one)
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        # Assign color and width based on road type
        if highway in ['motorway', 'motorway_link']:
            color = theme['road_motorway']
            width = 1.2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = theme['road_primary']
            width = 1.0
        elif highway in ['secondary', 'secondary_link']:
            color = theme['road_secondary']
            width = 0.8
        elif highway in ['tertiary', 'tertiary_link']:
            color = theme['road_tertiary']
            width = 0.6
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = theme['road_residential']
            width = 0.4
        else:
            color = theme['road_default']
            width = 0.4
        
        edge_colors.append(color)
        edge_widths.append(width)
    
    return edge_colors, edge_widths


def get_coordinates(city: str, country: str) -> Tuple[float, float]:
    """
    Fetches coordinates for a given city and country using geopy.
    Includes rate limiting to be respectful to the geocoding service.
    
    Args:
        city: City name
        country: Country name
        
    Returns:
        Tuple of (latitude, longitude)
        
    Raises:
        ValueError: If coordinates cannot be found
    """
    logger.info("Looking up coordinates...")
    geolocator = Nominatim(user_agent="city_map_poster")
    
    # Add a small delay to respect Nominatim's usage policy
    time.sleep(1)
    
    location = geolocator.geocode(f"{city}, {country}")
    
    if location:
        logger.info(f"Found: {location.address}")
        logger.info(f"Coordinates: {location.latitude}, {location.longitude}")
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")


def fetch_map_data(point: Tuple[float, float], distance: int, 
                   progress_callback: Optional[Callable] = None) -> Dict:
    """
    Fetch map data from OpenStreetMap for the specified location using parallel downloads.
    
    Args:
        point: Tuple of (latitude, longitude)
        distance: Distance in meters for the bounding box
        progress_callback: Optional callback function(step_name, completed, total) called when each data type completes
        
    Returns:
        Dictionary containing:
        - 'graph': Street network graph from OSMnx
        - 'water': Water features GeoDataFrame (or None if not found)
        - 'parks': Parks/green spaces GeoDataFrame (or None if not found)
        - 'bounds': Bounding box of the graph
    """
    logger.info(f"Fetching map data for coordinates {point}...")
    
    # Helper functions for parallel downloads
    def _fetch_streets(point, distance):
        """Download street network data."""
        logger.info("Starting street network download...")
        G = ox.graph_from_point(point, dist=distance, dist_type='bbox', network_type='all')
        logger.info("Street network downloaded")
        return ('streets', G)
    
    def _fetch_water(point, distance):
        """Download water features data."""
        logger.info("Starting water features download...")
        try:
            water = ox.features_from_point(point, tags={'natural': 'water', 'waterway': 'riverbank'}, dist=distance)
            logger.info("Water features downloaded")
            return ('water', water)
        except Exception as e:
            logger.info("Water features not found (this is normal for some locations)")
            return ('water', None)
    
    def _fetch_parks(point, distance):
        """Download parks/green spaces data."""
        logger.info("Starting parks download...")
        try:
            parks = ox.features_from_point(point, tags={'leisure': 'park', 'landuse': 'grass'}, dist=distance)
            logger.info("Parks downloaded")
            return ('parks', parks)
        except Exception as e:
            logger.info("Parks not found (this is normal for some locations)")
            return ('parks', None)
    
    map_data = {}
    
    # Use ThreadPoolExecutor to download all data in parallel
    logger.info("Downloading map data in parallel (3 concurrent requests)...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all three download tasks
        future_streets = executor.submit(_fetch_streets, point, distance)
        future_water = executor.submit(_fetch_water, point, distance)
        future_parks = executor.submit(_fetch_parks, point, distance)
        
        # Collect results as they complete
        futures = {
            future_streets: 'streets',
            future_water: 'water',
            future_parks: 'parks'
        }
        
        completed = 0
        total = len(futures)
        
        for future in as_completed(futures):
            completed += 1
            data_type, data = future.result()
            
            if data_type == 'streets':
                map_data['graph'] = data
            elif data_type == 'water':
                map_data['water'] = data
            elif data_type == 'parks':
                map_data['parks'] = data
            
            logger.info(f"[{completed}/{total}] {data_type} completed")
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(data_type, completed, total)
    
    # Get bounds from graph
    nodes = ox.graph_to_gdfs(map_data['graph'], edges=False)
    map_data['bounds'] = (nodes.x.min(), nodes.x.max(), nodes.y.min(), nodes.y.max())
    
    # Single rate limiting sleep after all downloads complete
    time.sleep(0.5)
    
    logger.info("All data downloaded successfully!")
    return map_data


def render_poster(map_data: Dict, theme: Dict, city: str, country: str, 
                 point: Tuple[float, float], output_file: str, 
                 preview_mode: bool = False, progress_callback: Optional[Callable] = None):
    """
    Render a map poster using pre-fetched map data.
    
    Args:
        map_data: Dictionary containing 'graph', 'water', 'parks', 'bounds' from fetch_map_data()
        theme: Theme dictionary with color and style settings
        city: City name for the poster text
        country: Country name for the poster text
        point: Tuple of (latitude, longitude)
        output_file: Path where the poster will be saved
        preview_mode: If True, use lower DPI (150) for faster preview rendering. Default False uses DPI 300.
        progress_callback: Optional callback function(stage_name) called at rendering stages
    """
    logger.info(f"Rendering map for {city}, {country}...")
    logger.info(f"Theme: {theme.get('name', 'Unknown')}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Preview mode: {preview_mode}")
    
    # Log theme colors for debugging
    logger.debug(f"Theme colors - BG: {theme.get('bg')}, Water: {theme.get('water')}, Parks: {theme.get('parks')}")
    logger.debug(f"Road colors - Motorway: {theme.get('road_motorway')}, Primary: {theme.get('road_primary')}")
    
    # Extract data from map_data dictionary
    G = map_data['graph']
    water = map_data['water']
    parks = map_data['parks']
    
    logger.info(f"Map data - Graph edges: {G.number_of_edges()}, Water features: {len(water) if water is not None and not water.empty else 0}, Parks: {len(parks) if parks is not None and not parks.empty else 0}")
    
    # Setup Plot
    if progress_callback:
        progress_callback("initializing")
    
    fig, ax = plt.subplots(figsize=(12, 16), facecolor=theme['bg'])
    ax.set_facecolor(theme['bg'])
    ax.set_position([0, 0, 1, 1])
    
    # Plot Layers
    # Layer 1: Polygons
    if progress_callback:
        progress_callback("plotting_features")
    
    if water is not None and not water.empty:
        logger.info(f"Plotting {len(water)} water features with color {theme['water']}")
        water.plot(ax=ax, facecolor=theme['water'], edgecolor='none', zorder=1)
    else:
        logger.info("No water features to plot")
    
    if parks is not None and not parks.empty:
        logger.info(f"Plotting {len(parks)} park features with color {theme['parks']}")
        parks.plot(ax=ax, facecolor=theme['parks'], edgecolor='none', zorder=2)
    else:
        logger.info("No park features to plot")
    
    # Layer 2: Roads with hierarchy coloring
    if progress_callback:
        progress_callback("plotting_roads")
    
    logger.info(f"Applying road hierarchy colors to {G.number_of_edges()} edges...")
    edge_colors, edge_widths = get_edge_attributes_by_type(G, theme)
    logger.info(f"Generated {len(edge_colors)} edge colors and {len(edge_widths)} edge widths")
    
    ox.plot_graph(
        G, ax=ax, bgcolor=theme['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )
    
    # Layer 3: Gradients (Top and Bottom)
    if progress_callback:
        progress_callback("adding_gradients")
    
    create_gradient_fade(ax, theme['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, theme['gradient_color'], location='top', zorder=10)
    
    # Typography using Roboto font
    if progress_callback:
        progress_callback("adding_typography")
    
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=60)
        font_top = FontProperties(fname=FONTS['bold'], size=40)
        font_sub = FontProperties(fname=FONTS['light'], size=22)
        font_coords = FontProperties(fname=FONTS['regular'], size=14)
    else:
        # Fallback to system fonts
        font_main = FontProperties(family='monospace', weight='bold', size=60)
        font_top = FontProperties(family='monospace', weight='bold', size=40)
        font_sub = FontProperties(family='monospace', weight='normal', size=22)
        font_coords = FontProperties(family='monospace', size=14)
    
    spaced_city = "  ".join(list(city.upper()))

    # --- BOTTOM TEXT ---
    ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
            color=theme['text'], ha='center', fontproperties=font_main, zorder=11)
    
    ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes,
            color=theme['text'], ha='center', fontproperties=font_sub, zorder=11)
    
    lat, lon = point
    coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    if lon < 0:
        coords = coords.replace("E", "W")
    
    ax.text(0.5, 0.07, coords, transform=ax.transAxes,
            color=theme['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)
    
    ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes,
            color=theme['text'], linewidth=1, zorder=11)

    # --- ATTRIBUTION (bottom right) ---
    if FONTS:
        font_attr = FontProperties(fname=FONTS['light'], size=8)
    else:
        font_attr = FontProperties(family='monospace', size=8)
    
    ax.text(0.98, 0.02, "© Aurorass maps", transform=ax.transAxes,
            color=theme['text'], alpha=0.5, ha='right', va='bottom',
            fontproperties=font_attr, zorder=11)

    # Save with appropriate DPI
    if progress_callback:
        progress_callback("saving")
    
    dpi = 150 if preview_mode else 300
    logger.info(f"Saving to {output_file}... (DPI: {dpi})")
    logger.debug(f"Figure background color: {theme['bg']}")
    plt.savefig(output_file, dpi=dpi, facecolor=theme['bg'])
    plt.close()
    logger.info(f"Done! Poster saved as {output_file}")
    
    # Verify file was created and get size
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        logger.info(f"File verified: {file_size / 1024 / 1024:.2f} MB")
    else:
        logger.warning(f"WARNING: File not found after save: {output_file}")


def create_poster(city: str, country: str, point: Tuple[float, float], 
                 dist: int, output_file: str, theme: Dict):
    """
    Create a map poster for the specified city.
    This function maintains backward compatibility by combining fetch and render operations.
    
    Args:
        city: City name
        country: Country name
        point: Tuple of (latitude, longitude)
        dist: Distance in meters for the bounding box
        output_file: Path where the poster will be saved
        theme: Theme dictionary with color and style settings
    """
    logger.info(f"Generating map for {city}, {country}...")
    
    # Fetch map data
    map_data = fetch_map_data(point, dist)
    
    # Render poster
    render_poster(map_data, theme, city, country, point, output_file)