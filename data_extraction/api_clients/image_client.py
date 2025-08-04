"""
Cliente para las APIs de imágenes de la NASA
Incluye APOD (Astronomy Picture of the Day) y NASA Image Library
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import logging
import os
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_client import BaseAPIClient

# Cargar variables de entorno de forma segura
try:
    load_dotenv()
except (UnicodeDecodeError, FileNotFoundError, PermissionError) as e:
    pass  # Si no se puede cargar .env, usar variables del sistema

logger = logging.getLogger(__name__)


class APODClient(BaseAPIClient):
    """
    Cliente para la API Astronomy Picture of the Day (APOD)
    Documentación: https://api.nasa.gov/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente APOD
        
        Args:
            api_key: NASA API key (si no se proporciona, busca en variables de entorno)
        """
        super().__init__("https://api.nasa.gov")
        self.api_key = api_key or os.getenv('NASA_API_KEY', 'DEMO_KEY')
        
        if self.api_key == 'DEMO_KEY':
            logger.warning("Usando DEMO_KEY - tiene límites estrictos de rate limit")
    
    def get_apod(
        self,
        date: Optional[str] = None,
        hd: bool = True,
        thumbs: bool = True
    ) -> Dict:
        """
        Obtiene la imagen astronómica del día
        
        Args:
            date: Fecha en formato YYYY-MM-DD (None = hoy)
            hd: Si devolver URL de alta resolución
            thumbs: Si devolver thumbnail para videos
            
        Returns:
            Diccionario con información de APOD
        """
        params = {
            'api_key': self.api_key,
            'hd': str(hd).lower(),
            'thumbs': str(thumbs).lower()
        }
        
        if date:
            params['date'] = date
        
        try:
            logger.info(f"Obteniendo APOD para fecha: {date or 'hoy'}")
            response = self.get('/planetary/apod', params=params)
            return response.json()
            
        except Exception as e:
            logger.error(f"Error obteniendo APOD: {e}")
            raise
    
    def get_apod_range(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        hd: bool = True
    ) -> pd.DataFrame:
        """
        Obtiene APODs en un rango de fechas
        
        Args:
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD). Si no se especifica, usa fecha actual
            hd: Si devolver URLs de alta resolución
            
        Returns:
            DataFrame con información de APODs
        """
        params = {
            'api_key': self.api_key,
            'start_date': start_date,
            'hd': str(hd).lower()
        }
        
        if end_date:
            params['end_date'] = end_date
        
        try:
            logger.info(f"Obteniendo APODs del {start_date} al {end_date or 'hoy'}")
            response = self.get('/planetary/apod', params=params)
            data = response.json()
            
            # Convertir a DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            
            # Convertir fecha a datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # Ordenar por fecha
            df = df.sort_values('date', ascending=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo rango APOD: {e}")
            raise


class NASAImageClient(BaseAPIClient):
    """
    Cliente para la API NASA Image and Video Library
    Documentación: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf
    """
    
    def __init__(self):
        """Inicializa el cliente NASA Image Library"""
        super().__init__("https://images-api.nasa.gov")
    
    def search(
        self,
        query: str,
        media_type: Optional[str] = 'image',
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        center: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Busca imágenes y videos en la biblioteca NASA
        
        Args:
            query: Términos de búsqueda
            media_type: Tipo de media ('image', 'video', 'audio')
            year_start: Año inicial
            year_end: Año final
            center: Centro NASA específico
            page: Número de página
            page_size: Resultados por página
            
        Returns:
            Tupla de (DataFrame con resultados, metadata)
        """
        params = {
            'q': query,
            'page': page,
            'page_size': min(page_size, 100)
        }
        
        if media_type:
            params['media_type'] = media_type
        if year_start:
            params['year_start'] = year_start
        if year_end:
            params['year_end'] = year_end
        if center:
            params['center'] = center
        
        try:
            logger.info(f"Buscando '{query}' en NASA Image Library")
            response = self.get('/search', params=params)
            data = response.json()
            
            # Extraer items
            items = []
            collection = data.get('collection', {})
            
            for item in collection.get('items', []):
                item_data = self._extract_item_data(item)
                items.append(item_data)
            
            df = pd.DataFrame(items)
            
            # Metadata
            metadata = collection.get('metadata', {})
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error buscando imágenes: {e}")
            raise
    
    def get_asset(self, nasa_id: str) -> Dict:
        """
        Obtiene los assets (URLs de archivos) para un item específico
        
        Args:
            nasa_id: ID del item NASA
            
        Returns:
            Diccionario con URLs de assets
        """
        try:
            logger.info(f"Obteniendo assets para {nasa_id}")
            response = self.get(f'/asset/{nasa_id}')
            data = response.json()
            
            # Organizar assets por tipo
            assets = {
                'original': [],
                'large': [],
                'medium': [],
                'small': [],
                'thumbnail': [],
                'metadata': []
            }
            
            items = data.get('collection', {}).get('items', [])
            
            for item in items:
                href = item.get('href', '')
                
                # Clasificar por tipo basado en el nombre del archivo
                if '~orig' in href or 'orig' in href:
                    assets['original'].append(href)
                elif '~large' in href or 'large' in href:
                    assets['large'].append(href)
                elif '~medium' in href or 'medium' in href:
                    assets['medium'].append(href)
                elif '~small' in href or 'small' in href:
                    assets['small'].append(href)
                elif '~thumb' in href or 'thumb' in href:
                    assets['thumbnail'].append(href)
                elif '.json' in href:
                    assets['metadata'].append(href)
                else:
                    # Si no se puede clasificar, considerar como original
                    assets['original'].append(href)
            
            return assets
            
        except Exception as e:
            logger.error(f"Error obteniendo assets: {e}")
            raise
    
    def _extract_item_data(self, item: Dict) -> Dict:
        """
        Extrae datos relevantes de un item
        
        Args:
            item: Item de la respuesta API
            
        Returns:
            Diccionario con datos extraídos
        """
        data = item.get('data', [{}])[0]
        links = item.get('links', [])
        
        # Buscar preview/thumbnail
        preview_url = None
        for link in links:
            if link.get('rel') == 'preview':
                preview_url = link.get('href')
                break
        
        return {
            'nasa_id': data.get('nasa_id'),
            'title': data.get('title'),
            'description': data.get('description'),
            'keywords': data.get('keywords', []),
            'date_created': data.get('date_created'),
            'center': data.get('center'),
            'media_type': data.get('media_type'),
            'photographer': data.get('photographer'),
            'location': data.get('location'),
            'preview_url': preview_url,
            'secondary_creator': data.get('secondary_creator')
        }


# Funciones de utilidad
def get_apod_client(api_key: Optional[str] = None) -> APODClient:
    """Factory function para crear cliente APOD"""
    return APODClient(api_key)


def get_nasa_image_client() -> NASAImageClient:
    """Factory function para crear cliente NASA Image"""
    return NASAImageClient()


if __name__ == "__main__":
    # Ejemplo de uso
    apod_client = get_apod_client()
    
    try:
        # Obtener APOD de hoy
        today_apod = apod_client.get_apod()
        print("APOD de hoy:")
        print(f"Título: {today_apod.get('title')}")
        print(f"URL: {today_apod.get('url')}")
    except Exception as e:
        print(f"Error con APOD: {e}")