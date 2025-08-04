"""
Cliente base para manejar peticiones HTTP con reintentos y validación
"""
import time
import logging
from typing import Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Cliente base para todas las APIs con funcionalidad común de:
    - Reintentos con backoff exponencial
    - Manejo de timeouts
    - Headers personalizados
    - Logging de peticiones
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Inicializa el cliente base
        
        Args:
            base_url: URL base de la API
            timeout: Tiempo máximo de espera en segundos
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Sistema-Solar-Explorer/1.0 (Educational Project)',
            'Accept': 'application/json'
        })
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RequestException, Timeout, ConnectionError))
    )
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Realiza una petición HTTP con reintentos
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint relativo a la URL base
            params: Parámetros de consulta
            data: Datos para enviar en el cuerpo
            headers: Headers adicionales
            
        Returns:
            Response object
            
        Raises:
            RequestException: Si falla después de todos los reintentos
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Combinar headers
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)
        
        logger.info(f"Realizando petición {method} a {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=req_headers,
                timeout=self.timeout
            )
            
            # Log de respuesta
            logger.info(f"Respuesta recibida: {response.status_code}")
            
            # Verificar status
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP: {e}")
            logger.error(f"Respuesta: {e.response.text if e.response else 'Sin respuesta'}")
            raise
        except Exception as e:
            logger.error(f"Error en petición: {type(e).__name__}: {e}")
            raise
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza petición GET"""
        return self._make_request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza petición POST"""
        return self._make_request('POST', endpoint, **kwargs)
    
    def close(self):
        """Cierra la sesión"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ScraperBase:
    """
    Clase base para scrapers con funcionalidad de:
    - Verificación de robots.txt
    - Delays entre peticiones
    - Headers éticos
    """
    
    def __init__(self, base_url: str, delay: float = 2.0):
        """
        Inicializa el scraper base
        
        Args:
            base_url: URL base del sitio
            delay: Segundos de espera entre peticiones
        """
        self.base_url = base_url.rstrip('/')
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Sistema-Solar-Explorer/1.0 (Educational Project; Contact: student@example.com)',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.last_request_time = 0
    
    def _wait_if_needed(self):
        """Aplica delay entre peticiones"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
    
    def fetch_page(self, url: str) -> str:
        """
        Descarga una página respetando delays
        
        Args:
            url: URL completa de la página
            
        Returns:
            Contenido HTML de la página
        """
        self._wait_if_needed()
        
        try:
            logger.info(f"Descargando página: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error descargando {url}: {e}")
            raise
    
    def check_robots_txt(self) -> bool:
        """
        Verifica robots.txt (implementación básica)
        
        Returns:
            True si se puede scrapear
        """
        robots_url = f"{self.base_url}/robots.txt"
        try:
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                # Verificación básica - en producción usar robotparser
                content = response.text.lower()
                if 'user-agent: *' in content and 'disallow: /' in content:
                    logger.warning("robots.txt no permite scraping")
                    return False
            return True
        except:
            # Si no hay robots.txt, asumimos que sí se puede
            return True