# Technical Overview

## Introduction

The City Map Poster Generator is a Python CLI tool that creates high-quality, artistic map posters (12×16 inches at 300 DPI) for any city worldwide. The tool leverages OpenStreetMap data to generate visually stunning map artwork with customizable themes and styling.

## System Architecture

### High-Level Architecture

```
User Input (CLI)
    ↓
Geocoding (Nominatim)
    ↓
OSM Data Fetching (OSMnx)
    ↓
Data Processing & Styling
    ↓
Rendering Pipeline (Matplotlib)
    ↓
PNG Export (300 DPI)
```

### Component Breakdown

1. **Input Layer**: Command-line argument parsing via [`argparse`](create_map_poster.py:407-425)
2. **Geocoding Layer**: City name → coordinates via [`get_coordinates()`](create_map_poster.py:196-214)
3. **Data Acquisition Layer**: OSM data fetching via [`create_poster()`](create_map_poster.py:216-323)
4. **Rendering Layer**: Multi-layer map visualization with themes
5. **Output Layer**: High-resolution PNG export

## Core Technologies

### Primary Dependencies

| Technology | Version | Role |
|------------|---------|------|
| **OSMnx** | 2.0.7 | OpenStreetMap data fetching and graph processing |
| **Matplotlib** | Latest | 2D plotting and rendering engine |
| **GeoPandas** | Latest | Geographic data manipulation |
| **GeoPy** | Latest | Geocoding services (Nominatim) |
| **NumPy** | Latest | Numerical operations for gradients |

### Technology Rationale

- **OSMnx**: Provides a clean Python interface to OSM data with built-in graph simplification
- **Matplotlib**: Industry-standard plotting library with precise control over visual elements
- **GeoPandas**: Simplifies handling of geographic polygons (water bodies, parks)
- **Nominatim**: Free geocoding service with global coverage

## Data Flow

### Complete Pipeline

```
1. INPUT PHASE
   └─ User provides: city, country, theme, distance
   └─ CLI parsing validates inputs

2. GEOCODING PHASE
   └─ get_coordinates() calls Nominatim API
   └─ Returns (latitude, longitude) tuple
   └─ Includes 1-second rate limiting

3. DATA ACQUISITION PHASE
   └─ create_poster() orchestrates three parallel data fetches:
      ├─ Street Network: graph_from_point()
      ├─ Water Features: features_from_point(natural=water)
      └─ Parks: features_from_point(leisure=park, landuse=grass)
   └─ Each fetch includes rate limiting (0.3-0.5s delays)

4. DATA PROCESSING PHASE
   └─ Road Hierarchy Analysis:
      ├─ get_edge_colors_by_type() → assigns colors based on road type
      └─ get_edge_widths_by_type() → assigns line widths
   └─ Theme application via JSON configuration

5. RENDERING PHASE
   └─ Layer-by-layer rendering (z-order):
      ├─ Layer 1: Water polygons (z=1)
      ├─ Layer 2: Park polygons (z=2)
      ├─ Layer 3: Road network (z=3, implicit)
      ├─ Layer 4: Gradient overlays (z=10)
      └─ Layer 5: Typography & metadata (z=11)

6. OUTPUT PHASE
   └─ Save as PNG at 300 DPI
   └─ Filename: {city}_{theme}_{timestamp}.png
```

## Key Functions and Modules

### Core Functions

#### [`get_coordinates(city, country)`](create_map_poster.py:196-214)
**Purpose**: Geocode city names to geographic coordinates

**Parameters**:
- `city` (str): City name
- `country` (str): Country name for disambiguation

**Returns**: `tuple(float, float)` - (latitude, longitude)

**Implementation Details**:
```python
geolocator = Nominatim(user_agent="city_map_poster")
time.sleep(1)  # Rate limiting
location = geolocator.geocode(f"{city}, {country}")
```

**Error Handling**: Raises `ValueError` if location not found

---

#### [`create_poster(city, country, point, dist, output_file)`](create_map_poster.py:216-323)
**Purpose**: Main rendering pipeline orchestrator

**Parameters**:
- `city` (str): City name for display
- `country` (str): Country name for display
- `point` (tuple): (latitude, longitude)
- `dist` (int): Bounding box distance in meters
- `output_file` (str): Output PNG path

**Process Flow**:
1. Fetch OSM data (streets, water, parks)
2. Setup 12×16" matplotlib figure
3. Render layers with z-ordering
4. Apply theme colors and styling
5. Add typography (city name, coordinates, attribution)
6. Export at 300 DPI

---

#### [`load_theme(theme_name)`](create_map_poster.py:66-95)
**Purpose**: Load theme configuration from JSON file

**Parameters**:
- `theme_name` (str): Theme identifier (default: "feature_based")

**Returns**: `dict` with theme properties

**Theme Structure**:
```json
{
  "name": "Display Name",
  "description": "Theme description",
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
```

**Fallback**: Returns embedded default theme if file not found

---

#### [`get_edge_colors_by_type(G)`](create_map_poster.py:134-165)
**Purpose**: Assign colors to road edges based on OSM highway classification

**Parameters**:
- `G` (networkx.MultiDiGraph): Street network graph from OSMnx

**Returns**: `list[str]` - Hex color codes for each edge

**Road Type Mapping**:
```python
motorway/motorway_link        → THEME['road_motorway']
trunk/primary + links         → THEME['road_primary']
secondary + link              → THEME['road_secondary']
tertiary + link               → THEME['road_tertiary']
residential/living_street     → THEME['road_residential']
default                       → THEME['road_default']
```

**Edge Case Handling**:
- Handles list-type highway values (takes first element)
- Gracefully handles missing highway attribute

---

#### [`get_edge_widths_by_type(G)`](create_map_poster.py:167-194)
**Purpose**: Assign line widths to roads based on importance

**Width Hierarchy**:
- Motorways: 1.2 pts
- Primary roads: 1.0 pts
- Secondary roads: 0.8 pts
- Tertiary roads: 0.6 pts
- Minor roads: 0.4 pts

---

#### [`create_gradient_fade(ax, color, location, zorder)`](create_map_poster.py:100-132)
**Purpose**: Create fade-to-background effect at top/bottom edges

**Parameters**:
- `ax` (matplotlib.axes.Axes): Plot axes
- `color` (str): Gradient color (matches background)
- `location` (str): 'top' or 'bottom'
- `zorder` (int): Layer order (typically 10)

**Implementation**:
- Creates 256-level alpha gradient
- Bottom fade: 25% height, alpha 1→0
- Top fade: 25% height, alpha 0→1
- Uses matplotlib imshow with custom colormap

## Data Structures

### Graph Structure (NetworkX MultiDiGraph)
```python
G = ox.graph_from_point(point, dist=dist, ...)

# Node attributes:
{
    'y': latitude,
    'x': longitude,
    'osmid': OpenStreetMap node ID
}

# Edge attributes:
{
    'highway': str or list,  # Road type classification
    'length': float,         # Length in meters
    'osmid': int or list,    # OSM way ID(s)
    'geometry': LineString   # Shapely geometry
}
```

### GeoDataFrame Structure (Water/Parks)
```python
water = ox.features_from_point(point, tags={'natural': 'water'}, ...)

# Columns:
- geometry: Polygon or MultiPolygon (Shapely)
- osmid: OSM feature ID
- natural: 'water'
- name: Optional feature name
```

## API Integrations

### Nominatim Geocoding API

**Endpoint**: `https://nominatim.openstreetmap.org/search`

**Usage via GeoPy**:
```python
geolocator = Nominatim(user_agent="city_map_poster")
location = geolocator.geocode("Paris, France")
# Returns: Location object with lat/lon
```

**Rate Limiting**: 1 request per second (enforced via `time.sleep(1)`)

**Error Scenarios**:
- City not found → Returns `None`
- Ambiguous location → Returns best match
- Network error → Raises exception

---

### OpenStreetMap Overpass API (via OSMnx)

**Queries Executed**:

1. **Street Network**:
```python
G = ox.graph_from_point(
    point=(lat, lon),
    dist=29000,              # Bounding box distance (meters)
    dist_type='bbox',        # Square bounding box
    network_type='all'       # All road types
)
```

2. **Water Features**:
```python
water = ox.features_from_point(
    point=(lat, lon),
    tags={'natural': 'water', 'waterway': 'riverbank'},
    dist=29000
)
```

3. **Parks/Green Spaces**:
```python
parks = ox.features_from_point(
    point=(lat, lon),
    tags={'leisure': 'park', 'landuse': 'grass'},
    dist=29000
)
```

**OSMnx Benefits**:
- Automatic retry logic
- Response caching (session-level)
- Graph simplification
- Coordinate system handling

**Rate Limiting**: 0.3-0.5 second delays between requests

## Rendering Pipeline

### Layer Order and Z-Index

```
Z=11: Typography (city name, coords, attribution)
Z=10: Gradient fades (top & bottom 25%)
Z=3:  Road network (implicit from ox.plot_graph)
Z=2:  Parks/green spaces (polygons)
Z=1:  Water bodies (polygons)
Z=0:  Background (figure facecolor)
```

### Typography System

**Font Family**: Roboto (loaded from `fonts/` directory)

**Text Elements**:
1. **City Name**: 
   - Font: Roboto Bold, 60pt
   - Position: Center, 14% from bottom
   - Spacing: 2 spaces between letters
   - Case: UPPERCASE

2. **Country Name**:
   - Font: Roboto Light, 22pt
   - Position: Center, 10% from bottom
   - Case: UPPERCASE

3. **Coordinates**:
   - Font: Roboto Regular, 14pt
   - Position: Center, 7% from bottom
   - Format: `XX.XXXX° N/S / XX.XXXX° E/W`
   - Alpha: 0.7

4. **Decorative Line**:
   - Position: Between city and country (12.5% from bottom)
   - Width: 20% of canvas
   - Color: Theme text color

5. **Attribution**:
   - Font: Roboto Light, 8pt
   - Position: Bottom-right (2% from edges)
   - Text: "© OpenStreetMap contributors"
   - Alpha: 0.5

### Canvas Specifications

- **Dimensions**: 12 × 16 inches (portrait orientation)
- **Resolution**: 300 DPI (3600 × 4800 pixels)
- **Color Space**: RGB
- **File Format**: PNG (lossless)
- **Axis Frame**: Hidden (frameless design)

## Performance Considerations

### Time Complexity

**Total Generation Time**: ~20-60 seconds

**Breakdown by Phase**:
- Geocoding: ~1-2 seconds
- Data fetching: ~10-30 seconds (network-dependent)
  - Street network: 5-15 seconds
  - Water features: 2-8 seconds
  - Parks: 2-7 seconds
- Rendering: ~5-15 seconds (CPU-bound)
- Export: ~2-5 seconds (disk I/O)

### Memory Usage

**Peak Memory**: ~500 MB - 2 GB (varies by city complexity)

**Memory Hotspots**:
1. OSM graph storage (street networks for large cities)
2. Matplotlib figure buffer at 300 DPI
3. GeoDataFrame polygon geometries

**Memory Optimization Opportunities**:
- Implement graph simplification thresholds
- Stream rendering for very large cities
- Compress intermediate data structures

### Network Dependencies

**Critical Dependencies**:
- Nominatim API availability
- Overpass API availability
- Stable internet connection

**Failure Modes**:
- Geocoding timeout → Retry or manual coordinate entry
- OSM data fetch failure → Partial rendering or abort
- Rate limit exceeded → Extended wait times

### Bottlenecks

1. **Network I/O**: OSM data fetching dominates execution time
2. **CPU**: Matplotlib rendering for dense street networks
3. **Disk I/O**: PNG export at 300 DPI

**Optimization Strategies**:
- Implement local caching (sqlite/file-based)
- Reduce DPI for preview mode
- Parallelize water/park fetching
- Use vector formats (SVG) for intermediate output

## File Output

### Filename Convention

**Pattern**: `{city_slug}_{theme_name}_{timestamp}.png`

**Example**: `new_york_noir_20260108_164217.png`

**Directory**: `posters/` (auto-created if missing)

### Output Characteristics

- **Format**: PNG (Portable Network Graphics)
- **Compression**: Default PNG compression (lossless)
- **Metadata**: Embedded color profile (sRGB)
- **File Size**: 5-25 MB (varies by city density)

## Error Handling

### Common Error Scenarios

1. **City Not Found**:
```python
ValueError: Could not find coordinates for {city}, {country}
```
**Solution**: Check spelling, try alternate city names

2. **Theme Not Found**:
```python
Error: Theme 'invalid_theme' not found.
Available themes: feature_based, noir, ...
```
**Solution**: Use `--list-themes` to see available options

3. **No OSM Data**:
```python
# Silent failure - empty GeoDataFrame
# Renders map without water/parks
```
**Detection**: Check for warning messages during data fetch

4. **Font Missing**:
```python
⚠ Font not found: fonts/Roboto-Bold.ttf
# Fallback to system monospace fonts
```

## Configuration

### Constants

Defined at module level in [`create_map_poster.py`](create_map_poster.py:14-16):

```python
THEMES_DIR = "themes"      # Theme JSON files
FONTS_DIR = "fonts"        # Roboto font files
POSTERS_DIR = "posters"    # Output directory
```

### Default Values

- **Theme**: `feature_based`
- **Distance**: `29000` meters (~18 miles)
- **Network Type**: `all` (includes all road types)
- **DPI**: `300` (print quality)

## Extension Points

### Adding New Themes

1. Create JSON file in `themes/` directory
2. Follow theme schema (see [THEME_SYSTEM.md](THEME_SYSTEM.md))
3. Theme automatically appears in `--list-themes`

### Adding New Features

**Potential OSM Feature Tags**:
- Buildings: `{'building': True}`
- Railways: `{'railway': True}`
- Landuse: `{'landuse': 'residential'}`
- Natural features: `{'natural': 'wood'}`

**Implementation Pattern**:
```python
buildings = ox.features_from_point(
    point, 
    tags={'building': True}, 
    dist=dist
)
buildings.plot(ax=ax, facecolor='#EEEEEE', zorder=1.5)
```

### Custom Renderers

Extend [`create_poster()`](create_map_poster.py:216-323) to support:
- Custom aspect ratios
- Multi-city collages
- Animated zoom sequences
- Interactive HTML output

## Dependencies Graph

```
create_map_poster.py
├── osmnx (2.0.7)
│   ├── networkx
│   ├── geopandas
│   ├── shapely
│   └── requests (Overpass API)
├── matplotlib
│   ├── numpy
│   └── PIL/pillow
├── geopy
│   └── requests (Nominatim API)
├── geopandas
│   ├── pandas
│   ├── shapely
│   └── pyproj
└── tqdm (progress bars)
```

Full dependency list: See [`requirements.txt`](requirements.txt)

## See Also

- [API Reference](API_REFERENCE.md) - Detailed function documentation
- [Theme System](THEME_SYSTEM.md) - Theme creation and customization
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Installation and setup
- [Future Agents Guide](FUTURE_AGENTS.md) - AI agent development reference