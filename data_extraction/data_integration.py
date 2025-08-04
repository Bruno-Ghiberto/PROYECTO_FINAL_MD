"""
Script principal de integración de datos del Sistema Solar
Combina datos de todas las fuentes (APIs y scrapers) en datasets unificados
"""
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar clientes API
from api_clients.horizons_client import get_horizons_client
from api_clients.sbdb_client import get_sbdb_client
from api_clients.neo_client import get_neo_client
from api_clients.opendata_client import get_solar_system_client
from api_clients.image_client import get_apod_client, get_nasa_image_client

# Importar scrapers
from scrapers.planetary_facts import get_planetary_facts_scraper
from scrapers.moon_facts import get_moon_facts_scraper
from scrapers.jovian_sats import get_jovian_satellite_scraper

# Importar validador
from data_validators.data_validator import validate_and_normalize_dataset, create_validator


class SolarSystemDataIntegrator:
    """
    Clase principal para integrar datos de múltiples fuentes del Sistema Solar
    """
    
    def __init__(self, output_dir: str = "../data/processed"):
        """
        Inicializa el integrador
        
        Args:
            output_dir: Directorio donde guardar los datos procesados
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Directorio para datos crudos
        self.raw_dir = os.path.join(os.path.dirname(output_dir), "raw")
        os.makedirs(self.raw_dir, exist_ok=True)
        
        # Inicializar clientes
        self.horizons_client = get_horizons_client()
        self.sbdb_client = get_sbdb_client()
        self.neo_client = get_neo_client()
        self.opendata_client = get_solar_system_client()
        self.apod_client = get_apod_client()
        self.nasa_images_client = get_nasa_image_client()
        
        # Inicializar scrapers
        self.planetary_scraper = get_planetary_facts_scraper()
        self.moon_scraper = get_moon_facts_scraper()
        self.jovian_scraper = get_jovian_satellite_scraper()
        
        # Validador
        self.validator = create_validator()
        
        # Resultados de validación
        self.validation_results = []
    
    def extract_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Extrae datos de todas las fuentes disponibles
        
        Returns:
            Diccionario con DataFrames de cada fuente
        """
        logger.info("Iniciando extracción de datos de todas las fuentes...")
        datasets = {}
        
        # 1. Datos de planetas
        logger.info("Extrayendo datos de planetas...")
        try:
            # OpenData
            planets_opendata = self.opendata_client.get_planets(include_dwarf=True)
            datasets['planets_opendata'] = planets_opendata
            self._save_raw_data(planets_opendata, 'planets_opendata.csv')
            
            # Planetary Facts
            planets_facts = self.planetary_scraper.scrape_planetary_facts()
            datasets['planets_facts'] = planets_facts
            self._save_raw_data(planets_facts, 'planets_facts.csv')
        except Exception as e:
            logger.error(f"Error extrayendo datos de planetas: {e}")
        
        # 2. Datos de lunas
        logger.info("Extrayendo datos de lunas...")
        try:
            # Todas las lunas de OpenData
            moons_opendata = self.opendata_client.get_moons()
            datasets['moons_opendata'] = moons_opendata
            self._save_raw_data(moons_opendata, 'moons_opendata.csv')
            
            # Luna terrestre
            moon_data = self.moon_scraper.scrape_moon_facts()
            moon_df = pd.DataFrame([moon_data])
            datasets['moon_facts'] = moon_df
            self._save_raw_data(moon_df, 'moon_facts.csv')
            
            # Lunas de Júpiter
            jovian_moons = self.jovian_scraper.scrape_jovian_satellites()
            datasets['jovian_moons'] = jovian_moons
            self._save_raw_data(jovian_moons, 'jovian_moons.csv')
        except Exception as e:
            logger.error(f"Error extrayendo datos de lunas: {e}")
        
        # 3. Datos de asteroides
        logger.info("Extrayendo datos de asteroides...")
        try:
            asteroids = self.sbdb_client.get_asteroids(
                asteroid_class='MBA',
                min_diameter=50,
                limit=1000
            )
            datasets['asteroids'] = asteroids
            self._save_raw_data(asteroids, 'asteroids.csv')
        except Exception as e:
            logger.error(f"Error extrayendo datos de asteroides: {e}")
        
        # 4. Datos de cometas
        logger.info("Extrayendo datos de cometas...")
        try:
            comets = self.sbdb_client.get_comets(
                comet_class='JFC',
                limit=500
            )
            datasets['comets'] = comets
            self._save_raw_data(comets, 'comets.csv')
        except Exception as e:
            logger.error(f"Error extrayendo datos de cometas: {e}")
        
        # 5. Datos de NEOs
        logger.info("Extrayendo datos de NEOs...")
        try:
            today = datetime.now()
            neos = self.neo_client.get_feed(
                start_date=today.strftime('%Y-%m-%d'),
                end_date=(today + timedelta(days=7)).strftime('%Y-%m-%d')
            )
            datasets['neos'] = neos
            self._save_raw_data(neos, 'neos_week.csv')
        except Exception as e:
            logger.error(f"Error extrayendo datos de NEOs: {e}")
        
        logger.info(f"Extracción completada. {len(datasets)} datasets obtenidos.")
        return datasets
    
    def integrate_planet_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Integra datos de planetas de múltiples fuentes
        
        Args:
            datasets: Diccionario con datasets crudos
            
        Returns:
            DataFrame integrado de planetas
        """
        logger.info("Integrando datos de planetas...")
        
        # Obtener datasets relevantes
        opendata_df = datasets.get('planets_opendata', pd.DataFrame())
        facts_df = datasets.get('planets_facts', pd.DataFrame())
        
        if opendata_df.empty and facts_df.empty:
            logger.warning("No hay datos de planetas para integrar")
            return pd.DataFrame()
        
        # Validar y normalizar cada dataset
        if not opendata_df.empty:
            opendata_clean, stats1 = validate_and_normalize_dataset(
                opendata_df, 'Planetas OpenData', 'planets'
            )
            self.validation_results.append(('Planetas OpenData', stats1))
        else:
            opendata_clean = pd.DataFrame()
        
        if not facts_df.empty:
            facts_clean, stats2 = validate_and_normalize_dataset(
                facts_df, 'Planetas Facts', 'planets'
            )
            self.validation_results.append(('Planetas Facts', stats2))
        else:
            facts_clean = pd.DataFrame()
        
        # Combinar datasets
        if not opendata_clean.empty and not facts_clean.empty:
            # Preparar para merge
            opendata_clean['name'] = opendata_clean['englishName'] if 'englishName' in opendata_clean.columns else opendata_clean['name']
            
            # Merge por nombre
            integrated = pd.merge(
                opendata_clean,
                facts_clean,
                on='name',
                how='outer',
                suffixes=('_opendata', '_facts')
            )
            
            # Resolver conflictos de columnas
            integrated = self._resolve_column_conflicts(integrated)
        elif not opendata_clean.empty:
            integrated = opendata_clean
        else:
            integrated = facts_clean
        
        # Agregar metadatos
        integrated['data_source'] = 'integrated'
        integrated['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Integración de planetas completada: {len(integrated)} registros")
        return integrated
    
    def integrate_moon_data(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Integra datos de lunas de múltiples fuentes
        
        Args:
            datasets: Diccionario con datasets crudos
            
        Returns:
            DataFrame integrado de lunas
        """
        logger.info("Integrando datos de lunas...")
        
        # Obtener datasets relevantes
        opendata_moons = datasets.get('moons_opendata', pd.DataFrame())
        moon_facts = datasets.get('moon_facts', pd.DataFrame())
        jovian_moons = datasets.get('jovian_moons', pd.DataFrame())
        
        all_moons = []
        
        # Validar y agregar lunas de OpenData
        if not opendata_moons.empty:
            moons_clean, stats = validate_and_normalize_dataset(
                opendata_moons, 'Lunas OpenData', 'moons'
            )
            self.validation_results.append(('Lunas OpenData', stats))
            all_moons.append(moons_clean)
        
        # Validar y agregar Luna terrestre
        if not moon_facts.empty:
            moon_clean, stats = validate_and_normalize_dataset(
                moon_facts, 'Luna Terrestre', 'moons'
            )
            self.validation_results.append(('Luna Terrestre', stats))
            all_moons.append(moon_clean)
        
        # Validar y agregar lunas jovianas
        if not jovian_moons.empty:
            jovian_clean, stats = validate_and_normalize_dataset(
                jovian_moons, 'Lunas Jovianas', 'moons'
            )
            self.validation_results.append(('Lunas Jovianas', stats))
            all_moons.append(jovian_clean)
        
        if all_moons:
            # Combinar todos los datasets de lunas
            integrated = pd.concat(all_moons, ignore_index=True)
            
            # Eliminar duplicados basados en nombre
            integrated = integrated.drop_duplicates(subset=['name'], keep='first')
            
            # Ordenar por planeta y distancia
            sort_cols = []
            if 'planet' in integrated.columns:
                sort_cols.append('planet')
            if 'mean_distance_from_jupiter_km' in integrated.columns:
                sort_cols.append('mean_distance_from_jupiter_km')
            elif 'mean_distance_from_earth_km' in integrated.columns:
                sort_cols.append('mean_distance_from_earth_km')
            
            if sort_cols:
                integrated = integrated.sort_values(sort_cols)
            
            # Agregar metadatos
            integrated['data_source'] = 'integrated'
            integrated['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"Integración de lunas completada: {len(integrated)} registros")
            return integrated
        
        logger.warning("No hay datos de lunas para integrar")
        return pd.DataFrame()
    
    def integrate_small_bodies(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Integra datos de cuerpos pequeños (asteroides, cometas, NEOs)
        
        Args:
            datasets: Diccionario con datasets crudos
            
        Returns:
            Diccionario con DataFrames integrados por tipo
        """
        logger.info("Integrando datos de cuerpos pequeños...")
        
        integrated = {}
        
        # Asteroides
        asteroids = datasets.get('asteroids', pd.DataFrame())
        if not asteroids.empty:
            asteroids_clean, stats = validate_and_normalize_dataset(
                asteroids, 'Asteroides', 'asteroids'
            )
            self.validation_results.append(('Asteroides', stats))
            integrated['asteroids'] = asteroids_clean
        
        # Cometas
        comets = datasets.get('comets', pd.DataFrame())
        if not comets.empty:
            comets_clean, stats = validate_and_normalize_dataset(
                comets, 'Cometas', 'comets'
            )
            self.validation_results.append(('Cometas', stats))
            integrated['comets'] = comets_clean
        
        # NEOs
        neos = datasets.get('neos', pd.DataFrame())
        if not neos.empty:
            neos_clean, stats = validate_and_normalize_dataset(
                neos, 'NEOs', 'neos'
            )
            self.validation_results.append(('NEOs', stats))
            integrated['neos'] = neos_clean
        
        # Agregar metadatos a cada dataset
        for key, df in integrated.items():
            df['data_source'] = key
            df['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Integración de cuerpos pequeños completada: {len(integrated)} tipos")
        return integrated
    
    def _resolve_column_conflicts(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resuelve conflictos entre columnas duplicadas después de un merge
        
        Args:
            df: DataFrame con posibles columnas duplicadas
            
        Returns:
            DataFrame con conflictos resueltos
        """
        # Buscar pares de columnas con sufijos
        base_columns = set()
        for col in df.columns:
            if col.endswith('_opendata') or col.endswith('_facts'):
                base_name = col.rsplit('_', 1)[0]
                base_columns.add(base_name)
        
        # Resolver conflictos
        for base_col in base_columns:
            col1 = f"{base_col}_opendata"
            col2 = f"{base_col}_facts"
            
            if col1 in df.columns and col2 in df.columns:
                # Priorizar valor no nulo, preferir OpenData si ambos existen
                df[base_col] = df[col1].fillna(df[col2])
                
                # Eliminar columnas originales
                df = df.drop(columns=[col1, col2])
        
        return df
    
    def _save_raw_data(self, df: pd.DataFrame, filename: str):
        """
        Guarda datos crudos en el directorio raw
        
        Args:
            df: DataFrame a guardar
            filename: Nombre del archivo
        """
        if not df.empty:
            filepath = os.path.join(self.raw_dir, filename)
            df.to_csv(filepath, index=False)
            logger.info(f"Datos crudos guardados en {filepath}")
    
    def save_integrated_data(self, integrated_data: Dict[str, pd.DataFrame]):
        """
        Guarda todos los datasets integrados
        
        Args:
            integrated_data: Diccionario con datasets integrados
        """
        logger.info("Guardando datos integrados...")
        
        for name, df in integrated_data.items():
            if not df.empty:
                # CSV
                csv_path = os.path.join(self.output_dir, f"{name}_integrated.csv")
                df.to_csv(csv_path, index=False)
                logger.info(f"Guardado {name} en {csv_path}")
                
                # JSON (para web app)
                json_path = os.path.join(self.output_dir, f"{name}_integrated.json")
                df.to_json(json_path, orient='records', indent=2)
    
    def generate_summary_report(self, integrated_data: Dict[str, pd.DataFrame]):
        """
        Genera un reporte resumen de la integración
        
        Args:
            integrated_data: Diccionario con datasets integrados
        """
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE INTEGRACIÓN DE DATOS DEL SISTEMA SOLAR")
        report.append("=" * 80)
        report.append(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Resumen de datasets
        report.append("DATASETS INTEGRADOS:")
        report.append("-" * 40)
        
        total_records = 0
        for name, df in integrated_data.items():
            record_count = len(df) if not df.empty else 0
            total_records += record_count
            report.append(f"  {name}: {record_count} registros")
        
        report.append(f"\nTotal de registros: {total_records}")
        
        # Resumen de validación
        if self.validation_results:
            report.append("\nRESUMEN DE VALIDACIÓN:")
            report.append("-" * 40)
            validation_report = self.validator.generate_validation_report(self.validation_results)
            report.append(validation_report)
        
        # Estadísticas por tipo
        report.append("\nESTADÍSTICAS POR TIPO:")
        report.append("-" * 40)
        
        # Planetas
        if 'planets' in integrated_data and not integrated_data['planets'].empty:
            planets_df = integrated_data['planets']
            report.append(f"\nPlanetas ({len(planets_df)} total):")
            if 'mass_kg' in planets_df.columns:
                report.append(f"  - Masa promedio: {planets_df['mass_kg'].mean():.2e} kg")
            if 'radius_km' in planets_df.columns:
                report.append(f"  - Radio promedio: {planets_df['radius_km'].mean():.0f} km")
        
        # Lunas
        if 'moons' in integrated_data and not integrated_data['moons'].empty:
            moons_df = integrated_data['moons']
            report.append(f"\nLunas ({len(moons_df)} total):")
            if 'planet' in moons_df.columns:
                planet_counts = moons_df['planet'].value_counts()
                for planet, count in planet_counts.items():
                    report.append(f"  - {planet}: {count} lunas")
        
        # Asteroides
        if 'asteroids' in integrated_data and not integrated_data['asteroids'].empty:
            asteroids_df = integrated_data['asteroids']
            report.append(f"\nAsteroides ({len(asteroids_df)} total):")
            if 'class' in asteroids_df.columns:
                class_counts = asteroids_df['class'].value_counts().head(5)
                report.append("  Clases más comunes:")
                for cls, count in class_counts.items():
                    report.append(f"    - {cls}: {count}")
        
        # Guardar reporte
        report_path = os.path.join(self.output_dir, 'integration_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        logger.info(f"Reporte de integración guardado en {report_path}")
        
        # También imprimir en consola
        print('\n'.join(report))
    
    def run_full_integration(self):
        """
        Ejecuta el proceso completo de integración
        """
        logger.info("=" * 60)
        logger.info("INICIANDO INTEGRACIÓN COMPLETA DE DATOS")
        logger.info("=" * 60)
        
        # 1. Extraer todos los datos
        raw_datasets = self.extract_all_data()
        
        # 2. Integrar por tipo
        integrated_data = {}
        
        # Planetas
        planets_integrated = self.integrate_planet_data(raw_datasets)
        if not planets_integrated.empty:
            integrated_data['planets'] = planets_integrated
        
        # Lunas
        moons_integrated = self.integrate_moon_data(raw_datasets)
        if not moons_integrated.empty:
            integrated_data['moons'] = moons_integrated
        
        # Cuerpos pequeños
        small_bodies = self.integrate_small_bodies(raw_datasets)
        integrated_data.update(small_bodies)
        
        # 3. Guardar datos integrados
        self.save_integrated_data(integrated_data)
        
        # 4. Generar reporte
        self.generate_summary_report(integrated_data)
        
        logger.info("=" * 60)
        logger.info("INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)
        
        return integrated_data


def main():
    """
    Función principal para ejecutar la integración
    """
    # Crear integrador
    integrator = SolarSystemDataIntegrator()
    
    # Ejecutar integración completa
    integrated_data = integrator.run_full_integration()
    
    # Mostrar resumen
    print("\nResumen de datasets integrados:")
    for name, df in integrated_data.items():
        print(f"  - {name}: {len(df)} registros")
    
    print(f"\nDatos guardados en: {integrator.output_dir}")


if __name__ == "__main__":
    main()