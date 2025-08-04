"""
Cliente para la API Near-Earth Object (NEO) de la NASA
====================================================

ESTRATEGIA: HÍBRIDA (Cache temporal + Real-time)
- Cache de 6-12 horas para datos de aproximaciones recientes
- Consulta real-time para fechas específicas del usuario
- Balance entre performance y actualización de datos

API: https://api.nasa.gov/neo/rest/v1/
Datos: NEOs próximos, aproximaciones, objetos potencialmente peligrosos
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
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


class NEOClient(BaseAPIClient):
    """
    Cliente para interactuar con la API NEO de la NASA
    Documentación: https://api.nasa.gov/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente NEO con cache híbrido
        
        Args:
            api_key: NASA API key (si no se proporciona, busca en variables de entorno)
        """
        super().__init__("https://api.nasa.gov")
        self.api_key = api_key or os.getenv('NASA_API_KEY', 'DEMO_KEY')
        
        # Configuración de cache híbrido
        self.cache_duration = timedelta(hours=6)  # Cache de 6 horas
        
        # Calcular ruta absoluta al directorio de datos
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(project_root, "data", "raw", "api_data")
        self.cache_dir = os.path.join(self.data_dir, "neo_cache")
        
        # Crear directorios si no existen
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if self.api_key == 'DEMO_KEY':
            logger.warning("Usando DEMO_KEY - tiene límites estrictos de rate limit")
    
    def get_feed(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        detailed: bool = True
    ) -> pd.DataFrame:
        """
        Obtiene objetos cercanos a la Tierra en un rango de fechas
        
        Args:
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD). Si no se especifica, usa start_date + 7 días
            detailed: Si incluir información detallada de cada aproximación
            
        Returns:
            DataFrame con información de NEOs
            
        Raises:
            ValueError: Si el rango excede 7 días
        """
        # Validar fechas
        start = datetime.strptime(start_date, '%Y-%m-%d')
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = start + timedelta(days=7)
            end_date = end.strftime('%Y-%m-%d')
        
        # Verificar límite de 7 días
        if (end - start).days > 7:
            raise ValueError("El rango de fechas no puede exceder 7 días")
        
        # Parámetros de la API
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'api_key': self.api_key
        }
        
        try:
            logger.info(f"Obteniendo NEOs del {start_date} al {end_date}")
            response = self.get('/neo/rest/v1/feed', params=params)
            data = response.json()
            
            # Parsear respuesta
            df = self._parse_feed_response(data, detailed)
            
            logger.info(f"Obtenidos {len(df)} acercamientos de NEOs")
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo feed NEO: {e}")
            raise
    
    def get_neo_by_id(self, neo_id: str) -> Dict:
        """
        Obtiene información detallada de un NEO específico
        
        Args:
            neo_id: ID del asteroide NEO
            
        Returns:
            Diccionario con información del NEO
        """
        params = {'api_key': self.api_key}
        
        try:
            logger.info(f"Obteniendo información del NEO {neo_id}")
            response = self.get(f'/neo/rest/v1/neo/{neo_id}', params=params)
            return response.json()
            
        except Exception as e:
            logger.error(f"Error obteniendo NEO {neo_id}: {e}")
            raise
    
    def browse_neos(
        self,
        page: int = 0,
        size: int = 20
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Navega por la base de datos completa de NEOs
        
        Args:
            page: Número de página (0-indexed)
            size: Tamaño de página (máximo 20)
            
        Returns:
            Tupla de (DataFrame con NEOs, metadata de paginación)
        """
        params = {
            'page': page,
            'size': min(size, 20),  # Máximo permitido
            'api_key': self.api_key
        }
        
        try:
            logger.info(f"Navegando NEOs - página {page}")
            response = self.get('/neo/rest/v1/neo/browse', params=params)
            data = response.json()
            
            # Extraer NEOs
            neos = []
            for neo in data.get('near_earth_objects', []):
                neo_data = self._extract_neo_info(neo)
                neos.append(neo_data)
            
            df = pd.DataFrame(neos)
            
            # Metadata de paginación
            page_info = data.get('page', {})
            
            return df, page_info
            
        except Exception as e:
            logger.error(f"Error navegando NEOs: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas generales sobre NEOs
        
        Returns:
            Diccionario con estadísticas
        """
        params = {'api_key': self.api_key}
        
        try:
            response = self.get('/neo/rest/v1/stats', params=params)
            return response.json()
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise
    
    def _parse_feed_response(self, data: Dict, detailed: bool) -> pd.DataFrame:
        """
        Parsea la respuesta del feed a DataFrame
        
        Args:
            data: Respuesta JSON del API
            detailed: Si incluir detalles de aproximación
            
        Returns:
            DataFrame con los datos parseados
        """
        # Verificar estructura
        if 'near_earth_objects' not in data:
            raise ValueError("Respuesta inesperada del API")
        
        neo_objects = data['near_earth_objects']
        element_count = data.get('element_count', 0)
        
        logger.info(f"Total de elementos en respuesta: {element_count}")
        
        # Procesar cada fecha
        all_approaches = []
        
        for date, neos in neo_objects.items():
            for neo in neos:
                # Información básica del NEO
                neo_info = self._extract_neo_info(neo)
                
                # Procesar aproximaciones
                for approach in neo.get('close_approach_data', []):
                    approach_data = {
                        'approach_date': date,
                        **neo_info
                    }
                    
                    if detailed:
                        # Añadir detalles de aproximación
                        approach_data.update({
                            'close_approach_date': approach.get('close_approach_date'),
                            'close_approach_date_full': approach.get('close_approach_date_full'),
                            'epoch_date_close_approach': approach.get('epoch_date_close_approach'),
                            'relative_velocity_kps': float(
                                approach.get('relative_velocity', {}).get('kilometers_per_second', 0)
                            ),
                            'relative_velocity_kph': float(
                                approach.get('relative_velocity', {}).get('kilometers_per_hour', 0)
                            ),
                            'miss_distance_astronomical': float(
                                approach.get('miss_distance', {}).get('astronomical', 0)
                            ),
                            'miss_distance_lunar': float(
                                approach.get('miss_distance', {}).get('lunar', 0)
                            ),
                            'miss_distance_km': float(
                                approach.get('miss_distance', {}).get('kilometers', 0)
                            ),
                            'orbiting_body': approach.get('orbiting_body')
                        })
                    
                    all_approaches.append(approach_data)
        
        # Crear DataFrame
        df = pd.DataFrame(all_approaches)
        
        # Ordenar por fecha y distancia
        if 'miss_distance_km' in df.columns:
            df = df.sort_values(['approach_date', 'miss_distance_km'])
        else:
            df = df.sort_values('approach_date')
        
        return df
    
    def _extract_neo_info(self, neo: Dict) -> Dict:
        """
        Extrae información básica de un NEO
        
        Args:
            neo: Diccionario con datos del NEO
            
        Returns:
            Diccionario con información extraída
        """
        # Diámetro estimado
        diameter_data = neo.get('estimated_diameter', {}).get('kilometers', {})
        
        return {
            'id': neo.get('id'),
            'neo_reference_id': neo.get('neo_reference_id'),
            'name': neo.get('name'),
            'designation': neo.get('designation'),
            'absolute_magnitude_h': float(neo.get('absolute_magnitude_h', 0)),
            'is_potentially_hazardous': neo.get('is_potentially_hazardous_asteroid', False),
            'is_sentry_object': neo.get('is_sentry_object', False),
            'diameter_km_min': float(diameter_data.get('estimated_diameter_min', 0)),
            'diameter_km_max': float(diameter_data.get('estimated_diameter_max', 0)),
            'diameter_km_avg': (
                float(diameter_data.get('estimated_diameter_min', 0)) + 
                float(diameter_data.get('estimated_diameter_max', 0))
            ) / 2.0 if diameter_data else 0,
            'nasa_jpl_url': neo.get('nasa_jpl_url')
        }
    
    def analyze_approaches(self, df: pd.DataFrame) -> Dict:
        """
        Analiza estadísticas de aproximaciones de NEOs
        
        Args:
            df: DataFrame con datos de aproximaciones
            
        Returns:
            Diccionario con estadísticas
        """
        if df.empty:
            return {}
        
        stats = {
            'total_approaches': len(df),
            'unique_objects': df['id'].nunique() if 'id' in df.columns else 0,
            'potentially_hazardous': df['is_potentially_hazardous'].sum() if 'is_potentially_hazardous' in df.columns else 0
        }
        
        # Estadísticas de distancia si están disponibles
        if 'miss_distance_km' in df.columns:
            stats.update({
                'closest_approach_km': df['miss_distance_km'].min(),
                'farthest_approach_km': df['miss_distance_km'].max(),
                'avg_approach_km': df['miss_distance_km'].mean(),
                'closest_object_name': df.loc[df['miss_distance_km'].idxmin(), 'name'] if 'name' in df.columns else 'Unknown'
            })
        
        # Estadísticas de velocidad
        if 'relative_velocity_kps' in df.columns:
            stats.update({
                'fastest_velocity_kps': df['relative_velocity_kps'].max(),
                'slowest_velocity_kps': df['relative_velocity_kps'].min(),
                'avg_velocity_kps': df['relative_velocity_kps'].mean()
            })
        
        # Estadísticas de tamaño
        if 'diameter_km_avg' in df.columns:
            stats.update({
                'largest_object_km': df['diameter_km_avg'].max(),
                'smallest_object_km': df['diameter_km_avg'].min(),
                'avg_size_km': df['diameter_km_avg'].mean()
            })
        
        return stats
    
    def get_current_week_neos_cached(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL HÍBRIDO: Obtiene NEOs de la semana actual con cache
        
        Args:
            use_cache: Si usar cache disponible (True) o forzar nueva consulta (False)
            
        Returns:
            Diccionario con datos de NEOs y información de cache
        """
        # Calcular fechas de la semana actual
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        
        cache_key = f"current_week_{today.strftime('%Y%m%d')}"
        
        # Intentar usar cache primero
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                cached_data['data_source'] = 'cache'
                cached_data['cache_age_hours'] = (
                    datetime.now() - datetime.fromisoformat(cached_data['cached_at'])
                ).total_seconds() / 3600
                print(f"[NEO] OK Datos obtenidos del cache ({cached_data['cache_age_hours']:.1f}h de antigüedad)")
                return cached_data
        
        # Si no hay cache válido, consultar API
        print(f"[NEO] Consultando API para NEOs del {today} al {week_end}")
        
        try:
            df = self.get_feed(
                start_date=today.strftime('%Y-%m-%d'),
                end_date=week_end.strftime('%Y-%m-%d'),
                detailed=True
            )
            
            # Analizar datos
            stats = self.analyze_approaches(df)
            
            # Preparar datos para cache
            neo_data = {
                'query_date': today.isoformat(),
                'start_date': today.isoformat(), 
                'end_date': week_end.isoformat(),
                'total_approaches': len(df),
                'data_points': len(df),
                'statistics': stats,
                'data_source': 'api',
                'cached_at': datetime.now().isoformat(),
                'cache_duration_hours': self.cache_duration.total_seconds() / 3600
            }
            
            # Agregar datos de muestra (los 10 más cercanos)
            if not df.empty:
                if 'miss_distance_km' in df.columns:
                    sample_df = df.nsmallest(10, 'miss_distance_km')
                else:
                    sample_df = df.head(10)
                
                neo_data['sample_data'] = sample_df.to_dict('records')
                neo_data['closest_approaches'] = sample_df[
                    ['name', 'approach_date', 'miss_distance_km', 'is_potentially_hazardous']
                ].to_dict('records') if all(col in sample_df.columns for col in 
                    ['name', 'approach_date', 'miss_distance_km', 'is_potentially_hazardous']) else []
            else:
                neo_data['sample_data'] = []
                neo_data['closest_approaches'] = []
            
            # Guardar en cache
            self._save_to_cache(cache_key, neo_data)
            
            print(f"[NEO] OK {len(df)} aproximaciones obtenidas y guardadas en cache")
            return neo_data
            
        except Exception as e:
            print(f"[NEO] ERROR Error obteniendo datos: {e}")
            return {
                'error': str(e),
                'query_date': today.isoformat(),
                'data_source': 'error',
                'cached_at': datetime.now().isoformat()
            }
    
    def get_neos_for_date_range(
        self, 
        start_date: str, 
        end_date: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        MÉTODO HÍBRIDO: Obtiene NEOs para rango de fechas específico con cache opcional
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            use_cache: Si intentar usar cache
            
        Returns:
            Diccionario con datos de NEOs
        """
        cache_key = f"range_{start_date}_{end_date}"
        
        # Intentar cache si está habilitado
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                cached_data['data_source'] = 'cache'
                print(f"[NEO] OK Datos de rango obtenidos del cache")
                return cached_data
        
        # Consultar API
        print(f"[NEO] Consultando API para rango {start_date} a {end_date}")
        
        try:
            df = self.get_feed(start_date=start_date, end_date=end_date, detailed=True)
            stats = self.analyze_approaches(df)
            
            range_data = {
                'start_date': start_date,
                'end_date': end_date,
                'total_approaches': len(df),
                'statistics': stats,
                'data_source': 'api',
                'cached_at': datetime.now().isoformat(),
                'sample_data': df.head(15).to_dict('records') if not df.empty else []
            }
            
            # Cache solo si el rango no incluye fechas futuras lejanas
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            if start_dt <= datetime.now().date() + timedelta(days=30):
                self._save_to_cache(cache_key, range_data)
            
            print(f"[NEO] OK {len(df)} aproximaciones obtenidas para el rango")
            return range_data
            
        except Exception as e:
            print(f"[NEO] ERROR Error obteniendo rango: {e}")
            return {
                'error': str(e),
                'start_date': start_date,
                'end_date': end_date,
                'data_source': 'error'
            }
    
    def get_potentially_hazardous_cached(self) -> Dict[str, Any]:
        """
        MÉTODO HÍBRIDO: Obtiene NEOs potencialmente peligrosos con cache de larga duración
        
        Returns:
            Diccionario con PHAs y información de cache
        """
        cache_key = "potentially_hazardous_current"
        
        # Cache más largo para PHAs (12 horas)
        cached_data = self._get_from_cache(cache_key, max_age_hours=12)
        if cached_data:
            cached_data['data_source'] = 'cache'
            print(f"[NEO] OK PHAs obtenidos del cache")
            return cached_data
        
        print(f"[NEO] Consultando PHAs desde API...")
        
        try:
            # Obtener semana actual
            today = datetime.now().date()
            week_end = today + timedelta(days=7)
            
            df = self.get_feed(
                start_date=today.strftime('%Y-%m-%d'),
                end_date=week_end.strftime('%Y-%m-%d'),
                detailed=True
            )
            
            # Filtrar solo PHAs
            if not df.empty and 'is_potentially_hazardous' in df.columns:
                phas = df[df['is_potentially_hazardous'] == True]
            else:
                phas = pd.DataFrame()
            
            pha_data = {
                'query_date': today.isoformat(),
                'total_phas': len(phas),
                'total_all_neos': len(df),
                'percentage_hazardous': (len(phas) / len(df) * 100) if len(df) > 0 else 0,
                'data_source': 'api',
                'cached_at': datetime.now().isoformat(),
                'hazardous_objects': phas.to_dict('records') if not phas.empty else []
            }
            
            # Estadísticas específicas de PHAs
            if not phas.empty:
                if 'miss_distance_km' in phas.columns:
                    pha_data['closest_pha_distance_km'] = phas['miss_distance_km'].min()
                    pha_data['closest_pha_name'] = phas.loc[
                        phas['miss_distance_km'].idxmin(), 'name'
                    ] if 'name' in phas.columns else 'Unknown'
                
                if 'diameter_km_avg' in phas.columns:
                    pha_data['largest_pha_size_km'] = phas['diameter_km_avg'].max()
            
            # Guardar en cache con duración extendida
            self._save_to_cache(cache_key, pha_data)
            
            print(f"[NEO] OK {len(phas)} PHAs de {len(df)} NEOs totales")
            return pha_data
            
        except Exception as e:
            print(f"[NEO] ERROR Error obteniendo PHAs: {e}")
            return {
                'error': str(e),
                'data_source': 'error',
                'cached_at': datetime.now().isoformat()
            }
    
    def _get_cache_filename(self, cache_key: str) -> str:
        """Genera nombre de archivo para cache"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _get_from_cache(self, cache_key: str, max_age_hours: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos del cache si están disponibles y son válidos
        
        Args:
            cache_key: Clave del cache
            max_age_hours: Edad máxima en horas (None = usar default)
            
        Returns:
            Datos del cache o None si no es válido
        """
        cache_file = self._get_cache_filename(cache_key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Verificar edad del cache
            cached_at = datetime.fromisoformat(cached_data['cached_at'])
            age = datetime.now() - cached_at
            max_age = timedelta(hours=max_age_hours or self.cache_duration.total_seconds() / 3600)
            
            if age <= max_age:
                return cached_data
            else:
                # Cache expirado, eliminarlo
                os.remove(cache_file)
                return None
                
        except Exception as e:
            logger.error(f"Error leyendo cache {cache_key}: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Guarda datos en cache
        
        Args:
            cache_key: Clave del cache
            data: Datos a guardar
        """
        cache_file = self._get_cache_filename(cache_key)
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error guardando cache {cache_key}: {e}")
    
    def clear_cache(self) -> int:
        """
        Limpia todo el cache de NEO
        
        Returns:
            Número de archivos eliminados
        """
        if not os.path.exists(self.cache_dir):
            return 0
        
        files_deleted = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                    files_deleted += 1
                except Exception as e:
                    logger.error(f"Error eliminando cache {filename}: {e}")
        
        print(f"[NEO] Cache limpiado: {files_deleted} archivos eliminados")
        return files_deleted
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Obtiene estado del cache NEO
        
        Returns:
            Información sobre el cache
        """
        cache_status = {
            'cache_dir': self.cache_dir,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
            'files': []
        }
        
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        stat = os.stat(filepath)
                        modified = datetime.fromtimestamp(stat.st_mtime)
                        age_hours = (datetime.now() - modified).total_seconds() / 3600
                        
                        cache_status['files'].append({
                            'filename': filename,
                            'modified': modified.isoformat(),
                            'age_hours': age_hours,
                            'is_valid': age_hours <= cache_status['cache_duration_hours']
                        })
                    except Exception as e:
                        logger.error(f"Error leyendo info de {filename}: {e}")
        
        return cache_status


# Funciones de utilidad
def get_neo_client(api_key: Optional[str] = None) -> NEOClient:
    """
    Factory function para crear cliente NEO
    
    Args:
        api_key: NASA API key opcional
        
    Returns:
        Instancia de NEOClient
    """
    return NEOClient(api_key)


if __name__ == "__main__":
    print("=== Demo NEO Client - Estrategia HÍBRIDA ===")
    
    client = get_neo_client()
    
    try:
        # Ejemplo 1: Estado del cache
        print("\n[CACHE] Estado actual del cache:")
        cache_status = client.get_cache_status()
        print(f"   Duración del cache: {cache_status['cache_duration_hours']} horas")
        print(f"   Archivos en cache: {len(cache_status['files'])}")
        
        for file_info in cache_status['files']:
            validity = "OK" if file_info['is_valid'] else "ERROR expirado"
            print(f"   - {file_info['filename']}: {file_info['age_hours']:.1f}h {validity}")
        
        # Ejemplo 2: NEOs de la semana actual (con cache)
        print("\n[EARTH] NEOs de la semana actual (estrategia híbrida):")
        current_week = client.get_current_week_neos_cached(use_cache=True)
        
        print(f"   Fuente de datos: {current_week['data_source']}")
        if current_week['data_source'] == 'cache':
            print(f"   Edad del cache: {current_week.get('cache_age_hours', 0):.1f} horas")
        
        if 'total_approaches' in current_week:
            print(f"   Total de aproximaciones: {current_week['total_approaches']}")
            
            if 'statistics' in current_week and current_week['statistics']:
                stats = current_week['statistics']
                print(f"   Objetos únicos: {stats.get('unique_objects', 0)}")
                print(f"   Potencialmente peligrosos: {stats.get('potentially_hazardous', 0)}")
                
                if 'closest_approach_km' in stats:
                    print(f"   Aproximación más cercana: {stats['closest_approach_km']:,.0f} km")
                    print(f"   Objeto más cercano: {stats.get('closest_object_name', 'N/A')}")
        
        # Ejemplo 3: Asteroides potencialmente peligrosos (cache largo)
        print("\n[WARNING] Asteroides potencialmente peligrosos:")
        phas = client.get_potentially_hazardous_cached()
        
        print(f"   Fuente: {phas['data_source']}")
        if 'total_phas' in phas:
            print(f"   PHAs encontrados: {phas['total_phas']}")
            print(f"   Total de NEOs: {phas['total_all_neos']}")
            print(f"   Porcentaje peligroso: {phas.get('percentage_hazardous', 0):.1f}%")
            
            if 'closest_pha_distance_km' in phas:
                print(f"   PHA más cercano: {phas['closest_pha_name']} a {phas['closest_pha_distance_km']:,.0f} km")
        
        # Ejemplo 4: Consulta para rango específico (híbrido)
        print("\n📅 NEOs para rango específico (próximos 3 días):")
        from datetime import date
        today = date.today()
        three_days = today + timedelta(days=3)
        
        range_data = client.get_neos_for_date_range(
            start_date=today.strftime('%Y-%m-%d'),
            end_date=three_days.strftime('%Y-%m-%d'),
            use_cache=True
        )
        
        print(f"   Fuente: {range_data['data_source']}")
        if 'total_approaches' in range_data:
            print(f"   Aproximaciones en 3 días: {range_data['total_approaches']}")
            print(f"   Datos de muestra: {len(range_data.get('sample_data', []))} registros")
        
        # Ejemplo 5: Limpiar cache (opcional)
        print("\n[CLEANUP] Gestión de cache:")
        print("   Para limpiar cache: client.clear_cache()")
        print("   Para forzar actualización: use_cache=False")
        
    except Exception as e:
        print(f"ERROR Error en demo: {e}")
        if "DEMO_KEY" in str(e):
            print("[TIP] Consejo: Obtén una API key gratuita en https://api.nasa.gov/")
    
    print("\n[TIP] Este cliente usa estrategia HÍBRIDA:")
    print("[TIP] - Cache de 6 horas para performance")
    print("[TIP] - Consultas real-time cuando es necesario")
    print("[TIP] - Cache extendido (12h) para datos menos volátiles") 