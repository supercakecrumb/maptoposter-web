#!/usr/bin/env python3
"""
Generate theme preview images for the web gallery.

This script creates small preview posters for all available themes using
a well-known city (Paris) with a small distance for fast generation.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import from root
sys.path.insert(0, str(Path(__file__).parent.parent))

import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
import time

# Configuration
THEMES_DIR = Path("themes")
FONTS_DIR = Path("fonts")
OUTPUT_DIR = Path("app/static/images/themes")
PREVIEW_CITY = "Paris"
PREVIEW_COUNTRY = "France"
PREVIEW_COORDS = (48.8566, 2.3522)  # Paris coordinates
PREVIEW_DISTANCE = 3000  # 3km for fast generation
PREVIEW_SIZE = (4, 6)  # Small size for previews
PREVIEW_DPI = 75  # Lower DPI for web display

def load_fonts():
    """Load Roboto fonts from the fonts directory."""
    fonts = {
        'bold': FONTS_DIR / 'Roboto-Bold.ttf',
        'regular': FONTS_DIR / 'Roboto-Regular.ttf',
        'light': FONTS_DIR / 'Roboto-Light.ttf'
    }
    
    # Verify fonts exist
    for weight, path in fonts.items():
        if not path.exists():
            print(f"⚠ Font not found: {path}")
            return None
    
    return {k: str(v) for k, v in fonts.items()}

def load_theme(theme_path):
    """Load theme from JSON file."""
    try:
        with open(theme_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Error loading theme {theme_path}: {e}")
        return None

def create_gradient_fade(ax, color, location='bottom', zorder=10):
    """Create a fade effect at the top or bottom of the map."""
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

def get_edge_colors_by_type(G, theme):
    """Assign colors to edges based on road type hierarchy."""
    edge_colors = []
    
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']:
            color = theme['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = theme['road_primary']
        elif highway in ['secondary', 'secondary_link']:
            color = theme['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']:
            color = theme['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = theme['road_residential']
        else:
            color = theme['road_default']
        
        edge_colors.append(color)
    
    return edge_colors

def get_edge_widths_by_type(G):
    """Assign line widths to edges based on road type."""
    edge_widths = []
    
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']:
            width = 0.6
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            width = 0.5
        elif highway in ['secondary', 'secondary_link']:
            width = 0.4
        elif highway in ['tertiary', 'tertiary_link']:
            width = 0.3
        else:
            width = 0.2
        
        edge_widths.append(width)
    
    return edge_widths

def generate_preview(theme_name, theme, G, water, parks, fonts, output_path):
    """Generate a single preview poster for a theme."""
    print(f"  Rendering {theme_name}...")
    
    # Setup plot
    fig, ax = plt.subplots(figsize=PREVIEW_SIZE, facecolor=theme['bg'])
    ax.set_facecolor(theme['bg'])
    ax.set_position([0, 0, 1, 1])
    
    # Plot layers
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor=theme['water'], edgecolor='none', zorder=1)
    if parks is not None and not parks.empty:
        parks.plot(ax=ax, facecolor=theme['parks'], edgecolor='none', zorder=2)
    
    # Roads with hierarchy coloring
    edge_colors = get_edge_colors_by_type(G, theme)
    edge_widths = get_edge_widths_by_type(G)
    
    ox.plot_graph(
        G, ax=ax, bgcolor=theme['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )
    
    # Gradients
    create_gradient_fade(ax, theme['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, theme['gradient_color'], location='top', zorder=10)
    
    # Typography (smaller for preview)
    if fonts:
        font_main = FontProperties(fname=fonts['bold'], size=24)
        font_sub = FontProperties(fname=fonts['light'], size=10)
    else:
        font_main = FontProperties(family='monospace', weight='bold', size=24)
        font_sub = FontProperties(family='monospace', size=10)
    
    spaced_city = "  ".join(list(PREVIEW_CITY.upper()))
    
    ax.text(0.5, 0.12, spaced_city, transform=ax.transAxes,
            color=theme['text'], ha='center', fontproperties=font_main, zorder=11)
    
    ax.text(0.5, 0.08, theme.get('name', theme_name).upper(), transform=ax.transAxes,
            color=theme['text'], ha='center', fontproperties=font_sub, zorder=11)
    
    ax.plot([0.4, 0.6], [0.10, 0.10], transform=ax.transAxes, 
            color=theme['text'], linewidth=0.5, zorder=11)
    
    # Save
    plt.savefig(output_path, dpi=PREVIEW_DPI, facecolor=theme['bg'], bbox_inches='tight', pad_inches=0.1)
    plt.close()
    
    print(f"    ✓ Saved: {output_path}")

def main():
    """Generate preview images for all themes."""
    print("=" * 60)
    print("Theme Preview Generator")
    print("=" * 60)
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR}")
    
    # Load fonts
    fonts = load_fonts()
    if not fonts:
        print("⚠ Fonts not found, using system defaults")
    else:
        print("✓ Fonts loaded")
    
    print()
    
    # Get all theme files
    if not THEMES_DIR.exists():
        print(f"✗ Themes directory not found: {THEMES_DIR}")
        return 1
    
    theme_files = sorted(THEMES_DIR.glob("*.json"))
    if not theme_files:
        print(f"✗ No theme files found in {THEMES_DIR}")
        return 1
    
    print(f"Found {len(theme_files)} themes")
    print()
    
    # Fetch map data once (reuse for all themes)
    print(f"Fetching map data for {PREVIEW_CITY}...")
    print(f"  Location: {PREVIEW_COORDS}")
    print(f"  Distance: {PREVIEW_DISTANCE}m")
    
    try:
        # Fetch street network
        print("  Downloading streets...")
        G = ox.graph_from_point(PREVIEW_COORDS, dist=PREVIEW_DISTANCE, 
                                dist_type='bbox', network_type='all')
        time.sleep(0.5)
        
        # Fetch water features
        print("  Downloading water features...")
        try:
            water = ox.features_from_point(PREVIEW_COORDS, 
                                          tags={'natural': 'water', 'waterway': 'riverbank'}, 
                                          dist=PREVIEW_DISTANCE)
        except:
            water = None
        time.sleep(0.3)
        
        # Fetch parks
        print("  Downloading parks...")
        try:
            parks = ox.features_from_point(PREVIEW_COORDS, 
                                          tags={'leisure': 'park', 'landuse': 'grass'}, 
                                          dist=PREVIEW_DISTANCE)
        except:
            parks = None
        
        print("  ✓ Map data downloaded")
        print()
        
    except Exception as e:
        print(f"✗ Error fetching map data: {e}")
        return 1
    
    # Generate previews for each theme
    print(f"Generating previews for {len(theme_files)} themes...")
    print()
    
    success_count = 0
    error_count = 0
    
    for theme_file in theme_files:
        theme_name = theme_file.stem
        output_path = OUTPUT_DIR / f"{theme_name}_preview.png"
        
        print(f"[{success_count + error_count + 1}/{len(theme_files)}] {theme_name}")
        
        # Load theme
        theme = load_theme(theme_file)
        if not theme:
            error_count += 1
            continue
        
        # Generate preview
        try:
            generate_preview(theme_name, theme, G, water, parks, fonts, output_path)
            success_count += 1
        except Exception as e:
            print(f"    ✗ Error: {e}")
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 60)
    print("Generation Complete!")
    print("=" * 60)
    print(f"  Success: {success_count}")
    print(f"  Errors:  {error_count}")
    print(f"  Total:   {len(theme_files)}")
    print()
    print(f"Preview images saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())