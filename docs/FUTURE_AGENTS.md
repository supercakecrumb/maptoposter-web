# Future Agents Guide

**Purpose**: This document is specifically designed for AI agents (like yourself) who will be working on this codebase. It provides essential context, insights, and guidance to help you understand the project quickly and make effective contributions.

## Table of Contents

- [Project Overview](#project-overview)
- [Codebase Mental Model](#codebase-mental-model)
- [Code Organization](#code-organization)
- [Key Implementation Patterns](#key-implementation-patterns)
- [Where to Find Functionality](#where-to-find-functionality)
- [Known Limitations](#known-limitations)
- [Enhancement Opportunities](#enhancement-opportunities)
- [Testing Strategies](#testing-strategies)
- [Common Modification Patterns](#common-modification-patterns)
- [Gotchas and Edge Cases](#gotchas-and-edge-cases)

---

## Project Overview

### What This Project Does

Generates high-quality artistic map posters (12×16", 300 DPI PNG) for any city worldwide using OpenStreetMap data. The tool is designed for print-quality artwork, not navigation.

**Core Value Proposition**: Transform any city's street network into beautiful wall art with minimal user input.

### Key Design Decisions

1. **Single-file architecture**: All logic in [`create_map_poster.py`](../create_map_poster.py) (471 lines)
   - **Rationale**: Simplicity, easy distribution, no package management overhead
   - **Tradeoff**: Limited modularity, harder to test individual components

2. **CLI-only interface**: No GUI or web interface
   - **Rationale**: Focus on core functionality, scriptable, batch processing friendly
   - **Opportunity**: Web interface would expand accessibility

3. **JSON-based themes**: External theme files instead of hardcoded styles
   - **Rationale**: User customization without code changes
   - **Strength**: Easy to add new themes, share community themes

4. **Fixed canvas size**: 12×16" portrait orientation
   - **Rationale**: Standard poster size, optimized typography layout
   - **Limitation**: No landscape or custom dimensions support

5. **No caching**: Re-downloads OSM data on every run
   - **Rationale**: Simplicity, always fresh data
   - **Limitation**: Slow, wastes bandwidth, API rate limiting issues

### Technical Stack Rationale

| Technology | Why Chosen | Alternative Considered |
|------------|------------|------------------------|
| **OSMnx** | Simplifies OSM API interaction, graph operations | Direct Overpass API calls (too complex) |
| **Matplotlib** | Full control over rendering, publication-quality output | Plotly (interactive, not print-focused), Pillow (too low-level) |
| **GeoPandas** | Standard for geographic polygons in Python | Shapely alone (more manual work) |
| **Nominatim** | Free, no API key required, good coverage | Google Maps API (requires key, costs money) |

---

## Codebase Mental Model

### Execution Flow

```
┌─────────────┐
│ CLI Input   │ (argparse)
└──────┬──────┘
       ↓
┌─────────────┐
│ Load Theme  │ (load_theme)
└──────┬──────┘
       ↓
┌─────────────┐
│ Geocode     │ (get_coordinates)
└──────┬──────┘
       ↓
┌─────────────────┐
│ Fetch OSM Data  │ (create_poster)
│  • Streets      │
│  • Water        │
│  • Parks        │
└──────┬──────────┘
       ↓
┌─────────────────┐
│ Style Data      │ (get_edge_colors/widths)
└──────┬──────────┘
       ↓
┌─────────────────┐
│ Render Layers   │ (matplotlib + OSMnx)
└──────┬──────────┘
       ↓
┌─────────────────┐
│ Add Typography  │ (city name, coords, etc.)
└──────┬──────────┘
       ↓
┌─────────────────┐
│ Export PNG      │ (savefig)
└─────────────────┘
```

### Data Flow

```
City Name (str)
    ↓ get_coordinates()
(lat, lon) tuple
    ↓ ox.graph_from_point()
NetworkX MultiDiGraph
    ↓ get_edge_colors_by_type()
List of hex colors (per edge)
    ↓ ox.plot_graph()
Matplotlib axes with rendered streets
    ↓ + water, parks, gradients, text
Complete matplotlib figure
    ↓ plt.savefig()
PNG file on disk
```

---

## Code Organization

### File Structure

```
maptoposter-web/
├── create_map_poster.py          # 471 lines - ALL logic here
├── requirements.txt              # 29 dependencies
├── README.md                     # User-facing documentation
├── LICENSE                       # Project license
├── docs/                         # Comprehensive documentation
│   ├── TECHNICAL_OVERVIEW.md     # Architecture deep-dive
│   ├── API_REFERENCE.md          # Function reference
│   ├── THEME_SYSTEM.md           # Theme creation guide
│   ├── DEPLOYMENT_GUIDE.md       # Installation instructions
│   └── FUTURE_AGENTS.md          # This file
├── themes/                       # 17 theme JSON files
├── fonts/                        # 3 Roboto TTF files
└── posters/                      # Output directory (auto-created)
```

### Code Sections (create_map_poster.py)

| Lines | Section | Purpose |
|-------|---------|---------|
| 1-12 | Imports | All external dependencies |
| 14-16 | Constants | Directory paths |
| 18-36 | Font Loading | `load_fonts()` |
| 39-49 | Filename Generation | `generate_output_filename()` |
| 51-64 | Theme Discovery | `get_available_themes()` |
| 66-95 | Theme Loading | `load_theme()` |
| 100-132 | Gradient Effect | `create_gradient_fade()` |
| 134-165 | Road Coloring | `get_edge_colors_by_type()` |
| 167-194 | Road Widths | `get_edge_widths_by_type()` |
| 196-214 | Geocoding | `get_coordinates()` |
| 216-323 | Main Pipeline | `create_poster()` |
| 325-379 | Help Text | `print_examples()` |
| 381-404 | Theme Listing | `list_themes()` |
| 406-471 | CLI Entry Point | `if __name__ == "__main__"` |

---

## Key Implementation Patterns

### Pattern 1: Global Theme State

```python
THEME = None  # Global variable, loaded in main()
```

**Implication**: Functions like `get_edge_colors_by_type()` depend on global `THEME` being set first.

**When modifying**: Ensure `THEME` is loaded before calling functions that reference it.

### Pattern 2: Graceful Degradation

```python
try:
    water = ox.features_from_point(...)
except:
    water = None

# Later...
if water is not None and not water.empty:
    water.plot(...)  # Only render if available
```

**Pattern**: Try to fetch features, but continue if they fail. Renders partial map instead of crashing.

**When adding features**: Follow this pattern for robustness.

### Pattern 3: Z-Order Layering

```python
water.plot(ax=ax, zorder=1)      # Bottom layer
parks.plot(ax=ax, zorder=2)      # Above water
ox.plot_graph(..., zorder=3)     # Roads (implicit)
create_gradient_fade(zorder=10)  # Above map content
ax.text(..., zorder=11)          # Typography on top
```

**Critical**: Higher z-order = rendered on top. Maintain this hierarchy when adding layers.

### Pattern 4: Edge Attribute Handling

```python
highway = data.get('highway', 'unclassified')
if isinstance(highway, list):
    highway = highway[0] if highway else 'unclassified'
```

**Why**: OSM highway tags can be single string or list. Must handle both.

**When working with edges**: Always check for list type.

### Pattern 5: Progress Feedback

```python
with tqdm(total=3, desc="Fetching map data") as pbar:
    # Fetch data
    pbar.update(1)
    # More fetching
    pbar.update(1)
```

**Pattern**: Use tqdm for user feedback during slow operations. Updates progress bar in console.

---

## Where to Find Functionality

### "How do I...?"

#### Change road styling?

→ [`get_edge_colors_by_type()`](../create_map_poster.py:134) for colors
→ [`get_edge_widths_by_type()`](../create_map_poster.py:167) for widths

**Example modification**:
```python
def get_edge_widths_by_type(G):
    for u, v, data in G.edges(data=True):
        # Change width logic here
        if highway == 'motorway':
            width = 2.0  # Make motorways thicker
```

#### Add a new map feature (e.g., buildings)?

→ [`create_poster()`](../create_map_poster.py:216), after parks fetch (line ~240)

**Example**:
```python
# After parks fetch
try:
    buildings = ox.features_from_point(point, tags={'building': True}, dist=dist)
except:
    buildings = None

# After parks plot (around line 257)
if buildings is not None and not buildings.empty:
    buildings.plot(ax=ax, facecolor=THEME['buildings'], zorder=2.5)
```

Don't forget to add `"buildings": "#EEEEEE"` to theme JSON schema.

#### Change output format (SVG instead of PNG)?

→ [`create_poster()`](../create_map_poster.py:321), line `plt.savefig(...)`

**Example**:
```python
# Change extension in generate_output_filename()
filename = f"{city_slug}_{theme_name}_{timestamp}.svg"

# In create_poster()
plt.savefig(output_file, format='svg', dpi=300)
```

#### Add custom fonts?

→ [`load_fonts()`](../create_map_poster.py:18) and [`create_poster()`](../create_map_poster.py:277-287)

**Example**:
```python
def load_fonts():
    fonts = {
        'bold': 'fonts/CustomFont-Bold.ttf',
        'regular': 'fonts/CustomFont-Regular.ttf',
        'light': 'fonts/CustomFont-Light.ttf'
    }
    return fonts
```

#### Implement caching?

→ [`get_coordinates()`](../create_map_poster.py:196) for geocoding cache
→ [`create_poster()`](../create_map_poster.py:220-243) for OSM data cache

**Example geocoding cache**:
```python
import shelve

def get_coordinates(city, country):
    cache_key = f"{city}_{country}"
    with shelve.open('cache/geocode') as cache:
        if cache_key in cache:
            return cache[cache_key]
        
        # Normal geocoding logic...
        coords = (location.latitude, location.longitude)
        cache[cache_key] = coords
        return coords
```

#### Change canvas size or orientation?

→ [`create_poster()`](../create_map_poster.py:248), line `figsize=(12, 16)`

**Example landscape**:
```python
fig, ax = plt.subplots(figsize=(16, 12), ...)  # Landscape
# Also adjust typography positions in transAxes coordinates
```

---

## Known Limitations

### Technical Limitations

1. **No Caching**
   - **Impact**: Every run downloads ~5-20 MB from OSM APIs
   - **Consequence**: Slow execution, API rate limiting, network dependency
   - **Workaround**: Manual coordinate caching (see [enhancement opportunities](#enhancement-opportunities))

2. **Single-Threaded**
   - **Impact**: Water and parks fetched sequentially
   - **Opportunity**: Parallel fetching could reduce time by 30-50%

3. **Fixed Canvas Size**
   - **Impact**: Only 12×16" portrait orientation supported
   - **Consequence**: Limited use cases (no square prints, no landscape)

4. **No Preview Mode**
   - **Impact**: Must wait for full 300 DPI render to see result
   - **Workaround**: User can manually reduce DPI in code for testing

5. **Memory Intensive**
   - **Impact**: Large cities (Mumbai, Tokyo) can use 1-2 GB RAM
   - **Consequence**: May crash on low-memory systems

### API Limitations

1. **Nominatim Rate Limiting**
   - **Limit**: 1 request per second
   - **Enforcement**: Built-in `time.sleep(1)` in [`get_coordinates()`](../create_map_poster.py:205)
   - **Impact**: Batch processing is slow

2. **Overpass API Rate Limiting**
   - **Limit**: Not explicitly documented, but exists
   - **OSMnx handles**: Automatic retry with exponential backoff
   - **Impact**: Occasional timeouts for large cities

### Design Limitations

1. **CLI Only**
   - **Impact**: Not accessible to non-technical users
   - **Opportunity**: Web interface would expand audience

2. **Limited Feature Types**
   - **Current**: Only roads, water, parks
   - **Missing**: Buildings, railways, landuse, points of interest
   - **Reason**: Keeps rendering simple and fast

3. **No Error Recovery**
   - **Impact**: Failed renders leave no partial output
   - **Opportunity**: Save progress/checkpoints

---

## Enhancement Opportunities

### High-Impact Enhancements

#### 1. Implement Caching System

**Impact**: 10x faster repeat renders, reduced API load

**Implementation**:
```python
import sqlite3
import hashlib
import pickle

class OSMCache:
    def __init__(self, db_path='cache/osm.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS graphs (
                key TEXT PRIMARY KEY,
                data BLOB,
                timestamp INTEGER
            )
        ''')
    
    def get_graph(self, point, dist):
        key = hashlib.md5(f"{point}_{dist}".encode()).hexdigest()
        cursor = self.conn.execute(
            "SELECT data FROM graphs WHERE key = ?", (key,)
        )
        result = cursor.fetchone()
        return pickle.loads(result[0]) if result else None
    
    def save_graph(self, point, dist, graph):
        key = hashlib.md5(f"{point}_{dist}".encode()).hexdigest()
        data = pickle.dumps(graph)
        self.conn.execute(
            "INSERT OR REPLACE INTO graphs VALUES (?, ?, ?)",
            (key, data, int(time.time()))
        )
        self.conn.commit()
```

**Usage in create_poster()**:
```python
cache = OSMCache()
cached_graph = cache.get_graph(point, dist)

if cached_graph:
    G = cached_graph
else:
    G = ox.graph_from_point(point, dist=dist, network_type='all')
    cache.save_graph(point, dist, G)
```

**Tradeoffs**:
- ✅ Massive speed improvement
- ✅ Reduced API calls
- ❌ Stale data (consider TTL)
- ❌ Disk space usage
- ❌ Increased complexity

---

#### 2. Add Web Interface

**Impact**: Makes tool accessible to non-developers

**Tech Stack Suggestion**:
- **Backend**: Flask or FastAPI
- **Frontend**: Simple HTML form
- **Job Queue**: Celery for async poster generation
- **Storage**: S3 or local filesystem

**Minimal Flask Example**:
```python
from flask import Flask, request, send_file
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return '''
        <form method="POST" action="/generate">
            City: <input name="city"><br>
            Country: <input name="country"><br>
            Theme: <select name="theme">
                <option>noir</option>
                <option>blueprint</option>
            </select><br>
            <button type="submit">Generate</button>
        </form>
    '''

@app.route('/generate', methods=['POST'])
def generate():
    city = request.form['city']
    country = request.form['country']
    theme = request.form['theme']
    
    # Load theme
    THEME = load_theme(theme)
    
    # Generate poster in background thread
    output = generate_output_filename(city, theme)
    
    def generate_poster_async():
        coords = get_coordinates(city, country)
        create_poster(city, country, coords, 29000, output)
    
    thread = threading.Thread(target=generate_poster_async)
    thread.start()
    
    return f"Generating poster... Check {output} in a few minutes."

if __name__ == '__main__':
    app.run(debug=True)
```

---

#### 3. Add Preview Mode

**Impact**: Faster iteration, better UX

**Implementation**:
```python
def create_poster(..., preview=False):
    # Reduce DPI and distance for preview
    if preview:
        dpi = 72  # Screen resolution
        dist = dist // 2  # Half the area
    else:
        dpi = 300  # Print resolution
    
    # ... rest of function
    
    plt.savefig(output_file, dpi=dpi, facecolor=THEME['bg'])
```

**CLI Addition**:
```python
parser.add_argument('--preview', action='store_true', help='Fast low-res preview')
```

---

### Medium-Impact Enhancements

#### 4. Support Custom Canvas Sizes

**Implementation**:
```python
def create_poster(..., width=12, height=16):
    fig, ax = plt.subplots(figsize=(width, height), ...)
    
    # Scale typography based on canvas size
    font_scale = (width + height) / 28  # 28 = 12 + 16 default
    font_main = FontProperties(fname=FONTS['bold'], size=60 * font_scale)
```

#### 5. Add More Feature Types

**Examples to add**:
- Buildings: `{'building': True}`
- Railways: `{'railway': 'rail'}`
- Coastline: `{'natural': 'coastline'}`
- Landuse: `{'landuse': 'residential'}`

**Pattern**:
```python
try:
    buildings = ox.features_from_point(point, tags={'building': True}, dist=dist)
except:
    buildings = None

if buildings is not None and not buildings.empty:
    buildings.plot(ax=ax, facecolor=THEME['buildings'], zorder=1.5)
```

#### 6. Batch Processing Support

**Implementation**:
```python
# batch_generate.py
import csv

with open('cities.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        city, country, theme = row['city'], row['country'], row['theme']
        THEME = load_theme(theme)
        coords = get_coordinates(city, country)
        output = generate_output_filename(city, theme)
        create_poster(city, country, coords, 29000, output)
        time.sleep(5)  # Rate limiting
```

---

### Low-Impact / Nice-to-Have

7. **Export SVG format** (scalable vector graphics)
8. **Custom color ramps** (gradient generation)
9. **Metadata embedding** (EXIF data in PNG)
10. **Multi-language support** (internationalization)

---

## Testing Strategies

### Unit Testing Approach

**Challenges**:
- Single-file architecture makes isolation difficult
- External API dependencies (Nominatim, Overpass)
- Large data structures (NetworkX graphs)

**Strategy**: Test pure functions first, mock API calls

**Example test file** (`tests/test_map_poster.py`):

```python
import unittest
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, '..')
from create_map_poster import *

class TestThemeLoading(unittest.TestCase):
    def test_load_valid_theme(self):
        theme = load_theme('noir')
        self.assertEqual(theme['bg'], '#000000')
        self.assertEqual(theme['text'], '#FFFFFF')
    
    def test_load_invalid_theme_returns_default(self):
        theme = load_theme('nonexistent_theme')
        self.assertEqual(theme['name'], 'Feature-Based Shading')

class TestFilenameGeneration(unittest.TestCase):
    def test_generate_filename_format(self):
        filename = generate_output_filename("New York", "noir")
        self.assertTrue(filename.startswith('posters/new_york_noir_'))
        self.assertTrue(filename.endswith('.png'))
    
    def test_spaces_replaced_with_underscores(self):
        filename = generate_output_filename("San Francisco", "blueprint")
        self.assertIn('san_francisco', filename)

class TestRoadStyling(unittest.TestCase):
    @patch('create_map_poster.THEME', {'road_motorway': '#FF0000'})
    def test_motorway_color_assignment(self):
        # Create mock graph
        G = Mock()
        G.edges.return_value = [
            (1, 2, {'highway': 'motorway'}),
            (2, 3, {'highway': 'residential'})
        ]
        
        colors = get_edge_colors_by_type(G)
        self.assertEqual(colors[0], '#FF0000')

if __name__ == '__main__':
    unittest.main()
```

**Run tests**:
```bash
python -m pytest tests/
```

---

### Integration Testing

**Test End-to-End Flow**:

```python
# tests/test_integration.py
import os
import unittest
from create_map_poster import *

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        global THEME
        THEME = load_theme('noir')
    
    def test_small_city_generation(self):
        """Test with small, fast city (Venice)"""
        coords = get_coordinates("Venice", "Italy")
        output = "test_output.png"
        
        create_poster("Venice", "Italy", coords, 4000, output)
        
        # Verify output exists
        self.assertTrue(os.path.exists(output))
        
        # Verify reasonable file size (5-20 MB)
        size_mb = os.path.getsize(output) / (1024 * 1024)
        self.assertGreater(size_mb, 2)
        self.assertLess(size_mb, 30)
        
        # Cleanup
        os.remove(output)
```

---

### Manual Testing Checklist

Before releasing changes:

- [ ] Test with **grid city** (New York, Chicago) - validates line rendering
- [ ] Test with **organic city** (Tokyo, London) - validates density handling
- [ ] Test with **coastal city** (San Francisco, Sydney) - validates water rendering
- [ ] Test with **small city** (Venice, Bruges) - validates feature visibility
- [ ] Test with **all 17 themes** - ensures theme compatibility
- [ ] Test with **invalid input** - error handling
- [ ] Test with **very large distance** (40km+) - memory/performance limits

---

## Common Modification Patterns

### Adding a New Theme

1. **Create JSON file**: `themes/my_theme.json`
2. **Follow schema**: Use existing themes as template
3. **Test rendering**: Generate poster with new theme
4. **Document**: Add to theme list in README

**Example**:
```json
{
  "name": "My Custom Theme",
  "description": "Brief description",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#B0E0E6",
  "parks": "#90EE90",
  "road_motorway": "#000000",
  "road_primary": "#1A1A1A",
  "road_secondary": "#333333",
  "road_tertiary": "#4D4D4D",
  "road_residential": "#666666",
  "road_default": "#4D4D4D"
}
```

---

### Modifying Typography

**Location**: [`create_poster()`](../create_map_poster.py:289-307)

**Current positions** (in `transAxes` coordinates, 0-1 scale):
- City name: `y=0.14`
- Decorative line: `y=0.125`
- Country: `y=0.10`
- Coordinates: `y=0.07`

**Example modification** (add subtitle):
```python
ax.text(0.5, 0.11, "CUSTOM SUBTITLE", transform=ax.transAxes,
        color=THEME['text'], ha='center', fontproperties=font_sub, 
        alpha=0.8, zorder=11)
```

---

### Adding CLI Arguments

**Location**: [`if __name__ == "__main__"`](../create_map_poster.py:406-471)

**Pattern**:
```python
parser.add_argument('--new-option', '-n', 
                    type=str, 
                    default='default_value',
                    help='Description of what this does')

# Access in code
args = parser.parse_args()
new_value = args.new_option
```

**Example** (add DPI control):
```python
parser.add_argument('--dpi', type=int, default=300, 
                    help='Output resolution (default: 300)')

# In create_poster()
plt.savefig(output_file, dpi=args.dpi, facecolor=THEME['bg'])
```

---

## Gotchas and Edge Cases

### 1. Highway Tag as List

**Problem**: OSM highway tags can be `str` or `list[str]`

```python
# Wrong - will crash on lists
color = THEME[f'road_{highway}']

# Correct - handles both cases
if isinstance(highway, list):
    highway = highway[0] if highway else 'unclassified'
color = THEME[f'road_{highway}']
```

### 2. Empty GeoDataFrames

**Problem**: `ox.features_from_point()` may return empty GeoDataFrame or raise exception

```python
# Wrong - may crash
water.plot(ax=ax, facecolor=THEME['water'])

# Correct - check existence and non-empty
if water is not None and not water.empty:
    water.plot(ax=ax, facecolor=THEME['water'], zorder=1)
```

### 3. Global THEME Dependency

**Problem**: Functions assume `THEME` is loaded globally

```python
# Wrong - will crash if THEME not loaded
colors = get_edge_colors_by_type(G)

# Correct - load theme first
THEME = load_theme('noir')
colors = get_edge_colors_by_type(G)
```

### 4. Rate Limiting

**Problem**: Too many API calls in short time = rate limit errors

```python
# Wrong - rapid requests
for city in cities:
    coords = get_coordinates(city, country)  # Has 1s delay
    create_poster(...)  # No delay

# Correct - add delays
for city in cities:
    coords = get_coordinates(city, country)
    create_poster(...)
    time.sleep(2)  # Extra delay between cities
```

### 5. Large City Memory Issues

**Problem**: Cities like Tokyo/Mumbai with large distances can OOM

**Solution**: Catch MemoryError and reduce distance:

```python
try:
    G = ox.graph_from_point(point, dist=dist, network_type='all')
except MemoryError:
    print(f"City too large at {dist}m, reducing to {dist//2}m")
    G = ox.graph_from_point(point, dist=dist//2, network_type='all')
```

### 6. Coordinate Format Variations

**Problem**: Coordinates format can vary (N/S, E/W)

**Current handling** (line 299-301):
```python
coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
if lon < 0:
    coords = coords.replace("E", "W")
```

**Edge case**: Southern hemisphere + Western hemisphere (e.g., Buenos Aires)

### 7. Font Loading Failure

**Problem**: Missing font files cause warnings but don't crash

```python
FONTS = load_fonts()  # May return None

# Later, in create_poster():
if FONTS:
    font_main = FontProperties(fname=FONTS['bold'], size=60)
else:
    font_main = FontProperties(family='monospace', weight='bold', size=60)
```

**Gotcha**: Fallback fonts may look different, affecting typography layout.

---

## Quick Reference

### Most Common Modifications

| Task | File | Function | Lines |
|------|------|----------|-------|
| Change road colors | create_map_poster.py | `get_edge_colors_by_type()` | 134-165 |
| Change road widths | create_map_poster.py | `get_edge_widths_by_type()` | 167-194 |
| Add map features | create_map_poster.py | `create_poster()` | 220-243 |
| Modify typography | create_map_poster.py | `create_poster()` | 289-307 |
| Add CLI options | create_map_poster.py | `if __name__` block | 406-425 |
| Create new theme | themes/ | N/A | New .json file |

### Key Constants

```python
THEMES_DIR = "themes"      # Theme directory
FONTS_DIR = "fonts"        # Font directory  
POSTERS_DIR = "posters"    # Output directory

# Canvas
figsize = (12, 16)         # 12×16 inches
dpi = 300                  # Print quality

# Defaults
default_theme = 'feature_based'
default_distance = 29000   # meters (~18 miles)
```

### External APIs

| Service | Rate Limit | Purpose | Endpoint |
|---------|------------|---------|----------|
| Nominatim | 1 req/sec | Geocoding | `nominatim.openstreetmap.org` |
| Overpass | Varies | OSM data | `overpass-api.de` (via OSMnx) |

---

## Conclusion

This codebase is **simple by design** - single file, minimal abstraction, straightforward data flow. The main complexity comes from:

1. **External APIs**: Rate limiting, error handling, data format variations
2. **Matplotlib rendering**: Layer management, coordinate systems, typography
3. **OSM data**: Graph structures, attribute handling, geographic projections

**When making changes**:
- ✅ **Do** follow existing patterns (graceful degradation, z-ordering)
- ✅ **Do** test with multiple cities (grid, organic, coastal)
- ✅ **Do** handle edge cases (empty data, list attributes)
- ⚠️ **Don't** break global THEME dependency without refactoring
- ⚠️ **Don't** remove error handling (try/except blocks)
- ⚠️ **Don't** ignore rate limits (respect API policies)

**Key insight**: This tool prioritizes **output quality** over **execution speed**. Changes that improve quality (better rendering, more features) are more valuable than optimization (unless performance is critically impaired).

Good luck, future agent! 🤖

---

## See Also

- [Technical Overview](TECHNICAL_OVERVIEW.md) - Architecture details
- [API Reference](API_REFERENCE.md) - Function signatures and behaviors
- [Theme System](THEME_SYSTEM.md) - Theme creation guide

---

## Web Application Architecture

The project has been expanded from a CLI-only tool to include a full-featured web application with REST API, background job processing, and a responsive UI.

### Web Application Overview

**Technology Stack**:
- **Backend**: Flask 3.x (Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL (prod) or SQLite (dev)
- **Background Jobs**: Celery 5.x with Redis message broker
- **Caching**: Redis for geocoding, theme data, and session storage
- **Frontend**: Alpine.js (reactive components) + Tailwind CSS
- **WSGI Server**: Gunicorn for production
- **Reverse Proxy**: Nginx (optional, for production with SSL)

### Project Structure

```
app/
├── __init__.py              # Flask app factory
├── config.py                # Configuration classes
├── extensions.py            # Flask extensions (db, cache, celery)
├── models.py                # Database models (Job, Poster)
│
├── api/                     # REST API Blueprint
│   ├── __init__.py          # Blueprint registration
│   ├── themes.py            # GET /api/v1/themes
│   ├── geocoding.py         # GET /api/v1/geocode
│   ├── posters.py           # POST /api/v1/posters, GET /api/v1/posters/{id}
│   ├── jobs.py              # GET /api/v1/jobs/{id}, POST /api/v1/jobs/{id}/cancel
│   └── health.py            # GET /api/v1/health
│
├── services/                # Business logic layer
│   ├── theme_service.py     # Theme operations (load, list, validate)
│   ├── geocoding_service.py # Geocoding with caching and rate limiting
│   └── poster_service.py    # Poster generation job management
│
├── tasks/                   # Celery background tasks
│   ├── __init__.py          # Celery configuration
│   └── poster_tasks.py      # generate_poster_task (async poster creation)
│
├── utils/                   # Utility functions
│   ├── cli_wrapper.py       # Wraps existing CLI code for web use
│   └── validators.py        # Input validation
│
├── web/                     # Web interface routes
│   └── __init__.py          # Web page routes (/, /create, /gallery, etc.)
│
├── templates/               # Jinja2 templates
│   ├── base.html            # Base template with navigation
│   ├── index.html           # Homepage
│   ├── create.html          # Poster creation form
│   ├── progress.html        # Real-time progress tracking
│   ├── result.html          # Poster download page
│   ├── gallery.html         # User's poster gallery
│   └── themes.html          # Theme browser
│
└── static/                  # Static assets
    ├── css/style.css        # Custom styles
    └── js/app.js            # Alpine.js components
```

### Key Files Reference

#### Application Core

- **[`app/__init__.py`](../app/__init__.py)**: Flask app factory
  - Creates and configures Flask app
  - Initializes extensions (database, cache, Celery)
  - Registers blueprints (API, web routes)
  - Creates database tables

- **[`app/config.py`](../app/config.py)**: Configuration classes
  - Environment-based configuration (development, production, testing)
  - Database URLs, Redis URLs, secret keys
  - File storage paths

- **[`app/extensions.py`](../app/extensions.py)**: Flask extensions
  - SQLAlchemy database instance
  - Flask-Caching instance
  - Celery initialization function

- **[`app/models.py`](../app/models.py)**: Database models
  - `Job`: Tracks poster generation jobs (status, progress, errors)
  - `Poster`: Stores generated poster metadata and file paths

#### REST API Layer

- **[`app/api/themes.py`](../app/api/themes.py)**: Theme endpoints
  - `GET /api/v1/themes` - List all themes
  - `GET /api/v1/themes/{id}` - Get theme details

- **[`app/api/geocoding.py`](../app/api/geocoding.py)**: Geocoding endpoints
  - `GET /api/v1/geocode?city=X&country=Y` - Geocode city to coordinates

- **[`app/api/posters.py`](../app/api/posters.py)**: Poster endpoints
  - `POST /api/v1/posters` - Create poster generation job
  - `GET /api/v1/posters` - List user's posters
  - `GET /api/v1/posters/{id}` - Get poster details
  - `GET /api/v1/posters/{id}/download` - Download poster file

- **[`app/api/jobs.py`](../app/api/jobs.py)**: Job status endpoints
  - `GET /api/v1/jobs/{id}` - Get job status and progress
  - `POST /api/v1/jobs/{id}/cancel` - Cancel running job

- **[`app/api/health.py`](../app/api/health.py)**: Health check
  - `GET /api/v1/health` - Service health status

#### Service Layer

- **[`app/services/theme_service.py`](../app/services/theme_service.py)**:
  - `get_all_themes()` - Returns list of available themes with metadata
  - `get_theme(theme_id)` - Returns specific theme configuration
  - `validate_theme_exists(theme_id)` - Checks if theme exists
  - Uses Redis caching (1 hour TTL)

- **[`app/services/geocoding_service.py`](../app/services/geocoding_service.py)**:
  - `geocode(city, country)` - Geocodes city to lat/lon
  - Implements Redis caching (30-day TTL)
  - Rate limiting (10 requests per minute)
  - Respects Nominatim usage policy (1 req/sec)

- **[`app/services/poster_service.py`](../app/services/poster_service.py)**:
  - `create_poster_job()` - Creates job and queues Celery task
  - `get_job_status()` - Returns current job status
  - `cancel_job()` - Cancels pending/running job
  - Manages Job and Poster database records

#### Background Tasks

- **[`app/tasks/poster_tasks.py`](../app/tasks/poster_tasks.py)**:
  - `generate_poster_task(job_id)` - Celery task for poster generation
  - Wraps existing CLI poster generation logic
  - Updates job progress in database
  - Handles errors and retries (max 3 attempts)
  - Creates Poster record on success

#### Utilities

- **[`app/utils/cli_wrapper.py`](../app/utils/cli_wrapper.py)**:
  - `PosterGenerator` class
  - Wraps [`create_map_poster.py`](../create_map_poster.py) functions
  - Provides progress callbacks for job status updates
  - Generates thumbnails for web display

#### Entry Points

- **[`run.py`](../run.py)**: Flask development server entry point
  - Creates app instance
  - Runs Flask development server (debug mode)

- **[`celery_worker.py`](../celery_worker.py)**: Celery worker entry point
  - Creates app instance
  - Starts Celery worker process
  - Processes background poster generation tasks

### Data Flow

#### Poster Generation Flow

```
1. User submits form (web UI) or API request
   ↓
2. POST /api/v1/posters endpoint
   ↓
3. PosterService.create_poster_job()
   - Creates Job record (status=PENDING)
   - Queues Celery task
   ↓
4. Returns job_id to client
   ↓
5. Client polls GET /api/v1/jobs/{job_id}
   ↓
6. Celery worker picks up task
   - Updates Job status to PROCESSING
   - Calls CLI wrapper to generate poster
   - Updates progress in database
   ↓
7. On completion:
   - Creates Poster record
   - Updates Job status to COMPLETED
   - Saves file, thumbnail, metadata
   ↓
8. Client receives completed status with download URL
```

#### Session-Based Tracking

- Users don't need accounts (anonymous usage)
- Session ID stored in cookie
- Jobs and posters associated with session ID
- Gallery shows only session's posters

### Integration with Existing CLI Code

The web application **wraps** the existing CLI code without modifying it:

**Pattern**:
```python
# app/utils/cli_wrapper.py

# Import existing CLI functions
import sys
sys.path.insert(0, '.')
from create_map_poster import (
    load_theme,
    get_coordinates,
    create_poster as cli_create_poster
)

class PosterGenerator:
    def create_poster(self, city, country, theme, point, distance):
        # Load theme using CLI function
        THEME = load_theme(theme)
        
        # Generate filename
        filename = generate_output_filename(city, theme)
        
        # Call CLI create_poster function
        cli_create_poster(city, country, point, distance, filename)
        
        # Generate thumbnail
        thumbnail = self.create_thumbnail(filename)
        
        return {
            'filename': filename,
            'file_path': f'posters/{filename}',
            'thumbnail_path': thumbnail,
            'width': 3600,
            'height': 4800
        }
```

This approach ensures:
- ✅ CLI continues to work unchanged
- ✅ Web app uses same rendering logic
- ✅ Consistent output quality
- ✅ Easy to maintain (single source of truth)

### Development Workflow

#### Running Locally

**Terminal 1: Redis**
```bash
redis-server
```

**Terminal 2: Flask Web Server**
```bash
# Activate virtual environment
source venv/bin/activate

# Start Flask
python run.py
# Access at http://localhost:5000
```

**Terminal 3: Celery Worker**
```bash
# Activate virtual environment
source venv/bin/activate

# Start Celery
python celery_worker.py
# Watch for task execution logs
```

#### Testing API Endpoints

**Using curl**:

```bash
# Health check
curl http://localhost:5000/api/v1/health

# List themes
curl http://localhost:5000/api/v1/themes | jq

# Geocode city
curl "http://localhost:5000/api/v1/geocode?city=Paris&country=France" | jq

# Create poster
curl -X POST http://localhost:5000/api/v1/posters \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country": "France",
    "theme": "noir",
    "distance": 12000
  }' | jq

# Check job status
curl http://localhost:5000/api/v1/jobs/{job_id} | jq

# List posters
curl http://localhost:5000/api/v1/posters | jq
```

**Using Python**:

```python
import requests

# Create poster
response = requests.post('http://localhost:5000/api/v1/posters', json={
    'city': 'Tokyo',
    'country': 'Japan',
    'theme': 'japanese_ink',
    'distance': 15000
})
job = response.json()
print(f"Job ID: {job['job_id']}")

# Poll for completion
import time
while True:
    status = requests.get(f"http://localhost:5000/api/v1/jobs/{job['job_id']}")
    data = status.json()
    print(f"Status: {data['status']}, Progress: {data.get('progress', 0)}%")
    
    if data['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)

# Download poster
if data['status'] == 'completed':
    poster_url = data['result']['download_url']
    poster = requests.get(f"http://localhost:5000{poster_url}")
    with open('tokyo.png', 'wb') as f:
        f.write(poster.content)
```

#### Debugging Celery Tasks

**View task logs**:
```bash
# In Celery worker terminal, you'll see:
# - Task received
# - Task started
# - Progress updates
# - Task completed or failed with traceback
```

**Debug specific task**:

```python
# In Python shell with app context
from app import create_app
from app.models import Job, Poster
from app.extensions import db

app = create_app()
with app.app_context():
    # Check failed jobs
    failed = Job.query.filter_by(status='failed').all()
    for job in failed:
        print(f"Job {job.id}:")
        print(f"  Error: {job.error_message}")
        print(f"  Traceback: {job.error_traceback}")
    
    # Check pending jobs
    pending = Job.query.filter_by(status='pending').count()
    print(f"Pending jobs: {pending}")
    
    # Manually trigger task (for testing)
    from app.tasks.poster_tasks import generate_poster_task
    result = generate_poster_task.delay(job_id)
    print(f"Task ID: {result.id}")
```

**Common Celery issues**:

1. **Task not registered**:
   ```python
   # Ensure task is imported in app/__init__.py
   from app.tasks.poster_tasks import register_tasks
   generate_poster_task = register_tasks(celery)
   ```

2. **Redis connection error**:
   ```bash
   # Check Redis is running
   redis-cli ping
   
   # Check CELERY_BROKER_URL in .env
   echo $CELERY_BROKER_URL
   ```

3. **Import errors in task**:
   ```bash
   # Test imports manually
   python -c "from app.tasks.poster_tasks import generate_poster_task; print('OK')"
   ```

### Adding New Features

#### Add New API Endpoint

**Example**: Add endpoint to list all jobs

1. **Create route** in [`app/api/jobs.py`](../app/api/jobs.py):

```python
@jobs_bp.route('', methods=['GET'])
def list_jobs():
    """List all jobs for current session"""
    session_id = session.get('session_id')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    jobs = Job.query.filter_by(session_id=session_id)\
        .order_by(Job.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'jobs': [job.to_dict() for job in jobs.items],
        'pagination': {
            'page': jobs.page,
            'per_page': jobs.per_page,
            'total': jobs.total,
            'pages': jobs.pages
        }
    })
```

2. **Test endpoint**:
```bash
curl http://localhost:5000/api/v1/jobs | jq
```

#### Add New Service Method

**Example**: Add batch poster generation

1. **Add method** to [`app/services/poster_service.py`](../app/services/poster_service.py):

```python
def create_batch_jobs(self, requests, session_id=None):
    """Create multiple poster generation jobs"""
    jobs = []
    
    for req in requests:
        job = self.create_poster_job(
            city=req['city'],
            country=req['country'],
            theme=req['theme'],
            distance=req.get('distance', 29000),
            latitude=req['latitude'],
            longitude=req['longitude'],
            session_id=session_id
        )
        jobs.append(job)
        
        # Rate limit between jobs
        time.sleep(0.5)
    
    return {'jobs': jobs, 'total': len(jobs)}
```

2. **Create API endpoint**:

```python
@posters_bp.route('/batch', methods=['POST'])
def create_batch():
    """Create multiple posters"""
    data = request.get_json()
    requests = data.get('requests', [])
    
    if not requests or len(requests) > 10:
        return jsonify({'error': 'Must provide 1-10 requests'}), 400
    
    service = PosterService()
    result = service.create_batch_jobs(requests, session.get('session_id'))
    
    return jsonify(result), 202
```

#### Add New Celery Task

**Example**: Add cleanup task for old files

1. **Create task** in [`app/tasks/cleanup_tasks.py`](../app/tasks/cleanup_tasks.py):

```python
from celery import shared_task
from datetime import datetime, timedelta
import os

@shared_task
def cleanup_old_files():
    """Delete posters older than 30 days"""
    from app import create_app
    from app.models import Poster
    from app.extensions import db
    
    app = create_app()
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=30)
        old_posters = Poster.query.filter(Poster.created_at < cutoff).all()
        
        for poster in old_posters:
            # Delete files
            if os.path.exists(poster.file_path):
                os.remove(poster.file_path)
            if os.path.exists(poster.thumbnail_path):
                os.remove(poster.thumbnail_path)
            
            # Delete database record
            db.session.delete(poster)
        
        db.session.commit()
        
        return {'deleted': len(old_posters)}
```

2. **Schedule task** with Celery Beat (add to config):

```python
# app/config.py

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-files': {
        'task': 'app.tasks.cleanup_tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    }
}
```

### Known Issues and Workarounds

#### SQLite Concurrency Limitation

**Issue**: SQLite doesn't handle concurrent writes well. Celery workers may encounter "database is locked" errors.

**Workaround**:
```python
# For development, use PostgreSQL or reduce concurrency
# docker-compose.dev.yml
command: celery -A celery_worker.celery worker --concurrency=1
```

**Solution**: Use PostgreSQL in production (already configured in docker-compose.yml).

#### Celery Task Registration Pattern

**Issue**: Tasks must be registered before Celery worker starts.

**Current pattern**:
```python
# app/__init__.py
from app.tasks.poster_tasks import register_tasks
generate_poster_task = register_tasks(celery)
app.generate_poster_task = generate_poster_task  # Store for access
```

**Why**: Flask app factory pattern requires explicit task registration.

#### Redis Caching Strategies

**Geocoding cache**:
- TTL: 30 days (locations don't change often)
- Key pattern: `geocode:{city}:{country}`
- Invalidation: Manual (via Redis CLI if needed)

**Theme cache**:
- TTL: 1 hour (themes rarely change)
- Key pattern: `theme:{theme_id}`
- Invalidation: Auto-expires, or flush on theme update

**Job status cache**:
- TTL: 5 minutes (real-time data)
- Key pattern: `job_status:{job_id}`
- Invalidation: Updated on each progress update

#### Session Management

**Current**: Flask session cookies (client-side)
- Simple, no server-side storage
- Works for anonymous users
- Limited to cookie size (~4KB)

**Alternative**: Server-side sessions (Redis)
- Better for large session data
- More secure
- Requires Redis Session extension

### Performance Considerations

**Bottlenecks**:
1. **Poster generation**: CPU-intensive (matplotlib rendering)
   - Solution: Scale Celery workers horizontally
   
2. **OSM data fetching**: Network I/O
   - Solution: Implement OSM data caching (future enhancement)
   
3. **Database queries**: Frequent job status checks
   - Solution: Use Redis cache for hot data

**Optimization tips**:
- Cache theme list (rarely changes)
- Cache geocoding results (30-day TTL)
- Use database connection pooling
- Serve static files via Nginx (production)
- Enable gzip compression
- Use CDN for static assets (if public)

### Testing Strategy

**Unit tests**:
```python
# tests/test_services.py
def test_theme_service(app):
    with app.app_context():
        service = ThemeService()
        themes = service.get_all_themes()
        assert len(themes) == 17
        assert all('name' in t for t in themes)
```

**API tests**:
```python
# tests/test_api.py
def test_create_poster(client):
    response = client.post('/api/v1/posters', json={
        'city': 'Paris',
        'country': 'France',
        'theme': 'noir',
        'distance': 12000
    })
    assert response.status_code == 202
    data = response.get_json()
    assert 'job_id' in data
```

**Integration tests**:
```python
# tests/test_integration.py
def test_full_poster_generation(app, celery_worker):
    # Create job
    # Wait for completion
    # Verify file exists
    # Check database records
    pass
```

---

## Web Application Quick Reference

### Common Tasks

**Restart services**:
```bash
# Development
pkill -f "python run.py"
pkill -f celery_worker
python run.py &
python celery_worker.py &

# Docker
docker-compose restart web celery
```

**View logs**:
```bash
# Development
tail -f logs/flask.log
tail -f logs/celery.log

# Docker
docker-compose logs -f web
docker-compose logs -f celery
```

**Clear Redis cache**:
```bash
redis-cli FLUSHDB
```

**Reset database**:
```bash
# Development (SQLite)
rm instance/posters.db
python run.py  # Will recreate tables

# Production (PostgreSQL)
docker-compose exec postgres psql -U maptoposter -d maptoposter -c "DROP TABLE jobs, posters CASCADE;"
docker-compose restart web  # Will recreate tables
```

**Check system status**:
```bash
# All services
curl http://localhost:5000/api/v1/health | jq

# Database
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.engine.execute('SELECT 1'); print('DB OK')"

# Redis
redis-cli ping

# Celery
docker-compose exec celery celery -A celery_worker.celery inspect active
```

### File Locations

**Development**:
- Posters: `./posters/`
- Thumbnails: `./thumbnails/`
- Database: `./instance/posters.db`
- Logs: `./logs/`

**Docker**:
- Posters: Docker volume `poster_data`
- Thumbnails: Docker volume `thumbnail_data`
- Database: Docker volume `postgres_data`
- Logs: `docker-compose logs`

### Environment Variables

See [`.env.example`](../.env.example) for complete list.

**Critical variables**:
- `SECRET_KEY`: Flask session encryption key
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection for caching
- `CELERY_BROKER_URL`: Redis connection for Celery tasks
- `CELERY_RESULT_BACKEND`: Redis connection for task results

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Installation instructions