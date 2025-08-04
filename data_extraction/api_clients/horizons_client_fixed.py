"""
Cliente Horizons Corregido - Implementación según investigacion.md
===============================================================

ESTRATEGIA DE DOS PASOS según investigacion.md:
1. Usar horizons_lookup.api para obtener SPK-ID único
2. Usar horizons.api con SPK-ID para obtener efemérides

APIs utilizadas:
- Lookup: https://ssd-api.jpl.nasa.gov/api/horizons_lookup.api
- Horizons: https://ssd.jpl.nasa.gov/api/horizons.api (GET, no POST)
"""

import requests
import json
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class HorizonsClientFixed:
    """
    Cliente Horizons corregido según especificaciones de investigacion.md
    Implementa la estrategia de dos pasos recomendada
    """
    
    def __init__(self):
        # URLs corregidas según investigacion.md
        self.lookup_url = "https://ssd-api.jpl.nasa.gov/api/horizons_lookup.api"
        self.horizons_url = "https://ssd.jpl.nasa.gov/api/horizons.api"
        self.timeout = 30
        
        # Cache para SPK-IDs ya resueltos
        self._spkid_cache = {}
    
    def get_spkid_for_object(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        PASO 1: Obtener SPK-ID único usando horizons_lookup.api
        Implementa la estrategia recomendada en investigacion.md sección 1.2
        """
        # Verificar cache primero
        if object_name.lower() in self._spkid_cache:
            logger.debug(f"Using cached SPK-ID for {object_name}")
            return self._spkid_cache[object_name.lower()]
        
        try:
            # Parámetros según investigacion.md
            params = {
                'sstr': object_name,
                'format': 'json'
            }
            
            # Agregar filtro de grupo si es posible detectar el tipo
            if self._is_likely_asteroid(object_name):
                params['group'] = 'ast'
            elif self._is_likely_comet(object_name):
                params['group'] = 'com'
            
            logger.info(f"Looking up SPK-ID for: {object_name}")
            response = requests.get(self.lookup_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar que hay resultados
            if not data.get('count', 0) or 'result' not in data:
                logger.warning(f"No SPK-ID found for {object_name}")
                return None
            
            # Tomar el primer resultado (más relevante)
            first_result = data['result'][0]
            
            object_info = {
                'spkid': first_result.get('spkid'),
                'name': first_result.get('name'),
                'aliases': first_result.get('alias', []),
                'type': first_result.get('type'),
                'query_name': object_name
            }
            
            # Guardar en cache
            self._spkid_cache[object_name.lower()] = object_info
            
            logger.info(f"Found SPK-ID for {object_name}: {object_info['spkid']} ({object_info['name']})")
            return object_info
            
        except requests.RequestException as e:
            logger.error(f"Error in SPK-ID lookup for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in SPK-ID lookup for {object_name}: {e}")
            return None
    
    def get_ephemeris_data(self, spkid: str, start_date: str, stop_date: str, 
                          step_size: str = '1d') -> Optional[Dict[str, Any]]:
        """
        PASO 2: Obtener efemérides usando horizons.api con SPK-ID
        Implementa las especificaciones de investigacion.md sección 1.3
        """
        try:
            # Construir parámetros según Tabla 1 de investigacion.md
            params = {
                'format': 'json',
                'COMMAND': f"'{spkid}'",  # SPK-ID obtenido del paso 1
                'OBJ_DATA': 'YES',       # Incluir datos del objeto
                'MAKE_EPHEM': 'YES',     # Generar efemérides
                'EPHEM_TYPE': 'OBSERVER', # Tipo según investigacion.md
                'CENTER': "'500@399'",   # Centro de la Tierra según investigacion.md
                'START_TIME': f"'{start_date}'",
                'STOP_TIME': f"'{stop_date}'",
                'STEP_SIZE': f"'{step_size}'",
                'QUANTITIES': "'1,9,20,23,24'"  # Cantidades recomendadas en investigacion.md
            }
            
            logger.info(f"Getting ephemeris for SPK-ID {spkid} from {start_date} to {stop_date}")
            
            # Usar GET según investigacion.md (no POST como en código original)
            response = requests.get(self.horizons_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar respuesta según investigacion.md
            if 'result' not in data:
                logger.error(f"No result field in Horizons response for SPK-ID {spkid}")
                return None
            
            result_text = data['result']
            
            # Verificar errores comunes
            if 'No such object record found' in result_text:
                logger.warning(f"Object not found in Horizons for SPK-ID {spkid}")
                return None
            
            # Parsear resultado usando la estrategia de investigacion.md sección 1.5
            parsed_data = self._parse_horizons_result(result_text)
            
            if parsed_data:
                logger.info(f"Successfully parsed {parsed_data.get('data_points', 0)} ephemeris points for SPK-ID {spkid}")
            
            return parsed_data
            
        except requests.RequestException as e:
            logger.error(f"Error getting ephemeris for SPK-ID {spkid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting ephemeris for SPK-ID {spkid}: {e}")
            return None
    
    def _parse_horizons_result(self, result_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta de Horizons según estrategia de investigacion.md sección 1.5
        Busca marcadores $$SOE y $$EOE para extraer la tabla de efemérides
        """
        try:
            # Paso 1: Extraer información del objeto
            object_data = self._extract_object_data(result_text)
            
            # Paso 2: Aislar la tabla de efemérides usando marcadores
            ephemeris_match = re.search(r'\$\$SOE(.*?)\$\$EOE', result_text, re.DOTALL)
            if not ephemeris_match:
                logger.warning("No ephemeris table found (no $$SOE/$$EOE markers)")
                return {'error': 'No ephemeris table found', 'data_points': 0}
            
            ephemeris_block = ephemeris_match.group(1).strip()
            
            # Paso 3: Parsear líneas de datos
            lines = ephemeris_block.split('\n')
            parsed_entries = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('*'):
                    continue
                
                # Parsear línea según formato de Horizons
                entry = self._parse_ephemeris_line(line)
                if entry:
                    parsed_entries.append(entry)
            
            result = {
                'object_data': object_data,
                'ephemeris': parsed_entries,
                'data_points': len(parsed_entries)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Horizons result: {e}")
            return {'error': str(e), 'data_points': 0}
    
    def _extract_object_data(self, result_text: str) -> Dict[str, Any]:
        """
        Extrae datos del objeto de la sección OBJ_DATA según investigacion.md
        """
        object_data = {}
        
        # Buscar líneas con información clave
        lines = result_text.split('\n')
        for line in lines:
            # Magnitud absoluta (H)
            if 'Absolute magnitude' in line and 'H =' in line:
                match = re.search(r'H\s*=\s*([\d.-]+)', line)
                if match:
                    object_data['absolute_magnitude_H'] = float(match.group(1))
            
            # Nombre del objeto
            if 'Target body name:' in line:
                parts = line.split(':', 1)[1].strip()
                object_data['target_name'] = parts
            
            # Diámetro si está disponible
            if 'diameter' in line.lower() and 'km' in line:
                match = re.search(r'([\d.]+)\s*km', line)
                if match:
                    object_data['diameter_km'] = float(match.group(1))
        
        return object_data
    
    def _parse_ephemeris_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parsea una línea individual de efemérides
        Implementa parsing robusto según investigacion.md
        """
        try:
            parts = line.split()
            if len(parts) < 3:
                return None
            
            # Detectar formato de fecha (YYYY-MMM-DD HH:MM)
            if len(parts) >= 2 and '-' in parts[0]:
                date_str = f"{parts[0]} {parts[1]}"
                data_start = 2
            else:
                date_str = parts[0]
                data_start = 1
            
            # Extraer valores numéricos del resto de la línea
            numeric_values = []
            for i in range(data_start, len(parts)):
                try:
                    if parts[i] not in ['n.a.', '*', 'N/A']:
                        numeric_values.append(float(parts[i]))
                    else:
                        numeric_values.append(None)
                except ValueError:
                    numeric_values.append(None)
            
            # Mapear valores según QUANTITIES='1,9,20,23,24' de investigacion.md
            entry = {
                'date_time': date_str,
                'raw_line': line
            }
            
            # Asignar valores según las cantidades solicitadas
            if len(numeric_values) >= 1:
                entry['apparent_magnitude'] = numeric_values[0] if numeric_values[0] and -10 <= numeric_values[0] <= 30 else None
            if len(numeric_values) >= 2:
                entry['distance_au'] = numeric_values[1] if numeric_values[1] and 0.01 <= numeric_values[1] <= 1000 else None
            if len(numeric_values) >= 3:
                entry['range_rate'] = numeric_values[2]
            
            return entry
            
        except Exception as e:
            logger.debug(f"Error parsing ephemeris line '{line}': {e}")
            return None
    
    def get_object_ephemeris_complete(self, object_name: str, days_ahead: int = 30) -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL: Implementa el flujo completo de dos pasos según investigacion.md
        """
        # Paso A: Búsqueda y validación
        object_info = self.get_spkid_for_object(object_name)
        if not object_info or not object_info.get('spkid'):
            return {
                'status': 'error',
                'error': f'No se pudo encontrar SPK-ID para {object_name}',
                'object_name': object_name
            }
        
        # Preparar fechas
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Paso B: Obtener datos científicos
        ephemeris_data = self.get_ephemeris_data(
            spkid=object_info['spkid'],
            start_date=start_date,
            stop_date=end_date
        )
        
        if not ephemeris_data or ephemeris_data.get('error'):
            return {
                'status': 'error',
                'error': f'No se pudieron obtener efemérides para {object_name}',
                'object_info': object_info
            }
        
        # Combinar información
        return {
            'status': 'success',
            'object_name': object_name,
            'object_info': object_info,
            'ephemeris_data': ephemeris_data,
            'query_period': f"{start_date} to {end_date}",
            'data_points': ephemeris_data.get('data_points', 0)
        }
    
    def _is_likely_asteroid(self, name: str) -> bool:
        """Detecta si el nombre probablemente corresponde a un asteroide"""
        name_lower = name.lower()
        # Asteroides suelen tener números al inicio o nombres específicos
        return (re.match(r'^\d+', name) or 
                name_lower in ['ceres', 'vesta', 'pallas', 'hygiea'] or
                'asteroid' in name_lower)
    
    def _is_likely_comet(self, name: str) -> bool:
        """Detecta si el nombre probablemente corresponde a un cometa"""
        name_lower = name.lower()
        return ('comet' in name_lower or 
                name_lower in ['halley', 'encke', 'tempel'] or
                re.match(r'^\d+P', name) or  # Cometas periódicos
                re.match(r'^C/', name))      # Cometas no periódicos


# Factory function
def get_fixed_horizons_client() -> HorizonsClientFixed:
    """Crea una instancia del cliente corregido"""
    return HorizonsClientFixed()


if __name__ == "__main__":
    print("=== Demo Cliente Horizons Corregido ===")
    print("Implementa estrategia de dos pasos según investigacion.md")
    
    client = get_fixed_horizons_client()
    
    # Ejemplo de uso del flujo completo
    test_objects = ['Apophis', 'Ceres', 'Mars']
    
    for obj_name in test_objects:
        print(f"\n--- Probando: {obj_name} ---")
        
        result = client.get_object_ephemeris_complete(obj_name, days_ahead=7)
        
        if result['status'] == 'success':
            print(f"✓ SUCCESS: {result['data_points']} puntos de datos obtenidos")
            print(f"  SPK-ID: {result['object_info']['spkid']}")
            print(f"  Nombre oficial: {result['object_info']['name']}")
            print(f"  Período: {result['query_period']}")
        else:
            print(f"✗ ERROR: {result['error']}")