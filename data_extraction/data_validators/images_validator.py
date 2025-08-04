"""
Validador avanzado para respuestas de la API de imágenes de NASA
"""
import logging
import re
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class ImagesValidator:
    """Validador especializado para respuestas de la API de imágenes de NASA"""
    
    def __init__(self):
        """Inicializa el validador con criterios de validación"""
        
        # Campos obligatorios en la estructura Collection+JSON
        self.required_collection_fields = ['version', 'href', 'items']
        self.required_item_fields = ['data', 'links']
        self.required_data_fields = ['title', 'nasa_id', 'date_created']
        
        # Tipos de media válidos
        self.valid_media_types = ['image', 'video', 'audio']
        
        # Patrones para URLs válidas
        self.valid_url_patterns = [
            r'^https?://',
            r'^/static/',
            r'^//',
        ]
        
        # Extensiones de archivo válidas para imágenes
        self.valid_image_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
        ]
        
        # Centros NASA válidos
        self.valid_nasa_centers = [
            'NASA', 'GSFC', 'JPL', 'JSC', 'KSC', 'LaRC', 'MSFC', 'ARC',
            'DFRC', 'GRC', 'SSC', 'NACA', 'HQ'
        ]
        
        # Campos opcionales pero recomendados
        self.recommended_fields = [
            'description', 'keywords', 'center', 'photographer', 
            'location', 'media_type'
        ]
    
    def validate_images_response(self, response_data: Union[Dict, str]) -> Dict:
        """
        Valida una respuesta completa de la API de imágenes de NASA
        
        Args:
            response_data: Respuesta de la API (dict JSON o string)
            
        Returns:
            Dict con resultado de validación:
            {
                'is_valid': bool,
                'error_type': str,
                'error_message': str,
                'data_quality': str,
                'total_items': int,
                'valid_items': int,
                'issues': List[str],
                'warnings': List[str]
            }
        """
        result = {
            'is_valid': False,
            'error_type': None,
            'error_message': None,
            'data_quality': 'unknown',
            'total_items': 0,
            'valid_items': 0,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Convertir string a dict si es necesario
            if isinstance(response_data, str):
                try:
                    response_data = json.loads(response_data)
                except json.JSONDecodeError as e:
                    result['error_type'] = 'invalid_json'
                    result['error_message'] = f'Invalid JSON format: {str(e)}'
                    return result
            
            if not isinstance(response_data, dict):
                result['error_type'] = 'invalid_format'
                result['error_message'] = 'Response must be a dictionary'
                return result
            
            # Validar estructura Collection+JSON
            collection_validation = self._validate_collection_structure(response_data)
            result.update(collection_validation)
            
            if not result['is_valid']:
                return result
            
            # Validar elementos individuales
            items_validation = self._validate_items(response_data.get('collection', {}).get('items', []))
            result['total_items'] = items_validation['total_items']
            result['valid_items'] = items_validation['valid_items']
            result['issues'].extend(items_validation['issues'])
            result['warnings'].extend(items_validation['warnings'])
            
            # Evaluar calidad general
            quality_assessment = self._assess_response_quality(response_data, items_validation)
            result['data_quality'] = quality_assessment['quality']
            result['warnings'].extend(quality_assessment['warnings'])
            
            # Determinar validez final
            if result['valid_items'] == 0 and result['total_items'] > 0:
                result['is_valid'] = False
                result['error_type'] = 'no_valid_items'
                result['error_message'] = 'No valid items found in response'
            elif result['total_items'] == 0:
                result['is_valid'] = True  # Búsqueda sin resultados es válida
                result['warnings'].append('No items found in search results')
            
            logger.debug(f"Images API validation: {result['valid_items']}/{result['total_items']} valid items")
            
        except Exception as e:
            result['error_type'] = 'validation_error'
            result['error_message'] = f'Validation process failed: {str(e)}'
            logger.error(f"Error validating Images API response: {e}")
        
        return result
    
    def _validate_collection_structure(self, response_data: Dict) -> Dict:
        """Valida la estructura Collection+JSON básica"""
        result = {
            'is_valid': False,
            'error_type': None,
            'error_message': None,
            'issues': [],
            'warnings': []
        }
        
        # Verificar campo 'collection'
        if 'collection' not in response_data:
            result['error_type'] = 'missing_collection'
            result['error_message'] = 'Missing required "collection" field'
            return result
        
        collection = response_data['collection']
        if not isinstance(collection, dict):
            result['error_type'] = 'invalid_collection'
            result['error_message'] = 'Collection field must be an object'
            return result
        
        # Verificar campos obligatorios de collection
        for field in self.required_collection_fields:
            if field not in collection:
                result['issues'].append(f'Missing required collection field: {field}')
        
        # Verificar estructura de items
        items = collection.get('items', [])
        if not isinstance(items, list):
            result['error_type'] = 'invalid_items'
            result['error_message'] = 'Items field must be an array'
            return result
        
        # Si llegamos aquí, la estructura básica es válida
        result['is_valid'] = True
        
        # Advertencias sobre campos recomendados
        if 'metadata' not in collection:
            result['warnings'].append('Missing metadata field (recommended)')
        
        if 'version' in collection:
            version = collection['version']
            if version != '1.0':
                result['warnings'].append(f'Unexpected collection version: {version}')
        
        return result
    
    def _validate_items(self, items: List[Dict]) -> Dict:
        """Valida los elementos individuales de la colección"""
        result = {
            'total_items': len(items),
            'valid_items': 0,
            'issues': [],
            'warnings': []
        }
        
        for i, item in enumerate(items):
            item_validation = self._validate_single_item(item, i)
            
            if item_validation['is_valid']:
                result['valid_items'] += 1
            
            # Agregar issues con índice para mejor debugging
            for issue in item_validation['issues']:
                result['issues'].append(f'Item {i}: {issue}')
            
            for warning in item_validation['warnings']:
                result['warnings'].append(f'Item {i}: {warning}')
        
        return result
    
    def _validate_single_item(self, item: Dict, index: int) -> Dict:
        """Valida un elemento individual de la colección"""
        result = {
            'is_valid': False,
            'issues': [],
            'warnings': []
        }
        
        # Verificar estructura básica del item
        for field in self.required_item_fields:
            if field not in item:
                result['issues'].append(f'Missing required field: {field}')
        
        if result['issues']:
            return result
        
        # Validar campo 'data'
        data_list = item.get('data', [])
        if not isinstance(data_list, list) or len(data_list) == 0:
            result['issues'].append('Data field must be a non-empty array')
            return result
        
        data = data_list[0]  # Primer elemento de data
        if not isinstance(data, dict):
            result['issues'].append('Data element must be an object')
            return result
        
        # Verificar campos obligatorios en data
        for field in self.required_data_fields:
            if field not in data:
                result['issues'].append(f'Missing required data field: {field}')
        
        if result['issues']:
            return result
        
        # Validar contenido de los campos
        nasa_id = data.get('nasa_id', '')
        if not nasa_id or not isinstance(nasa_id, str):
            result['issues'].append('Invalid or missing NASA ID')
        
        title = data.get('title', '')
        if not title or not isinstance(title, str) or len(title.strip()) == 0:
            result['issues'].append('Invalid or missing title')
        
        # Validar fecha
        date_created = data.get('date_created', '')
        if not self._is_valid_date_format(date_created):
            result['warnings'].append(f'Invalid date format: {date_created}')
        
        # Validar tipo de media
        media_type = data.get('media_type', '')
        if media_type and media_type not in self.valid_media_types:
            result['warnings'].append(f'Unknown media type: {media_type}')
        
        # Validar centro NASA
        center = data.get('center', '')
        if center and center not in self.valid_nasa_centers:
            result['warnings'].append(f'Unknown NASA center: {center}')
        
        # Validar campo 'links'
        links = item.get('links', [])
        if not isinstance(links, list):
            result['issues'].append('Links field must be an array')
        else:
            link_validation = self._validate_links(links)
            result['issues'].extend(link_validation['issues'])
            result['warnings'].extend(link_validation['warnings'])
        
        # Verificar campos recomendados
        missing_recommended = [field for field in self.recommended_fields 
                             if field not in data or not data[field]]
        if missing_recommended:
            result['warnings'].append(f'Missing recommended fields: {missing_recommended}')
        
        # Si no hay issues críticos, es válido
        result['is_valid'] = len(result['issues']) == 0
        
        return result
    
    def _validate_links(self, links: List[Dict]) -> Dict:
        """Valida los enlaces de un elemento"""
        result = {
            'issues': [],
            'warnings': []
        }
        
        if not links:
            result['warnings'].append('No links provided')
            return result
        
        has_preview = False
        valid_urls = 0
        
        for i, link in enumerate(links):
            if not isinstance(link, dict):
                result['issues'].append(f'Link {i} must be an object')
                continue
            
            href = link.get('href', '')
            rel = link.get('rel', '')
            
            if not href:
                result['issues'].append(f'Link {i} missing href')
                continue
            
            # Validar URL
            if self._is_valid_url(href):
                valid_urls += 1
                
                # Verificar si hay link de preview
                if rel == 'preview':
                    has_preview = True
                    
                    # Verificar extensión de imagen para preview
                    if not any(href.lower().endswith(ext) for ext in self.valid_image_extensions):
                        result['warnings'].append(f'Preview link may not be an image: {href}')
            else:
                result['warnings'].append(f'Invalid URL format: {href}')
        
        if not has_preview:
            result['warnings'].append('No preview link found')
        
        if valid_urls == 0:
            result['issues'].append('No valid URLs found in links')
        
        return result
    
    def _is_valid_url(self, url: str) -> bool:
        """Verifica si una URL tiene formato válido"""
        if not url or not isinstance(url, str):
            return False
        
        # Verificar patrones básicos
        for pattern in self.valid_url_patterns:
            if re.match(pattern, url):
                return True
        
        # Verificar con urlparse para URLs completas
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Verifica si una fecha tiene formato válido"""
        if not date_str or not isinstance(date_str, str):
            return False
        
        # Patrones de fecha comunes
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$',  # ISO format
            r'^\d{4}-\d{2}-\d{2}$',                       # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',                       # MM/DD/YYYY
            r'^\d{4}/\d{2}/\d{2}$'                        # YYYY/MM/DD
        ]
        
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    def _assess_response_quality(self, response_data: Dict, items_validation: Dict) -> Dict:
        """Evalúa la calidad general de la respuesta"""
        warnings = []
        
        total_items = items_validation['total_items']
        valid_items = items_validation['valid_items']
        
        # Calcular métricas de calidad
        if total_items == 0:
            completeness = 1.0  # Respuesta vacía pero válida
            validity_rate = 1.0
        else:
            completeness = 1.0  # Respuesta completa si no hay errores estructurales
            validity_rate = valid_items / total_items
        
        # Verificar metadatos
        collection = response_data.get('collection', {})
        metadata = collection.get('metadata', {})
        
        has_metadata = bool(metadata)
        has_pagination = 'total_hits' in metadata or 'page' in metadata
        
        # Calcular score de calidad
        quality_score = (
            validity_rate * 0.4 +        # 40% validez de items
            completeness * 0.3 +         # 30% completitud
            (1.0 if has_metadata else 0.5) * 0.2 +  # 20% metadatos
            (1.0 if has_pagination else 0.7) * 0.1  # 10% paginación
        )
        
        # Determinar calidad
        if quality_score >= 0.9:
            quality = 'excellent'
        elif quality_score >= 0.7:
            quality = 'good'
        elif quality_score >= 0.5:
            quality = 'fair'
        else:
            quality = 'poor'
        
        # Agregar advertencias basadas en métricas
        if validity_rate < 0.8:
            warnings.append(f'Low item validity rate: {validity_rate:.1%}')
        
        if not has_metadata:
            warnings.append('Missing collection metadata')
        
        if not has_pagination and total_items > 0:
            warnings.append('Missing pagination information')
        
        if total_items > 100:
            warnings.append('Large result set, consider pagination')
        
        return {'quality': quality, 'warnings': warnings}
    
    def validate_normalized_response(self, normalized_data: Dict) -> Dict:
        """
        Valida una respuesta normalizada del servicio de imágenes
        
        Args:
            normalized_data: Datos normalizados con estructura simplificada
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'is_valid': False,
            'issues': [],
            'warnings': [],
            'valid_items': 0,
            'total_items': 0
        }
        
        # Verificar estructura normalizada
        if 'items' not in normalized_data:
            result['issues'].append('Missing items field in normalized data')
            return result
        
        items = normalized_data['items']
        if not isinstance(items, list):
            result['issues'].append('Items field must be an array')
            return result
        
        result['total_items'] = len(items)
        
        # Validar cada item normalizado
        required_normalized_fields = ['title', 'nasa_id']
        recommended_normalized_fields = ['description', 'thumbnail_url', 'keywords']
        
        for i, item in enumerate(items):
            item_issues = []
            item_warnings = []
            
            # Verificar campos obligatorios
            for field in required_normalized_fields:
                if field not in item or not item[field]:
                    item_issues.append(f'Missing required field: {field}')
            
            # Verificar campos recomendados
            missing_recommended = [field for field in recommended_normalized_fields
                                 if field not in item or not item[field]]
            if missing_recommended:
                item_warnings.append(f'Missing recommended fields: {missing_recommended}')
            
            # Validar URL de thumbnail si existe
            thumbnail_url = item.get('thumbnail_url')
            if thumbnail_url and not self._is_valid_url(thumbnail_url):
                item_warnings.append(f'Invalid thumbnail URL: {thumbnail_url}')
            
            # Si no hay issues críticos, contar como válido
            if not item_issues:
                result['valid_items'] += 1
            else:
                for issue in item_issues:
                    result['issues'].append(f'Item {i}: {issue}')
            
            for warning in item_warnings:
                result['warnings'].append(f'Item {i}: {warning}')
        
        # Verificar metadatos opcionales
        optional_metadata = ['total_hits', 'page', 'total_pages']
        missing_metadata = [field for field in optional_metadata
                          if field not in normalized_data]
        if missing_metadata:
            result['warnings'].append(f'Missing metadata fields: {missing_metadata}')
        
        result['is_valid'] = len(result['issues']) == 0
        
        return result


def validate_images_response(response_data: Union[Dict, str]) -> Dict:
    """
    Función de conveniencia para validar respuesta de Images API
    
    Args:
        response_data: Respuesta de la API de imágenes de NASA
        
    Returns:
        Dict con resultado de validación
    """
    validator = ImagesValidator()
    return validator.validate_images_response(response_data)


def validate_normalized_response(normalized_data: Dict) -> Dict:
    """
    Función de conveniencia para validar respuesta normalizada
    
    Args:
        normalized_data: Datos normalizados del servicio de imágenes
        
    Returns:
        Dict con resultado de validación
    """
    validator = ImagesValidator()
    return validator.validate_normalized_response(normalized_data)


if __name__ == "__main__":
    # Ejemplo de uso
    validator = ImagesValidator()
    
    # Simular respuesta exitosa
    good_response = {
        "collection": {
            "version": "1.0",
            "href": "https://images-api.nasa.gov/search?q=earth",
            "items": [
                {
                    "data": [
                        {
                            "title": "Earth from Space",
                            "nasa_id": "PIA12345",
                            "date_created": "2024-01-01T10:00:00Z",
                            "media_type": "image",
                            "center": "NASA",
                            "description": "Beautiful view of Earth from the International Space Station"
                        }
                    ],
                    "links": [
                        {
                            "href": "https://images-assets.nasa.gov/image/PIA12345/PIA12345~thumb.jpg",
                            "rel": "preview"
                        }
                    ]
                }
            ],
            "metadata": {
                "total_hits": 1234
            }
        }
    }
    
    print("Testing good response:")
    result = validator.validate_images_response(good_response)
    print(f"Valid: {result['is_valid']}")
    print(f"Valid items: {result['valid_items']}/{result['total_items']}")
    print(f"Quality: {result['data_quality']}")
    print(f"Issues: {result['issues']}")
    print(f"Warnings: {result['warnings']}")