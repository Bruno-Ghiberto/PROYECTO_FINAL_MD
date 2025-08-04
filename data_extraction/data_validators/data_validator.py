"""
Módulo de validación y normalización de datos astronómicos
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Clase para validar y normalizar datos astronómicos de múltiples fuentes
    """
    
    def __init__(self):
        """Inicializa el validador con rangos esperados para diferentes parámetros"""
        
        # Rangos válidos para diferentes parámetros (min, max)
        self.valid_ranges = {
            # Masas en kg
            'mass_kg': (1e16, 2e30),  # Desde asteroides pequeños hasta el Sol
            
            # Radios en km
            'radius_km': (0.1, 700000),  # Desde asteroides hasta el Sol
            'mean_radius_km': (0.1, 700000),
            
            # Densidades en kg/m³
            'density_kg_m3': (100, 150000),  # Desde cometas hasta núcleos planetarios
            'mean_density_kg_m3': (100, 150000),
            
            # Gravedad en m/s²
            'gravity_m_s2': (0.001, 300),  # Desde asteroides hasta el Sol
            'surface_gravity_m_s2': (0.001, 300),
            
            # Distancias en km
            'distance_from_sun_km': (1e6, 1e11),  # Desde cerca del Sol hasta Plutón
            'perihelion_km': (1e6, 1e11),
            'aphelion_km': (1e6, 1e11),
            
            # Períodos orbitales en días
            'orbital_period_days': (0.1, 1e6),  # Desde satélites hasta cometas largos
            
            # Velocidades en km/s
            'escape_velocity_km_s': (0.001, 700),  # Desde asteroides hasta el Sol
            'orbital_velocity_km_s': (0.1, 100),
            
            # Temperaturas en Kelvin
            'temperature_k': (10, 6000),  # Desde Plutón hasta superficie solar
            'mean_temperature_c': (-273, 500),  # En Celsius
            
            # Magnitudes
            'absolute_magnitude_h': (-30, 40),  # Desde el Sol hasta asteroides débiles
            'magnitude_v0': (-30, 30),
            
            # Albedos
            'albedo': (0.01, 1.0),
            'geometric_albedo': (0.01, 1.0),
            
            # Excentricidades
            'eccentricity': (0.0, 0.999),  # Casi circular hasta muy elíptica
            'orbital_eccentricity': (0.0, 0.999),
            
            # Inclinaciones en grados
            'inclination_degrees': (0.0, 180.0),
            'orbital_inclination_degrees': (0.0, 180.0)
        }
        
        # Mapeo de nombres alternativos a nombres estándar
        self.name_mapping = {
            # Planetas
            'earth': 'Earth',
            'terre': 'Earth',
            'tierra': 'Earth',
            'jupiter': 'Jupiter',
            'jup': 'Jupiter',
            'saturn': 'Saturn',
            'sat': 'Saturn',
            'mars': 'Mars',
            'mercury': 'Mercury',
            'merc': 'Mercury',
            'venus': 'Venus',
            'ven': 'Venus',
            'uranus': 'Uranus',
            'neptune': 'Neptune',
            'nep': 'Neptune',
            'pluto': 'Pluto',
            
            # Lunas
            'moon': 'Moon',
            'luna': 'Moon',
            'io': 'Io',
            'europa': 'Europa',
            'ganymede': 'Ganymede',
            'callisto': 'Callisto',
            'titan': 'Titan',
            'enceladus': 'Enceladus',
            'triton': 'Triton'
        }
        
        # Unidades de conversión
        self.unit_conversions = {
            # Masa
            'mass_1024kg': 1e24,
            'mass_1023kg': 1e23,
            'mass_1022kg': 1e22,
            'mass_1021kg': 1e21,
            'mass_1020kg': 1e20,
            'mass_1016kg': 1e16,
            
            # Distancia
            'distance_106km': 1e6,
            'distance_1000km': 1e3,
            'distance_au': 1.496e8,  # AU a km
            
            # Volumen
            'volume_1010km3': 1e10,
            
            # GM
            'gm_106km3_s2': 1e6,
            'gm_million_km3_s2': 1e6
        }
    
    def validate_dataframe(self, df: pd.DataFrame, data_type: str = 'general') -> Tuple[pd.DataFrame, Dict]:
        """
        Valida y limpia un DataFrame completo
        
        Args:
            df: DataFrame a validar
            data_type: Tipo de datos ('planets', 'moons', 'asteroids', 'comets', 'neos', 'general')
            
        Returns:
            Tupla de (DataFrame validado, diccionario de estadísticas de validación)
        """
        if df.empty:
            return df, {'status': 'empty', 'records': 0}
        
        df_clean = df.copy()
        stats = {
            'original_records': len(df),
            'original_columns': len(df.columns),
            'issues_found': [],
            'records_removed': 0,
            'values_corrected': 0,
            'null_values_found': 0
        }
        
        # 1. Validar y limpiar nombres
        if 'name' in df_clean.columns:
            df_clean['name'] = df_clean['name'].apply(self._standardize_name)
        
        # 2. Detectar y remover duplicados
        if 'name' in df_clean.columns:
            duplicates = df_clean.duplicated(subset=['name'], keep='first')
            if duplicates.any():
                stats['issues_found'].append(f"Duplicados encontrados: {duplicates.sum()}")
                stats['records_removed'] += duplicates.sum()
                df_clean = df_clean[~duplicates]
        
        # 3. Validar rangos numéricos
        for col in df_clean.columns:
            if col in self.valid_ranges and pd.api.types.is_numeric_dtype(df_clean[col]):
                min_val, max_val = self.valid_ranges[col]
                
                # Detectar valores fuera de rango
                out_of_range = (df_clean[col] < min_val) | (df_clean[col] > max_val)
                if out_of_range.any():
                    count = out_of_range.sum()
                    stats['issues_found'].append(
                        f"Valores fuera de rango en {col}: {count} registros"
                    )
                    # Marcar como NaN los valores fuera de rango
                    df_clean.loc[out_of_range, col] = np.nan
                    stats['values_corrected'] += count
        
        # 4. Detectar valores nulos
        null_counts = df_clean.isnull().sum()
        total_nulls = null_counts.sum()
        if total_nulls > 0:
            stats['null_values_found'] = total_nulls
            stats['null_distribution'] = null_counts[null_counts > 0].to_dict()
        
        # 5. Validaciones específicas por tipo de datos
        if data_type == 'planets':
            df_clean = self._validate_planets(df_clean, stats)
        elif data_type == 'moons':
            df_clean = self._validate_moons(df_clean, stats)
        elif data_type == 'asteroids':
            df_clean = self._validate_asteroids(df_clean, stats)
        elif data_type == 'neos':
            df_clean = self._validate_neos(df_clean, stats)
        
        # 6. Remover registros con demasiados valores faltantes
        null_threshold = 0.5  # Más del 50% de valores nulos
        null_percentage = df_clean.isnull().sum(axis=1) / len(df_clean.columns)
        too_many_nulls = null_percentage > null_threshold
        if too_many_nulls.any():
            stats['records_removed'] += too_many_nulls.sum()
            stats['issues_found'].append(
                f"Registros con >50% valores nulos: {too_many_nulls.sum()}"
            )
            df_clean = df_clean[~too_many_nulls]
        
        stats['final_records'] = len(df_clean)
        stats['final_columns'] = len(df_clean.columns)
        stats['validation_complete'] = True
        
        return df_clean, stats
    
    def normalize_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza todas las unidades a estándares SI
        
        Args:
            df: DataFrame con datos a normalizar
            
        Returns:
            DataFrame con unidades normalizadas
        """
        df_norm = df.copy()
        
        # Convertir masas a kg
        for col, factor in self.unit_conversions.items():
            if col.startswith('mass_') and col in df_norm.columns:
                target_col = 'mass_kg'
                if target_col not in df_norm.columns:
                    df_norm[target_col] = pd.to_numeric(df_norm[col], errors='coerce') * factor
                    logger.info(f"Convertido {col} a {target_col}")
        
        # Convertir distancias
        distance_conversions = {
            'distance_106km': ('distance_km', 1e6),
            'distance_1000km': ('distance_km', 1e3),
            'perihelion_106km': ('perihelion_km', 1e6),
            'aphelion_106km': ('aphelion_km', 1e6),
            'mean_distance_from_jupiter_1000km': ('mean_distance_from_jupiter_km', 1e3),
            'mean_distance_from_jupiter_million_km': ('mean_distance_from_jupiter_km', 1e6)
        }
        
        for source_col, (target_col, factor) in distance_conversions.items():
            if source_col in df_norm.columns and target_col not in df_norm.columns:
                df_norm[target_col] = pd.to_numeric(df_norm[source_col], errors='coerce') * factor
                logger.info(f"Convertido {source_col} a {target_col}")
        
        # Convertir densidades g/cm³ a kg/m³
        if 'mean_density_g_cm3' in df_norm.columns:
            df_norm['mean_density_kg_m3'] = pd.to_numeric(
                df_norm['mean_density_g_cm3'], errors='coerce'
            ) * 1000
        
        # Convertir temperaturas Celsius a Kelvin
        if 'mean_temperature_c' in df_norm.columns and 'mean_temperature_k' not in df_norm.columns:
            df_norm['mean_temperature_k'] = pd.to_numeric(
                df_norm['mean_temperature_c'], errors='coerce'
            ) + 273.15
        
        # Convertir AU a km
        if 'semimajorAxis' in df_norm.columns:
            # Verificar si está en AU (valores típicamente < 100)
            if df_norm['semimajorAxis'].max() < 100:
                df_norm['semimajorAxis_km'] = df_norm['semimajorAxis'] * self.unit_conversions['distance_au']
        
        return df_norm
    
    def merge_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fusiona columnas que representan el mismo dato con diferentes nombres
        
        Args:
            df: DataFrame con posibles columnas duplicadas
            
        Returns:
            DataFrame con columnas fusionadas
        """
        df_merged = df.copy()
        
        # Definir grupos de columnas equivalentes
        column_groups = [
            ['radius_km', 'mean_radius_km', 'meanRadius'],
            ['density_kg_m3', 'mean_density_kg_m3', 'density'],
            ['gravity_m_s2', 'surface_gravity_m_s2', 'gravity'],
            ['orbital_period_days', 'orbit_period_days', 'sideralOrbit'],
            ['rotation_period_days', 'rotational_period_days', 'sideralRotation'],
            ['escape_velocity_km_s', 'escape'],
            ['temperature_k', 'mean_temperature_k', 'avgTemp'],
            ['albedo', 'geometric_albedo'],
            ['eccentricity', 'orbital_eccentricity'],
            ['inclination_degrees', 'orbital_inclination_degrees', 'inclination']
        ]
        
        for group in column_groups:
            # Encontrar columnas presentes
            present_cols = [col for col in group if col in df_merged.columns]
            
            if len(present_cols) > 1:
                # Usar la primera columna como destino
                target_col = present_cols[0]
                
                # Fusionar valores (priorizar no-nulos)
                for col in present_cols[1:]:
                    # Llenar valores faltantes en target con valores de col
                    mask = df_merged[target_col].isna() & df_merged[col].notna()
                    df_merged.loc[mask, target_col] = df_merged.loc[mask, col]
                    
                    # Eliminar columna fusionada
                    df_merged = df_merged.drop(columns=[col])
                    logger.info(f"Fusionado {col} en {target_col}")
        
        return df_merged
    
    def _standardize_name(self, name: str) -> str:
        """
        Estandariza nombres de cuerpos celestes
        
        Args:
            name: Nombre a estandarizar
            
        Returns:
            Nombre estandarizado
        """
        if pd.isna(name):
            return name
        
        # Convertir a string y limpiar
        name_str = str(name).strip()
        
        # Buscar en mapeo
        name_lower = name_str.lower()
        if name_lower in self.name_mapping:
            return self.name_mapping[name_lower]
        
        # Capitalizar primera letra si no está en mapeo
        return name_str.capitalize()
    
    def _validate_planets(self, df: pd.DataFrame, stats: Dict) -> pd.DataFrame:
        """
        Validaciones específicas para planetas
        
        Args:
            df: DataFrame de planetas
            stats: Diccionario de estadísticas
            
        Returns:
            DataFrame validado
        """
        # Verificar que todos los planetas conocidos estén presentes
        known_planets = [
            'Mercury', 'Venus', 'Earth', 'Mars', 
            'Jupiter', 'Saturn', 'Uranus', 'Neptune'
        ]
        
        if 'name' in df.columns:
            missing_planets = set(known_planets) - set(df['name'].values)
            if missing_planets:
                stats['issues_found'].append(f"Planetas faltantes: {missing_planets}")
        
        # Verificar orden por distancia al Sol
        if 'semimajorAxis' in df.columns or 'distance_from_sun_km' in df.columns:
            distance_col = 'semimajorAxis' if 'semimajorAxis' in df.columns else 'distance_from_sun_km'
            df = df.sort_values(distance_col)
        
        return df
    
    def _validate_moons(self, df: pd.DataFrame, stats: Dict) -> pd.DataFrame:
        """
        Validaciones específicas para lunas
        
        Args:
            df: DataFrame de lunas
            stats: Diccionario de estadísticas
            
        Returns:
            DataFrame validado
        """
        # Verificar que tengan planeta padre
        if 'planet' not in df.columns and 'planet_name' not in df.columns:
            stats['issues_found'].append("Lunas sin planeta padre identificado")
        
        # Verificar distancia al planeta
        distance_cols = ['mean_distance_from_jupiter_km', 'mean_distance_from_earth_km']
        has_distance = any(col in df.columns for col in distance_cols)
        if not has_distance:
            stats['issues_found'].append("Lunas sin distancia al planeta padre")
        
        return df
    
    def _validate_asteroids(self, df: pd.DataFrame, stats: Dict) -> pd.DataFrame:
        """
        Validaciones específicas para asteroides
        
        Args:
            df: DataFrame de asteroides
            stats: Diccionario de estadísticas
            
        Returns:
            DataFrame validado
        """
        # Verificar clasificación
        if 'class' in df.columns:
            valid_classes = ['MBA', 'NEO', 'TNO', 'CEN', 'TJN', 'AMO', 'APO', 'ATE']
            invalid_classes = df[~df['class'].isin(valid_classes)]['class'].unique()
            if len(invalid_classes) > 0:
                stats['issues_found'].append(f"Clases de asteroides no reconocidas: {invalid_classes}")
        
        return df
    
    def _validate_neos(self, df: pd.DataFrame, stats: Dict) -> pd.DataFrame:
        """
        Validaciones específicas para NEOs
        
        Args:
            df: DataFrame de NEOs
            stats: Diccionario de estadísticas
            
        Returns:
            DataFrame validado
        """
        # Verificar campos críticos de NEO
        critical_fields = ['miss_distance_km', 'relative_velocity_kps', 'is_potentially_hazardous']
        missing_fields = [field for field in critical_fields if field not in df.columns]
        
        if missing_fields:
            stats['issues_found'].append(f"Campos NEO faltantes: {missing_fields}")
        
        # Verificar aproximaciones futuras vs pasadas
        if 'approach_date' in df.columns:
            df['approach_date'] = pd.to_datetime(df['approach_date'], errors='coerce')
            future_approaches = df['approach_date'] > datetime.now()
            stats['future_approaches'] = future_approaches.sum()
            stats['past_approaches'] = (~future_approaches).sum()
        
        return df
    
    def generate_validation_report(self, validation_results: List[Tuple[str, Dict]]) -> str:
        """
        Genera un reporte de validación consolidado
        
        Args:
            validation_results: Lista de tuplas (nombre_dataset, estadísticas)
            
        Returns:
            Reporte en formato string
        """
        report = ["=" * 60]
        report.append("REPORTE DE VALIDACIÓN DE DATOS")
        report.append("=" * 60)
        report.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_issues = 0
        total_records = 0
        
        for dataset_name, stats in validation_results:
            report.append(f"\n{dataset_name.upper()}")
            report.append("-" * len(dataset_name))
            
            if stats.get('status') == 'empty':
                report.append("Dataset vacío - no hay datos para validar")
                continue
            
            report.append(f"Registros originales: {stats.get('original_records', 0)}")
            report.append(f"Registros finales: {stats.get('final_records', 0)}")
            report.append(f"Registros removidos: {stats.get('records_removed', 0)}")
            report.append(f"Valores corregidos: {stats.get('values_corrected', 0)}")
            report.append(f"Valores nulos encontrados: {stats.get('null_values_found', 0)}")
            
            if stats.get('issues_found'):
                report.append("\nProblemas encontrados:")
                for issue in stats['issues_found']:
                    report.append(f"  - {issue}")
                    total_issues += 1
            
            if stats.get('null_distribution'):
                report.append("\nDistribución de valores nulos:")
                for col, count in stats['null_distribution'].items():
                    report.append(f"  - {col}: {count}")
            
            total_records += stats.get('final_records', 0)
        
        report.append("\n" + "=" * 60)
        report.append("RESUMEN")
        report.append("=" * 60)
        report.append(f"Total de datasets procesados: {len(validation_results)}")
        report.append(f"Total de registros finales: {total_records}")
        report.append(f"Total de problemas encontrados: {total_issues}")
        report.append("=" * 60)
        
        return "\n".join(report)


# Funciones de utilidad
def create_validator() -> DataValidator:
    """
    Factory function para crear un validador de datos
    
    Returns:
        Instancia de DataValidator
    """
    return DataValidator()


def validate_and_normalize_dataset(
    df: pd.DataFrame, 
    dataset_name: str, 
    data_type: str = 'general'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Función completa para validar y normalizar un dataset
    
    Args:
        df: DataFrame a procesar
        dataset_name: Nombre del dataset para logging
        data_type: Tipo de datos
        
    Returns:
        Tupla de (DataFrame procesado, estadísticas)
    """
    validator = create_validator()
    
    logger.info(f"Iniciando validación de {dataset_name}")
    
    # 1. Normalizar unidades
    df_normalized = validator.normalize_units(df)
    
    # 2. Fusionar columnas duplicadas
    df_merged = validator.merge_duplicate_columns(df_normalized)
    
    # 3. Validar y limpiar
    df_clean, stats = validator.validate_dataframe(df_merged, data_type)
    
    logger.info(f"Validación de {dataset_name} completada")
    
    return df_clean, stats


if __name__ == "__main__":
    # Ejemplo de uso
    import pandas as pd
    
    # Crear datos de ejemplo
    sample_data = pd.DataFrame({
        'name': ['Earth', 'mars', 'jupiter', 'Unknown'],
        'mass_1024kg': [5.97, 0.642, 1898, -999],  # Valor inválido
        'radius_km': [6371, 3389, 69911, 0.001],  # Valor fuera de rango
        'density_g_cm3': [5.51, 3.93, 1.33, None],
        'temperature_c': [15, -65, -110, 1000]  # Valor fuera de rango
    })
    
    # Validar y normalizar
    df_clean, stats = validate_and_normalize_dataset(
        sample_data, 
        'Planetas de ejemplo',
        'planets'
    )
    
    print("\nDatos originales:")
    print(sample_data)
    print("\nDatos validados y normalizados:")
    print(df_clean)
    print("\nEstadísticas de validación:")
    for key, value in stats.items():
        print(f"{key}: {value}")