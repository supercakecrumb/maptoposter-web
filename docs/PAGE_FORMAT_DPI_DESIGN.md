# Page Format and DPI Selection - Technical Design Document

**Version**: 1.0  
**Date**: 2026-01-21  
**Status**: Design Phase

## Table of Contents
1. [Overview](#overview)
2. [Current State Analysis](#current-state-analysis)
3. [Configuration Schema](#configuration-schema)
4. [Database Schema Changes](#database-schema-changes)
5. [API Design](#api-design)
6. [UI Design](#ui-design)
7. [Rendering Logic](#rendering-logic)
8. [Backward Compatibility](#backward-compatibility)
9. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Goals
- Support multiple standard print formats (A4, A3, A2, 30×40cm, 40×50cm, 50×70cm)
- Keep current 12×16" as "Classic" format
- Allow custom dimensions
- Support Portrait/Landscape orientation
- Provide 3 DPI options: 150 (preview), 300 (standard), 600 (high-quality)
- Include educational guidance on DPI selection
- Maintain full backward compatibility with existing posters

### Success Criteria
- ✅ Users can select from 8 predefined formats + custom option
- ✅ Users can choose orientation (portrait/landscape)
- ✅ Users can select DPI with clear explanations
- ✅ Existing posters continue to display correctly
- ✅ Database stores all format metadata
- ✅ Rendering engine dynamically calculates dimensions

---

## Current State Analysis

### Fixed Dimensions
- **Current size**: 12×16 inches (portrait)
- **Aspect ratio**: 3:4
- **Location**: Hardcoded in [`map_generator.py:395`](../app/services/map_generator.py:395)
  ```python
  fig, ax = plt.subplots(figsize=(12, 16), facecolor=theme['bg'])
  ```

### Fixed DPI
- **Preview mode**: 150 DPI (line 489)
- **Final mode**: 300 DPI (line 489)
- **Location**: [`map_generator.py:489`](../app/services/map_generator.py:489)
  ```python
  dpi = 150 if preview_mode else 300
  ```

### Implications
- No flexibility in output size
- No support for standard print formats
- Limited resolution options for professional printing
- Preview mode tied to DPI rather than being a separate concept

---

## Configuration Schema

### 1. Page Format Configuration (`app/config.py`)

Add to the `Config` class:

```python
class Config:
    # ... existing config ...
    
    # Page Format Configuration
    PAGE_FORMATS = {
        'classic': {
            'name': 'Classic Poster',
            'width_inches': 12,
            'height_inches': 16,
            'aspect_ratio': 0.75,  # 3:4
            'description': 'Original 12×16 inch format',
            'orientable': True
        },
        'a4': {
            'name': 'A4',
            'width_mm': 210,
            'height_mm': 297,
            'width_inches': 8.27,
            'height_inches': 11.69,
            'aspect_ratio': 0.707,  # √2
            'description': 'Standard A4 (210×297mm)',
            'orientable': True
        },
        'a3': {
            'name': 'A3',
            'width_mm': 297,
            'height_mm': 420,
            'width_inches': 11.69,
            'height_inches': 16.54,
            'aspect_ratio': 0.707,  # √2
            'description': 'Standard A3 (297×420mm)',
            'orientable': True
        },
        'a2': {
            'name': 'A2',
            'width_mm': 420,
            'height_mm': 594,
            'width_inches': 16.54,
            'height_inches': 23.39,
            'aspect_ratio': 0.707,  # √2
            'description': 'Standard A2 (420×594mm)',
            'orientable': True
        },
        '30x40': {
            'name': '30×40 cm',
            'width_cm': 30,
            'height_cm': 40,
            'width_inches': 11.81,
            'height_inches': 15.75,
            'aspect_ratio': 0.75,  # 3:4
            'description': 'Popular print size 30×40cm',
            'orientable': True
        },
        '40x50': {
            'name': '40×50 cm',
            'width_cm': 40,
            'height_cm': 50,
            'width_inches': 15.75,
            'height_inches': 19.69,
            'aspect_ratio': 0.8,  # 4:5
            'description': 'Popular print size 40×50cm',
            'orientable': True
        },
        '50x70': {
            'name': '50×70 cm',
            'width_cm': 50,
            'height_cm': 70,
            'width_inches': 19.69,
            'height_inches': 27.56,
            'aspect_ratio': 0.714,  # 5:7
            'description': 'Popular print size 50×70cm',
            'orientable': True
        },
        'custom': {
            'name': 'Custom Size',
            'description': 'User-defined dimensions',
            'orientable': True,
            'requires_dimensions': True
        }
    }
    
    # DPI Configuration
    DPI_OPTIONS = {
        150: {
            'name': 'Screen/Web (150 DPI)',
            'description': 'Fast preview, suitable for screen viewing',
            'use_cases': ['Digital display', 'Quick preview', 'Social media'],
            'recommended_for': 'Preview and web use',
            'file_size': 'Small (~2-5 MB)',
            'quality': 'Basic'
        },
        300: {
            'name': 'Standard Print (300 DPI)',
            'description': 'Standard print quality for most applications',
            'use_cases': ['Home printing', 'Photo prints', 'Standard posters'],
            'recommended_for': 'Most printing needs',
            'file_size': 'Medium (~8-20 MB)',
            'quality': 'High'
        },
        600: {
            'name': 'Professional Print (600 DPI)',
            'description': 'Highest quality for professional printing',
            'use_cases': ['Commercial printing', 'Gallery quality', 'Fine art'],
            'recommended_for': 'Professional print services',
            'file_size': 'Large (~30-80 MB)',
            'quality': 'Maximum'
        }
    }
    
    # Validation Limits
    MIN_PAGE_SIZE_INCHES = 4    # Minimum 4 inches
    MAX_PAGE_SIZE_INCHES = 48   # Maximum 48 inches (4 feet)
    DEFAULT_PAGE_FORMAT = 'classic'
    DEFAULT_DPI = 300
    DEFAULT_ORIENTATION = 'portrait'
```

### 2. Format Validation Helper Functions

Add utility module `app/utils/format_helpers.py`:

```python
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
```

---

## Database Schema Changes

### 1. Job Model Changes (`app/models.py`)

Add new fields to the `Job` model:

```python
class Job(db.Model):
    # ... existing fields ...
    
    # Page format fields (NEW)
    page_format = db.Column(db.String(20), nullable=False, default='classic')
    orientation = db.Column(db.String(10), nullable=False, default='portrait')  # portrait/landscape
    custom_width_inches = db.Column(db.Float, nullable=True)  # Only for custom format
    custom_height_inches = db.Column(db.Float, nullable=True)  # Only for custom format
    dpi = db.Column(db.Integer, nullable=False, default=300)
    
    # ... rest of existing fields ...
```

### 2. Poster Model Changes (`app/models.py`)

Add new fields to the `Poster` model:

```python
class Poster(db.Model):
    # ... existing fields ...
    
    # Page format fields (NEW)
    page_format = db.Column(db.String(20), nullable=False, default='classic')
    orientation = db.Column(db.String(10), nullable=False, default='portrait')
    custom_width_inches = db.Column(db.Float, nullable=True)
    custom_height_inches = db.Column(db.Float, nullable=True)
    dpi = db.Column(db.Integer, nullable=False, default=300)
    width_inches = db.Column(db.Float, nullable=False, default=12.0)
    height_inches = db.Column(db.Float, nullable=False, default=16.0)
    
    # Note: width/height fields already exist as pixel dimensions
    # width_inches/height_inches store the physical print size
    
    # ... rest of existing fields ...
    
    def to_dict(self, include_urls=True):
        """Convert poster to dictionary for API responses."""
        result = {
            # ... existing fields ...
            'page_format': self.page_format,
            'orientation': self.orientation,
            'dpi': self.dpi,
            'dimensions': {
                'width_px': self.width,
                'height_px': self.height,
                'width_inches': self.width_inches,
                'height_inches': self.height_inches,
                'dpi': self.dpi
            },
            # ... rest of existing fields ...
        }
        
        # Add custom dimensions if applicable
        if self.page_format == 'custom':
            result['custom_dimensions'] = {
                'width_inches': self.custom_width_inches,
                'height_inches': self.custom_height_inches
            }
        
        return result
```

### 3. Migration Script

Create migration file `migrations/add_page_format_fields.sql`:

```sql
-- Add page format fields to jobs table
ALTER TABLE jobs ADD COLUMN page_format VARCHAR(20) DEFAULT 'classic' NOT NULL;
ALTER TABLE jobs ADD COLUMN orientation VARCHAR(10) DEFAULT 'portrait' NOT NULL;
ALTER TABLE jobs ADD COLUMN custom_width_inches FLOAT;
ALTER TABLE jobs ADD COLUMN custom_height_inches FLOAT;
ALTER TABLE jobs ADD COLUMN dpi INTEGER DEFAULT 300 NOT NULL;

-- Add page format fields to posters table
ALTER TABLE posters ADD COLUMN page_format VARCHAR(20) DEFAULT 'classic' NOT NULL;
ALTER TABLE posters ADD COLUMN orientation VARCHAR(10) DEFAULT 'portrait' NOT NULL;
ALTER TABLE posters ADD COLUMN custom_width_inches FLOAT;
ALTER TABLE posters ADD COLUMN custom_height_inches FLOAT;
ALTER TABLE posters ADD COLUMN dpi INTEGER DEFAULT 300 NOT NULL;
ALTER TABLE posters ADD COLUMN width_inches FLOAT DEFAULT 12.0 NOT NULL;
ALTER TABLE posters ADD COLUMN height_inches FLOAT DEFAULT 16.0 NOT NULL;

-- Create indices for common queries
CREATE INDEX idx_posters_page_format ON posters(page_format);
CREATE INDEX idx_posters_dpi ON posters(dpi);
CREATE INDEX idx_jobs_page_format ON jobs(page_format);
```

---

## API Design

### 1. Request Parameters (`app/api/posters.py`)

Update the `create_poster` endpoint:

```python
@api_v1.route('/posters', methods=['POST'])
def create_poster():
    """
    Create a new poster generation job.
    
    Request Body:
        city: City name (required)
        country: Country name (required)
        theme: Theme name (required)
        distance: Map radius in meters (optional, default 29000)
        latitude: Latitude (optional, will geocode if missing)
        longitude: Longitude (optional)
        
        # NEW FORMAT PARAMETERS
        page_format: Format ID (optional, default 'classic')
                    Options: 'classic', 'a4', 'a3', 'a2', '30x40', '40x50', '50x70', 'custom'
        orientation: 'portrait' or 'landscape' (optional, default 'portrait')
        custom_width: Width in inches for custom format (required if page_format='custom')
        custom_height: Height in inches for custom format (required if page_format='custom')
        dpi: DPI resolution (optional, default 300)
             Options: 150 (preview), 300 (standard), 600 (professional)
        
        preview_mode: Boolean for preview mode (optional, default False)
        
    Returns:
        JSON response with job information
    """
    # ... implementation ...
```

### 2. Validation Logic

Add validation function in `app/api/posters.py`:

```python
def validate_format_parameters(data: dict) -> dict:
    """
    Validate page format parameters.
    
    Args:
        data: Request data dictionary
        
    Returns:
        Dict with validated format parameters
        
    Raises:
        ValueError with descriptive message if validation fails
    """
    from app.utils.format_helpers import get_format_dimensions, validate_dpi
    
    # Get parameters with defaults
    page_format = data.get('page_format', current_app.config['DEFAULT_PAGE_FORMAT'])
    orientation = data.get('orientation', current_app.config['DEFAULT_ORIENTATION'])
    dpi = data.get('dpi', current_app.config['DEFAULT_DPI'])
    
    # Validate format exists
    if page_format not in current_app.config['PAGE_FORMATS']:
        valid_formats = list(current_app.config['PAGE_FORMATS'].keys())
        raise ValueError(f"Invalid page_format. Must be one of: {valid_formats}")
    
    # Validate orientation
    if orientation not in ['portrait', 'landscape']:
        raise ValueError("orientation must be 'portrait' or 'landscape'")
    
    # Validate DPI
    try:
        dpi = int(dpi)
        dpi = validate_dpi(dpi)
    except (ValueError, TypeError) as e:
        valid_dpis = list(current_app.config['DPI_OPTIONS'].keys())
        raise ValueError(f"Invalid DPI. Must be one of: {valid_dpis}")
    
    # Handle custom format
    custom_width = None
    custom_height = None
    if page_format == 'custom':
        custom_width = data.get('custom_width')
        custom_height = data.get('custom_height')
        
        if custom_width is None or custom_height is None:
            raise ValueError("custom_width and custom_height are required for custom format")
        
        try:
            custom_width = float(custom_width)
            custom_height = float(custom_height)
        except (ValueError, TypeError):
            raise ValueError("custom_width and custom_height must be numeric")
    
    # Get actual dimensions (validates custom dimensions if applicable)
    try:
        width_inches, height_inches = get_format_dimensions(
            page_format, orientation, custom_width, custom_height
        )
    except ValueError as e:
        raise ValueError(f"Format validation error: {str(e)}")
    
    return {
        'page_format': page_format,
        'orientation': orientation,
        'custom_width_inches': custom_width,
        'custom_height_inches': custom_height,
        'dpi': dpi,
        'width_inches': width_inches,
        'height_inches': height_inches
    }
```

### 3. Updated Create Endpoint

```python
@api_v1.route('/posters', methods=['POST'])
def create_poster():
    """Create a new poster generation job."""
    try:
        data = request.get_json()
        
        # ... existing validation for city, country, theme, distance ...
        
        # NEW: Validate format parameters
        try:
            format_params = validate_format_parameters(data)
        except ValueError as e:
            return jsonify({
                'error': 'Format validation error',
                'message': str(e)
            }), 400
        
        # Create poster generation job with format parameters
        poster_service = PosterService()
        result = poster_service.create_poster_job(
            city=city,
            country=country,
            theme=theme,
            distance=distance,
            latitude=latitude,
            longitude=longitude,
            preview_mode=preview_mode,
            session_id=session_id,
            # NEW format parameters
            page_format=format_params['page_format'],
            orientation=format_params['orientation'],
            custom_width_inches=format_params.get('custom_width_inches'),
            custom_height_inches=format_params.get('custom_height_inches'),
            dpi=format_params['dpi']
        )
        
        return jsonify(result), 202
        
    except Exception as e:
        current_app.logger.error(f"Error creating poster job: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to create poster generation job'
        }), 500
```

### 4. New Endpoints

Add helper endpoints:

```python
@api_v1.route('/formats', methods=['GET'])
def get_page_formats():
    """
    Get available page formats.
    
    Returns:
        JSON response with format configurations and DPI options
    """
    return jsonify({
        'formats': current_app.config['PAGE_FORMATS'],
        'dpi_options': current_app.config['DPI_OPTIONS'],
        'defaults': {
            'page_format': current_app.config['DEFAULT_PAGE_FORMAT'],
            'orientation': current_app.config['DEFAULT_ORIENTATION'],
            'dpi': current_app.config['DEFAULT_DPI']
        }
    }), 200
```

---

## UI Design

### 1. HTML Structure (`app/templates/create.html`)

Add new section after the "Map Radius" section:

```html
<!-- Page Format & Print Settings -->
<div class="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
    <h2 class="text-xl font-semibold text-white mb-4">Page Format & Print Settings</h2>
    
    <!-- Format Selection -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-300 mb-2">Page Size *</label>
        <select
            x-model="form.page_format"
            @change="onFormatChange()"
            class="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500"
        >
            <template x-for="format in formats" :key="format.id">
                <option :value="format.id" x-text="format.name + ' - ' + format.description"></option>
            </template>
        </select>
        
        <!-- Format Info Display -->
        <div x-show="selectedFormat" class="mt-2 text-xs text-gray-400">
            <span x-text="formatDimensionsText"></span>
        </div>
    </div>
    
    <!-- Custom Dimensions (only shown for custom format) -->
    <div x-show="form.page_format === 'custom'" class="mb-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Width (inches) *</label>
                <input
                    type="number"
                    x-model="form.custom_width"
                    min="4"
                    max="48"
                    step="0.1"
                    class="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 12"
                >
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Height (inches) *</label>
                <input
                    type="number"
                    x-model="form.custom_height"
                    min="4"
                    max="48"
                    step="0.1"
                    class="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., 16"
                >
            </div>
        </div>
        <p class="text-xs text-gray-400">💡 Dimensions must be between 4 and 48 inches</p>
    </div>
    
    <!-- Orientation Toggle -->
    <div class="mb-6" x-show="canChangeOrientation">
        <label class="block text-sm font-medium text-gray-300 mb-2">Orientation</label>
        <div class="flex gap-3">
            <button
                type="button"
                @click="form.orientation = 'portrait'"
                :class="form.orientation === 'portrait' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-gray-300'"
                class="flex-1 px-4 py-3 rounded-lg border border-slate-600 hover:bg-blue-500 transition"
            >
                <svg class="w-6 h-8 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <rect x="7" y="3" width="10" height="18" stroke-width="2" rx="1"/>
                </svg>
                Portrait
            </button>
            <button
                type="button"
                @click="form.orientation = 'landscape'"
                :class="form.orientation === 'landscape' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-gray-300'"
                class="flex-1 px-4 py-3 rounded-lg border border-slate-600 hover:bg-blue-500 transition"
            >
                <svg class="w-8 h-6 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <rect x="3" y="7" width="18" height="10" stroke-width="2" rx="1"/>
                </svg>
                Landscape
            </button>
        </div>
    </div>
    
    <!-- DPI Selection -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-300 mb-2">
            Print Quality (DPI) *
            <button
                type="button"
                @click="showDpiHelp = !showDpiHelp"
                class="ml-2 text-blue-400 hover:text-blue-300"
            >
                <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            </button>
        </label>
        
        <!-- DPI Help Text (Collapsible) -->
        <div x-show="showDpiHelp" class="mb-3 p-3 bg-blue-900/20 border border-blue-700/30 rounded text-xs text-gray-300">
            <p class="font-semibold text-blue-400 mb-2">🎨 Understanding DPI (Dots Per Inch)</p>
            <p class="mb-2">DPI determines the resolution and detail of your printed poster. Higher DPI = more detail, but larger files and longer processing.</p>
            <ul class="list-disc pl-5 space-y-1">
                <li><strong>150 DPI:</strong> Best for digital viewing, social media, or quick previews</li>
                <li><strong>300 DPI:</strong> Standard print quality - suitable for most home and commercial printing</li>
                <li><strong>600 DPI:</strong> Professional quality - for gallery prints, fine art, and professional print services</li>
            </ul>
            <p class="mt-2 text-yellow-400">💡 <strong>Recommendation:</strong> Use 300 DPI for most prints. Only use 600 DPI if you need professional-quality output or plan to print very large sizes.</p>
        </div>
        
        <!-- DPI Options -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <template x-for="dpi in dpiOptions" :key="dpi.value">
                <button
                    type="button"
                    @click="form.dpi = dpi.value"
                    :class="form.dpi === dpi.value ? 'bg-blue-600 border-blue-500' : 'bg-slate-700 border-slate-600'"
                    class="p-4 rounded-lg border-2 hover:border-blue-400 transition text-left"
                >
                    <div class="font-semibold text-white mb-1" x-text="dpi.name"></div>
                    <div class="text-xs text-gray-400 mb-2" x-text="dpi.recommended_for"></div>
                    <div class="text-xs space-y-1">
                        <div class="flex items-center text-gray-400">
                            <span class="mr-2">📦</span>
                            <span x-text="dpi.file_size"></span>
                        </div>
                        <div class="flex items-center text-gray-400">
                            <span class="mr-2">⏱️</span>
                            <span x-text="dpi.processing_time"></span>
                        </div>
                    </div>
                </button>
            </template>
        </div>
    </div>
    
    <!-- Estimated Output Info -->
    <div class="mt-4 p-3 bg-slate-700/50 rounded-lg text-sm text-gray-300">
        <div class="flex items-start">
            <svg class="w-5 h-5 mr-2 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
                <p class="font-semibold mb-1">Output Details</p>
                <p x-text="outputDetailsText"></p>
            </div>
        </div>
    </div>
</div>
```

### 2. JavaScript Component Updates (`app/static/js/app.js`)

Update the `posterCreator` function:

```javascript
function posterCreator() {
    return {
        form: {
            location: '',
            theme: 'noir',
            distance: 29000,
            latitude: null,
            longitude: null,
            // NEW format fields
            page_format: 'classic',
            orientation: 'portrait',
            custom_width: 12,
            custom_height: 16,
            dpi: 300
        },
        formats: [],
        dpiOptions: [],
        showDpiHelp: false,
        themes: [],
        selectedThemeIds: [],
        suggestions: [],
        showSuggestions: false,
        searchTimeout: null,
        loading: false,
        error: null,
        
        async init() {
            try {
                // Load themes
                const themesResponse = await fetch('/api/v1/themes');
                const themesData = await themesResponse.json();
                this.themes = themesData.themes;
                
                // Load formats and DPI options
                const formatsResponse = await fetch('/api/v1/formats');
                const formatsData = await formatsResponse.json();
                
                // Convert formats object to array
                this.formats = Object.entries(formatsData.formats).map(([id, config]) => ({
                    id,
                    ...config
                }));
                
                // Convert DPI options object to array with additional UI info
                this.dpiOptions = Object.entries(formatsData.dpi_options).map(([value, config]) => ({
                    value: parseInt(value),
                    ...config,
                    processing_time: this.estimateProcessingTime(parseInt(value))
                }));
                
                // Set defaults
                this.form.page_format = formatsData.defaults.page_format;
                this.form.orientation = formatsData.defaults.orientation;
                this.form.dpi = formatsData.defaults.dpi;
                
                // ... rest of existing init logic ...
            } catch (error) {
                console.error('Failed to load configuration:', error);
            }
        },
        
        estimateProcessingTime(dpi) {
            // Rough estimates based on DPI
            const times = {
                150: '~30-60 seconds',
                300: '~60-120 seconds',
                600: '~2-5 minutes'
            };
            return times[dpi] || 'Unknown';
        },
        
        get selectedFormat() {
            return this.formats.find(f => f.id === this.form.page_format);
        },
        
        get canChangeOrientation() {
            const format = this.selectedFormat;
            return format && format.orientable !== false;
        },
        
        get formatDimensionsText() {
            const format = this.selectedFormat;
            if (!format) return '';
            
            if (format.id === 'custom') {
                return 'Enter custom dimensions below';
            }
            
            const width = format.width_inches;
            const height = format.height_inches;
            
            if (this.form.orientation === 'landscape') {
                return `${Math.max(width, height).toFixed(2)}" × ${Math.min(width, height).toFixed(2)}" (landscape)`;
            } else {
                return `${Math.min(width, height).toFixed(2)}" × ${Math.max(width, height).toFixed(2)}" (portrait)`;
            }
        },
        
        get outputDetailsText() {
            const format = this.selectedFormat;
            if (!format) return '';
            
            let width, height;
            
            if (format.id === 'custom') {
                width = parseFloat(this.form.custom_width) || 0;
                height = parseFloat(this.form.custom_height) || 0;
            } else {
                width = format.width_inches;
                height = format.height_inches;
            }
            
            if (this.form.orientation === 'landscape') {
                [width, height] = [Math.max(width, height), Math.min(width, height)];
            } else {
                [width, height] = [Math.min(width, height), Math.max(width, height)];
            }
            
            const widthPx = Math.round(width * this.form.dpi);
            const heightPx = Math.round(height * this.form.dpi);
            const mpx = ((widthPx * heightPx) / 1000000).toFixed(1);
            
            return `${width.toFixed(1)}" × ${height.toFixed(1)}" at ${this.form.dpi} DPI = ${widthPx} × ${heightPx} pixels (${mpx} megapixels)`;
        },
        
        onFormatChange() {
            // Reset custom dimensions when switching from custom
            if (this.form.page_format !== 'custom') {
                // Auto-adjust orientation based on format
                const format = this.selectedFormat;
                if (format && format.aspect_ratio) {
                    // Keep current orientation if possible
                    if (!format.orientable) {
                        this.form.orientation = 'portrait';
                    }
                }
            }
        },
        
        async createPoster() {
            this.loading = true;
            this.error = null;
            
            try {
                const locationParts = this.form.location.split(',').map(s => s.trim());
                
                const basePayload = {
                    city: locationParts[0] || this.form.location,
                    country: locationParts[1] || '',
                    distance: this.form.distance,
                    latitude: this.form.latitude,
                    longitude: this.form.longitude,
                    // NEW format parameters
                    page_format: this.form.page_format,
                    orientation: this.form.orientation,
                    dpi: this.form.dpi
                };
                
                // Add custom dimensions if applicable
                if (this.form.page_format === 'custom') {
                    basePayload.custom_width = parseFloat(this.form.custom_width);
                    basePayload.custom_height = parseFloat(this.form.custom_height);
                }
                
                if (this.selectedThemeIds.length > 1) {
                    await this.submitBatchPoster(basePayload);
                } else {
                    await this.submitSinglePoster(basePayload);
                }
            } catch (error) {
                this.error = 'Network error. Please try again.';
            } finally {
                this.loading = false;
            }
        },
        
        async submitSinglePoster(basePayload) {
            const payload = {
                ...basePayload,
                theme: this.selectedThemeIds[0]
            };
            
            const response = await fetch('/api/v1/posters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                window.location.href = `/generate/${data.job_id}`;
            } else {
                this.error = data.message || 'Failed to create poster';
            }
        },
        
        async submitBatchPoster(basePayload) {
            const payload = {
                ...basePayload,
                themes: this.selectedThemeIds
            };
            
            const response = await fetch('/api/v1/posters/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            };
            
            const data = await response.json();
            
            if (response.ok) {
                window.location.href = `/batch/${data.batch_id}`;
            } else {
                this.error = data.message || 'Failed to create batch posters';
            }
        },
        
        // ... rest of existing methods ...
    };
}
```

---

## Rendering Logic

### 1. Update Map Generator (`app/services/map_generator.py`)

Modify the `render_poster` function signature and implementation:

```python
def render_poster(
    map_data: Dict,
    theme: Dict,
    city: str,
    country: str,
    point: Tuple[float, float],
    output_file: str,
    width_inches: float,
    height_inches: float,
    dpi: int,
    progress_callback: Optional[Callable] = None
):
    """
    Render a map poster using pre-fetched map data.
    
    Args:
        map_data: Dictionary containing 'graph', 'water', 'parks', 'bounds'
        theme: Theme dictionary with color and style settings
        city: City name for the poster text
        country: Country name for the poster text
        point: Tuple of (latitude, longitude)
        output_file: Path where the poster will be saved
        width_inches: Width of the poster in inches
        height_inches: Height of the poster in inches
        dpi: DPI resolution for output
        progress_callback: Optional callback function(stage_name)
    """
    logger.info(f"Rendering map for {city}, {country}...")
    logger.info(f"Theme: {theme.get('name', 'Unknown')}")
    logger.info(f"Dimensions: {width_inches}\" × {height_inches}\" at {dpi} DPI")
    logger.info(f"Output: {output_file}")
    
    # Extract data from map_data dictionary
    G = map_data['graph']
    water = map_data['water']
    parks = map_data['parks']
    
    logger.info(f"Map data - Graph edges: {G.number_of_edges()}, "
                f"Water features: {len(water) if water is not None and not water.empty else 0}, "
                f"Parks: {len(parks) if parks is not None and not parks.empty else 0}")
    
    # Setup Plot with dynamic figsize
    if progress_callback:
        progress_callback("initializing")
    
    # CHANGED: Use provided dimensions instead of hardcoded (12, 16)
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), facecolor=theme['bg'])
    ax.set_facecolor(theme['bg'])
    ax.set_position([0, 0, 1, 1])
    
    # ... (rest of the rendering logic remains the same) ...
    
    # Save with specified DPI
    if progress_callback:
        progress_callback("saving")
    
    # CHANGED: Use provided DPI instead of conditional logic
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
```

### 2. Update Task Handler (`app/tasks/poster_tasks.py`)

Modify the `generate_poster` task:

```python
@celery_app.task(bind=True, name='app.tasks.generate_poster')
def generate_poster(self, job_id: str):
    """Generate poster in background."""
    # ... existing job lookup logic ...
    
    try:
        # ... existing status update logic ...
        
        # Get dimensions from job
        from app.utils.format_helpers import get_format_dimensions, calculate_output_dimensions
        
        width_inches, height_inches = get_format_dimensions(
            format_id=job.page_format,
            orientation=job.orientation,
            custom_width=job.custom_width_inches,
            custom_height=job.custom_height_inches
        )
        
        # Calculate output pixel dimensions
        width_px, height_px = calculate_output_dimensions(
            width_inches, height_inches, job.dpi
        )
        
        # ... existing fetch and render logic ...
        
        render_poster(
            map_data=map_data,
            theme=theme_obj,
            city=job.city,
            country=job.country,
            point=point,
            output_file=output_file,
            width_inches=width_inches,  # NEW
            height_inches=height_inches,  # NEW
            dpi=job.dpi,  # NEW (replaces preview_mode logic)
            progress_callback=render_progress_callback
        )
        
        # ... existing file verification ...
        
        # Create poster record with format info
        poster = Poster(
            id=str(uuid.uuid4()),
            job_id=job.id,
            city=job.city,
            country=job.country,
            theme=job.theme,
            distance=job.distance,
            latitude=job.latitude,
            longitude=job.longitude,
            filename=result['filename'],
            file_path=result['file_path'],
            file_size=result['file_size'],
            width=width_px,  # Pixel dimensions
            height=height_px,
            width_inches=width_inches,  # NEW: Physical dimensions
            height_inches=height_inches,  # NEW
            page_format=job.page_format,  # NEW
            orientation=job.orientation,  # NEW
            custom_width_inches=job.custom_width_inches,  # NEW
            custom_height_inches=job.custom_height_inches,  # NEW
            dpi=job.dpi,  # NEW
            thumbnail_path=result.get('thumbnail_path'),
            session_id=job.session_id,
            created_at=datetime.utcnow()
        )
        
        # ... rest of completion logic ...
    
    except Exception as e:
        # ... existing error handling ...
```

### 3. Update Service Layer (`app/services/poster_service.py`)

Update `create_poster_job` method:

```python
def create_poster_job(
    self,
    city: str,
    country: str,
    theme: str,
    distance: int,
    latitude: float,
    longitude: float,
    preview_mode: bool,
    session_id: str,
    # NEW format parameters
    page_format: str = 'classic',
    orientation: str = 'portrait',
    custom_width_inches: Optional[float] = None,
    custom_height_inches: Optional[float] = None,
    dpi: int = 300
) -> Dict:
    """Create a poster generation job."""
    
    job = Job(
        id=str(uuid.uuid4()),
        city=city,
        country=country,
        theme=theme,
        distance=distance,
        latitude=latitude,
        longitude=longitude,
        preview_mode=preview_mode,
        session_id=session_id,
        # NEW format fields
        page_format=page_format,
        orientation=orientation,
        custom_width_inches=custom_width_inches,
        custom_height_inches=custom_height_inches,
        dpi=dpi,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.session.add(job)
    db.session.commit()
    
    # Queue the task
    from app.tasks.poster_tasks import generate_poster
    generate_poster.delay(job.id)
    
    return job.to_dict()
```

---

## Backward Compatibility

### Strategy

1. **Default Values**: All new fields have defaults matching current behavior
   - `page_format='classic'` (12×16")
   - `orientation='portrait'`
   - `dpi=300` (or 150 for preview_mode)

2. **Migration**: Existing records get default values via SQL `DEFAULT` clause

3. **API Compatibility**: New parameters are optional; old requests work unchanged

4. **Display Logic**: When displaying existing posters without format data:
   ```python
   def get_display_dimensions(poster):
       if poster.page_format:
           return f"{poster.width_inches}\" × {poster.height_inches}\" at {poster.dpi} DPI"
       else:
           # Legacy poster - infer from pixel dimensions
           return f"{poster.width}px × {poster.height}px"
   ```

5. **Preview Mode Conversion**: For jobs with `preview_mode=True` and no DPI set:
   ```python
   # In create_poster_job
   if preview_mode and dpi == 300:  # Default DPI
       dpi = 150  # Use preview DPI
   ```

### Validation for Legacy Data

Add to poster display logic:

```python
def ensure_format_metadata(poster):
    """Ensure poster has format metadata (add defaults for legacy posters)."""
    if not poster.page_format:
        poster.page_format = 'classic'
        poster.orientation = 'portrait'
        poster.width_inches = 12.0
        poster.height_inches = 16.0
        poster.dpi = 300 if poster.width >= 3600 else 150
        # Don't commit - just for display purposes
    return poster
```

---

## Implementation Checklist

### Phase 1: Configuration & Database
- [ ] Add `PAGE_FORMATS` and `DPI_OPTIONS` to [`app/config.py`](../app/config.py)
- [ ] Create `app/utils/format_helpers.py` with utility functions
- [ ] Add fields to [`Job`](../app/models.py) model
- [ ] Add fields to [`Poster`](../app/models.py) model
- [ ] Create and run migration script
- [ ] Update model `to_dict()` methods

### Phase 2: API Layer
- [ ] Create `validate_format_parameters()` in [`app/api/posters.py`](../app/api/posters.py)
- [ ] Update `create_poster()` endpoint
- [ ] Update `create_batch_posters()` endpoint
- [ ] Create `/api/v1/formats` endpoint
- [ ] Add format parameters to [`PosterService.create_poster_job()`](../app/services/poster_service.py)
- [ ] Add format parameters to `PosterService.create_batch_poster_job()`

### Phase 3: Rendering Engine
- [ ] Update [`render_poster()`](../app/services/map_generator.py) signature
- [ ] Remove hardcoded figsize at [line 395](../app/services/map_generator.py:395)
- [ ] Remove hardcoded DPI at [line 489](../app/services/map_generator.py:489)
- [ ] Update [`generate_poster`](../app/tasks/poster_tasks.py) task
- [ ] Update `generate_batch_posters` task
- [ ] Test rendering with different formats/DPIs

### Phase 4: UI Components
- [ ] Add format section to [`create.html`](../app/templates/create.html)
- [ ] Add custom dimensions inputs
- [ ] Add orientation toggle
- [ ] Add DPI selector with help text
- [ ] Update [`posterCreator()`](../app/static/js/app.js) component
- [ ] Add format loading logic
- [ ] Add dimension calculation logic
- [ ] Test UI responsiveness

### Phase 5: Testing & Documentation
- [ ] Test with all predefined formats
- [ ] Test custom dimensions
- [ ] Test orientation switching
- [ ] Test all DPI options
- [ ] Test backward compatibility with existing posters
- [ ] Test batch generation with new formats
- [ ] Update API documentation
- [ ] Update user guide

### Phase 6: Deployment
- [ ] Run database migration
- [ ] Deploy updated code
- [ ] Monitor error logs
- [ ] Verify existing posters display correctly
- [ ] Create sample posters with new formats

---

## Additional Considerations

### Performance Impact

**DPI 600 Processing Time**:
- File size: ~30-80 MB (vs ~8-20 MB at 300 DPI)
- Processing time: ~2-5× longer
- Memory usage: ~4× higher

**Mitigation**:
- Show clear warnings about processing time
- Consider adding a queue priority system
- Implement file size limits (e.g., 100 MB max)

### Storage Considerations

**Disk Space**:
- 600 DPI posters: ~40 MB average
- 100 posters: ~4 GB
- Recommend implementing cleanup policy for old previews

### User Education

**DPI Help Text** (already included in UI design):
- Explain what DPI means in simple terms
- Show use cases for each option
- Provide file size estimates
- Recommend 300 DPI as default
- Warn about 600 DPI processing time

### Future Enhancements

1. **PDF Output**: Support PDF format for vector graphics
2. **Crop Marks**: Add printer crop marks for professional printing
3. **Bleed Area**: Support bleed margins for edge-to-edge printing
4. **Format Presets**: Save user's favorite format/DPI combinations
5. **Batch Format Mix**: Allow different formats in same batch
6. **Print Templates**: Predefined layouts for common poster sizes

---

## Conclusion

This design provides a comprehensive solution for adding flexible page format and DPI selection to the maptoposter-web application while maintaining backward compatibility and providing clear user guidance. The modular approach allows for phased implementation and easy testing of each component.

Key benefits:
- ✅ Flexible format system supporting industry-standard sizes
- ✅ Three DPI options with clear explanations
- ✅ Custom dimensions for specialized needs
- ✅ Orientation support for all formats
- ✅ Full backward compatibility
- ✅ Clean separation of concerns
- ✅ User-friendly UI with educational content
- ✅ Comprehensive validation at all layers

The implementation can proceed in phases, with each phase being testable independently.