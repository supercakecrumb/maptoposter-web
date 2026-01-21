"""Page format utility functions."""

from typing import Dict, Tuple, Optional
from flask import current_app


def get_format_dimensions(
    format_id: str,
    orientation: str = 'portrait',
    custom_width: Optional[float] = None,
    custom_height: Optional[float] = None
) -> Tuple[float, float]:
    """
    Get dimensions in inches for a given format.
    
    Args:
        format_id: Format identifier (e.g., 'a4', 'classic', 'custom')
        orientation: 'portrait' or 'landscape'
        custom_width: Width in inches for custom format
        custom_height: Height in inches for custom format
        
    Returns:
        Tuple of (width_inches, height_inches)
        
    Raises:
        ValueError: If format is invalid or custom dimensions missing
    """
    formats = current_app.config['PAGE_FORMATS']
    
    if format_id not in formats:
        raise ValueError(f"Unknown format: {format_id}")
    
    format_config = formats[format_id]
    
    if format_id == 'custom':
        if custom_width is None or custom_height is None:
            raise ValueError("Custom format requires width and height")
        
        # Validate custom dimensions
        min_size = current_app.config['MIN_PAGE_SIZE_INCHES']
        max_size = current_app.config['MAX_PAGE_SIZE_INCHES']
        
        if not (min_size <= custom_width <= max_size):
            raise ValueError(f"Width must be between {min_size} and {max_size} inches")
        if not (min_size <= custom_height <= max_size):
            raise ValueError(f"Height must be between {min_size} and {max_size} inches")
        
        width, height = custom_width, custom_height
    else:
        width = format_config['width_inches']
        height = format_config['height_inches']
    
    # Apply orientation
    if orientation == 'landscape':
        width, height = max(width, height), min(width, height)
    else:  # portrait
        width, height = min(width, height), max(width, height)
    
    return width, height


def validate_dpi(dpi: int) -> int:
    """
    Validate DPI value.
    
    Args:
        dpi: DPI value to validate
        
    Returns:
        Validated DPI value
        
    Raises:
        ValueError: If DPI is invalid
    """
    valid_dpis = current_app.config['DPI_OPTIONS'].keys()
    if dpi not in valid_dpis:
        raise ValueError(f"DPI must be one of: {list(valid_dpis)}")
    return dpi


def calculate_output_dimensions(width_inches: float, height_inches: float, dpi: int) -> Tuple[int, int]:
    """
    Calculate output pixel dimensions.
    
    Args:
        width_inches: Width in inches
        height_inches: Height in inches
        dpi: DPI resolution
        
    Returns:
        Tuple of (width_pixels, height_pixels)
    """
    width_px = int(width_inches * dpi)
    height_px = int(height_inches * dpi)
    return width_px, height_px


def get_format_display_name(format_id: str, orientation: str = 'portrait') -> str:
    """
    Get human-readable format name.
    
    Args:
        format_id: Format identifier
        orientation: 'portrait' or 'landscape'
        
    Returns:
        Display name string
    """
    formats = current_app.config['PAGE_FORMATS']
    if format_id not in formats:
        return f"Unknown ({format_id})"
    
    name = formats[format_id]['name']
    if orientation == 'landscape' and formats[format_id].get('orientable', True):
        name += " (Landscape)"
    elif orientation == 'portrait':
        name += " (Portrait)"
    
    return name