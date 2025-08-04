import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data' / 'web_ready'
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # API Keys
    NASA_API_KEY = os.environ.get('NASA_API_KEY') or 'DEMO_KEY'
    
    # Cache configuration
    CACHE_TTL = 3600  # 1 hour
    CACHE_DIR = Path(__file__).resolve().parent / 'cache'
    
    # API endpoints
    HORIZONS_API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
    HORIZONS_LOOKUP_API_URL = "https://ssd-api.jpl.nasa.gov/api/horizons_lookup.api"
    NASA_IMAGE_API_URL = "https://images-api.nasa.gov/search"
    
    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200