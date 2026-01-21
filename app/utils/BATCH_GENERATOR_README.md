# Batch Poster Generator

## Overview

The `BatchPosterGenerator` class enables efficient generation of multiple themed map posters from a single location by fetching OpenStreetMap data once and reusing it for all themes. This provides **dramatic performance improvements** when creating multiple themed posters for the same city.

## Performance Benefits

### Traditional Approach (Sequential)
- Fetch OSM data for Theme 1 → Render Theme 1
- Fetch OSM data for Theme 2 → Render Theme 2  
- Fetch OSM data for Theme 3 → Render Theme 3

**Total Time**: ~3-5 minutes per theme × N themes

### Batch Approach (Optimized)
- Fetch OSM data **once** → Render all themes in parallel

**Total Time**: ~3-5 minutes (data fetch) + ~30-60 seconds (parallel rendering)

**Speedup**: Up to **5-10x faster** for 3+ themes!

## Features

✅ **Single Data Fetch**: OSM data fetched only once per location  
✅ **Parallel Rendering**: Multiple themes rendered concurrently using ThreadPoolExecutor  
✅ **Progress Tracking**: Optional callbacks for monitoring generation progress  
✅ **Error Resilience**: Failed themes don't block successful ones  
✅ **Comprehensive Results**: Detailed status, timing, and error information for each theme  
✅ **CLI Support**: Standalone command-line interface for testing  
✅ **Flexible API**: Both class-based and convenience function interfaces

## Installation

The batch generator is part of the `app/utils` package and requires the same dependencies as the main poster generation system:

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start (Convenience Function)

```python
from app.utils import create_batch_posters

# Generate 3 themed posters for Paris
results = create_batch_posters(
    'Paris',
    'France',
    ['noir', 'midnight_blue', 'pastel_dream']
)

# Check results
for result in results:
    if result['status'] == 'success':
        print(f"✓ {result['theme']}: {result['filename']}")
    else:
        print(f"✗ {result['theme']}: {result['error']}")
```

### With Progress Tracking

```python
from app.utils import create_batch_posters

def progress_callback(current_step, total_steps, message):
    percentage = int((current_step / total_steps) * 100)
    print(f"[{percentage}%] {message}")

results = create_batch_posters(
    'Tokyo',
    'Japan',
    ['japanese_ink', 'neon_cyberpunk', 'midnight_blue'],
    distance=15000,
    progress_callback=progress_callback
)
```

### Advanced Usage (Class-Based)

```python
from app.utils import BatchPosterGenerator

# Create generator with custom settings
generator = BatchPosterGenerator(
    output_dir='my_posters',
    max_render_workers=2  # Limit parallel workers
)

# Generate batch
results = generator.create_batch_posters(
    city='Barcelona',
    country='Spain',
    themes=['warm_beige', 'blueprint', 'terracotta'],
    distance=10000,
    preview_mode=True  # Faster preview rendering (150 DPI vs 300 DPI)
)

# Process results with detailed information
for result in results:
    print(f"Theme: {result['theme']}")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  File: {result['filename']}")
        print(f"  Path: {result['file_path']}")
        print(f"  Size: {result['file_size'] / 1024 / 1024:.2f} MB")
        print(f"  Render Time: {result['render_time']:.2f}s")
    else:
        print(f"  Error: {result['error']}")
```

## Command-Line Interface

The batch generator includes a standalone CLI for testing and batch generation from the command line:

```bash
# Basic usage
python app/utils/batch_poster_generator.py Paris France \
    --themes noir midnight_blue pastel_dream

# Custom output directory
python app/utils/batch_poster_generator.py Tokyo Japan \
    --themes japanese_ink neon_cyberpunk \
    --output-dir my_custom_posters

# Custom distance and parallel workers
python app/utils/batch_poster_generator.py "New York" USA \
    --themes noir blueprint sunset \
    --distance 15000 \
    --workers 2

# Preview mode (faster, lower quality)
python app/utils/batch_poster_generator.py Barcelona Spain \
    --themes warm_beige blueprint \
    --preview

# Show help
python app/utils/batch_poster_generator.py --help
```

## API Reference

### `BatchPosterGenerator` Class

#### Constructor

```python
BatchPosterGenerator(output_dir: str = 'posters', max_render_workers: int = 4)
```

**Parameters:**
- `output_dir`: Directory where posters will be saved (default: 'posters')
- `max_render_workers`: Maximum number of parallel rendering workers (default: 4)

#### Methods

##### `create_batch_posters()`

```python
create_batch_posters(
    city: str,
    country: str,
    themes: List[str],
    distance: int = 29000,
    preview_mode: bool = False,
    progress_callback: Optional[Callable] = None
) -> List[Dict]
```

Main method for batch generation.

**Parameters:**
- `city`: City name
- `country`: Country name  
- `themes`: List of theme names to generate
- `distance`: Map radius in meters (default: 29000)
- `preview_mode`: Use lower DPI (150) for faster rendering (default: False uses 300 DPI)
- `progress_callback`: Optional callback function `(current_step, total_steps, message)`

**Returns:** List of result dictionaries with fields:
- `status`: 'success' or 'error'
- `theme`: Theme name
- `filename`: Output filename (if successful)
- `file_path`: Full path to file (if successful)
- `file_size`: File size in bytes (if successful)
- `render_time`: Rendering time in seconds
- `error`: Error message (if failed)

##### `generate_filename()`

```python
generate_filename(city: str, theme: str, timestamp: str = None) -> str
```

Generate consistent filenames for batch-generated posters.

**Parameters:**
- `city`: City name
- `theme`: Theme name
- `timestamp`: Optional timestamp string (uses current time if not provided)

**Returns:** Full path: `{output_dir}/{city_slug}_{theme}_{timestamp}.png`

### Convenience Function

```python
create_batch_posters(city: str, country: str, themes: List[str], **kwargs) -> List[Dict]
```

Convenience wrapper that creates a `BatchPosterGenerator` instance and generates posters.

**Accepts all parameters from:**
- Constructor: `output_dir`, `max_render_workers`
- Method: `distance`, `preview_mode`, `progress_callback`

## Performance Tips

1. **Parallel Workers**: Adjust `max_render_workers` based on CPU cores
   - 2-4 workers optimal for most systems
   - More workers = higher memory usage

2. **Preview Mode**: Use for testing/previews to save time
   - 150 DPI vs 300 DPI = ~4x faster rendering
   - Smaller file sizes (~1/4 size)

3. **Distance Parameter**: Smaller areas render faster
   - 4000-6000m: Dense cities (Venice, Amsterdam)
   - 8000-12000m: Medium cities (Paris, Barcelona)
   - 15000-20000m: Large metros (Tokyo, Mumbai)

4. **Theme Selection**: Start with 2-3 themes for testing
   - Verify results before large batch jobs
   - Consider error handling for production

## Error Handling

The batch generator is designed to be resilient:

- **Individual Theme Failures**: If one theme fails, others continue
- **Graceful Degradation**: Failed themes return error dictionaries
- **Comprehensive Logging**: Detailed error messages and stack traces
- **Progress Tracking**: Callbacks receive failure notifications

Example error handling:

```python
results = create_batch_posters('Paris', 'France', ['noir', 'invalid_theme', 'sunset'])

success_count = sum(1 for r in results if r['status'] == 'success')
error_count = len(results) - success_count

print(f"Generated {success_count}/{len(results)} posters")

# Handle errors
for result in results:
    if result['status'] == 'error':
        print(f"Failed: {result['theme']}")
        print(f"  Error: {result['error']}")
```

## Integration with Web Application

The batch generator can be integrated with the existing Flask/Celery web application:

```python
# In a Celery task
from app.utils import BatchPosterGenerator
from app.models import PosterJob

@celery.task
def generate_batch_posters_task(job_id, city, country, themes, distance):
    """Celery task for batch poster generation."""
    job = PosterJob.query.get(job_id)
    
    def progress_callback(current, total, message):
        job.progress = int((current / total) * 100)
        job.status_message = message
        db.session.commit()
    
    generator = BatchPosterGenerator()
    results = generator.create_batch_posters(
        city, country, themes, distance,
        progress_callback=progress_callback
    )
    
    # Store results in database
    for result in results:
        if result['status'] == 'success':
            # Create poster record
            pass
    
    return results
```

## Architecture

### Data Flow

1. **Geocoding**: Get coordinates for city/country
2. **Data Fetching**: Single OSM query via `fetch_map_data()`
   - Street network (parallel download)
   - Water features (parallel download)
   - Parks/green spaces (parallel download)
3. **Parallel Rendering**: ThreadPoolExecutor distributes themes
   - Each worker calls `_render_single_theme()`
   - Independent theme rendering with isolated errors
4. **Result Collection**: Aggregated results with timing/status

### Thread Safety

- **ThreadPoolExecutor**: Used for I/O-bound matplotlib rendering
- **Matplotlib Backend**: 'Agg' backend is thread-safe
- **Isolated Rendering**: Each theme renders in its own context
- **No Shared State**: Workers don't share mutable data

## Examples

See `app/utils/batch_example.py` for complete usage examples.

## Related Files

- [`batch_poster_generator.py`](./batch_poster_generator.py) - Main implementation
- [`batch_example.py`](./batch_example.py) - Usage examples
- [`cli_wrapper.py`](./cli_wrapper.py) - Single poster generation wrapper
- [`../../create_map_poster.py`](../../create_map_poster.py) - Core poster generation

## License

Same license as the main project.