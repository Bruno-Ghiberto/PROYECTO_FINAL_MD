import json
import hashlib
import os
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from flask import request, jsonify, current_app

class SimpleCache:
    """Simple file-based cache for API responses"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Generate a safe filename from cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if exists and not expired"""
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Check expiration
            expires_at = datetime.fromisoformat(data['expires_at'])
            if datetime.now() > expires_at:
                cache_file.unlink()  # Delete expired cache
                return None
            
            return data['value']
            
        except Exception:
            return None
    
    def set(self, key: str, value: Dict, timeout: int = 3600):
        """Cache a value with expiration time"""
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        
        data = {
            'key': key,
            'value': value,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=timeout)).isoformat()
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Fail silently on cache write errors
    
    def clear(self):
        """Clear all cached files"""
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
            except Exception:
                pass

# Global cache instance
_cache = None

def get_cache():
    """Get or create cache instance"""
    global _cache
    if _cache is None:
        from config import Config
        _cache = SimpleCache(Config.CACHE_DIR)
    return _cache

def cached_response(timeout=3600):
    """
    Decorator to cache Flask endpoint responses
    
    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from endpoint and arguments
            cache_key_parts = [
                request.endpoint,
                str(kwargs),
                str(sorted(request.args.items()))
            ]
            cache_key = ':'.join(cache_key_parts)
            
            # Try to get from cache
            cache = get_cache()
            cached = cache.get(cache_key)
            if cached is not None:
                response = jsonify(cached)
                response.headers['X-Cache-Status'] = 'HIT'
                return response
            
            # Call original function
            result = f(*args, **kwargs)
            
            # Cache successful JSON responses
            if hasattr(result, 'json') and result.status_code == 200:
                cache.set(cache_key, result.json, timeout)
                result.headers['X-Cache-Status'] = 'MISS'
            
            return result
            
        return decorated_function
    return decorator