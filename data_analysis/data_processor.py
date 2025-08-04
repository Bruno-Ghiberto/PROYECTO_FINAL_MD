"""
Procesador principal de datos del Sistema Solar
Aplica técnicas de minería de datos según la consigna del proyecto
"""
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SolarSystemDataProcessor:
    """
    Clase principal para procesar y analizar datos del Sistema Solar
    Implementa al menos 2 técnicas de minería de datos según consigna
    """
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        Inicializa el procesador de datos
        
        Args:
            data_dir: Directorio con datos integrados
        """
        self.data_dir = data_dir
        self.results_dir = os.path.join(os.path.dirname(data_dir), "results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Cargar datos integrados
        self.datasets = self._load_integrated_datasets()
        
        # Almacenar resultados de análisis
        self.analysis_results = {}
    
    def _load_integrated_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Carga todos los datasets integrados disponibles
        
        Returns:
            Diccionario con DataFrames cargados
        """
        datasets = {}
        
        if not os.path.exists(self.data_dir):
            logger.warning(f"Directorio de datos no encontrado: {self.data_dir}")
            return datasets
        
        # Buscar archivos CSV integrados
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_integrated.csv'):
                dataset_name = filename.replace('_integrated.csv', '')
                filepath = os.path.join(self.data_dir, filename)
                
                try:
                    df = pd.read_csv(filepath)
                    datasets[dataset_name] = df
                    logger.info(f"Cargado dataset {dataset_name}: {len(df)} registros")
                except Exception as e:
                    logger.error(f"Error cargando {filename}: {e}")
        
        return datasets
    
    def clean_and_prepare_data(self) -> Dict[str, pd.DataFrame]:
        """
        Limpia y prepara los datos para análisis
        
        Returns:
            Diccionario con datasets limpios
        """
        logger.info("Iniciando limpieza y preparación de datos...")
        clean_datasets = {}
        
        for name, df in self.datasets.items():
            logger.info(f"Procesando dataset {name}...")
            
            # Hacer una copia para no modificar el original
            clean_df = df.copy()
            
            # Limpieza general
            clean_df = self._clean_basic_data(clean_df)
            
            # Limpieza específica por tipo
            if name == 'planets':
                clean_df = self._clean_planet_data(clean_df)
            elif name == 'moons':
                clean_df = self._clean_moon_data(clean_df)
            elif name == 'asteroids':
                clean_df = self._clean_asteroid_data(clean_df)
            elif name == 'comets':
                clean_df = self._clean_comet_data(clean_df)
            elif name == 'neos':
                clean_df = self._clean_neo_data(clean_df)
            
            clean_datasets[name] = clean_df
            logger.info(f"Dataset {name} limpio: {len(clean_df)} registros")
        
        return clean_datasets
    
    def _clean_basic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica limpieza básica común a todos los datasets
        """
        # Eliminar duplicados
        df = df.drop_duplicates()
        
        # Convertir columnas numéricas
        numeric_columns = df.select_dtypes(include=[object]).columns
        for col in numeric_columns:
            if col not in ['name', 'englishName', 'data_source', 'last_updated']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        return df
    
    def _clean_planet_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpieza específica para datos de planetas
        """
        # Estandarizar nombres
        if 'englishName' in df.columns and 'name' not in df.columns:
            df['name'] = df['englishName']
        
        # Convertir masas a kg si están en otras unidades
        if 'mass_kg' in df.columns:
            df['mass_kg'] = pd.to_numeric(df['mass_kg'], errors='coerce')
        
        # Calcular densidad si no existe
        if 'density_g_cm3' not in df.columns and 'mass_kg' in df.columns and 'volume_km3' in df.columns:
            # Convertir volumen de km³ a m³ y masa a g
            volume_m3 = df['volume_km3'] * 1e9  # km³ to m³
            mass_g = df['mass_kg'] * 1000  # kg to g
            df['density_g_cm3'] = mass_g / (volume_m3 * 1e-6)  # g/cm³
        
        return df
    
    def _clean_moon_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpieza específica para datos de lunas
        """
        # Asegurar que existe columna de planeta
        if 'aroundPlanet' in df.columns and 'planet' not in df.columns:
            df['planet'] = df['aroundPlanet'].apply(lambda x: x.get('englishName') if isinstance(x, dict) else x)
        
        return df
    
    def _clean_asteroid_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpieza específica para datos de asteroides
        """
        # Convertir parámetros orbitales
        orbital_params = ['a', 'e', 'i', 'q', 'ad', 'per']
        for param in orbital_params:
            if param in df.columns:
                df[param] = pd.to_numeric(df[param], errors='coerce')
        
        return df
    
    def _clean_comet_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpieza específica para datos de cometas
        """
        # Similar a asteroides
        return self._clean_asteroid_data(df)
    
    def _clean_neo_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpieza específica para datos de NEOs
        """
        # Convertir fechas
        date_columns = ['close_approach_date', 'discovery_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    # TÉCNICA 1: ANÁLISIS DESCRIPTIVO Y COMPARATIVO
    def perform_descriptive_analysis(self, clean_datasets: Dict[str, pd.DataFrame]) -> Dict:
        """
        Realiza análisis descriptivo y comparativo de los datos
        (Primera técnica de minería de datos requerida)
        """
        logger.info("Ejecutando análisis descriptivo y comparativo...")
        results = {}
        
        # Análisis de planetas
        if 'planets' in clean_datasets:
            results['planets'] = self._analyze_planets(clean_datasets['planets'])
        
        # Análisis de lunas
        if 'moons' in clean_datasets:
            results['moons'] = self._analyze_moons(clean_datasets['moons'])
        
        # Análisis de cuerpos pequeños
        small_bodies = ['asteroids', 'comets', 'neos']
        for body_type in small_bodies:
            if body_type in clean_datasets:
                results[body_type] = self._analyze_small_bodies(clean_datasets[body_type], body_type)
        
        # Análisis comparativo entre tipos
        results['comparative'] = self._comparative_analysis(clean_datasets)
        
        self.analysis_results['descriptive'] = results
        return results
    
    def _analyze_planets(self, df: pd.DataFrame) -> Dict:
        """
        Análisis descriptivo específico para planetas
        """
        analysis = {
            'count': len(df),
            'statistics': {},
            'distributions': {},
            'correlations': {}
        }
        
        # Estadísticas básicas para parámetros físicos
        numeric_cols = ['mass_kg', 'radius_km', 'density_g_cm3', 'gravity_m_s2', 
                       'escape_velocity_km_s', 'rotation_period_hours']
        
        for col in numeric_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['statistics'][col] = {
                        'mean': float(col_data.mean()),
                        'median': float(col_data.median()),
                        'std': float(col_data.std()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'range': float(col_data.max() - col_data.min())
                    }
        
        # Correlaciones entre parámetros físicos
        numeric_df = df[numeric_cols].select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            correlations = numeric_df.corr()
            analysis['correlations'] = correlations.to_dict()
        
        return analysis
    
    def _analyze_moons(self, df: pd.DataFrame) -> Dict:
        """
        Análisis descriptivo específico para lunas
        """
        analysis = {
            'count': len(df),
            'by_planet': {},
            'statistics': {}
        }
        
        # Distribución por planeta
        if 'planet' in df.columns:
            planet_counts = df['planet'].value_counts()
            analysis['by_planet'] = planet_counts.to_dict()
        
        # Estadísticas de características físicas
        numeric_cols = ['mass_kg', 'radius_km', 'density_g_cm3']
        for col in numeric_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['statistics'][col] = {
                        'mean': float(col_data.mean()),
                        'median': float(col_data.median()),
                        'std': float(col_data.std())
                    }
        
        return analysis
    
    def _analyze_small_bodies(self, df: pd.DataFrame, body_type: str) -> Dict:
        """
        Análisis descriptivo para cuerpos pequeños
        """
        analysis = {
            'count': len(df),
            'type': body_type,
            'orbital_stats': {},
            'physical_stats': {}
        }
        
        # Parámetros orbitales
        orbital_cols = ['a', 'e', 'i', 'q', 'ad', 'per']
        for col in orbital_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['orbital_stats'][col] = {
                        'mean': float(col_data.mean()),
                        'std': float(col_data.std()),
                        'range': [float(col_data.min()), float(col_data.max())]
                    }
        
        # Parámetros físicos
        physical_cols = ['diameter', 'H', 'albedo', 'rot_per']
        for col in physical_cols:
            if col in df.columns:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    analysis['physical_stats'][col] = {
                        'mean': float(col_data.mean()),
                        'median': float(col_data.median()),
                        'std': float(col_data.std())
                    }
        
        return analysis
    
    def _comparative_analysis(self, datasets: Dict[str, pd.DataFrame]) -> Dict:
        """
        Análisis comparativo entre diferentes tipos de cuerpos
        """
        comparative = {
            'size_comparison': {},
            'mass_comparison': {},
            'density_comparison': {}
        }
        
        # Comparación de tamaños (radios/diámetros)
        for name, df in datasets.items():
            size_data = None
            if 'radius_km' in df.columns:
                size_data = df['radius_km'].dropna()
            elif 'diameter' in df.columns:
                size_data = df['diameter'].dropna() / 2  # convertir a radio
            
            if size_data is not None and len(size_data) > 0:
                comparative['size_comparison'][name] = {
                    'mean_radius_km': float(size_data.mean()),
                    'max_radius_km': float(size_data.max()),
                    'min_radius_km': float(size_data.min())
                }
        
        # Comparación de masas
        for name, df in datasets.items():
            if 'mass_kg' in df.columns:
                mass_data = df['mass_kg'].dropna()
                if len(mass_data) > 0:
                    comparative['mass_comparison'][name] = {
                        'mean_mass_kg': float(mass_data.mean()),
                        'total_mass_kg': float(mass_data.sum()),
                        'count': len(mass_data)
                    }
        
        return comparative
    
    # TÉCNICA 2: CLUSTERING Y CLASIFICACIÓN
    def perform_clustering_analysis(self, clean_datasets: Dict[str, pd.DataFrame]) -> Dict:
        """
        Realiza análisis de clustering para identificar grupos naturales
        (Segunda técnica de minería de datos requerida)
        """
        logger.info("Ejecutando análisis de clustering...")
        results = {}
        
        # Clustering de asteroides por parámetros orbitales
        if 'asteroids' in clean_datasets:
            results['asteroid_clusters'] = self._cluster_asteroids(clean_datasets['asteroids'])
        
        # Clustering de cometas
        if 'comets' in clean_datasets:
            results['comet_clusters'] = self._cluster_comets(clean_datasets['comets'])
        
        # Clustering de lunas por características físicas
        if 'moons' in clean_datasets:
            results['moon_clusters'] = self._cluster_moons(clean_datasets['moons'])
        
        self.analysis_results['clustering'] = results
        return results
    
    def _cluster_asteroids(self, df: pd.DataFrame) -> Dict:
        """
        Clustering de asteroides basado en parámetros orbitales
        Usa K-means simple implementado manualmente
        """
        # Seleccionar características para clustering
        features = ['a', 'e', 'i']  # semieje mayor, excentricidad, inclinación
        
        # Filtrar datos válidos
        clustering_data = df[features].dropna()
        
        if len(clustering_data) < 3:
            return {'error': 'Datos insuficientes para clustering'}
        
        # Normalizar datos (z-score)
        normalized_data = (clustering_data - clustering_data.mean()) / clustering_data.std()
        
        # Implementar K-means simple
        k = 3  # Número de clusters
        clusters = self._simple_kmeans(normalized_data.values, k)
        
        # Asignar clusters al DataFrame
        clustering_data['cluster'] = clusters
        
        # Analizar clusters
        cluster_analysis = {}
        for cluster_id in range(k):
            cluster_mask = clusters == cluster_id
            if np.any(cluster_mask):
                cluster_data = clustering_data[cluster_mask]
                cluster_analysis[f'cluster_{cluster_id}'] = {
                    'count': len(cluster_data),
                    'centroid': {
                        'a': float(cluster_data['a'].mean()),
                        'e': float(cluster_data['e'].mean()),
                        'i': float(cluster_data['i'].mean())
                    },
                    'characteristics': self._describe_asteroid_cluster(cluster_data)
                }
        
        return {
            'n_clusters': k,
            'total_objects': len(clustering_data),
            'features_used': features,
            'clusters': cluster_analysis
        }
    
    def _cluster_comets(self, df: pd.DataFrame) -> Dict:
        """
        Clustering de cometas basado en características orbitales
        """
        features = ['a', 'e', 'q']  # semieje mayor, excentricidad, perihelio
        
        clustering_data = df[features].dropna()
        
        if len(clustering_data) < 3:
            return {'error': 'Datos insuficientes para clustering'}
        
        # Normalizar
        normalized_data = (clustering_data - clustering_data.mean()) / clustering_data.std()
        
        # K-means con k=2 (cometas de periodo corto vs largo)
        k = 2
        clusters = self._simple_kmeans(normalized_data.values, k)
        
        clustering_data['cluster'] = clusters
        
        cluster_analysis = {}
        for cluster_id in range(k):
            cluster_mask = clusters == cluster_id
            if np.any(cluster_mask):
                cluster_data = clustering_data[cluster_mask]
                cluster_analysis[f'cluster_{cluster_id}'] = {
                    'count': len(cluster_data),
                    'centroid': {
                        'a': float(cluster_data['a'].mean()),
                        'e': float(cluster_data['e'].mean()),
                        'q': float(cluster_data['q'].mean())
                    }
                }
        
        return {
            'n_clusters': k,
            'total_objects': len(clustering_data),
            'clusters': cluster_analysis
        }
    
    def _cluster_moons(self, df: pd.DataFrame) -> Dict:
        """
        Clustering de lunas basado en características físicas
        """
        features = ['mass_kg', 'radius_km']
        
        clustering_data = df[features].dropna()
        
        if len(clustering_data) < 3:
            return {'error': 'Datos insuficientes para clustering'}
        
        # Log-transform para manejar rangos amplios
        log_data = np.log10(clustering_data + 1e-10)  # evitar log(0)
        
        # Normalizar
        normalized_data = (log_data - log_data.mean()) / log_data.std()
        
        k = 3
        clusters = self._simple_kmeans(normalized_data.values, k)
        
        clustering_data['cluster'] = clusters
        
        cluster_analysis = {}
        for cluster_id in range(k):
            cluster_mask = clusters == cluster_id
            if np.any(cluster_mask):
                cluster_data = clustering_data[cluster_mask]
                cluster_analysis[f'cluster_{cluster_id}'] = {
                    'count': len(cluster_data),
                    'avg_mass_kg': float(cluster_data['mass_kg'].mean()),
                    'avg_radius_km': float(cluster_data['radius_km'].mean())
                }
        
        return {
            'n_clusters': k,
            'total_objects': len(clustering_data),
            'clusters': cluster_analysis
        }
    
    def _simple_kmeans(self, data: np.ndarray, k: int, max_iters: int = 100) -> np.ndarray:
        """
        Implementación simple de K-means
        """
        n_samples, n_features = data.shape
        
        # Inicializar centroides aleatoriamente
        np.random.seed(42)  # Para reproducibilidad
        centroids = data[np.random.choice(n_samples, k, replace=False)]
        
        for _ in range(max_iters):
            # Asignar puntos al centroide más cercano
            distances = np.sqrt(((data - centroids[:, np.newaxis])**2).sum(axis=2))
            clusters = np.argmin(distances, axis=0)
            
            # Actualizar centroides
            new_centroids = np.array([data[clusters == i].mean(axis=0) for i in range(k)])
            
            # Verificar convergencia
            if np.allclose(centroids, new_centroids):
                break
                
            centroids = new_centroids
        
        return clusters
    
    def _describe_asteroid_cluster(self, cluster_data: pd.DataFrame) -> str:
        """
        Describe las características de un cluster de asteroides
        """
        mean_a = cluster_data['a'].mean()
        mean_e = cluster_data['e'].mean()
        mean_i = cluster_data['i'].mean()
        
        if mean_a < 2.0:
            region = "Cinturón interior"
        elif mean_a < 3.3:
            region = "Cinturón principal"
        else:
            region = "Cinturón exterior"
        
        if mean_e < 0.1:
            orbit_type = "circular"
        elif mean_e < 0.3:
            orbit_type = "ligeramente elíptica"
        else:
            orbit_type = "muy elíptica"
        
        return f"{region}, órbita {orbit_type}"
    
    def save_analysis_results(self):
        """
        Guarda todos los resultados de análisis
        """
        logger.info("Guardando resultados de análisis...")
        
        # Guardar como JSON
        results_file = os.path.join(self.results_dir, "analysis_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Resultados guardados en {results_file}")
        
        # Generar reporte readable
        self._generate_analysis_report()
    
    def _generate_analysis_report(self):
        """
        Genera un reporte legible de los análisis
        """
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE ANÁLISIS DE MINERÍA DE DATOS")
        report.append("Explorador del Sistema Solar")
        report.append("=" * 80)
        report.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Análisis descriptivo
        if 'descriptive' in self.analysis_results:
            report.append("1. ANÁLISIS DESCRIPTIVO Y COMPARATIVO")
            report.append("-" * 50)
            
            desc_results = self.analysis_results['descriptive']
            
            if 'planets' in desc_results:
                planet_stats = desc_results['planets']
                report.append(f"\nPlanetas analizados: {planet_stats['count']}")
                
                if 'statistics' in planet_stats:
                    report.append("\nEstadísticas principales:")
                    for param, stats in planet_stats['statistics'].items():
                        report.append(f"  {param}:")
                        report.append(f"    - Promedio: {stats['mean']:.2e}")
                        report.append(f"    - Rango: {stats['min']:.2e} - {stats['max']:.2e}")
            
            if 'comparative' in desc_results:
                comp = desc_results['comparative']
                report.append("\nComparación entre tipos de cuerpos:")
                if 'size_comparison' in comp:
                    report.append("  Tamaños promedio (radio en km):")
                    for body_type, data in comp['size_comparison'].items():
                        report.append(f"    - {body_type}: {data['mean_radius_km']:.1f}")
        
        # Análisis de clustering
        if 'clustering' in self.analysis_results:
            report.append("\n\n2. ANÁLISIS DE CLUSTERING")
            report.append("-" * 50)
            
            cluster_results = self.analysis_results['clustering']
            
            if 'asteroid_clusters' in cluster_results:
                ast_clusters = cluster_results['asteroid_clusters']
                if 'clusters' in ast_clusters:
                    report.append(f"\nAsteroides: {ast_clusters['total_objects']} objetos en {ast_clusters['n_clusters']} clusters")
                    for cluster_name, cluster_data in ast_clusters['clusters'].items():
                        report.append(f"  {cluster_name}: {cluster_data['count']} asteroides")
                        if 'characteristics' in cluster_data:
                            report.append(f"    Características: {cluster_data['characteristics']}")
            
            if 'comet_clusters' in cluster_results:
                comet_clusters = cluster_results['comet_clusters']
                if 'clusters' in comet_clusters:
                    report.append(f"\nCometas: {comet_clusters['total_objects']} objetos en {comet_clusters['n_clusters']} clusters")
                    for cluster_name, cluster_data in comet_clusters['clusters'].items():
                        report.append(f"  {cluster_name}: {cluster_data['count']} cometas")
        
        # Guardar reporte
        report_file = os.path.join(self.results_dir, "analysis_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        logger.info(f"Reporte de análisis guardado en {report_file}")
        
        # Imprimir resumen en consola
        print('\n'.join(report))
    
    def run_complete_analysis(self):
        """
        Ejecuta el análisis completo de minería de datos
        """
        logger.info("=" * 60)
        logger.info("INICIANDO ANÁLISIS COMPLETO DE MINERÍA DE DATOS")
        logger.info("=" * 60)
        
        # 1. Limpiar y preparar datos
        clean_datasets = self.clean_and_prepare_data()
        
        if not clean_datasets:
            logger.error("No hay datasets disponibles para análisis")
            return
        
        # 2. Análisis descriptivo (Técnica 1)
        descriptive_results = self.perform_descriptive_analysis(clean_datasets)
        
        # 3. Análisis de clustering (Técnica 2)  
        clustering_results = self.perform_clustering_analysis(clean_datasets)
        
        # 4. Guardar resultados
        self.save_analysis_results()
        
        logger.info("=" * 60)
        logger.info("ANÁLISIS COMPLETO FINALIZADO")
        logger.info("=" * 60)
        
        return {
            'descriptive': descriptive_results,
            'clustering': clustering_results
        }


def main():
    """
    Función principal para ejecutar el procesamiento
    """
    processor = SolarSystemDataProcessor()
    results = processor.run_complete_analysis()
    
    print("\nProcesamiento completado exitosamente!")
    print(f"Resultados guardados en: {processor.results_dir}")


if __name__ == "__main__":
    main()