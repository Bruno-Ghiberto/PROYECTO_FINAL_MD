"""
Utilidades para carga y preprocesamiento de datos astronómicos
"""
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional

class AstronomicalDataLoader:
    """Cargador de datos astronómicos con preprocesamiento"""
    
    def __init__(self, data_dir: str = "data/raw/api_data"):
        self.data_dir = data_dir
        self.opendata_files = {
            'all_bodies': 'opendata_all_bodies.csv',
            'planets': 'opendata_planets.csv', 
            'moons': 'opendata_moons.csv'
        }
        self.sbdb_files = {
            'neos': 'sbdb_neos.csv',
            'main_belt': 'sbdb_main_belt.csv',
            'trojans': 'sbdb_trojans.csv',
            'comets_jfc': 'sbdb_comets_jfc.csv',
            'comets_htc': 'sbdb_comets_htc.csv',
            'phas': 'sbdb_phas.csv',
            'centaurs': 'sbdb_centaurs.csv'
        }
    
    def load_opendata_bodies(self) -> pd.DataFrame:
        """Cargar datos físicos de cuerpos del sistema solar"""
        file_path = os.path.join(self.data_dir, self.opendata_files['all_bodies'])
        df = pd.read_csv(file_path)
        
        # Calcular masa en kg si existe mass_value y mass_exponent
        if 'mass_value' in df.columns and 'mass_exponent' in df.columns:
            df['mass_kg'] = df['mass_value'] * (10 ** df['mass_exponent'])
        
        # Limpiar valores nulos críticos
        numeric_cols = ['meanRadius', 'density', 'gravity', 'avgTemp']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def load_sbdb_data(self) -> Dict[str, pd.DataFrame]:
        """Cargar todos los datasets SBDB para clustering"""
        sbdb_data = {}
        
        for category, filename in self.sbdb_files.items():
            file_path = os.path.join(self.data_dir, filename)
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                
                # Limpiar y convertir columnas numéricas
                numeric_cols = ['a', 'e', 'i', 'per', 'q', 'ad', 'H']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Agregar categoría
                df['category'] = category
                sbdb_data[category] = df
                print(f"Cargado {category}: {len(df)} registros")
        
        return sbdb_data
    
    def combine_sbdb_for_clustering(self) -> pd.DataFrame:
        """Combinar todos los datasets SBDB para análisis de clustering"""
        sbdb_data = self.load_sbdb_data()
        combined_df = pd.concat(sbdb_data.values(), ignore_index=True)
        
        # Filtrar filas con datos válidos para clustering
        clustering_cols = ['a', 'e', 'i', 'per', 'H']
        combined_df = combined_df.dropna(subset=clustering_cols)
        
        print(f"Dataset combinado para clustering: {len(combined_df)} registros")
        return combined_df
    
    def get_data_summary(self) -> Dict:
        """Obtener resumen de todos los datos disponibles"""
        summary = {
            'opendata': {},
            'sbdb': {},
            'total_records': 0
        }
        
        # Resumen OpenData
        try:
            opendata_df = self.load_opendata_bodies()
            summary['opendata'] = {
                'total_bodies': len(opendata_df),
                'body_types': opendata_df['bodyType'].value_counts().to_dict() if 'bodyType' in opendata_df.columns else {},
                'has_mass_data': opendata_df['mass_kg'].notna().sum() if 'mass_kg' in opendata_df.columns else 0
            }
            summary['total_records'] += len(opendata_df)
        except Exception as e:
            print(f"Error cargando OpenData: {e}")
        
        # Resumen SBDB
        try:
            sbdb_data = self.load_sbdb_data()
            for category, df in sbdb_data.items():
                summary['sbdb'][category] = len(df)
                summary['total_records'] += len(df)
        except Exception as e:
            print(f"Error cargando SBDB: {e}")
        
        return summary

def load_scraping_data() -> Dict[str, pd.DataFrame]:
    """Cargar datos de scraping si están disponibles"""
    scraping_data = {}
    scraping_dir = "data/raw/scraping_data"
    
    files = {
        'wikipedia_size': 'wikipedia_objects_by_size.csv',
        'johnstons': 'johnstons_physical_data.csv'
    }
    
    for name, filename in files.items():
        file_path = os.path.join(scraping_dir, filename)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                scraping_data[name] = df
                print(f"Cargado scraping {name}: {len(df)} registros")
            except Exception as e:
                print(f"Error cargando {filename}: {e}")
    
    return scraping_data

if __name__ == "__main__":
    # Prueba básica del cargador
    loader = AstronomicalDataLoader()
    summary = loader.get_data_summary()
    print("\nResumen de datos disponibles:")
    print(f"Total de registros: {summary['total_records']}")
    print(f"OpenData: {summary['opendata']}")
    print(f"SBDB: {summary['sbdb']}")