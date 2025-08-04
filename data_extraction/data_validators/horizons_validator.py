"""
Validador avanzado para respuestas de la API de Horizons de NASA
"""
import logging
import re
from typing import Dict, List, Optional, Union
import json

logger = logging.getLogger(__name__)

class HorizonsValidator:
    """Validador especializado para respuestas de la API de Horizons"""
    
    def __init__(self):
        """Inicializa el validador con patrones de error conocidos"""
        
        # Patrones de error comunes en respuestas de Horizons
        self.error_patterns = [
            r"Object not found",
            r"No ephemerides",
            r"No such object",
            r"Target body not found",
            r"Invalid object",
            r"Unrecognized target",
            r"No data available",
            r"Request failed",
            r"Error in input",
            r"Cannot process",
            r"Invalid command",
            r"Target not found",
            r"Ephemeris not available",
            r"Time span too long",
            r"Time span too short"
        ]
        
        # Patrones para validar marcadores de datos
        self.data_markers = {
            'start': r'\$\$SOE',  # Start of Ephemeris
            'end': r'\$\$EOE'     # End of Ephemeris
        }
        
        # Campos esperados en datos orbitales válidos
        self.expected_orbital_fields = [
            'date', 'time', 'julian_day', 'distance', 'magnitude', 
            'right_ascension', 'declination', 'delta', 'phase_angle'
        ]
        
        # Rangos válidos para parámetros orbitales
        self.valid_ranges = {
            'distance_au': (0.1, 100.0),      # Distancia en AU
            'magnitude': (-30.0, 30.0),        # Magnitud visual
            'delta_km': (1000, 1e10),          # Distancia a la Tierra en km
            'phase_angle': (0.0, 180.0),       # Ángulo de fase en grados
            'right_ascension': (0.0, 360.0),   # Ascensión recta en grados
            'declination': (-90.0, 90.0)       # Declinación en grados
        }
    
    def validate_horizons_response(self, response_data: Union[Dict, str]) -> Dict:
        """
        Valida una respuesta completa de la API de Horizons
        
        Args:
            response_data: Respuesta de la API (dict JSON o string)
            
        Returns:
            Dict con resultado de validación:
            {
                'is_valid': bool,
                'error_type': str,
                'error_message': str,
                'data_quality': str,
                'data_points': int,
                'issues': List[str],
                'warnings': List[str]
            }
        """
        result = {
            'is_valid': False,
            'error_type': None,
            'error_message': None,
            'data_quality': 'unknown',
            'data_points': 0,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Paso 1: Validar estructura de respuesta
            if isinstance(response_data, str):
                # Respuesta de texto directo
                validation = self._validate_text_response(response_data)
            elif isinstance(response_data, dict):
                # Respuesta JSON
                validation = self._validate_json_response(response_data)
            else:
                result['error_type'] = 'invalid_format'
                result['error_message'] = 'Response format not supported'
                return result
            
            result.update(validation)
            
            # Paso 2: Si hay datos, validar calidad orbital
            if result['is_valid'] and result['data_points'] > 0:
                quality_check = self._assess_data_quality(response_data)
                result['data_quality'] = quality_check['quality']
                result['warnings'].extend(quality_check['warnings'])
                
                # Si la calidad es muy baja, marcar como inválido
                if quality_check['quality'] == 'poor':
                    result['is_valid'] = False
                    result['error_type'] = 'poor_data_quality'
                    result['error_message'] = 'Data quality below acceptable threshold'
            
            logger.debug(f"Horizons validation result: {result['data_quality']} quality, {result['data_points']} points")
            
        except Exception as e:
            result['error_type'] = 'validation_error'
            result['error_message'] = f"Validation process failed: {str(e)}"
            logger.error(f"Error validating Horizons response: {e}")
        
        return result
    
    def _validate_json_response(self, json_data: Dict) -> Dict:
        """Valida respuesta JSON de Horizons"""
        result = {
            'is_valid': False,
            'error_type': None,
            'error_message': None,
            'data_points': 0,
            'issues': [],
            'warnings': []
        }
        
        # Verificar campo 'error' explícito
        if 'error' in json_data:
            result['error_type'] = 'api_error'
            result['error_message'] = json_data['error']
            return result
        
        # Verificar si hay campo 'result' con datos
        result_text = json_data.get('result', '')
        if not result_text or not result_text.strip():
            result['error_type'] = 'empty_result'
            result['error_message'] = 'No result data in response'
            return result
        
        # Validar el contenido del resultado como texto
        text_validation = self._validate_text_response(result_text)
        result.update(text_validation)
        
        return result
    
    def _validate_text_response(self, text_data: str) -> Dict:
        """Valida respuesta de texto de Horizons"""
        result = {
            'is_valid': False,
            'error_type': None,
            'error_message': None,
            'data_points': 0,
            'issues': [],
            'warnings': []
        }
        
        if not text_data or not text_data.strip():
            result['error_type'] = 'empty_response'
            result['error_message'] = 'Empty response text'
            return result
        
        # Buscar patrones de error en el texto
        for pattern in self.error_patterns:
            if re.search(pattern, text_data, re.IGNORECASE):
                result['error_type'] = 'horizons_error'
                result['error_message'] = f'Horizons error pattern found: {pattern}'
                return result
        
        # Verificar marcadores de datos ($$SOE...$$EOE)
        has_start_marker = re.search(self.data_markers['start'], text_data)
        has_end_marker = re.search(self.data_markers['end'], text_data)
        
        if not has_start_marker or not has_end_marker:
            result['issues'].append('Missing standard data markers ($$SOE/$$EOE)')
            
            # Intentar encontrar datos sin marcadores
            lines = text_data.split('\n')
            data_lines = [line for line in lines if line.strip() and 
                         not line.startswith('*') and not line.startswith('!')]
            
            if len(data_lines) < 3:  # Muy pocas líneas de datos
                result['error_type'] = 'insufficient_data'
                result['error_message'] = 'Insufficient data lines found'
                return result
            
            result['warnings'].append('Data found without standard markers')
            result['data_points'] = len(data_lines)
        else:
            # Contar líneas de datos entre marcadores
            start_match = has_start_marker
            end_match = has_end_marker
            
            start_pos = start_match.end()
            end_pos = end_match.start()
            
            data_section = text_data[start_pos:end_pos]
            data_lines = [line for line in data_section.split('\n') if line.strip()]
            result['data_points'] = len(data_lines)
        
        # Validar coherencia de datos orbitales
        coherence_check = self._validate_orbital_coherence(text_data)
        result['issues'].extend(coherence_check['issues'])
        result['warnings'].extend(coherence_check['warnings'])
        
        # Determinar si es válido
        if result['data_points'] > 0 and not result['error_type']:
            result['is_valid'] = True
        elif result['data_points'] == 0:
            result['error_type'] = 'no_data_points'
            result['error_message'] = 'No valid data points found'
        
        return result
    
    def _validate_orbital_coherence(self, text_data: str) -> Dict:
        """Valida coherencia de datos orbitales"""
        issues = []
        warnings = []
        
        lines = text_data.split('\n')
        numeric_lines = []
        
        # Extraer líneas con datos numéricos
        for line in lines:
            line = line.strip()
            if not line or line.startswith('*') or line.startswith('!'):
                continue
            
            # Buscar líneas con múltiples números (datos orbitales)
            numbers = re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', line)
            if len(numbers) >= 3:  # Al menos fecha, distancia, magnitud
                numeric_lines.append(line)
        
        if len(numeric_lines) < 2:
            issues.append('Insufficient orbital data lines for coherence check')
            return {'issues': issues, 'warnings': warnings}
        
        # Verificar patrones en los datos
        try:
            # Extraer valores numéricos de muestra
            sample_values = []
            for line in numeric_lines[:5]:  # Revisar primeras 5 líneas
                parts = line.split()
                values = []
                for part in parts:
                    try:
                        val = float(part)
                        values.append(val)
                    except ValueError:
                        continue
                
                if values:
                    sample_values.append(values)
            
            # Verificar rangos razonables
            if sample_values:
                # Buscar valores que podrían ser distancias
                for values in sample_values:
                    for val in values:
                        # Distancia en AU (típicamente 0.1 a 100)
                        if 0.1 <= val <= 100.0:
                            if val < 0.1 or val > 50.0:
                                warnings.append(f'Unusual distance value: {val} AU')
                        
                        # Magnitud (típicamente -30 a 30)
                        elif -30.0 <= val <= 30.0:
                            if val < -10 or val > 25:
                                warnings.append(f'Unusual magnitude value: {val}')
            
        except Exception as e:
            warnings.append(f'Could not perform coherence check: {str(e)}')
        
        return {'issues': issues, 'warnings': warnings}
    
    def _assess_data_quality(self, response_data: Union[Dict, str]) -> Dict:
        """Evalúa la calidad general de los datos"""
        quality_metrics = {
            'completeness': 0,
            'consistency': 0,
            'accuracy': 0,
            'warnings': []
        }
        
        # Obtener texto de datos
        if isinstance(response_data, dict):
            text_data = response_data.get('result', '')
        else:
            text_data = response_data
        
        if not text_data:
            return {'quality': 'poor', 'warnings': ['No data to assess']}
        
        lines = text_data.split('\n')
        data_lines = [line for line in lines if line.strip() and 
                     not line.startswith('*') and not line.startswith('!')]
        
        # Métrica de completitud
        if len(data_lines) >= 10:
            quality_metrics['completeness'] = 1.0
        elif len(data_lines) >= 5:
            quality_metrics['completeness'] = 0.7
        elif len(data_lines) >= 1:
            quality_metrics['completeness'] = 0.4
        else:
            quality_metrics['completeness'] = 0.0
        
        # Métrica de consistencia (líneas con formato similar)
        if len(data_lines) > 1:
            first_line_parts = len(data_lines[0].split())
            consistent_lines = sum(1 for line in data_lines 
                                 if abs(len(line.split()) - first_line_parts) <= 1)
            quality_metrics['consistency'] = consistent_lines / len(data_lines)
        else:
            quality_metrics['consistency'] = 1.0 if len(data_lines) == 1 else 0.0
        
        # Métrica de precisión (valores en rangos esperados)
        accurate_values = 0
        total_values = 0
        
        for line in data_lines[:5]:  # Revisar muestra
            numbers = re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', line)
            for num_str in numbers:
                try:
                    val = float(num_str)
                    total_values += 1
                    
                    # Verificar si está en algún rango esperado
                    if (0.1 <= val <= 100.0 or      # Distancia AU
                        -30.0 <= val <= 30.0 or      # Magnitud
                        0.0 <= val <= 360.0 or       # Ángulos
                        1000 <= val <= 1e10):        # Distancias km
                        accurate_values += 1
                        
                except ValueError:
                    continue
        
        if total_values > 0:
            quality_metrics['accuracy'] = accurate_values / total_values
        else:
            quality_metrics['accuracy'] = 0.0
        
        # Calcular calidad general
        overall_score = (
            quality_metrics['completeness'] * 0.4 +
            quality_metrics['consistency'] * 0.3 +
            quality_metrics['accuracy'] * 0.3
        )
        
        if overall_score >= 0.8:
            quality = 'excellent'
        elif overall_score >= 0.6:
            quality = 'good'
        elif overall_score >= 0.4:
            quality = 'fair'
        else:
            quality = 'poor'
        
        # Agregar advertencias basadas en métricas
        if quality_metrics['completeness'] < 0.5:
            quality_metrics['warnings'].append('Low data completeness')
        if quality_metrics['consistency'] < 0.7:
            quality_metrics['warnings'].append('Inconsistent data format')
        if quality_metrics['accuracy'] < 0.6:
            quality_metrics['warnings'].append('Values outside expected ranges')
        
        return {'quality': quality, 'warnings': quality_metrics['warnings']}
    
    def validate_ephemeris_data(self, ephemeris_dict: Dict) -> Dict:
        """
        Valida un diccionario de datos de efemérides ya parseados
        
        Args:
            ephemeris_dict: Dict con datos parseados de efemérides
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'is_valid': False,
            'issues': [],
            'warnings': [],
            'data_quality': 'unknown'
        }
        
        # Verificar estructura básica
        required_fields = ['dates', 'distances', 'magnitudes', 'data_points']
        for field in required_fields:
            if field not in ephemeris_dict:
                result['issues'].append(f'Missing required field: {field}')
        
        if result['issues']:
            return result
        
        # Verificar consistencia de longitudes
        dates = ephemeris_dict.get('dates', [])
        distances = ephemeris_dict.get('distances', [])
        magnitudes = ephemeris_dict.get('magnitudes', [])
        
        lengths = [len(dates), len(distances), len(magnitudes)]
        if len(set(lengths)) > 1:
            result['issues'].append(f'Inconsistent array lengths: {lengths}')
            return result
        
        data_points = ephemeris_dict.get('data_points', 0)
        if data_points != len(dates):
            result['warnings'].append(f'Data points count mismatch: {data_points} vs {len(dates)}')
        
        # Verificar valores en rangos válidos
        for i, distance in enumerate(distances):
            if distance is not None:
                if not (0.1 <= distance <= 100.0):
                    result['warnings'].append(f'Distance out of range at index {i}: {distance}')
        
        for i, magnitude in enumerate(magnitudes):
            if magnitude is not None:
                if not (-30.0 <= magnitude <= 30.0):
                    result['warnings'].append(f'Magnitude out of range at index {i}: {magnitude}')
        
        # Determinar calidad
        valid_distances = sum(1 for d in distances if d is not None)
        valid_magnitudes = sum(1 for m in magnitudes if m is not None)
        total_points = len(dates)
        
        if total_points == 0:
            result['data_quality'] = 'poor'
        else:
            completeness = (valid_distances + valid_magnitudes) / (2 * total_points)
            if completeness >= 0.8:
                result['data_quality'] = 'excellent'
            elif completeness >= 0.6:
                result['data_quality'] = 'good'
            elif completeness >= 0.4:
                result['data_quality'] = 'fair'
            else:
                result['data_quality'] = 'poor'
        
        # Es válido si no hay problemas críticos
        result['is_valid'] = len(result['issues']) == 0 and total_points > 0
        
        return result


def validate_horizons_response(response_data: Union[Dict, str]) -> Dict:
    """
    Función de conveniencia para validar respuesta de Horizons
    
    Args:
        response_data: Respuesta de la API de Horizons
        
    Returns:
        Dict con resultado de validación
    """
    validator = HorizonsValidator()
    return validator.validate_horizons_response(response_data)


def validate_ephemeris_data(ephemeris_dict: Dict) -> Dict:
    """
    Función de conveniencia para validar datos de efemérides parseados
    
    Args:
        ephemeris_dict: Dict con datos de efemérides
        
    Returns:
        Dict con resultado de validación
    """
    validator = HorizonsValidator()
    return validator.validate_ephemeris_data(ephemeris_dict)


if __name__ == "__main__":
    # Ejemplo de uso
    validator = HorizonsValidator()
    
    # Simular respuesta exitosa
    good_response = {
        'result': '''
*******************************************************************************
JPL/HORIZONS                    Earth (399)              2024-Jan-01 00:00:00
*******************************************************************************
$$SOE
2024-Jan-01 00:00     1.983234  12.34   ...
2024-Jan-02 00:00     1.985123  12.35   ...
2024-Jan-03 00:00     1.987012  12.36   ...
$$EOE
*******************************************************************************
        '''
    }
    
    # Simular respuesta con error
    error_response = {
        'error': 'Object not found in database'
    }
    
    print("Testing good response:")
    result = validator.validate_horizons_response(good_response)
    print(f"Valid: {result['is_valid']}")
    print(f"Data points: {result['data_points']}")
    print(f"Quality: {result['data_quality']}")
    
    print("\nTesting error response:")
    result = validator.validate_horizons_response(error_response)
    print(f"Valid: {result['is_valid']}")
    print(f"Error: {result['error_message']}")