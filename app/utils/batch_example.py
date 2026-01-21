"""
Example usage of BatchPosterGenerator.

This demonstrates how to use the batch poster generator
from Python code.
"""

from batch_poster_generator import BatchPosterGenerator, create_batch_posters


def example_basic():
    """Basic example - generate 3 themes for a city."""
    print("Example 1: Basic batch generation")
    print("-" * 60)
    
    results = create_batch_posters(
        city='Paris',
        country='France',
        themes=['noir', 'midnight_blue', 'pastel_dream'],
        distance=10000  # Smaller distance for faster testing
    )
    
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['theme']}: {result['filename']}")
        else:
            print(f"✗ {result['theme']}: {result['error']}")


def example_with_progress():
    """Example with progress callback."""
    print("\nExample 2: With progress callback")
    print("-" * 60)
    
    def progress_callback(current, total, message):
        percent = int((current / total) * 100)
        print(f"[{percent}%] {message}")
    
    results = create_batch_posters(
        city='Tokyo',
        country='Japan',
        themes=['japanese_ink', 'neon_cyberpunk'],
        distance=15000,
        progress_callback=progress_callback
    )
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n{success_count}/{len(results)} posters generated successfully")


def example_custom_class():
    """Example using the class directly with custom settings."""
    print("\nExample 3: Custom class usage")
    print("-" * 60)
    
    # Create generator with custom settings
    generator = BatchPosterGenerator(
        output_dir='my_custom_posters',
        max_render_workers=2  # Limit parallel workers
    )
    
    # Generate batch
    results = generator.create_batch_posters(
        city='Barcelona',
        country='Spain',
        themes=['warm_beige', 'blueprint'],
        distance=8000,
        preview_mode=True  # Faster preview rendering
    )
    
    # Process results
    for result in results:
        print(f"{result['theme']}: {result['status']}")
        if result['status'] == 'success':
            print(f"  Size: {result['file_size'] / 1024:.1f} KB")
            print(f"  Time: {result['render_time']:.2f}s")


if __name__ == '__main__':
    print("=" * 60)
    print("BatchPosterGenerator Examples")
    print("=" * 60)
    print()
    
    # Uncomment to run examples:
    # example_basic()
    # example_with_progress()
    # example_custom_class()
    
    print("\nUncomment examples in the code to run them.")