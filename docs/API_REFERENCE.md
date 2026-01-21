# API Reference

Complete reference documentation for all functions in the City Map Poster Generator.

## Table of Contents

- [Core Functions](#core-functions)
  - [get_coordinates](#get_coordinates)
  - [create_poster](#create_poster)
  - [load_theme](#load_theme)
  - [get_available_themes](#get_available_themes)
- [Styling Functions](#styling-functions)
  - [get_edge_colors_by_type](#get_edge_colors_by_type)
  - [get_edge_widths_by_type](#get_edge_widths_by_type)
  - [create_gradient_fade](#create_gradient_fade)
- [Utility Functions](#utility-functions)
  - [load_fonts](#load_fonts)
  - [generate_output_filename](#generate_output_filename)
  - [print_examples](#print_examples)
  - [list_themes](#list_themes)
- [REST API Endpoints](#rest-api-endpoints)
  - [Base URL](#base-url)
  - [Authentication](#authentication)
  - [Response Format](#response-format)
  - [Error Handling](#error-handling)
  - [Theme Endpoints](#theme-endpoints)
  - [Geocoding Endpoints](#geocoding-endpoints)
  - [Poster Endpoints](#poster-endpoints)
  - [Job Status Endpoints](#job-status-endpoints)
  - [Health Check Endpoints](#health-check-endpoints)

---

## Core Functions

### get_coordinates

Fetches geographic coordinates for a given city using the Nominatim geocoding service.

**Location**: [`create_map_poster.py:196-214`](../create_map_poster.py:196)

#### Signature

```python
def get_coordinates(city: str, country: str) -> tuple[float, float]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | str | Yes | City name (e.g., "New York", "Tokyo") |
| `country` | str | Yes | Country name for disambiguation (e.g., "USA", "Japan") |

#### Returns

`tuple[float, float]` - A tuple containing `(latitude, longitude)` as decimal degrees.

#### Raises

- `ValueError`: If the location cannot be found by the geocoding service

#### Behavior

1. Creates Nominatim geocoder with user agent "city_map_poster"
2. Implements 1-second rate limiting (required by Nominatim usage policy)
3. Queries the service with "{city}, {country}" format
4. Prints location details to console upon success
5. Raises error if no results found

#### Example Usage

```python
# Basic usage
coords = get_coordinates("Paris", "France")
print(coords)  # (48.8566, 2.3522)

# Error handling
try:
    coords = get_coordinates("InvalidCity", "NoCountry")
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: Could not find coordinates for InvalidCity, NoCountry
```

#### Rate Limiting

**IMPORTANT**: This function enforces a 1-second delay before making the API request. This is required by Nominatim's [usage policy](https://operations.osmfoundation.org/policies/nominatim/).

#### Edge Cases

- **Ambiguous city names**: Returns the first (most relevant) match
- **Multiple locations with same name**: Country helps disambiguate
- **Special characters**: Handles Unicode city names correctly
- **Network errors**: Will raise exception from underlying library

---

### create_poster

Main orchestrator function that handles the complete poster generation pipeline.

**Location**: [`create_map_poster.py:216-323`](../create_map_poster.py:216)

#### Signature

```python
def create_poster(
    city: str,
    country: str,
    point: tuple[float, float],
    dist: int,
    output_file: str
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | str | Yes | City name for display on poster |
| `country` | str | Yes | Country name for display on poster |
| `point` | tuple | Yes | (latitude, longitude) coordinates |
| `dist` | int | Yes | Bounding box distance in meters from center point |
| `output_file` | str | Yes | Full path for output PNG file |

#### Returns

`None` - Saves poster to disk at `output_file` path

#### Dependencies

**Global Variables**:
- `THEME`: Must be loaded before calling (use [`load_theme()`](#load_theme))
- `FONTS`: Optional, loaded from [`load_fonts()`](#load_fonts)

#### Process Flow

```
1. Data Acquisition (with progress bar)
   ├─ Fetch street network graph
   ├─ Fetch water features (with error handling)
   └─ Fetch parks/green spaces (with error handling)

2. Figure Setup
   ├─ Create 12×16" matplotlib figure
   └─ Apply background color from theme

3. Layer Rendering (z-order)
   ├─ Water polygons (z=1)
   ├─ Park polygons (z=2)
   ├─ Road network with hierarchy coloring (z=3)
   ├─ Gradient fades top/bottom (z=10)
   └─ Typography and metadata (z=11)

4. Export
   └─ Save as PNG at 300 DPI
```

#### Example Usage

```python
# Load theme first
THEME = load_theme("noir")

# Get coordinates
coords = get_coordinates("Barcelona", "Spain")

# Generate output filename
output = generate_output_filename("Barcelona", "noir")

# Create poster
create_poster(
    city="Barcelona",
    country="Spain",
    point=coords,
    dist=8000,  # 8km radius
    output_file=output
)
```

#### Error Handling

**Silent Failures** (graceful degradation):
- Missing water data: Renders without water layer
- Missing parks data: Renders without parks layer

**Fatal Errors** (will raise exception):
- Street network fetch failure
- Matplotlib rendering errors
- File write permission errors

#### Performance Notes

- **Execution Time**: 20-60 seconds depending on city size and network speed
- **Memory Usage**: 500MB-2GB peak (larger for dense cities)
- **Network Calls**: 3 separate OSM API requests with rate limiting

#### Rate Limiting

Includes delays between OSM requests:
- After street network: 0.5 seconds
- After water features: 0.3 seconds

---

### load_theme

Loads theme configuration from a JSON file in the themes directory.

**Location**: [`create_map_poster.py:66-95`](../create_map_poster.py:66)

#### Signature

```python
def load_theme(theme_name: str = "feature_based") -> dict
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `theme_name` | str | No | "feature_based" | Name of theme file (without .json extension) |

#### Returns

`dict` - Theme configuration with the following structure:

```python
{
    "name": str,              # Display name
    "description": str,       # Theme description (optional)
    "bg": str,                # Background color (hex)
    "text": str,              # Text color (hex)
    "gradient_color": str,    # Gradient overlay color (hex)
    "water": str,             # Water bodies color (hex)
    "parks": str,             # Parks/green spaces color (hex)
    "road_motorway": str,     # Motorway color (hex)
    "road_primary": str,      # Primary road color (hex)
    "road_secondary": str,    # Secondary road color (hex)
    "road_tertiary": str,     # Tertiary road color (hex)
    "road_residential": str,  # Residential road color (hex)
    "road_default": str       # Default road color (hex)
}
```

#### Behavior

1. Constructs path: `themes/{theme_name}.json`
2. Attempts to load and parse JSON
3. Prints theme name and description (if available)
4. Falls back to embedded default theme if file not found

#### Example Usage

```python
# Load predefined theme
theme = load_theme("noir")
print(theme['bg'])  # "#000000"

# Load with default
theme = load_theme()  # Uses "feature_based"

# Handle non-existent theme
theme = load_theme("nonexistent")
# Prints warning, returns default theme
```

#### Fallback Behavior

If theme file is not found, returns embedded "feature_based" theme:

```python
{
    "name": "Feature-Based Shading",
    "bg": "#FFFFFF",
    "text": "#000000",
    # ... additional properties
}
```

#### Theme Validation

**No validation performed** - assumes well-formed JSON with required keys. Missing keys will cause errors during rendering.

See [THEME_SYSTEM.md](THEME_SYSTEM.md) for theme creation guidelines.

---

### get_available_themes

Scans the themes directory and returns a list of available theme names.

**Location**: [`create_map_poster.py:51-64`](../create_map_poster.py:51)

#### Signature

```python
def get_available_themes() -> list[str]
```

#### Parameters

None

#### Returns

`list[str]` - Sorted list of theme names (without .json extensions)

#### Behavior

1. Checks if `themes/` directory exists (creates if missing)
2. Scans directory for `.json` files
3. Strips `.json` extension from filenames
4. Returns sorted list alphabetically

#### Example Usage

```python
themes = get_available_themes()
print(themes)
# ['autumn', 'blueprint', 'contrast_zones', 'copper_patina', ...]

# Check if theme exists
if 'noir' in get_available_themes():
    theme = load_theme('noir')
else:
    print("Theme not found")
```

#### Edge Cases

- **Empty directory**: Returns empty list `[]`
- **No .json files**: Returns empty list `[]`
- **Invalid JSON files**: Still included in list (error occurs on load)

---

## Styling Functions

### get_edge_colors_by_type

Assigns colors to road edges based on OpenStreetMap highway classification.

**Location**: [`create_map_poster.py:134-165`](../create_map_poster.py:134)

#### Signature

```python
def get_edge_colors_by_type(G: networkx.MultiDiGraph) -> list[str]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `G` | networkx.MultiDiGraph | Yes | Street network graph from OSMnx |

#### Returns

`list[str]` - List of hex color codes, one per edge in graph order

#### Behavior

Iterates through all edges in the graph and assigns colors based on the `highway` attribute:

**Road Type Hierarchy**:

| OSM Highway Type | Theme Key | Typical Usage |
|------------------|-----------|---------------|
| motorway, motorway_link | `road_motorway` | Interstate highways, freeways |
| trunk, trunk_link, primary, primary_link | `road_primary` | Major roads, arterials |
| secondary, secondary_link | `road_secondary` | Secondary arterials |
| tertiary, tertiary_link | `road_tertiary` | Collector roads |
| residential, living_street, unclassified | `road_residential` | Local streets |
| All others | `road_default` | Catch-all for unusual types |

#### Dependencies

**Global Variables**:
- `THEME`: Must be loaded before calling

#### Example Usage

```python
import osmnx as ox

# Load theme
THEME = load_theme("noir")

# Fetch street network
G = ox.graph_from_point((48.8566, 2.3522), dist=5000, network_type='all')

# Get colors for each edge
colors = get_edge_colors_by_type(G)
print(len(colors))  # Number of edges
print(colors[0])    # "#FFFFFF" (example motorway in noir theme)

# Use with OSMnx plotting
ox.plot_graph(G, edge_color=colors, show=False)
```

#### Edge Case Handling

```python
# Handle list-type highway values
highway = data.get('highway', 'unclassified')
if isinstance(highway, list):
    highway = highway[0] if highway else 'unclassified'
```

**Why**: Some OSM ways have multiple highway classifications (e.g., `["primary", "trunk"]`). The function takes the first (most specific) type.

---

### get_edge_widths_by_type

Assigns line widths to road edges based on road importance.

**Location**: [`create_map_poster.py:167-194`](../create_map_poster.py:167)

#### Signature

```python
def get_edge_widths_by_type(G: networkx.MultiDiGraph) -> list[float]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `G` | networkx.MultiDiGraph | Yes | Street network graph from OSMnx |

#### Returns

`list[float]` - List of line widths in points, one per edge

#### Width Mapping

| Road Type | Width (pts) | Visual Impact |
|-----------|-------------|---------------|
| Motorway | 1.2 | Thickest, most prominent |
| Primary | 1.0 | Major roads |
| Secondary | 0.8 | Medium roads |
| Tertiary | 0.6 | Collector roads |
| Residential/Other | 0.4 | Thinnest, local streets |

#### Example Usage

```python
import osmnx as ox

# Fetch street network
G = ox.graph_from_point((40.7580, -73.9855), dist=3000, network_type='all')

# Get coordinated colors and widths
colors = get_edge_colors_by_type(G)
widths = get_edge_widths_by_type(G)

# Plot with hierarchy
ox.plot_graph(
    G,
    edge_color=colors,
    edge_linewidth=widths,
    show=False
)
```

#### Design Rationale

Width hierarchy creates visual depth:
- Major roads (motorways, highways) appear dominant
- Secondary roads provide structure
- Residential streets add texture without overwhelming

**Scale Independence**: Widths are absolute (not scaled to map), ensuring consistent appearance across different zoom levels.

---

### create_gradient_fade

Creates a smooth alpha-gradient fade effect at the top or bottom of the map.

**Location**: [`create_map_poster.py:100-132`](../create_map_poster.py:100)

#### Signature

```python
def create_gradient_fade(
    ax: matplotlib.axes.Axes,
    color: str,
    location: str = 'bottom',
    zorder: int = 10
) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ax` | matplotlib.axes.Axes | Yes | - | Matplotlib axes to draw on |
| `color` | str | Yes | - | Hex color for gradient (typically matches background) |
| `location` | str | No | 'bottom' | 'top' or 'bottom' |
| `zorder` | int | No | 10 | Layer order (higher = on top) |

#### Returns

`None` - Draws gradient directly on axes

#### Behavior

**Gradient Specifications**:
- **Resolution**: 256 alpha levels for smooth transition
- **Coverage**: 25% of canvas height (from edge)
- **Direction**:
  - Bottom: Alpha 1.0 → 0.0 (solid to transparent)
  - Top: Alpha 0.0 → 1.0 (transparent to solid)

**Implementation Details**:
```python
# Alpha gradient array
if location == 'bottom':
    alphas = np.linspace(1, 0, 256)  # Fade out upward
    y_start, y_end = 0, 0.25
else:  # top
    alphas = np.linspace(0, 1, 256)  # Fade in downward
    y_start, y_end = 0.75, 1.0
```

#### Example Usage

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 16))
ax.set_facecolor('#FFFFFF')

# ... plot map content ...

# Add subtle fade effects
create_gradient_fade(ax, color='#FFFFFF', location='bottom', zorder=10)
create_gradient_fade(ax, color='#FFFFFF', location='top', zorder=10)

plt.savefig('output.png')
```

#### Visual Purpose

Gradient fades serve two purposes:
1. **Aesthetic**: Creates soft transition from map to typography area
2. **Readability**: Reduces visual clutter near text labels

**Best Practice**: Always use the same color as the background for seamless blending.

---

## Utility Functions

### load_fonts

Loads Roboto font files from the fonts directory and verifies their existence.

**Location**: [`create_map_poster.py:18-36`](../create_map_poster.py:18)

#### Signature

```python
def load_fonts() -> dict[str, str] | None
```

#### Parameters

None

#### Returns

- `dict[str, str]` - Dictionary mapping font weights to file paths
- `None` - If any font file is missing

**Dictionary Structure**:
```python
{
    'bold': 'fonts/Roboto-Bold.ttf',
    'regular': 'fonts/Roboto-Regular.ttf',
    'light': 'fonts/Roboto-Light.ttf'
}
```

#### Behavior

1. Constructs paths for three Roboto font files
2. Verifies each file exists
3. Prints warning if any font is missing
4. Returns `None` if incomplete (triggers fallback to system fonts)

#### Example Usage

```python
fonts = load_fonts()

if fonts:
    # Use custom Roboto fonts
    from matplotlib.font_manager import FontProperties
    bold_font = FontProperties(fname=fonts['bold'], size=60)
else:
    # Fallback to system fonts
    bold_font = FontProperties(family='monospace', weight='bold', size=60)
```

#### Fallback Mechanism

If fonts cannot be loaded, [`create_poster()`](#create_poster) falls back to system monospace fonts:

```python
if FONTS:
    font_main = FontProperties(fname=FONTS['bold'], size=60)
else:
    font_main = FontProperties(family='monospace', weight='bold', size=60)
```

---

### generate_output_filename

Generates a unique output filename with timestamp to prevent overwrites.

**Location**: [`create_map_poster.py:39-49`](../create_map_poster.py:39)

#### Signature

```python
def generate_output_filename(city: str, theme_name: str) -> str
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | str | Yes | City name |
| `theme_name` | str | Yes | Theme identifier |

#### Returns

`str` - Full file path in format: `posters/{city_slug}_{theme_name}_{timestamp}.png`

#### Behavior

1. Creates `posters/` directory if it doesn't exist
2. Generates timestamp in format `YYYYMMDD_HHMMSS`
3. Converts city name to slug (lowercase, spaces to underscores)
4. Constructs filename with all components

#### Example Usage

```python
filename = generate_output_filename("New York", "noir")
print(filename)
# Output: posters/new_york_noir_20260119_152530.png

filename = generate_output_filename("São Paulo", "sunset")
print(filename)
# Output: posters/são_paulo_sunset_20260119_152531.png
```

#### Filename Components

**Pattern**: `{city_slug}_{theme_name}_{timestamp}.png`

- **city_slug**: Lowercase city name with spaces → underscores
- **theme_name**: Theme identifier as-is
- **timestamp**: `datetime.now().strftime("%Y%m%d_%H%M%S")`

#### Edge Cases

- **Special characters**: Preserved in slug (e.g., "São Paulo" → "são_paulo")
- **Multiple spaces**: Each space becomes one underscore
- **Rapid calls**: Timestamp resolution (1 second) may cause duplicates if called twice in same second

---

### print_examples

Displays comprehensive usage examples and documentation in the terminal.

**Location**: [`create_map_poster.py:325-379`](../create_map_poster.py:325)

#### Signature

```python
def print_examples() -> None
```

#### Parameters

None

#### Returns

`None` - Prints to stdout

#### Content Sections

1. **Usage syntax**
2. **Example commands by city type**:
   - Grid patterns (NYC, Barcelona)
   - Waterfront cities (Venice, Dubai)
   - Radial patterns (Paris, Moscow)
   - Organic layouts (Tokyo, Marrakech)
   - Coastal cities (San Francisco, Mumbai)
   - River cities (London, Budapest)
3. **Command-line options**
4. **Distance guidelines**
5. **General information**

#### Example Output

```
City Map Poster Generator
=========================

Usage:
  python create_map_poster.py --city <city> --country <country> [options]

Examples:
  # Iconic grid patterns
  python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000
  ...
```

#### When Called

Automatically displayed when:
- No command-line arguments provided
- User needs help/examples

---

### list_themes

Lists all available themes with their display names and descriptions.

**Location**: [`create_map_poster.py:381-404`](../create_map_poster.py:381)

#### Signature

```python
def list_themes() -> None
```

#### Parameters

None

#### Returns

`None` - Prints to stdout

#### Behavior

1. Calls [`get_available_themes()`](#get_available_themes)
2. For each theme:
   - Loads JSON to read metadata
   - Prints theme identifier
   - Prints display name
   - Prints description (if available)
3. Handles JSON parsing errors gracefully

#### Example Output

```
Available Themes:
------------------------------------------------------------
  noir
    Noir
    Pure black background with white/gray roads - modern gallery aesthetic

  blueprint
    Blueprint
    Classic architectural blueprint - technical drawing aesthetic

  warm_beige
    Warm Beige
    Earthy warm neutrals with sepia tones - vintage map aesthetic
```

#### Command-Line Usage

```bash
python create_map_poster.py --list-themes
```

---

## Usage Patterns

### Basic Workflow

```python
# 1. Load theme
THEME = load_theme("noir")

# 2. Get coordinates
coords = get_coordinates("Tokyo", "Japan")

# 3. Generate filename
output = generate_output_filename("Tokyo", "noir")

# 4. Create poster
create_poster(
    city="Tokyo",
    country="Japan",
    point=coords,
    dist=15000,
    output_file=output
)
```

### Error Handling Pattern

```python
try:
    # Validate theme exists
    if theme_name not in get_available_themes():
        print(f"Error: Theme '{theme_name}' not found")
        list_themes()
        exit(1)
    
    # Load theme
    THEME = load_theme(theme_name)
    
    # Geocode
    coords = get_coordinates(city, country)
    
    # Generate poster
    output = generate_output_filename(city, theme_name)
    create_poster(city, country, coords, distance, output)
    
    print(f"Success! Saved to {output}")

except ValueError as e:
    print(f"Geocoding error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()
```

### Custom Styling

```python
import osmnx as ox
import matplotlib.pyplot as plt

# Manual approach for custom requirements
THEME = load_theme("custom_theme")

# Fetch data
G = ox.graph_from_point(coords, dist=10000, network_type='all')

# Get styling
colors = get_edge_colors_by_type(G)
widths = get_edge_widths_by_type(G)

# Custom rendering
fig, ax = plt.subplots(figsize=(12, 16))
ox.plot_graph(
    G,
    ax=ax,
    edge_color=colors,
    edge_linewidth=widths,
    node_size=0,
    show=False
)

# Add custom gradient
create_gradient_fade(ax, THEME['bg'], 'bottom', zorder=10)
```

---

## Best Practices

### Theme Loading

**Always load theme before creating poster**:
```python
# ✅ Correct
THEME = load_theme("noir")
create_poster(...)

# ❌ Wrong - THEME is None
create_poster(...)  # Will crash
```

### Rate Limiting

**Respect API usage policies**:
```python
# ✅ Good - Sequential with delays
for city in cities:
    coords = get_coordinates(city, country)  # Has built-in delay
    time.sleep(1)  # Additional delay between cities
    create_poster(...)

# ❌ Bad - Rapid-fire requests
for city in cities:
    coords = get_coordinates(city, country)
    create_poster(...)  # No delay between iterations
```

### Error Recovery

**Handle partial data gracefully**:
```python
# create_poster() handles missing water/parks automatically
# No need to check for None before calling

create_poster(...)  # Will render without water if fetch fails
```

### Memory Management

**For batch processing**:
```python
import matplotlib.pyplot as plt


---

## REST API Endpoints

The web application provides a RESTful API for programmatic access to poster generation functionality.

### Base URL

**Local Development**: `http://localhost:5000/api/v1`

**Production**: `https://yourdomain.com/api/v1`

### Authentication

**Current**: Session-based (cookie)
- No API key required
- Automatic session creation
- Session stored in secure HTTP-only cookie

**Future**: Optional JWT tokens for API-only access

### Response Format

All API responses use JSON format with consistent structure:

**Success Response**:
```json
{
  "data": { ... },
  "meta": { ... }
}
```

**Error Response**:
```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": { ... }
}
```

### Error Handling

**HTTP Status Codes**:

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET request |
| 201 | Created | Resource successfully created |
| 202 | Accepted | Async operation queued |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Theme Endpoints

#### GET /api/v1/themes

List all available themes.

**Request**:
```bash
GET /api/v1/themes
```

**Response** (200 OK):
```json
{
  "themes": [
    {
      "id": "noir",
      "name": "Noir",
      "description": "Pure black background with white/gray roads",
      "preview_url": "/static/theme-previews/noir.png",
      "colors": {
        "bg": "#000000",
        "text": "#FFFFFF"
      }
    },
    {
      "id": "blueprint",
      "name": "Blueprint",
      "description": "Classic architectural blueprint aesthetic",
      "preview_url": "/static/theme-previews/blueprint.png",
      "colors": {
        "bg": "#0C2340",
        "text": "#FFFFFF"
      }
    }
  ],
  "total": 17
}
```

**Implementation**: [`app/api/themes.py:list_themes()`](../app/api/themes.py)

**Caching**: Results cached in Redis for 1 hour

---

#### GET /api/v1/themes/{theme_id}

Get detailed information about a specific theme.

**Request**:
```bash
GET /api/v1/themes/noir
```

**Response** (200 OK):
```json
{
  "id": "noir",
  "name": "Noir",
  "description": "Pure black background with white/gray roads - modern gallery aesthetic",
  "preview_url": "/static/theme-previews/noir.png",
  "colors": {
    "bg": "#000000",
    "text": "#FFFFFF",
    "gradient_color": "#000000",
    "water": "#0A0A0A",
    "parks": "#111111",
    "road_motorway": "#FFFFFF",
    "road_primary": "#E0E0E0",
    "road_secondary": "#B0B0B0",
    "road_tertiary": "#808080",
    "road_residential": "#505050",
    "road_default": "#808080"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Theme not found",
  "message": "Theme 'invalid_theme' does not exist"
}
```

**Implementation**: [`app/api/themes.py:get_theme()`](../app/api/themes.py)

---

### Geocoding Endpoints

#### GET /api/v1/geocode

Geocode a city name to geographic coordinates.

**Request**:
```bash
GET /api/v1/geocode?city=Paris&country=France
```

**Query Parameters**:
- `city` (required): City name
- `country` (required): Country name

**Response** (200 OK):
```json
{
  "city": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "display_name": "Paris, Île-de-France, France métropolitaine, France",
  "cached": true
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Location not found",
  "message": "Could not geocode 'InvalidCity, NoCountry'"
}
```

**Error Response** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded",
  "message": "Please wait 60 seconds before trying again",
  "retry_after": 60
}
```

**Implementation**: [`app/api/geocoding.py:geocode_location()`](../app/api/geocoding.py)

**Caching**: Results cached in Redis for 30 days

**Rate Limiting**: 10 requests per minute per IP

---

### Poster Endpoints

#### POST /api/v1/posters

Create a new poster generation job.

**Request**:
```bash
POST /api/v1/posters
Content-Type: application/json

{
  "city": "New York",
  "country": "USA",
  "theme": "noir",
  "distance": 12000,
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

**Request Body**:
```json
{
  "city": "string (required, 1-100 chars)",
  "country": "string (required, 1-100 chars)",
  "theme": "string (required, must exist)",
  "distance": "integer (optional, 1000-50000, default: 29000)",
  "latitude": "float (optional, -90 to 90)",
  "longitude": "float (optional, -180 to 180)",
  "preview_mode": "boolean (optional, default: false)"
}
```

**Validation Rules**:
- If `latitude`/`longitude` not provided, automatic geocoding is performed
- `theme` must be valid (use `/themes` endpoint to list)
- `distance` affects map coverage area (meters from center)

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-01-19T15:30:00Z",
  "estimated_duration": 45,
  "status_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Validation error",
  "message": "Invalid distance value",
  "field": "distance",
  "value": 100000
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Theme not found",
  "message": "Theme 'invalid_theme' does not exist",
  "available_themes": ["noir", "sunset", "blueprint", "..."]
}
```

**Implementation**: [`app/api/posters.py:create_poster()`](../app/api/posters.py)

**Next Steps**: Use `/api/v1/jobs/{job_id}` to poll for completion

---

#### GET /api/v1/posters

List generated posters for the current session.

**Request**:
```bash
GET /api/v1/posters?page=1&per_page=20&sort=created_at&order=desc
```

**Query Parameters**:
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 20, max: 100): Items per page
- `sort` (optional, default: created_at): Sort field (created_at, city, theme)
- `order` (optional, default: desc): Sort order (asc, desc)

**Response** (200 OK):
```json
{
  "posters": [
    {
      "id": "abc123",
      "city": "New York",
      "country": "USA",
      "theme": "noir",
      "distance": 12000,
      "created_at": "2026-01-19T15:30:52Z",
      "thumbnail_url": "/api/v1/posters/abc123/thumbnail",
      "preview_url": "/posters/abc123/preview",
      "download_url": "/api/v1/posters/abc123/download",
      "file_size": 15728640
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

**Implementation**: [`app/api/posters.py:list_posters()`](../app/api/posters.py)

---

#### GET /api/v1/posters/{poster_id}

Get detailed information about a specific poster.

**Request**:
```bash
GET /api/v1/posters/abc123
```

**Response** (200 OK):
```json
{
  "id": "abc123",
  "city": "New York",
  "country": "USA",
  "theme": "noir",
  "distance": 12000,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "created_at": "2026-01-19T15:30:52Z",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "new_york_noir_20260119_153052.png",
  "file_size": 15728640,
  "dimensions": {
    "width": 3600,
    "height": 4800,
    "dpi": 300
  },
  "download_url": "/api/v1/posters/abc123/download",
  "thumbnail_url": "/api/v1/posters/abc123/thumbnail",
  "preview_url": "/posters/abc123/preview"
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Poster not found",
  "message": "Poster 'abc123' does not exist"
}
```

**Implementation**: [`app/api/posters.py:get_poster()`](../app/api/posters.py)

---

#### GET /api/v1/posters/{poster_id}/download

Download the full-resolution poster file.

**Request**:
```bash
GET /api/v1/posters/abc123/download
```

**Response** (200 OK):
- **Content-Type**: `image/png`
- **Content-Disposition**: `attachment; filename="new_york_noir_20260119_153052.png"`
- **Content-Length**: File size in bytes
- **Body**: Binary PNG data

**Response Headers**:
```
Content-Type: image/png
Content-Disposition: attachment; filename="new_york_noir_20260119_153052.png"
Content-Length: 15728640
ETag: "abc123-hash"
Cache-Control: public, max-age=31536000
```

**Implementation**: [`app/api/posters.py:download_poster()`](../app/api/posters.py)

---

#### GET /api/v1/posters/{poster_id}/thumbnail

Get a thumbnail preview (400px width) of the poster.

**Request**:
```bash
GET /api/v1/posters/abc123/thumbnail
```

**Response** (200 OK):
- **Content-Type**: `image/jpeg`
- **Body**: Binary JPEG data (400px width, proportional height)

**Implementation**: [`app/api/posters.py:get_thumbnail()`](../app/api/posters.py)

---

#### DELETE /api/v1/posters/{poster_id}

Delete a poster (removes file and database record).

**Request**:
```bash
DELETE /api/v1/posters/abc123
```

**Response** (204 No Content)

**Error Response** (404 Not Found):
```json
{
  "error": "Poster not found",
  "message": "Poster 'abc123' does not exist"
}
```

**Implementation**: [`app/api/posters.py:delete_poster()`](../app/api/posters.py)

---

### Job Status Endpoints

#### GET /api/v1/jobs/{job_id}

Get the current status of a poster generation job.

**Request**:
```bash
GET /api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response - Pending** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": null,
  "completed_at": null,
  "estimated_completion": "2026-01-19T15:31:00Z"
}
```

**Response - Processing** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "current_step": "Downloading water features",
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": "2026-01-19T15:30:05Z",
  "estimated_completion": "2026-01-19T15:31:00Z"
}
```

**Response - Completed** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": "2026-01-19T15:30:05Z",
  "completed_at": "2026-01-19T15:30:52Z",
  "duration": 47,
  "result": {
    "poster_id": "abc123",
    "download_url": "/api/v1/posters/abc123/download",
    "thumbnail_url": "/api/v1/posters/abc123/thumbnail",
    "preview_url": "/posters/abc123/preview",
    "filename": "new_york_noir_20260119_153052.png",
    "file_size": 15728640,
    "dimensions": {
      "width": 3600,
      "height": 4800
    }
  }
}
```

**Response - Failed** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 30,
  "error": "Network timeout",
  "error_message": "Failed to download OSM data for coordinates (40.7128, -74.0060)",
  "created_at": "2026-01-19T15:30:00Z",
  "started_at": "2026-01-19T15:30:05Z",
  "failed_at": "2026-01-19T15:30:35Z",
  "retry_allowed": true
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Job not found",
  "message": "Job '550e8400-e29b-41d4-a716-446655440000' does not exist"
}
```

**Implementation**: [`app/api/jobs.py:get_job_status()`](../app/api/jobs.py)

**Polling Strategy**: Poll every 2-5 seconds until status is `completed` or `failed`

---

#### POST /api/v1/jobs/{job_id}/cancel

Cancel a pending or running poster generation job.

**Request**:
```bash
POST /api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/cancel
```

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Cannot cancel job",
  "message": "Job is already completed"
}
```

**Implementation**: [`app/api/jobs.py:cancel_job()`](../app/api/jobs.py)

---

### Health Check Endpoints

#### GET /api/v1/health

Check the health status of the application and its dependencies.

**Request**:
```bash
GET /api/v1/health
```

**Response - Healthy** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-19T15:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "storage": "healthy"
  }
}
```

**Response - Unhealthy** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2026-01-19T15:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "unhealthy",
    "celery": "unhealthy",
    "storage": "healthy"
  },
  "errors": [
    "Redis connection failed",
    "No Celery workers available"
  ]
}
```

**Implementation**: [`app/api/health.py:health_check()`](../app/api/health.py)

**Use Case**: Monitoring, load balancer health checks

---

### API Usage Examples

#### Complete Workflow Example (Python)

```python
import requests
import time

BASE_URL = "http://localhost:5000/api/v1"

# 1. List available themes
themes_response = requests.get(f"{BASE_URL}/themes")
themes = themes_response.json()['themes']
print(f"Available themes: {[t['id'] for t in themes]}")

# 2. Geocode a city
geocode_response = requests.get(f"{BASE_URL}/geocode", params={
    'city': 'Tokyo',
    'country': 'Japan'
})
location = geocode_response.json()
print(f"Tokyo coordinates: ({location['latitude']}, {location['longitude']})")

# 3. Create poster generation job
poster_request = {
    'city': 'Tokyo',
    'country': 'Japan',
    'theme': 'japanese_ink',
    'distance': 15000,
    'latitude': location['latitude'],
    'longitude': location['longitude']
}

job_response = requests.post(f"{BASE_URL}/posters", json=poster_request)
job = job_response.json()
job_id = job['job_id']
print(f"Job created: {job_id}")

# 4. Poll for completion
while True:
    status_response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    status = status_response.json()
    
    print(f"Status: {status['status']}, Progress: {status.get('progress', 0)}%")
    
    if status['status'] == 'completed':
        print("Poster generation completed!")
        break
    elif status['status'] == 'failed':
        print(f"Poster generation failed: {status['error_message']}")
        break
    
    time.sleep(3)  # Poll every 3 seconds

# 5. Download poster
if status['status'] == 'completed':
    poster_id = status['result']['poster_id']
    download_url = f"{BASE_URL}/posters/{poster_id}/download"
    
    poster_response = requests.get(download_url)
    with open('tokyo_poster.png', 'wb') as f:
        f.write(poster_response.content)
    
    print(f"Poster saved as tokyo_poster.png ({status['result']['file_size']} bytes)")

# 6. List all my posters
posters_response = requests.get(f"{BASE_URL}/posters")
posters = posters_response.json()
print(f"Total posters: {posters['pagination']['total']}")
```

#### Complete Workflow Example (JavaScript)

```javascript
const BASE_URL = 'http://localhost:5000/api/v1';

async function generatePoster(city, country, theme, distance = 29000) {
  try {
    // 1. Geocode city
    const geocodeRes = await fetch(
      `${BASE_URL}/geocode?city=${city}&country=${country}`
    );
    const location = await geocodeRes.json();
    console.log(`Coordinates: ${location.latitude}, ${location.longitude}`);
    
    // 2. Create job
    const jobRes = await fetch(`${BASE_URL}/posters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        city,
        country,
        theme,
        distance,
        latitude: location.latitude,
        longitude: location.longitude
      })
    });
    
    const job = await jobRes.json();
    console.log(`Job created: ${job.job_id}`);
    
    // 3. Poll for completion
    const checkStatus = async () => {
      const statusRes = await fetch(`${BASE_URL}/jobs/${job.job_id}`);
      const status = await statusRes.json();
      
      console.log(`Status: ${status.status}, Progress: ${status.progress}%`);
      
      if (status.status === 'completed') {
        console.log('Completed!', status.result);
        return status.result;
      } else if (status.status === 'failed') {
        throw new Error(status.error_message);
      } else {
        // Continue polling
        await new Promise(resolve => setTimeout(resolve, 2000));
        return checkStatus();
      }
    };
    
    const result = await checkStatus();
    
    // 4. Get download URL
    console.log(`Download: ${BASE_URL}${result.download_url}`);
    return result;
    
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usage
generatePoster('Paris', 'France', 'noir', 12000)
  .then(result => console.log('Poster ready:', result))
  .catch(error => console.error('Failed:', error));
```

#### Complete Workflow Example (curl)

```bash
#!/bin/bash

BASE_URL="http://localhost:5000/api/v1"
CITY="Barcelona"
COUNTRY="Spain"
THEME="warm_beige"
DISTANCE=8000

# 1. Geocode city
echo "Geocoding $CITY, $COUNTRY..."
LOCATION=$(curl -s "${BASE_URL}/geocode?city=${CITY}&country=${COUNTRY}")
LAT=$(echo $LOCATION | jq -r '.latitude')
LON=$(echo $LOCATION | jq -r '.longitude')
echo "Coordinates: $LAT, $LON"

# 2. Create poster job
echo "Creating poster job..."
JOB=$(curl -s -X POST "${BASE_URL}/posters" \
  -H "Content-Type: application/json" \
  -d "{
    \"city\": \"${CITY}\",
    \"country\": \"${COUNTRY}\",
    \"theme\": \"${THEME}\",
    \"distance\": ${DISTANCE},
    \"latitude\": ${LAT},
    \"longitude\": ${LON}
  }")

JOB_ID=$(echo $JOB | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 3. Poll for completion
echo "Waiting for completion..."
while true; do
  STATUS=$(curl -s "${BASE_URL}/jobs/${JOB_ID}")
  STATE=$(echo $STATUS | jq -r '.status')
  PROGRESS=$(echo $STATUS | jq -r '.progress')
  
  echo "Status: $STATE ($PROGRESS%)"
  
  if [ "$STATE" = "completed" ]; then
    echo "Completed!"
    POSTER_ID=$(echo $STATUS | jq -r '.result.poster_id')
    DOWNLOAD_URL="${BASE_URL}/posters/${POSTER_ID}/download"
    break
  elif [ "$STATE" = "failed" ]; then
    echo "Failed: $(echo $STATUS | jq -r '.error_message')"
    exit 1
  fi
  
  sleep 3
done

# 4. Download poster
echo "Downloading poster..."
curl -o "${CITY}_${THEME}.png" "${DOWNLOAD_URL}"
echo "Saved as ${CITY}_${THEME}.png"
```

---

for city in cities:
    create_poster(...)
    plt.close('all')  # Free memory after each poster
    
    # Optional: Garbage collection for large batches
    if i % 10 == 0:
        import gc
        gc.collect()
```

---

## See Also

- [Technical Overview](TECHNICAL_OVERVIEW.md) - Architecture and design
- [Theme System](THEME_SYSTEM.md) - Theme creation guide
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Installation instructions