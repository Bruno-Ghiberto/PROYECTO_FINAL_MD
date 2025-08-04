"""
Análisis de Clustering de Asteroides y Cometas
Implementa K-means, DBSCAN y clustering jerárquico con interpretación astronómica
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import scipy.cluster.hierarchy as sch
import os
import sys
from typing import Dict

# Agregar el path del proyecto para importar utilidades
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from data_analysis.utils.data_loader import AstronomicalDataLoader

class ClusteringAnalysis:
    """Análisis de clustering para asteroides y cometas"""
    
    def __init__(self, output_dir: str = "data/results/clustering_analysis"):
        self.output_dir = output_dir
        self.viz_dir = os.path.join(output_dir, "visualizations")
        self.loader = AstronomicalDataLoader()
        
        # Características para clustering orbital
        self.clustering_features = ['a', 'e', 'i', 'per', 'q', 'ad', 'H']
        
        # Configurar matplotlib
        plt.style.use('default')
        sns.set_palette("tab10")
        
    def prepare_clustering_data(self) -> pd.DataFrame:
        """Preparar datos para clustering"""
        print("Preparando datos para clustering...")
        
        # Cargar y combinar datos SBDB
        df = self.loader.combine_sbdb_for_clustering()
        
        # Verificar columnas disponibles
        available_features = [col for col in self.clustering_features if col in df.columns]
        print(f"Características disponibles para clustering: {available_features}")
        
        if len(available_features) < 3:
            raise ValueError("Insuficientes características para clustering")
        
        # Filtrar datos válidos
        clustering_data = df[available_features + ['category']].dropna()
        
        print(f"Datos preparados: {len(clustering_data)} objetos con {len(available_features)} características")
        
        return clustering_data
    
    def kmeans_analysis(self, data: pd.DataFrame, n_clusters: int = 6) -> Dict:
        """Análisis K-means con validación de clusters"""
        print(f"Ejecutando K-means con {n_clusters} clusters...")
        
        # Preparar datos
        features = [col for col in self.clustering_features if col in data.columns]
        X = data[features].values
        
        # Normalización
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Métricas de evaluación
        silhouette_avg = silhouette_score(X_scaled, clusters)
        inertia = kmeans.inertia_
        
        # PCA para visualización
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # Agregar clusters al dataframe
        data_with_clusters = data.copy()
        data_with_clusters['kmeans_cluster'] = clusters
        data_with_clusters['pca_1'] = X_pca[:, 0]
        data_with_clusters['pca_2'] = X_pca[:, 1]
        
        results = {
            'data': data_with_clusters,
            'clusters': clusters,
            'silhouette_score': silhouette_avg,
            'inertia': inertia,
            'pca_data': X_pca,
            'scaler': scaler,
            'pca_model': pca,
            'centroids': kmeans.cluster_centers_
        }
        
        print(f"K-means completado. Silhouette Score: {silhouette_avg:.3f}")
        
        return results
    
    def dbscan_analysis(self, data: pd.DataFrame, eps: float = 0.5, min_samples: int = 10) -> Dict:
        """Análisis DBSCAN para detección de anomalías"""
        print(f"Ejecutando DBSCAN (eps={eps}, min_samples={min_samples})...")
        
        # Preparar datos
        features = [col for col in self.clustering_features if col in data.columns]
        X = data[features].values
        
        # Normalización
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(X_scaled)
        
        # Identificar anomalías (cluster = -1)
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_anomalies = list(clusters).count(-1)
        
        # Agregar clusters al dataframe
        data_with_clusters = data.copy()
        data_with_clusters['dbscan_cluster'] = clusters
        
        # Separar objetos normales y anomalías
        normal_objects = data_with_clusters[data_with_clusters['dbscan_cluster'] != -1]
        anomalies = data_with_clusters[data_with_clusters['dbscan_cluster'] == -1]
        
        results = {
            'data': data_with_clusters,
            'clusters': clusters,
            'n_clusters': n_clusters,
            'n_anomalies': n_anomalies,
            'normal_objects': normal_objects,
            'anomalies': anomalies
        }
        
        print(f"DBSCAN completado. Clusters: {n_clusters}, Anomalías: {n_anomalies}")
        
        return results
    
    def find_optimal_clusters(self, data: pd.DataFrame, max_clusters: int = 10) -> int:
        """Encontrar número óptimo de clusters usando método del codo"""
        print("Buscando número óptimo de clusters...")
        
        features = [col for col in self.clustering_features if col in data.columns]
        X = data[features].values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Calcular inercia para diferentes números de clusters
        inertias = []
        silhouette_scores = []
        k_range = range(2, max_clusters + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(X_scaled, clusters))
        
        # Visualizar curva del codo
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Método del codo
        ax1.plot(k_range, inertias, 'bo-')
        ax1.set_xlabel('Número de Clusters')
        ax1.set_ylabel('Inercia')
        ax1.set_title('Método del Codo')
        ax1.grid(True)
        
        # Silhouette scores
        ax2.plot(k_range, silhouette_scores, 'ro-')
        ax2.set_xlabel('Número de Clusters')
        ax2.set_ylabel('Silhouette Score')
        ax2.set_title('Análisis Silhouette')
        ax2.grid(True)
        
        plt.tight_layout()
        
        # Guardar visualización
        elbow_file = os.path.join(self.viz_dir, "optimal_clusters_analysis.png")
        plt.savefig(elbow_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Encontrar k óptimo (mayor silhouette score)
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        print(f"Número óptimo de clusters: {optimal_k}")
        print(f"Análisis guardado en: {elbow_file}")
        
        return optimal_k
    
    def interpret_clusters_astronomically(self, data: pd.DataFrame, cluster_col: str = 'kmeans_cluster') -> pd.DataFrame:
        """Interpretación astronómica de los clusters"""
        print("Interpretando clusters astronómicamente...")
        
        cluster_stats = []
        
        for cluster_id in sorted(data[cluster_col].unique()):
            if cluster_id == -1:  # Saltar anomalías en DBSCAN
                continue
                
            cluster_data = data[data[cluster_col] == cluster_id]
            
            # Estadísticas orbitales promedio
            stats = {
                'cluster_id': cluster_id,
                'count': len(cluster_data),
                'avg_semimajor_axis': cluster_data['a'].mean() if 'a' in cluster_data.columns else np.nan,
                'avg_eccentricity': cluster_data['e'].mean() if 'e' in cluster_data.columns else np.nan,
                'avg_inclination': cluster_data['i'].mean() if 'i' in cluster_data.columns else np.nan,
                'avg_period': cluster_data['per'].mean() if 'per' in cluster_data.columns else np.nan,
                'dominant_category': cluster_data['category'].mode()[0] if len(cluster_data['category'].mode()) > 0 else 'Unknown'
            }
            
            # Clasificación astronómica
            stats['astronomical_classification'] = self.classify_cluster_type(stats)
            
            # Distribución de categorías
            category_dist = cluster_data['category'].value_counts().to_dict()
            stats['category_distribution'] = category_dist
            
            cluster_stats.append(stats)
        
        # Convertir a DataFrame
        interpretation_df = pd.DataFrame(cluster_stats)
        
        # Guardar interpretación
        interp_file = os.path.join(self.output_dir, "interpretacion_astronomica.csv")
        interpretation_df.to_csv(interp_file, index=False)
        
        print(f"Interpretación astronómica guardada en: {interp_file}")
        
        return interpretation_df
    
    def classify_cluster_type(self, stats: Dict) -> str:
        """Clasificar cluster según características orbitales"""
        a = stats.get('avg_semimajor_axis', 0)
        e = stats.get('avg_eccentricity', 0)
        i = stats.get('avg_inclination', 0)
        
        if np.isnan(a) or np.isnan(e):
            return "Datos insuficientes"
        
        # Clasificación basada en elementos orbitales típicos
        if 2.0 <= a <= 3.5 and e < 0.3:
            return "Asteroides del Cinturón Principal"
        elif 4.8 <= a <= 5.5:
            return "Asteroides Troyanos de Júpiter"
        elif a < 1.3 or (a < 1.7 and e > 0.6):
            return "Objetos Cercanos a la Tierra (NEO)"
        elif e > 0.7 and a > 3:
            return "Objetos Tipo Cometa (Alta Excentricidad)"
        elif 9 <= a <= 30:
            return "Centauros"
        elif i > 30:
            return "Objetos de Alta Inclinación"
        else:
            return "Población Mixta"
    
    def create_clustering_visualizations(self, kmeans_results: Dict, dbscan_results: Dict) -> None:
        """Crear visualizaciones del análisis de clustering"""
        print("Creando visualizaciones de clustering...")
        
        # 1. Scatter plot PCA con clusters K-means
        plt.figure(figsize=(12, 8))
        
        data = kmeans_results['data']
        scatter = plt.scatter(data['pca_1'], data['pca_2'], 
                            c=data['kmeans_cluster'], 
                            cmap='tab10', alpha=0.6, s=30)
        plt.colorbar(scatter)
        plt.xlabel('Primera Componente Principal')
        plt.ylabel('Segunda Componente Principal')
        plt.title('Clusters K-means en Espacio PCA')
        
        pca_file = os.path.join(self.viz_dir, "kmeans_pca_clusters.png")
        plt.savefig(pca_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Distribución orbital (a vs e)
        if 'a' in data.columns and 'e' in data.columns:
            plt.figure(figsize=(12, 8))
            scatter = plt.scatter(data['a'], data['e'], 
                                c=data['kmeans_cluster'], 
                                cmap='tab10', alpha=0.6, s=30)
            plt.colorbar(scatter)
            plt.xlabel('Semieje Mayor (AU)')
            plt.ylabel('Excentricidad')
            plt.title('Clusters en Espacio Orbital (a-e)')
            plt.grid(True, alpha=0.3)
            
            orbital_file = os.path.join(self.viz_dir, "orbital_elements_clusters.png")
            plt.savefig(orbital_file, dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Anomalías DBSCAN
        if 'anomalies' in dbscan_results and len(dbscan_results['anomalies']) > 0:
            plt.figure(figsize=(12, 8))
            
            # Objetos normales
            normal = dbscan_results['normal_objects']
            if len(normal) > 0:
                plt.scatter(normal['a'], normal['e'], 
                           c='lightblue', alpha=0.5, s=20, label='Objetos Normales')
            
            # Anomalías
            anomalies = dbscan_results['anomalies']
            plt.scatter(anomalies['a'], anomalies['e'], 
                       c='red', s=50, marker='x', label=f'Anomalías ({len(anomalies)})')
            
            plt.xlabel('Semieje Mayor (AU)')
            plt.ylabel('Excentricidad')
            plt.title('Detección de Anomalías - DBSCAN')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            anomaly_file = os.path.join(self.viz_dir, "dbscan_anomalies.png")
            plt.savefig(anomaly_file, dpi=300, bbox_inches='tight')
            plt.close()
        
        print("Visualizaciones creadas:")
        print(f"- {pca_file}")
        if 'a' in data.columns:
            print(f"- {orbital_file}")
        if 'anomalies' in dbscan_results:
            print(f"- {anomaly_file}")
    
    def run_complete_clustering(self) -> Dict:
        """Ejecutar análisis de clustering completo"""
        print("=== INICIANDO ANÁLISIS DE CLUSTERING COMPLETO ===")
        
        results = {}
        
        try:
            # 1. Preparar datos
            data = self.prepare_clustering_data()
            
            # 2. Encontrar número óptimo de clusters
            optimal_k = self.find_optimal_clusters(data)
            
            # 3. K-means analysis
            kmeans_results = self.kmeans_analysis(data, n_clusters=optimal_k)
            results['kmeans'] = kmeans_results
            
            # 4. DBSCAN analysis
            dbscan_results = self.dbscan_analysis(data, eps=0.5, min_samples=10)
            results['dbscan'] = dbscan_results
            
            # 5. Interpretación astronómica
            interpretation = self.interpret_clusters_astronomically(kmeans_results['data'])
            results['interpretation'] = interpretation
            
            # 6. Crear visualizaciones
            self.create_clustering_visualizations(kmeans_results, dbscan_results)
            
            # 7. Guardar resultados
            self.save_clustering_results(results)
            
            # 8. Generar reporte
            self.generate_clustering_report(results)
            
            print("=== ANÁLISIS DE CLUSTERING COMPLETADO ===")
            
        except Exception as e:
            print(f"Error en análisis de clustering: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def save_clustering_results(self, results: Dict) -> None:
        """Guardar resultados del clustering"""
        print("Guardando resultados de clustering...")
        
        # Guardar clusters K-means
        if 'kmeans' in results:
            kmeans_file = os.path.join(self.output_dir, "kmeans_clusters.csv")
            results['kmeans']['data'].to_csv(kmeans_file, index=False)
            print(f"Resultados K-means guardados en: {kmeans_file}")
        
        # Guardar anomalías DBSCAN
        if 'dbscan' in results and len(results['dbscan']['anomalies']) > 0:
            anomaly_file = os.path.join(self.output_dir, "dbscan_anomalies.csv")
            results['dbscan']['anomalies'].to_csv(anomaly_file, index=False)
            print(f"Anomalías DBSCAN guardadas en: {anomaly_file}")
    
    def generate_clustering_report(self, results: Dict) -> None:
        """Generar reporte del análisis de clustering"""
        report_file = os.path.join(self.output_dir, "reporte_clustering.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== REPORTE DE ANÁLISIS DE CLUSTERING ===\n\n")
            
            # Resumen de datos
            if 'kmeans' in results:
                data = results['kmeans']['data']
                f.write(f"Total de objetos analizados: {len(data)}\n")
                f.write(f"Características utilizadas: {len([col for col in self.clustering_features if col in data.columns])}\n\n")
                
                # Resultados K-means
                f.write("RESULTADOS K-MEANS:\n")
                f.write(f"Número de clusters: {len(data['kmeans_cluster'].unique())}\n")
                f.write(f"Silhouette Score: {results['kmeans']['silhouette_score']:.3f}\n")
                f.write(f"Inercia: {results['kmeans']['inertia']:.2f}\n\n")
                
                # Distribución por cluster
                cluster_dist = data['kmeans_cluster'].value_counts().sort_index()
                f.write("Distribución de objetos por cluster:\n")
                for cluster, count in cluster_dist.items():
                    f.write(f"  Cluster {cluster}: {count} objetos\n")
                f.write("\n")
            
            # Resultados DBSCAN
            if 'dbscan' in results:
                f.write("RESULTADOS DBSCAN:\n")
                f.write(f"Clusters encontrados: {results['dbscan']['n_clusters']}\n")
                f.write(f"Anomalías detectadas: {results['dbscan']['n_anomalies']}\n\n")
            
            # Interpretación astronómica
            if 'interpretation' in results:
                f.write("INTERPRETACIÓN ASTRONÓMICA:\n")
                interp = results['interpretation']
                for _, row in interp.iterrows():
                    f.write(f"Cluster {row['cluster_id']}: {row['astronomical_classification']}\n")
                    f.write(f"  - {row['count']} objetos\n")
                    f.write(f"  - Categoría dominante: {row['dominant_category']}\n")
                    if not np.isnan(row['avg_semimajor_axis']):
                        f.write(f"  - Semieje mayor promedio: {row['avg_semimajor_axis']:.2f} AU\n")
                    f.write("\n")
            
            f.write("Archivos generados:\n")
            f.write("- kmeans_clusters.csv\n")
            f.write("- dbscan_anomalies.csv\n")
            f.write("- interpretacion_astronomica.csv\n")
            f.write("- visualizations/kmeans_pca_clusters.png\n")
            f.write("- visualizations/orbital_elements_clusters.png\n")
            f.write("- visualizations/dbscan_anomalies.png\n")
            f.write("- visualizations/optimal_clusters_analysis.png\n")
        
        print(f"Reporte de clustering generado en: {report_file}")

if __name__ == "__main__":
    # Ejecutar análisis de clustering
    analyzer = ClusteringAnalysis()
    results = analyzer.run_complete_clustering()