"""
File helper utilities for map poster generation.

This module provides centralized file path logic and thumbnail generation
for consistent file handling across CLI and web application.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Tuple, List
from PIL import Image

logger = logging.getLogger(__name__)


def generate_poster_filename(city: str, theme: str, timestamp: str = None) -> str:
    """
    Generate consistent filenames for poster images.
    
    Args:
        city: City name to slugify
        theme: Theme name to use
        timestamp: Optional timestamp string. If None, current time is used
        
    Returns:
        Filename in format: {city_slug}_{theme}_{timestamp}.png
        
    Examples:
        >>> generate_poster_filename("New York", "noir")
        'new_york_noir_20260120_172930.png'
        >>> generate_poster_filename("San Francisco", "sunset", "20260101_120000")
        'san_francisco_sunset_20260101_120000.png'
    """
    # Slugify city name: lowercase, replace spaces with underscores
    city_slug = city.lower().replace(' ', '_').replace('-', '_')
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure theme is lowercase for consistency
    theme_slug = theme.lower().replace(' ', '_')
    
    return f"{city_slug}_{theme_slug}_{timestamp}.png"


def ensure_directory(path: str) -> str:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        The path that was created/verified
        
    Raises:
        OSError: If directory creation fails due to permissions or other errors
    """
    try:
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")
        return path
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise


def get_poster_path(filename: str, output_dir: str = 'posters') -> str:
    """
    Return full path to poster file, creating directory if needed.
    
    Args:
        filename: Name of the poster file
        output_dir: Directory to store posters (default: 'posters')
        
    Returns:
        Full path to the poster file
        
    Examples:
        >>> get_poster_path("new_york_noir_20260120.png")
        'posters/new_york_noir_20260120.png'
        >>> get_poster_path("paris_sunset.png", "custom_output")
        'custom_output/paris_sunset.png'
    """
    ensure_directory(output_dir)
    return os.path.join(output_dir, filename)


def get_thumbnail_path(poster_path: str, thumbnail_dir: str = None) -> str:
    """
    Generate thumbnail path from poster path.
    
    Args:
        poster_path: Path to the original poster image
        thumbnail_dir: Optional separate directory for thumbnails.
                      If None, thumbnail is placed in same directory as poster
                      
    Returns:
        Path to the thumbnail file
        
    Examples:
        >>> get_thumbnail_path("posters/new_york_noir.png")
        'posters/new_york_noir_thumb.png'
        >>> get_thumbnail_path("posters/paris_sunset.png", "thumbnails")
        'thumbnails/paris_sunset_thumb.png'
    """
    # Split path into directory, filename, and extension
    dir_name = os.path.dirname(poster_path)
    base_name = os.path.basename(poster_path)
    name, ext = os.path.splitext(base_name)
    
    # Generate thumbnail filename with _thumb suffix
    thumbnail_filename = f"{name}_thumb{ext}"
    
    # Use specified thumbnail directory or same as poster
    if thumbnail_dir:
        ensure_directory(thumbnail_dir)
        return os.path.join(thumbnail_dir, thumbnail_filename)
    else:
        return os.path.join(dir_name, thumbnail_filename)


def generate_thumbnail(
    source_path: str,
    thumbnail_path: str = None,
    size: Tuple[int, int] = (400, 533)
) -> str:
    """
    Generate thumbnail from poster image.
    
    Args:
        source_path: Path to the source poster image
        thumbnail_path: Optional path for thumbnail. If None, auto-generated
        size: Thumbnail size as (width, height). Default: (400, 533)
        
    Returns:
        Path to the generated thumbnail
        
    Raises:
        FileNotFoundError: If source image doesn't exist
        IOError: If image processing fails
        
    Examples:
        >>> generate_thumbnail("posters/paris_noir.png")
        'posters/paris_noir_thumb.png'
        >>> generate_thumbnail("posters/tokyo.png", "thumbs/tokyo_small.png", (200, 266))
        'thumbs/tokyo_small.png'
    """
    # Check if source file exists
    if not os.path.exists(source_path):
        error_msg = f"Source image not found: {source_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Auto-generate thumbnail path if not provided
    if thumbnail_path is None:
        thumbnail_path = get_thumbnail_path(source_path)
    
    try:
        # Open and process image
        logger.info(f"Generating thumbnail for {source_path}")
        with Image.open(source_path) as img:
            # Maintain aspect ratio while resizing
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Ensure directory exists for thumbnail
            thumb_dir = os.path.dirname(thumbnail_path)
            if thumb_dir:
                ensure_directory(thumb_dir)
            
            # Save optimized PNG
            img.save(thumbnail_path, 'PNG', optimize=True)
            logger.info(f"Thumbnail generated: {thumbnail_path}")
            
        return thumbnail_path
        
    except IOError as e:
        error_msg = f"Failed to generate thumbnail for {source_path}: {e}"
        logger.error(error_msg)
        raise IOError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error generating thumbnail for {source_path}: {e}"
        logger.error(error_msg)
        raise


def generate_thumbnails_batch(
    poster_paths: List[str],
    size: Tuple[int, int] = (400, 533)
) -> List[Tuple[str, Optional[str], bool]]:
    """
    Generate thumbnails for multiple posters.
    
    Args:
        poster_paths: List of paths to poster images
        size: Thumbnail size as (width, height). Default: (400, 533)
        
    Returns:
        List of tuples: (poster_path, thumbnail_path, success)
        where success is True if thumbnail was generated, False otherwise
        
    Examples:
        >>> paths = ["posters/paris.png", "posters/tokyo.png"]
        >>> results = generate_thumbnails_batch(paths)
        >>> for poster, thumb, success in results:
        ...     if success:
        ...         print(f"Generated: {thumb}")
    """
    results = []
    
    logger.info(f"Starting batch thumbnail generation for {len(poster_paths)} posters")
    
    for poster_path in poster_paths:
        try:
            thumbnail_path = generate_thumbnail(poster_path, size=size)
            results.append((poster_path, thumbnail_path, True))
            logger.debug(f"Success: {poster_path} -> {thumbnail_path}")
        except (FileNotFoundError, IOError, Exception) as e:
            logger.warning(f"Failed to generate thumbnail for {poster_path}: {e}")
            results.append((poster_path, None, False))
    
    # Log summary
    successful = sum(1 for _, _, success in results if success)
    logger.info(f"Batch complete: {successful}/{len(poster_paths)} thumbnails generated")
    
    return results


# Utility function for checking if thumbnail exists
def thumbnail_exists(poster_path: str, thumbnail_dir: str = None) -> bool:
    """
    Check if thumbnail already exists for a poster.
    
    Args:
        poster_path: Path to the poster image
        thumbnail_dir: Optional separate thumbnail directory
        
    Returns:
        True if thumbnail exists, False otherwise
    """
    thumbnail_path = get_thumbnail_path(poster_path, thumbnail_dir)
    return os.path.exists(thumbnail_path)


# Utility function for getting file size
def get_file_size(path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        path: Path to the file
        
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(path)
    except OSError:
        return 0