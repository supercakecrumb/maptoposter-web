"""Geocoding service with caching and rate limiting."""

from typing import Dict, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import json
from flask import current_app
from app.extensions import get_redis_client


class GeocodingError(Exception):
    """Base exception for geocoding errors."""
    pass


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class GeocodingService:
    """Service for geocoding with caching and rate limiting."""
    
    def __init__(self):
        """Initialize geocoding service."""
        self.geolocator = Nominatim(user_agent="city_map_poster_web")
        self.cache_ttl = 86400 * 30  # 30 days
        self.rate_limit_key = "geocoding:rate_limit"
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max = 10  # 10 requests per minute
    
    def geocode(self, city: str, country: str) -> Optional[Dict]:
        """
        Geocode city to coordinates with caching.
        
        Args:
            city: City name
            country: Country name
            
        Returns:
            Dict with latitude, longitude, display_name, cached flag
            None if location not found
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
            GeocodingError: If geocoding fails
        """
        # Check cache first
        cache_key = f"geocode:{city.lower()}:{country.lower()}"
        
        try:
            redis_client = get_redis_client(current_app)
            cached = redis_client.get(cache_key)
            
            if cached:
                result = json.loads(cached)
                result['cached'] = True
                current_app.logger.info(f"Geocoding cache hit for {city}, {country}")
                return result
        except Exception as e:
            current_app.logger.warning(f"Redis cache error: {e}")
            # Continue without cache
        
        # Check rate limit
        if not self._check_rate_limit():
            raise RateLimitExceeded("Geocoding rate limit exceeded")
        
        # Geocode
        try:
            current_app.logger.info(f"Geocoding {city}, {country}")
            time.sleep(1)  # Respect Nominatim usage policy
            location = self.geolocator.geocode(f"{city}, {country}")
            
            if not location:
                return None
            
            result = {
                'city': city,
                'country': country,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'display_name': location.address,
                'cached': False
            }
            
            # Cache result
            try:
                redis_client = get_redis_client(current_app)
                redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(result)
                )
                current_app.logger.info(f"Cached geocoding result for {city}, {country}")
            except Exception as e:
                current_app.logger.warning(f"Failed to cache geocoding result: {e}")
            
            return result
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            current_app.logger.error(f"Geocoding failed for {city}, {country}: {e}")
            raise GeocodingError(f"Geocoding failed: {str(e)}")
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows request.
        
        Returns:
            True if request is allowed, False otherwise
        """
        try:
            redis_client = get_redis_client(current_app)
            current = redis_client.incr(self.rate_limit_key)
            
            if current == 1:
                redis_client.expire(self.rate_limit_key, self.rate_limit_window)
            
            return current <= self.rate_limit_max
        except Exception as e:
            current_app.logger.warning(f"Rate limit check failed: {e}")
            # Allow request if rate limiting fails
            return True