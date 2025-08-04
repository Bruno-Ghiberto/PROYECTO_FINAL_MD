import requests
import time
import os
from typing import Optional, Dict, List
from pathlib import Path
from urllib.parse import quote
import logging

from config import Config

logger = logging.getLogger(__name__)

class ImagesService:
    """Enhanced service for fetching images - prioritizes local images over API calls"""
    
    def __init__(self):
        self.api_url = Config.NASA_IMAGE_API_URL
        self.api_key = Config.NASA_API_KEY
        self.timeout = 5  # Reduced timeout for faster response
        self.retry_delay = 0.5
        
        # Local image paths
        self.local_images_dir = Config.BASE_DIR / 'data' / 'raw' / 'wikipedia_images'
        self.image_mapping_file = Config.DATA_DIR / 'image_mapping.json'
        
        # Load image mapping
        self._image_mapping = self._load_image_mapping()
        
        # Cache for API responses
        self._api_cache = {}
    
    def _load_image_mapping(self) -> Dict:
        """Load the image mapping from JSON file"""
        try:
            import json
            if self.image_mapping_file.exists():
                with open(self.image_mapping_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading image mapping: {e}")
        return {}
    
    def get_local_image(self, object_id: str, object_name: str) -> Optional[Dict]:
        """
        Try to get a local image first
        
        Args:
            object_id: ID of the object
            object_name: Name of the object
            
        Returns:
            Dict with local image info or None
        """
        # Check image mapping first
        if str(object_id) in self._image_mapping:
            image_path = self._image_mapping[str(object_id)]
            full_path = Config.BASE_DIR / 'data' / 'raw' / image_path
            
            if full_path.exists():
                # Create a static URL for the local image
                # We'll need to serve these through Flask
                relative_path = image_path.replace('\\', '/')
                return {
                    'url': f'/api/local-image/{relative_path}',
                    'title': f'Local image of {object_name}',
                    'source': 'local',
                    'is_local': True
                }
        
        # Try alternative ID formats
        try:
            numeric_id = int(object_id)
            if str(numeric_id) in self._image_mapping:
                return self.get_local_image(str(numeric_id), object_name)
        except ValueError:
            pass
        
        # Try to find by name in the images directory
        if self.local_images_dir.exists():
            name_lower = object_name.lower().replace(' ', '_')
            
            # Search for files containing the object name
            for image_file in self.local_images_dir.glob('*'):
                if name_lower in image_file.name.lower():
                    relative_path = f"wikipedia_images/{image_file.name}"
                    return {
                        'url': f'/api/local-image/{relative_path}',
                        'title': f'Local image of {object_name}',
                        'source': 'local',
                        'is_local': True
                    }
        
        return None
    
    def fetch_image(self, object_name: str, object_type: Optional[str] = None, 
                   aliases: Optional[List[str]] = None, object_id: Optional[str] = None) -> Dict:
        """
        Enhanced image fetching - tries local first, then API
        
        Args:
            object_name: Primary name of the object
            object_type: Type of object (e.g., 'asteroid', 'moon')
            aliases: Alternative names for the object
            object_id: ID of the object for local lookup
            
        Returns:
            Dict with image URL and metadata
        """
        # First, try to get local image if object_id is provided
        if object_id:
            local_image = self.get_local_image(object_id, object_name)
            if local_image:
                logger.info(f"Found local image for {object_name}")
                return local_image
        
        # Check cache
        cache_key = f"{object_name}_{object_type}"
        if cache_key in self._api_cache:
            logger.info(f"Using cached API result for {object_name}")
            return self._api_cache[cache_key]
        
        # If no local image, try NASA API (but with optimizations)
        result = self._fetch_from_nasa_api(object_name, object_type, aliases)
        
        # Cache the result
        self._api_cache[cache_key] = result
        
        return result
    
    def _fetch_from_nasa_api(self, object_name: str, object_type: Optional[str] = None, 
                            aliases: Optional[List[str]] = None) -> Dict:
        """
        Fetch image from NASA Image API
        """
        # Build list of search terms
        search_terms = [object_name]
        if aliases and len(aliases) > 0:
            # Limit aliases to prevent too many API calls
            search_terms.extend(aliases[:2])
        
        # Try each search term
        for i, term in enumerate(search_terms):
            # Skip if we've tried too many times
            if i >= 3:
                break
                
            # Build search query
            query = self._build_search_query(term, object_type)
            
            # Make API request
            params = {
                'q': query,
                'media_type': 'image',
                'page_size': 10  # Limit results for faster response
            }
            
            # Only add API key if it's not DEMO_KEY
            if self.api_key and self.api_key != 'DEMO_KEY':
                params['api_key'] = self.api_key
            
            try:
                response = requests.get(self.api_url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if we got results
                    if data.get('collection', {}).get('metadata', {}).get('total_hits', 0) > 0:
                        items = data['collection']['items']
                        
                        # Find best match
                        for item in items[:3]:  # Only check first 3 results
                            if self._is_relevant_image(item, term):
                                image_data = self._extract_image_data(item)
                                if image_data:
                                    logger.info(f"Found NASA API image for {object_name}")
                                    return image_data
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching image for '{query}'")
                break  # Don't retry on timeout
            except Exception as e:
                logger.error(f"Error fetching image for '{query}': {e}")
            
            # Small delay between requests
            if i < len(search_terms) - 1:
                time.sleep(self.retry_delay)
        
        # Return placeholder if no image found
        return self._get_placeholder_image(object_name, object_type)
    
    def _build_search_query(self, term: str, object_type: Optional[str]) -> str:
        """Build optimized search query"""
        query = f'"{term}"'
        
        if object_type:
            # Simplified type mapping
            type_keywords = {
                'Moon': 'moon',
                'Lunas': 'moon',
                'NEO': 'asteroid',
                'Objetos Cercanos': 'asteroid',
                'Asteroides': 'asteroid',
                'Asteroides Peligrosos': 'asteroid',
                'Asteroides Troyanos': 'trojan',
                'Centauros': 'centaur',
                'Cometas': 'comet',
                'Planetas': 'planet'
            }
            
            if object_type in type_keywords:
                query += f' {type_keywords[object_type]}'
        
        return query
    
    def _is_relevant_image(self, item: Dict, search_term: str) -> bool:
        """Check if image is relevant to our search"""
        try:
            item_data = item['data'][0]
            
            # Quick relevance check
            title = item_data.get('title', '').lower()
            keywords = item_data.get('keywords', [])
            
            term_lower = search_term.lower()
            
            # Check title
            if term_lower in title:
                return True
            
            # Check keywords (limited)
            for keyword in keywords[:5]:
                if term_lower in keyword.lower():
                    return True
            
            return False
            
        except (KeyError, IndexError):
            return False
    
    def _extract_image_data(self, item: Dict) -> Optional[Dict]:
        """Extract image data from API response item"""
        try:
            item_data = item['data'][0]
            
            # Get thumbnail URL
            image_url = None
            for link in item.get('links', []):
                if link.get('render') == 'image' and link.get('rel') == 'preview':
                    image_url = link.get('href')
                    break
            
            if image_url:
                return {
                    'url': image_url,
                    'title': item_data.get('title', 'NASA Image'),
                    'nasa_id': item_data.get('nasa_id'),
                    'source': 'NASA Image Library',
                    'is_local': False
                }
                
        except (KeyError, IndexError):
            pass
        
        return None
    
    def _get_placeholder_image(self, object_name: str, object_type: Optional[str]) -> Dict:
        """Get appropriate placeholder image based on object type"""
        # Type-specific placeholders
        placeholder_map = {
            'Planetas': 'placeholder_planet.svg',
            'Lunas': 'placeholder_moon.svg',
            'Asteroides': 'placeholder_asteroid.svg',
            'Cometas': 'placeholder_comet.svg',
            'default': 'placeholder_space.svg'
        }
        
        placeholder = placeholder_map.get(object_type, placeholder_map['default'])
        
        return {
            'url': f'/static/images/{placeholder}',
            'title': f'No image available for {object_name}',
            'source': 'placeholder',
            'is_local': False
        }