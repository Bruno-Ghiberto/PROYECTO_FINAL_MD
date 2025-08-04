import requests
import json
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
import hashlib

from config import Config

logger = logging.getLogger(__name__)

class HorizonsService:
    """Enhanced service for fetching orbital data from NASA JPL Horizons API"""
    
    def __init__(self):
        self.lookup_url = Config.HORIZONS_LOOKUP_API_URL
        self.horizons_url = Config.HORIZONS_API_URL
        self.timeout = 10
        self._spkid_cache = {}
        
        # File-based cache for Horizons data
        self.cache_dir = Config.CACHE_DIR / 'horizons'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 86400  # 24 hours
    
    def get_orbital_data(self, object_id: str, object_name: str) -> Optional[Dict]:
        """
        Get orbital data for an object using Horizons API with caching
        
        Args:
            object_id: ID of the object (may not be SPK-ID)
            object_name: Name of the object
            
        Returns:
            Dict with orbital data or None if not found
        """
        # Check cache first
        cache_key = self._get_cache_key(object_id, object_name)
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            logger.info(f"Using cached Horizons data for {object_name}")
            return cached_data
        
        try:
            # Try to get minimal data - don't always need full ephemeris
            # For display purposes, we mainly need basic orbital parameters
            
            # First try to get SPK-ID
            spkid_info = self._get_spkid(object_name)
            if not spkid_info:
                # If we can't find it in Horizons, return basic info
                return self._get_basic_info(object_id, object_name)
            
            # Get basic orbital data without full ephemeris (faster)
            orbital_data = self._get_basic_orbital_data(spkid_info)
            
            # Cache the result
            if orbital_data:
                self._save_to_cache(cache_key, orbital_data)
            
            return orbital_data
            
        except Exception as e:
            logger.error(f"Error getting orbital data for {object_name}: {e}")
            return self._get_basic_info(object_id, object_name)
    
    def _get_basic_info(self, object_id: str, object_name: str) -> Dict:
        """Return basic info when Horizons data is not available"""
        return {
            'object_id': object_id,
            'name': object_name,
            'source': 'local_data',
            'note': 'Detailed orbital data not available from Horizons'
        }
    
    def _get_cache_key(self, object_id: str, object_name: str) -> str:
        """Generate cache key"""
        key = f"{object_id}_{object_name}".lower()
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if exists and not expired"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            # Check if cache is still valid
            mtime = cache_file.stat().st_mtime
            age = datetime.now().timestamp() - mtime
            
            if age < self.cache_ttl:
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error reading cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save data to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def _get_spkid(self, object_name: str) -> Optional[Dict]:
        """Get SPK-ID for an object using Horizons lookup API"""
        # Check memory cache first
        cache_key = object_name.lower()
        if cache_key in self._spkid_cache:
            return self._spkid_cache[cache_key]
        
        try:
            params = {
                'sstr': object_name,
                'format': 'json'
            }
            
            response = requests.get(self.lookup_url, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if not data.get('count', 0) or 'result' not in data:
                return None
            
            # Take first result
            first_result = data['result'][0]
            
            spkid_info = {
                'spkid': first_result.get('spkid'),
                'name': first_result.get('name'),
                'aliases': first_result.get('alias', []),
                'type': first_result.get('type')
            }
            
            # Cache result in memory
            self._spkid_cache[cache_key] = spkid_info
            
            return spkid_info
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout looking up SPK-ID for {object_name}")
            return None
        except Exception as e:
            logger.error(f"Error looking up SPK-ID for {object_name}: {e}")
            return None
    
    def _get_basic_orbital_data(self, spkid_info: Dict) -> Optional[Dict]:
        """Get basic orbital data without full ephemeris (faster)"""
        try:
            # Request only object data, no ephemeris for speed
            params = {
                'format': 'json',
                'COMMAND': f"'{spkid_info['spkid']}'",
                'OBJ_DATA': 'YES',
                'MAKE_EPHEM': 'NO'  # Don't generate ephemeris table
            }
            
            response = requests.get(self.horizons_url, params=params, timeout=self.timeout)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'result' not in data:
                return None
            
            # Parse just the object data
            result_text = data['result']
            
            orbital_data = {
                'spkid': spkid_info['spkid'],
                'official_name': spkid_info['name'],
                'object_type': spkid_info.get('type'),
                'aliases': spkid_info.get('aliases', []),
                'source': 'horizons'
            }
            
            # Extract basic parameters with simple regex
            # Absolute magnitude
            mag_match = re.search(r'Absolute\s+magnitude.*?H\s*=\s*([\d.-]+)', result_text)
            if mag_match:
                orbital_data['absolute_magnitude'] = float(mag_match.group(1))
            
            # Diameter
            diam_match = re.search(r'diameter.*?([\d.]+)\s*km', result_text, re.IGNORECASE)
            if diam_match:
                orbital_data['diameter_km'] = float(diam_match.group(1))
            
            # Rotation period
            rot_match = re.search(r'Rotation.*?period.*?([\d.]+)\s*h', result_text, re.IGNORECASE)
            if rot_match:
                orbital_data['rotation_period_hours'] = float(rot_match.group(1))
            
            # Add basic ephemeris info if needed
            orbital_data['ephemeris_note'] = 'For detailed position data, please visit JPL Horizons'
            
            return orbital_data
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout getting data for SPK-ID {spkid_info['spkid']}")
            return None
        except Exception as e:
            logger.error(f"Error getting data for SPK-ID {spkid_info['spkid']}: {e}")
            return None