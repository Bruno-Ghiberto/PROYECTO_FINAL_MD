"""
Cliente para la API Solar System OpenData
==========================================

ESTRATEGIA: BATCH PROCESSING (Datos estáticos/semi-estáticos)
- Descarga masiva periódica (semanal)
- Almacenamiento en base de datos local
- Web app consulta datos locales para mayor performance

API: https://api.le-systeme-solaire.net/rest/bodies/
Datos: Planetas, lunas, asteroides con parámetros físicos completos
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_client import BaseAPIClient

import logging
logger = logging.getLogger(__name__)


class SolarSystemOpenDataClient(BaseAPIClient):
    """
    Cliente para Solar System OpenData API
    
    BATCH PROCESSING: Descarga datos estables para almacenamiento local
    - Datos físicos de planetas, lunas, asteroides
    - Cache semanal (los datos físicos no cambian frecuentemente)
    - Almacenamiento en CSV/JSON para análisis posterior
    """
    
    def __init__(self):
        super().__init__("https://api.le-systeme-solaire.net")
        
        # Cache duration para datos estáticos
        self.cache_duration = timedelta(days=7)
        
        # Calcular ruta absoluta al directorio de datos
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(project_root, "data", "raw", "api_data")
        
        # Campos por defecto para consultas básicas
        self.default_fields = [
            'id', 'name', 'englishName', 'isPlanet', 'isMoon', 'bodyType',
            'mass', 'meanRadius', 'density', 'gravity', 'escape',
            'semimajorAxis', 'eccentricity', 'inclination', 
            'sideralOrbitPeriod', 'avgTemp', 'aroundPlanet', 'moons'
        ]
        
        # Campos más completos para análisis
        self.comprehensive_fields = [
            'id', 'name', 'englishName', 'isPlanet', 'isMoon', 'bodyType',
            'mass', 'vol', 'density', 'gravity', 'escape', 'meanRadius',
            'semimajorAxis', 'perihelion', 'aphelion', 'eccentricity', 
            'inclination', 'sideralOrbitPeriod', 'sideralRotationPeriod',
            'axialTilt', 'avgTemp', 'mainAnomaly', 'argPeriapsis', 'longAscNode',
            'aroundPlanet', 'discoveredBy', 'discoveryDate', 'moons'
        ]
        
        # Tipos de cuerpos disponibles
        self.body_types = ['Planet', 'DwarfPlanet', 'Moon', 'Asteroid', 'Comet']
    
    def get_all_bodies(
        self,
        fields: Optional[List[str]] = None,
        body_type: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Obtiene todos los cuerpos del sistema solar
        
        Args:
            fields: Lista de campos a incluir (None = campos por defecto)
            body_type: Filtrar por tipo de cuerpo
            order_by: Campo para ordenar resultados
            
        Returns:
            DataFrame con los cuerpos
        """
        params = {}
        
        # Campos a incluir
        if fields:
            params['data'] = ','.join(fields)
        else:
            params['data'] = ','.join(self.default_fields)
        
        # Filtro por tipo
        if body_type and body_type in self.body_types:
            params['filter[]'] = f'bodyType,eq,{body_type}'
        
        # Ordenamiento
        if order_by:
            params['order'] = order_by
        
        try:
            logger.info("Obteniendo todos los cuerpos del sistema solar")
            response = self.get('/rest/bodies/', params=params)
            data = response.json()
            
            # Convertir a DataFrame
            if isinstance(data, dict) and 'bodies' in data:
                df = pd.DataFrame(data['bodies'])
            else:
                df = pd.DataFrame(data)
            
            # Procesar campos complejos
            df = self._process_complex_fields(df)
            
            logger.info(f"Obtenidos {len(df)} cuerpos")
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo cuerpos: {e}")
            raise
    
    def get_body_by_id(self, body_id: str) -> Dict:
        """
        Obtiene información detallada de un cuerpo específico
        
        Args:
            body_id: ID del cuerpo (ej: 'terre', 'jupiter', 'europa')
            
        Returns:
            Diccionario con información del cuerpo
        """
        try:
            logger.info(f"Obteniendo información del cuerpo {body_id}")
            response = self.get(f'/rest/bodies/{body_id}')
            return response.json()
            
        except Exception as e:
            logger.error(f"Error obteniendo cuerpo {body_id}: {e}")
            raise
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        Busca un cuerpo por su nombre en inglés
        
        Args:
            name: Nombre del cuerpo (ej: 'Earth', 'Mars', 'Jupiter')
            
        Returns:
            Diccionario con información del cuerpo o None si no se encuentra
        """
        try:
            # Buscar en todos los cuerpos
            all_bodies = self.get_all_bodies()
            
            # Buscar por nombre exacto (case insensitive)
            matches = all_bodies[all_bodies['englishName'].str.lower() == name.lower()]
            
            if not matches.empty:
                # Retornar el primer match como diccionario
                return matches.iloc[0].to_dict()
            else:
                logger.warning(f"No se encontró cuerpo con nombre: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error buscando cuerpo por nombre {name}: {e}")
            return None
    
    def get_planets(self, include_dwarf: bool = False) -> pd.DataFrame:
        """
        Obtiene todos los planetas
        
        Args:
            include_dwarf: Si incluir planetas enanos
            
        Returns:
            DataFrame con planetas
        """
        # Filtro para planetas
        params = {
            'data': ','.join(self.default_fields + ['moons']),
            'filter[]': 'isPlanet,eq,true'
        }
        
        if include_dwarf:
            params['satisfy'] = 'any'
            params['filter[]'] = ['isPlanet,eq,true', 'bodyType,eq,dwarfPlanet']
        
        try:
            response = self.get('/rest/bodies/', params=params)
            data = response.json()
            
            df = pd.DataFrame(data['bodies'] if 'bodies' in data else data)
            df = self._process_complex_fields(df)
            
            # Ordenar por distancia al Sol
            df = df.sort_values('semimajorAxis')
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo planetas: {e}")
            raise
    
    def get_moons(self, planet_id: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene lunas del sistema solar
        
        Args:
            planet_id: ID del planeta para obtener sus lunas (None = todas)
            
        Returns:
            DataFrame con lunas
        """
        params = {
            'data': ','.join(self.default_fields + ['aroundPlanet', 'discoveredBy', 'discoveryDate']),
            'filter[]': 'aroundPlanet,sw,'  # sw = starts with
        }
        
        if planet_id:
            # Buscar lunas de un planeta específico
            params['filter[]'] = f'aroundPlanet.id,eq,{planet_id}'
        
        try:
            response = self.get('/rest/bodies/', params=params)
            data = response.json()
            
            df = pd.DataFrame(data['bodies'] if 'bodies' in data else data)
            df = self._process_complex_fields(df)
            
            # Procesar información del planeta
            if 'aroundPlanet' in df.columns:
                df['planet_id'] = df['aroundPlanet'].apply(
                    lambda x: x.get('id') if isinstance(x, dict) else None
                )
                df['planet_name'] = df['aroundPlanet'].apply(
                    lambda x: x.get('englishName') if isinstance(x, dict) else None
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo lunas: {e}")
            raise
    
    def _process_complex_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Procesa campos complejos del DataFrame
        
        Args:
            df: DataFrame a procesar
            
        Returns:
            DataFrame procesado
        """
        if df.empty:
            return df
        
        # Procesar masa (viene como dict con value y exponent)
        if 'mass' in df.columns:
            df['mass_value'] = df['mass'].apply(
                lambda x: x.get('massValue', 0) if isinstance(x, dict) else 0
            )
            df['mass_exponent'] = df['mass'].apply(
                lambda x: x.get('massExponent', 0) if isinstance(x, dict) else 0
            )
            df['mass_kg'] = df.apply(
                lambda row: row['mass_value'] * 10 ** row['mass_exponent'],
                axis=1
            )
        
        # Procesar volumen
        if 'vol' in df.columns:
            df['vol_value'] = df['vol'].apply(
                lambda x: x.get('volValue', 0) if isinstance(x, dict) else 0
            )
            df['vol_exponent'] = df['vol'].apply(
                lambda x: x.get('volExponent', 0) if isinstance(x, dict) else 0
            )
            df['vol_km3'] = df.apply(
                lambda row: row['vol_value'] * 10 ** row['vol_exponent'],
                axis=1
            )
        
        # Procesar lunas (contar si es lista)
        if 'moons' in df.columns:
            df['moon_count'] = df['moons'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
        
        # Convertir valores numéricos
        numeric_fields = [
            'semimajorAxis', 'perihelion', 'aphelion', 'eccentricity',
            'inclination', 'density', 'gravity', 'escape',
            'meanRadius', 'equaRadius', 'polarRadius', 'flattening',
            'sideralOrbit', 'sideralRotation', 'axialTilt', 'avgTemp',
            'mainAnomaly', 'argPeriapsis', 'longAscNode'
        ]
        
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        return df
    
    def batch_download_all(self) -> Dict[str, str]:
        """
        MÉTODO PRINCIPAL: Descarga masiva de todos los datos para almacenamiento local
        
        Returns:
            Diccionario con rutas de archivos generados
        """
        print("[OpenData] *** INICIANDO DESCARGA MASIVA ***")
        
        # Crear directorio de datos
        os.makedirs(self.data_dir, exist_ok=True)
        files_created = {}
        
        try:
            # 1. Todos los cuerpos del sistema solar
            print("[OpenData] Descargando todos los cuerpos...")
            all_bodies = self.get_all_bodies(fields=self.comprehensive_fields)
            if not all_bodies.empty:
                filepath = os.path.join(self.data_dir, "opendata_all_bodies.csv")
                all_bodies.to_csv(filepath, index=False, encoding='utf-8')
                files_created['all_bodies'] = filepath
                print(f"[OpenData] OK - Guardados {len(all_bodies)} cuerpos en {filepath}")
            
            # 2. Solo planetas (incluyendo enanos)
            print("[OpenData] Descargando planetas...")
            planets = self.get_planets(include_dwarf=True)
            if not planets.empty:
                filepath = os.path.join(self.data_dir, "opendata_planets.csv")
                planets.to_csv(filepath, index=False, encoding='utf-8')
                files_created['planets'] = filepath
                print(f"[OpenData] OK - Guardados {len(planets)} planetas en {filepath}")
            
            # 3. Solo lunas
            print("[OpenData] Descargando lunas...")
            moons = self.get_moons()
            if not moons.empty:
                filepath = os.path.join(self.data_dir, "opendata_moons.csv")
                moons.to_csv(filepath, index=False, encoding='utf-8')
                files_created['moons'] = filepath
                print(f"[OpenData] OK - Guardadas {len(moons)} lunas en {filepath}")
            
            # 4. Metadatos del proceso
            metadata = {
                'download_date': datetime.now().isoformat(),
                'api_source': 'https://api.le-systeme-solaire.net',
                'files_generated': list(files_created.keys()),
                'total_records': sum([
                    len(all_bodies) if not all_bodies.empty else 0,
                    len(planets) if not planets.empty else 0,
                    len(moons) if not moons.empty else 0
                ]),
                'next_update_recommended': (datetime.now() + self.cache_duration).isoformat()
            }
            
            metadata_path = os.path.join(self.data_dir, "opendata_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            files_created['metadata'] = metadata_path
            
            print(f"[OpenData] *** DESCARGA COMPLETADA ***")
            print(f"[OpenData] {len(files_created)} archivos creados")
            print(f"[OpenData] Proxima actualizacion recomendada: {metadata['next_update_recommended'][:10]}")
            
        except Exception as e:
            logger.error(f"Error en descarga masiva: {e}")
            print(f"[ERROR] Error en descarga masiva: {e}")
        
        return files_created
    
    def check_cache_status(self) -> Dict[str, Any]:
        """
        Verifica el estado del cache local
        
        Returns:
            Información sobre el estado del cache
        """
        cache_status = {
            'cache_exists': False,
            'last_update': None,
            'days_old': None,
            'needs_update': True,
            'files': {}
        }
        
        metadata_path = os.path.join(self.data_dir, "opendata_metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                download_date = datetime.fromisoformat(metadata['download_date'])
                days_old = (datetime.now() - download_date).days
                
                cache_status.update({
                    'cache_exists': True,
                    'last_update': metadata['download_date'],
                    'days_old': days_old,
                    'needs_update': days_old > self.cache_duration.days,
                    'total_records': metadata.get('total_records', 0)
                })
                
                # Verificar archivos individuales
                for file_type in ['all_bodies', 'planets', 'moons']:
                    filepath = os.path.join(self.data_dir, f"opendata_{file_type}.csv")
                    if os.path.exists(filepath):
                        df = pd.read_csv(filepath)
                        cache_status['files'][file_type] = {
                            'exists': True,
                            'records': len(df),
                            'path': filepath
                        }
                    else:
                        cache_status['files'][file_type] = {'exists': False}
                        
            except Exception as e:
                logger.error(f"Error leyendo metadata: {e}")
        
        return cache_status


def get_solar_system_client() -> SolarSystemOpenDataClient:
    """
    Factory function para crear cliente Solar System OpenData
    
    Returns:
        Instancia de SolarSystemOpenDataClient
    """
    return SolarSystemOpenDataClient()


if __name__ == "__main__":
    print("=== Demo OpenData Client - Estrategia BATCH ===")
    
    client = get_solar_system_client()
    
    # Verificar estado del cache
    cache_status = client.check_cache_status()
    print(f"Cache existe: {cache_status['cache_exists']}")
    print(f"Necesita actualización: {cache_status['needs_update']}")
    
    if cache_status['needs_update']:
        print("\n🔄 Iniciando descarga masiva...")
        files = client.batch_download_all()
        print(f"✅ Archivos creados: {list(files.keys())}")
    else:
        print(f"✅ Cache actualizado (última actualización: {cache_status['last_update'][:10]})")
        print(f"📊 Total de registros: {cache_status.get('total_records', 0)}")
        
        # Mostrar ejemplo de datos cacheados
        if cache_status['files']['planets']['exists']:
            planets_path = cache_status['files']['planets']['path']
            planets_df = pd.read_csv(planets_path)
            print(f"\n🪐 Planetas en cache ({len(planets_df)}):")
            print(planets_df[['englishName', 'meanRadius', 'mass_kg']].head().to_string())