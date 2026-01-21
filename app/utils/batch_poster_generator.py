"""
Batch Poster Generator for multi-theme map poster creation.

This module provides efficient batch generation of map posters with multiple themes
by fetching OSM data once and rendering with different themes in parallel.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# Import from app.services.map_generator
from app.services.map_generator import fetch_map_data, render_poster, load_theme, get_coordinates

logger = logging.getLogger(__name__)


class BatchPosterGenerator:
    """
    Efficient batch generator for creating multiple themed posters.
    
    This class dramatically improves performance when generating multiple themes
    for the same location by fetching OSM data once and reusing it for all themes.
    """
    
    def __init__(self, output_dir: str = 'posters', max_render_workers: int = 4):
        """
        Initialize batch poster generator.
        
        Args:
            output_dir: Directory where posters will be saved
            max_render_workers: Maximum number of parallel rendering workers
        """
        self.output_dir = output_dir
        self.max_render_workers = max_render_workers
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
    
    def generate_filename(self, city: str, theme: str, timestamp: str = None) -> str:
        """
        Generate consistent filenames for batch-generated posters.
        
        Args:
            city: City name
            theme: Theme name
            timestamp: Optional timestamp string (uses current time if not provided)
            
        Returns:
            Full path to output file: {output_dir}/{city_slug}_{theme}_{timestamp}.png
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        city_slug = city.lower().replace(' ', '_')
        filename = f"{city_slug}_{theme}_{timestamp}.png"
        return os.path.join(self.output_dir, filename)
    
    def create_batch_posters(
        self,
        city: str,
        country: str,
        themes: List[str],
        distance: int = 29000,
        preview_mode: bool = False,
        width_inches: float = 12.0,
        height_inches: float = 16.0,
        dpi: int = 300,
        progress_callback: Optional[Callable] = None,
        job_progress_callback: Optional[Callable] = None,
        result_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Generate multiple themed posters from a single OSM data fetch.
        
        This is the main method for batch generation, providing significant
        performance improvements by fetching OSM data once and rendering
        multiple themes in parallel.
        
        Args:
            city: City name
            country: Country name
            themes: List of theme names to generate
            distance: Map radius in meters (default: 29000)
            preview_mode: Use lower DPI for faster preview rendering (deprecated, use dpi parameter)
            width_inches: Width of poster in inches (default: 12.0)
            height_inches: Height of poster in inches (default: 16.0)
            dpi: DPI resolution (default: 300)
            progress_callback: Optional callback(current_step, total_steps, message)
            job_progress_callback: Optional callback(theme, step_message, progress_percent)
                                   Called for each individual job's progress
            result_callback: Optional callback(result_dict) called immediately when each theme completes
                           This allows processing results as they complete rather than at the end
            
        Returns:
            List of result dictionaries, one per theme:
                - status: 'success' or 'error'
                - theme: Theme name
                - filename: Output filename (if successful)
                - file_path: Full path to file (if successful)
                - file_size: File size in bytes (if successful)
                - error: Error message (if failed)
                - render_time: Time taken to render in seconds
        """
        results = []
        total_steps = len(themes) + 2  # +2 for geocoding and data fetch
        current_step = 0
        
        try:
            # Step 1: Get coordinates
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, f"Looking up coordinates for {city}, {country}")
            
            logger.info(f"Batch generation started for {city}, {country} with {len(themes)} themes")
            point = get_coordinates(city, country)
            logger.info(f"Coordinates found: {point}")
            
            # Step 2: Fetch OSM data ONCE
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, "Fetching map data (streets, water, parks)")
            
            # Update all jobs to show data fetching
            if job_progress_callback:
                for theme_name in themes:
                    job_progress_callback(theme_name, "Downloading map data...", 30)
            
            logger.info(f"Fetching map data for distance={distance}m")
            
            # Define a callback for fetch_map_data to track download progress
            def fetch_progress_callback(data_type, completed, total):
                """Handle progress from fetch_map_data"""
                if job_progress_callback:
                    if data_type == 'streets':
                        for theme_name in themes:
                            job_progress_callback(theme_name, "Streets downloaded ✓", 40)
                    elif data_type == 'water':
                        for theme_name in themes:
                            job_progress_callback(theme_name, "Water features downloaded ✓", 50)
                    elif data_type == 'parks':
                        for theme_name in themes:
                            job_progress_callback(theme_name, "Parks downloaded ✓", 60)
            
            map_data = fetch_map_data(point, distance, progress_callback=fetch_progress_callback)
            logger.info("Map data fetched successfully")
            
            # Use a shared timestamp for all posters in this batch
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Step 3: Render each theme SEQUENTIALLY (matplotlib is not thread-safe)
            # Even with 'Agg' backend, parallel rendering causes color corruption and blank outputs
            logger.info(f"Starting SEQUENTIAL rendering of {len(themes)} themes (matplotlib thread-safety)")
            logger.warning("Note: Parallel rendering disabled due to matplotlib thread-safety issues")
            
            for theme_name in themes:
                current_step += 1
                output_file = self.generate_filename(city, theme_name, timestamp)
                
                logger.info(f"[{current_step-2}/{len(themes)}] Starting render: {theme_name}")
                
                # Update job to show rendering
                if job_progress_callback:
                    job_progress_callback(theme_name, f"Rendering {theme_name}...", 65)
                
                try:
                    result = self._render_single_theme(
                        map_data=map_data,
                        theme_name=theme_name,
                        city=city,
                        country=country,
                        point=point,
                        output_file=output_file,
                        width_inches=width_inches,
                        height_inches=height_inches,
                        dpi=dpi
                    )
                    results.append(result)
                    
                    if progress_callback:
                        status_msg = "✓" if result['status'] == 'success' else "✗"
                        progress_callback(
                            current_step,
                            total_steps,
                            f"{status_msg} Rendered {theme_name}"
                        )
                    
                    # Update job progress based on result
                    if job_progress_callback:
                        if result['status'] == 'success':
                            job_progress_callback(theme_name, f"Complete! {theme_name}", 100)
                        else:
                            job_progress_callback(theme_name, f"Failed: {result.get('error', 'Unknown error')}", 100)
                    
                    # Call result callback immediately for incremental processing
                    if result_callback:
                        try:
                            result_callback(result)
                        except Exception as e:
                            logger.error(f"Error in result callback for theme {theme_name}: {e}")
                    
                    if result['status'] == 'success':
                        logger.info(f"Theme '{theme_name}' rendered successfully in {result.get('render_time', 0):.2f}s")
                        logger.info(f"  File: {result['filename']} ({result['file_size'] / 1024 / 1024:.2f} MB)")
                    else:
                        logger.error(f"Theme '{theme_name}' failed: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    # Handle any unexpected errors
                    error_msg = f"Unexpected error rendering {theme_name}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    results.append({
                        'status': 'error',
                        'theme': theme_name,
                        'error': error_msg
                    })
                    
                    if progress_callback:
                        progress_callback(current_step, total_steps, f"✗ Error rendering {theme_name}")
            
            # Final summary
            success_count = sum(1 for r in results if r['status'] == 'success')
            logger.info(f"Batch generation complete: {success_count}/{len(themes)} successful")
            
            if progress_callback:
                progress_callback(
                    total_steps,
                    total_steps,
                    f"Batch complete: {success_count}/{len(themes)} posters generated"
                )
            
        except Exception as e:
            # Handle errors in geocoding or data fetching
            error_msg = f"Batch generation failed: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Return error results for all themes
            for theme_name in themes:
                results.append({
                    'status': 'error',
                    'theme': theme_name,
                    'error': error_msg
                })
            
            if progress_callback:
                progress_callback(current_step, total_steps, f"✗ {error_msg}")
        
        return results
    
    def _render_single_theme(
        self,
        map_data: Dict,
        theme_name: str,
        city: str,
        country: str,
        point: Tuple[float, float],
        output_file: str,
        width_inches: float = 12.0,
        height_inches: float = 16.0,
        dpi: int = 300
    ) -> Dict:
        """
        Helper method to render a single theme.
        
        This method is designed to be called in parallel by ThreadPoolExecutor.
        Each call is isolated and handles its own errors.
        
        Args:
            map_data: Pre-fetched map data dictionary
            theme_name: Name of theme to render
            city: City name
            country: Country name
            point: (latitude, longitude) tuple
            output_file: Path where poster will be saved
            width_inches: Width of poster in inches
            height_inches: Height of poster in inches
            dpi: DPI resolution
            
        Returns:
            Result dictionary with status, filename, or error information
        """
        start_time = datetime.now()
        
        try:
            # Load theme
            logger.info(f"Loading theme: {theme_name}")
            theme = load_theme(theme_name)
            
            # Render poster
            logger.info(f"Rendering {theme_name} to {output_file} at {width_inches}\"x{height_inches}\" @ {dpi} DPI")
            render_poster(
                map_data=map_data,
                theme=theme,
                city=city,
                country=country,
                point=point,
                output_file=output_file,
                width_inches=width_inches,
                height_inches=height_inches,
                dpi=dpi
            )
            
            # Verify file was created
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"Output file was not created: {output_file}")
            
            # Get file info and dimensions
            file_size = os.path.getsize(output_file)
            render_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate pixel dimensions
            width = int(width_inches * dpi)
            height = int(height_inches * dpi)
            
            # Try to get actual dimensions from image file
            try:
                from PIL import Image
                with Image.open(output_file) as img:
                    width, height = img.size
                    logger.info(f"Image dimensions: {width}x{height}")
            except Exception as e:
                logger.warning(f"Could not read image dimensions, using calculated: {e}")
            
            result = {
                'status': 'success',
                'theme': theme_name,
                'filename': os.path.basename(output_file),
                'file_path': os.path.abspath(output_file),
                'file_size': file_size,
                'width': width,
                'height': height,
                'render_time': render_time
            }
            
            logger.info(f"Theme '{theme_name}' rendered successfully in {render_time:.2f}s ({width}x{height})")
            return result
            
        except Exception as e:
            render_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error rendering theme '{theme_name}': {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            return {
                'status': 'error',
                'theme': theme_name,
                'error': error_msg,
                'render_time': render_time
            }


def create_batch_posters(city: str, country: str, themes: List[str], **kwargs) -> List[Dict]:
    """
    Convenience function for batch poster generation.
    
    Creates a BatchPosterGenerator instance and generates posters for all themes.
    
    Args:
        city: City name
        country: Country name
        themes: List of theme names to generate
        **kwargs: Additional arguments passed to BatchPosterGenerator constructor
                  and create_batch_posters method (output_dir, max_render_workers,
                  distance, preview_mode, progress_callback)
    
    Returns:
        List of result dictionaries
    
    Example:
        results = create_batch_posters(
            'Paris',
            'France',
            ['noir', 'midnight_blue', 'pastel_dream'],
            output_dir='my_posters',
            max_render_workers=2,
            distance=15000
        )
    """
    # Extract constructor kwargs
    constructor_kwargs = {}
    if 'output_dir' in kwargs:
        constructor_kwargs['output_dir'] = kwargs.pop('output_dir')
    if 'max_render_workers' in kwargs:
        constructor_kwargs['max_render_workers'] = kwargs.pop('max_render_workers')
    
    # Create generator and run batch
    generator = BatchPosterGenerator(**constructor_kwargs)
    return generator.create_batch_posters(city, country, themes, **kwargs)


if __name__ == '__main__':
    # Simple CLI for testing batch generation
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate multiple themed posters efficiently',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 3 themes for Paris
  python batch_poster_generator.py Paris France --themes noir midnight_blue pastel_dream
  
  # Generate with custom output directory
  python batch_poster_generator.py Tokyo Japan --themes japanese_ink neon_cyberpunk --output-dir my_posters
  
  # Generate with custom distance and workers
  python batch_poster_generator.py "New York" USA --themes noir blueprint --distance 15000 --workers 2
        """
    )
    
    parser.add_argument('city', help='City name')
    parser.add_argument('country', help='Country name')
    parser.add_argument('--themes', nargs='+', required=True, help='List of themes to generate')
    parser.add_argument('--output-dir', default='posters', help='Output directory (default: posters)')
    parser.add_argument('--distance', type=int, default=29000, help='Map radius in meters (default: 29000)')
    parser.add_argument('--workers', type=int, default=4, help='Max parallel rendering workers (default: 4)')
    parser.add_argument('--preview', action='store_true', help='Generate preview (lower DPI)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Batch Map Poster Generator")
    print("=" * 60)
    print(f"City: {args.city}, {args.country}")
    print(f"Themes: {', '.join(args.themes)}")
    print(f"Distance: {args.distance}m")
    print(f"Workers: {args.workers}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)
    print()
    
    # Progress callback for CLI
    def progress_callback(current, total, message):
        percentage = int((current / total) * 100)
        print(f"[{current}/{total} - {percentage}%] {message}")
    
    # Run batch generation
    results = create_batch_posters(
        args.city,
        args.country,
        args.themes,
        output_dir=args.output_dir,
        max_render_workers=args.workers,
        distance=args.distance,
        preview_mode=args.preview,
        progress_callback=progress_callback
    )
    
    # Print results
    print()
    print("=" * 60)
    print("Results:")
    print("=" * 60)
    
    success_count = 0
    for r in results:
        status_symbol = "✓" if r['status'] == 'success' else "✗"
        print(f"{status_symbol} {r['theme']}: {r['status']}")
        
        if r['status'] == 'success':
            success_count += 1
            print(f"  File: {r['filename']}")
            print(f"  Size: {r['file_size'] / 1024 / 1024:.2f} MB")
            print(f"  Time: {r['render_time']:.2f}s")
        else:
            print(f"  Error: {r.get('error', 'Unknown error')}")
        print()
    
    print("=" * 60)
    print(f"Summary: {success_count}/{len(results)} posters generated successfully")
    print("=" * 60)
    
    # Exit with error code if any failed
    sys.exit(0 if success_count == len(results) else 1)