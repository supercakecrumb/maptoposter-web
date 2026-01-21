"""Theme service for managing poster themes."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from flask import current_app


class ThemeService:
    """Service for theme operations."""
    
    def __init__(self, themes_dir: str = "themes"):
        """
        Initialize theme service.
        
        Args:
            themes_dir: Directory containing theme JSON files
        """
        self.themes_dir = Path(themes_dir)
    
    def get_all_themes(self) -> List[Dict]:
        """
        Get all available themes with metadata.
        
        Returns:
            List of theme dictionaries
        """
        themes = []
        
        if not self.themes_dir.exists():
            current_app.logger.warning(f"Themes directory not found: {self.themes_dir}")
            return themes
        
        for theme_file in sorted(self.themes_dir.glob("*.json")):
            theme_data = self._load_theme_file(theme_file)
            if theme_data:
                themes.append({
                    'id': theme_file.stem,
                    'name': theme_data.get('name', theme_file.stem),
                    'description': theme_data.get('description', ''),
                    'preview_url': f'/static/images/themes/{theme_file.stem}_preview.png',
                    'colors': {
                        'bg': theme_data.get('bg'),
                        'text': theme_data.get('text')
                    }
                })
        
        return themes
    
    def get_theme(self, theme_id: str) -> Optional[Dict]:
        """
        Get single theme by ID.
        
        Args:
            theme_id: Theme identifier
            
        Returns:
            Theme dictionary or None if not found
        """
        theme_file = self.themes_dir / f"{theme_id}.json"
        
        if not theme_file.exists():
            return None
        
        theme_data = self._load_theme_file(theme_file)
        if theme_data:
            return {
                'id': theme_id,
                'name': theme_data.get('name', theme_id),
                'description': theme_data.get('description', ''),
                'preview_url': f'/static/images/themes/{theme_id}_preview.png',
                'colors': theme_data
            }
        
        return None
    
    def _load_theme_file(self, file_path: Path) -> Optional[Dict]:
        """
        Load and parse theme JSON file.
        
        Args:
            file_path: Path to theme JSON file
            
        Returns:
            Theme data dictionary or None on error
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.error(f"Error loading theme file {file_path}: {e}")
            return None
    
    def validate_theme_exists(self, theme_id: str) -> bool:
        """
        Check if theme exists.
        
        Args:
            theme_id: Theme identifier
            
        Returns:
            True if theme exists, False otherwise
        """
        return (self.themes_dir / f"{theme_id}.json").exists()