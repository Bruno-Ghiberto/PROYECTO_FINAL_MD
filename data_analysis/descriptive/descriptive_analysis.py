"""
Análisis Descriptivo y Comparativo de Objetos Astronómicos
Implementa estadísticas básicas, comparaciones entre tipos y correlaciones
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from typing import Dict

# Agregar el path del proyecto para importar utilidades
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from data_analysis.utils.data_loader import AstronomicalDataLoader

class DescriptiveAnalysis:
    """Análisis descriptivo de objetos astronómicos"""
    
    def __init__(self, output_dir: str = "data/results/descriptive_analysis"):
        self.output_dir = output_dir
        self.viz_dir = os.path.join(output_dir, "visualizations")
        self.loader = AstronomicalDataLoader()
        
        # Configurar matplotlib para mejor visualización
        plt.style.use('default')
        sns.set_palette("husl")
        
    def analyze_body_types(self) -> pd.DataFrame:
        """Análisis estadístico por tipo de cuerpo"""
        print("Ejecutando análisis por tipo de cuerpo...")
        
        # Cargar datos OpenData
        df = self.loader.load_opendata_bodies()
        
        # Verificar columnas disponibles
        print(f"Columnas disponibles: {list(df.columns)}")
        
        # Definir columnas numéricas para análisis
        numeric_cols = []
        potential_cols = ['meanRadius', 'mass_kg', 'density', 'gravity', 'avgTemp']
        
        for col in potential_cols:
            if col in df.columns:
                numeric_cols.append(col)
        
        if not numeric_cols:
            print("No se encontraron columnas numéricas para análisis")
            return pd.DataFrame()
        
        # Agrupar por tipo de cuerpo si existe la columna
        if 'bodyType' in df.columns:
            stats_by_type = df.groupby('bodyType')[numeric_cols].agg([
                'count', 'mean', 'median', 'std', 'min', 'max'
            ]).round(4)
        else:
            # Si no hay bodyType, crear estadísticas generales
            stats_by_type = df[numeric_cols].agg([
                'count', 'mean', 'median', 'std', 'min', 'max'
            ]).round(4)
        
        # Guardar resultados
        output_file = os.path.join(self.output_dir, "estadisticas_por_tipo.csv")
        stats_by_type.to_csv(output_file)
        print(f"Estadísticas por tipo guardadas en: {output_file}")
        
        return stats_by_type
    
    def correlation_analysis(self) -> pd.DataFrame:
        """Análisis de correlaciones entre parámetros físicos"""
        print("Ejecutando análisis de correlaciones...")
        
        df = self.loader.load_opendata_bodies()
        
        # Seleccionar solo columnas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            print("Insuficientes columnas numéricas para análisis de correlación")
            return pd.DataFrame()
        
        # Calcular matriz de correlaciones
        correlation_matrix = df[numeric_cols].corr()
        
        # Crear heatmap
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(correlation_matrix))
        sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', 
                   center=0, square=True, fmt='.2f')
        plt.title('Matriz de Correlaciones - Parámetros Físicos')
        plt.tight_layout()
        
        # Guardar visualización
        heatmap_file = os.path.join(self.viz_dir, "correlacion_heatmap.png")
        plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Guardar matriz
        corr_file = os.path.join(self.output_dir, "matriz_correlaciones.csv")
        correlation_matrix.to_csv(corr_file)
        
        print(f"Matriz de correlaciones guardada en: {corr_file}")
        print(f"Heatmap guardado en: {heatmap_file}")
        
        return correlation_matrix
    
    def distribution_analysis(self) -> None:
        """Análisis de distribuciones de parámetros físicos"""
        print("Ejecutando análisis de distribuciones...")
        
        df = self.loader.load_opendata_bodies()
        
        # Parámetros clave para análisis
        key_params = ['meanRadius', 'mass_kg', 'density', 'gravity']
        available_params = [col for col in key_params if col in df.columns]
        
        if not available_params:
            print("No hay parámetros disponibles para análisis de distribución")
            return
        
        # Crear subplots para distribuciones
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, param in enumerate(available_params[:4]):
            if i >= 4:
                break
                
            # Filtrar datos válidos
            valid_data = df[param].dropna()
            
            if len(valid_data) == 0:
                continue
            
            # Histograma
            axes[i].hist(valid_data, bins=30, alpha=0.7, edgecolor='black')
            axes[i].set_title(f'Distribución de {param}')
            axes[i].set_xlabel(param)
            axes[i].set_ylabel('Frecuencia')
            
            # Agregar estadísticas
            mean_val = valid_data.mean()
            median_val = valid_data.median()
            axes[i].axvline(mean_val, color='red', linestyle='--', label=f'Media: {mean_val:.2f}')
            axes[i].axvline(median_val, color='green', linestyle='--', label=f'Mediana: {median_val:.2f}')
            axes[i].legend()
        
        # Ocultar subplots vacíos
        for i in range(len(available_params), 4):
            axes[i].axis('off')
        
        plt.tight_layout()
        
        # Guardar visualización
        dist_file = os.path.join(self.viz_dir, "distribuciones_parametros.png")
        plt.savefig(dist_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Análisis de distribuciones guardado en: {dist_file}")
    
    def comparative_analysis(self) -> pd.DataFrame:
        """Análisis comparativo entre tipos de objetos"""
        print("Ejecutando análisis comparativo...")
        
        df = self.loader.load_opendata_bodies()
        
        if 'bodyType' not in df.columns:
            print("No se puede realizar análisis comparativo sin columna bodyType")
            return pd.DataFrame()
        
        # Parámetros para comparación
        comparison_params = ['meanRadius', 'mass_kg', 'density']
        available_params = [col for col in comparison_params if col in df.columns]
        
        if not available_params:
            print("No hay parámetros disponibles para comparación")
            return pd.DataFrame()
        
        # Crear boxplots comparativos
        fig, axes = plt.subplots(1, len(available_params), figsize=(15, 5))
        
        if len(available_params) == 1:
            axes = [axes]
        
        for i, param in enumerate(available_params):
            # Filtrar datos válidos
            valid_df = df[[param, 'bodyType']].dropna()
            
            if len(valid_df) == 0:
                continue
            
            # Boxplot
            sns.boxplot(data=valid_df, x='bodyType', y=param, ax=axes[i])
            axes[i].set_title(f'Comparación de {param} por Tipo')
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Guardar visualización
        comp_file = os.path.join(self.viz_dir, "comparacion_tipos.png")
        plt.savefig(comp_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Crear tabla de comparación
        comparison_stats = df.groupby('bodyType')[available_params].agg([
            'count', 'mean', 'median', 'std'
        ]).round(4)
        
        # Guardar tabla
        comp_table_file = os.path.join(self.output_dir, "comparacion_tipos.csv")
        comparison_stats.to_csv(comp_table_file)
        
        print(f"Análisis comparativo guardado en: {comp_file}")
        print(f"Tabla comparativa guardada en: {comp_table_file}")
        
        return comparison_stats
    
    def run_complete_analysis(self) -> Dict:
        """Ejecutar análisis descriptivo completo"""
        print("=== INICIANDO ANÁLISIS DESCRIPTIVO COMPLETO ===")
        
        results = {}
        
        try:
            # 1. Análisis por tipo de cuerpo
            results['body_types'] = self.analyze_body_types()
            
            # 2. Análisis de correlaciones
            results['correlations'] = self.correlation_analysis()
            
            # 3. Análisis de distribuciones
            self.distribution_analysis()
            
            # 4. Análisis comparativo
            results['comparative'] = self.comparative_analysis()
            
            # 5. Generar resumen
            self.generate_summary_report(results)
            
            print("=== ANÁLISIS DESCRIPTIVO COMPLETADO ===")
            
        except Exception as e:
            print(f"Error en análisis descriptivo: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def generate_summary_report(self, results: Dict) -> None:
        """Generar reporte resumen del análisis descriptivo"""
        report_file = os.path.join(self.output_dir, "reporte_descriptivo.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== REPORTE DE ANÁLISIS DESCRIPTIVO ===\n\n")
            
            # Resumen de datos
            summary = self.loader.get_data_summary()
            f.write(f"Total de registros analizados: {summary['total_records']}\n")
            f.write(f"Cuerpos OpenData: {summary['opendata']['total_bodies']}\n")
            f.write(f"Categorías SBDB: {len(summary['sbdb'])}\n\n")
            
            # Estadísticas clave
            if 'body_types' in results and not results['body_types'].empty:
                f.write("ESTADÍSTICAS POR TIPO DE CUERPO:\n")
                f.write(str(results['body_types']))
                f.write("\n\n")
            
            # Correlaciones importantes
            if 'correlations' in results and not results['correlations'].empty:
                f.write("CORRELACIONES SIGNIFICATIVAS (>0.5):\n")
                corr_matrix = results['correlations']
                
                # Encontrar correlaciones altas
                high_corr = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.5:
                            high_corr.append((
                                corr_matrix.columns[i], 
                                corr_matrix.columns[j], 
                                corr_val
                            ))
                
                for var1, var2, corr in high_corr:
                    f.write(f"  {var1} - {var2}: {corr:.3f}\n")
                
                f.write("\n")
            
            f.write("Archivos generados:\n")
            f.write("- estadisticas_por_tipo.csv\n")
            f.write("- matriz_correlaciones.csv\n")
            f.write("- comparacion_tipos.csv\n")
            f.write("- visualizations/correlacion_heatmap.png\n")
            f.write("- visualizations/distribuciones_parametros.png\n")
            f.write("- visualizations/comparacion_tipos.png\n")
        
        print(f"Reporte resumen generado en: {report_file}")

if __name__ == "__main__":
    # Ejecutar análisis descriptivo
    analyzer = DescriptiveAnalysis()
    results = analyzer.run_complete_analysis()