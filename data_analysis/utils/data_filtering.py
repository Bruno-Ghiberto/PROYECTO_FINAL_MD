"""
Filtrado y Organización de Datos para Aplicación Web
===================================================

Este módulo procesa y organiza todos los datos del proyecto (raw + results)
para generar tablas limpias y optimizadas para la aplicación web.

FUNCIONES PRINCIPALES:
1. Eliminar duplicados entre fuentes de datos
2. Unificar esquemas y nomenclaturas 
3. Crear tablas especializadas por función (clustering, descriptivo, búsqueda)
4. Generar índices y metadatos para búsquedas rápidas
5. Exportar datos listos para Flask + SQLite

AUTOR: Claude Code AI Assistant
FECHA: Agosto 2025
"""

import pandas as pd
import numpy as np
import json
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import hashlib
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SolarSystemDataFilter:
    """
    Filtrador y organizador maestro de datos del sistema solar
    
    Procesa datos de múltiples fuentes y genera tablas limpias para web app:
    - Elimina duplicados inteligentemente
    - Unifica nomenclaturas y esquemas
    - Crea vistas especializadas por funcionalidad
    - Genera metadatos para búsquedas
    """
    
    def __init__(self, project_root: str = None):
        """
        Inicializa el filtrador de datos
        
        Args:
            project_root: Ruta raíz del proyecto (auto-detecta si None)
        """
        if project_root is None:
            # Auto-detectar directorio raíz del proyecto
            current_dir = Path(__file__).parent
            self.project_root = current_dir.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Directorios de datos
        self.raw_data_dir = self.project_root / "data" / "raw"
        self.results_dir = self.project_root / "data" / "results"
        self.output_dir = self.project_root / "data" / "web_ready"
        
        # Crear directorio de salida
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Metadatos de procesamiento
        self.processing_metadata = {
            'processing_date': datetime.now().isoformat(),
            'sources_processed': [],
            'duplicates_removed': 0,
            'records_unified': 0,
            'tables_created': [],
            'data_quality_issues': []
        }
        
        logger.info(f"Inicializado SolarSystemDataFilter en: {self.project_root}")
    
    def run_complete_filtering(self) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de filtrado y organización de datos
        
        Returns:
            Diccionario con resultados del procesamiento
        """
        logger.info("=== INICIANDO FILTRADO COMPLETO DE DATOS ===")
        
        try:
            # 1. Cargar y analizar todas las fuentes
            raw_sources = self._load_all_raw_sources()
            analysis_results = self._load_analysis_results()
            
            # 2. Identificar y eliminar duplicados
            unified_objects = self._unify_and_deduplicate(raw_sources)
            
            # 3. Enriquecer con resultados de análisis
            enriched_objects = self._enrich_with_analysis(unified_objects, analysis_results)
            
            # 4. Crear tablas especializadas para web app
            web_tables = self._create_web_tables(enriched_objects, analysis_results)
            
            # 5. Generar metadatos e índices de búsqueda
            search_metadata = self._create_search_metadata(web_tables)
            
            # 6. Exportar todos los datos organizados
            self._export_web_ready_data(web_tables, search_metadata)
            
            # 7. Generar reporte de procesamiento
            processing_report = self._generate_processing_report()
            
            logger.info("=== FILTRADO COMPLETO FINALIZADO ===")
            return processing_report
            
        except Exception as e:
            logger.error(f"Error en filtrado completo: {e}")
            raise
    
    def _load_all_raw_sources(self) -> Dict[str, pd.DataFrame]:
        """
        Carga todos los archivos de datos raw disponibles
        
        Returns:
            Diccionario con DataFrames por fuente
        """
        logger.info("Cargando fuentes de datos raw...")
        
        raw_sources = {}
        
        # API Data - OpenData
        opendata_files = {
            'opendata_all_bodies': 'api_data/opendata_all_bodies.csv',
            'opendata_planets': 'api_data/opendata_planets.csv', 
            'opendata_moons': 'api_data/opendata_moons.csv'
        }
        
        # API Data - SBDB
        sbdb_files = {
            'sbdb_neos': 'api_data/sbdb_neos.csv',
            'sbdb_main_belt': 'api_data/sbdb_main_belt.csv',
            'sbdb_trojans': 'api_data/sbdb_trojans.csv',
            'sbdb_comets_jfc': 'api_data/sbdb_comets_jfc.csv',
            'sbdb_comets_htc': 'api_data/sbdb_comets_htc.csv',
            'sbdb_phas': 'api_data/sbdb_phas.csv',
            'sbdb_centaurs': 'api_data/sbdb_centaurs.csv'
        }
        
        # Scraping Data
        scraping_files = {
            'wikipedia_objects': 'scraping data/wikipedia_objects_by_size.csv',
            'johnstons_data': 'scraping data/johnstons_physical_data.csv'
        }
        
        # Cargar todos los archivos disponibles
        all_files = {**opendata_files, **sbdb_files, **scraping_files}
        
        for source_name, relative_path in all_files.items():
            file_path = self.raw_data_dir / relative_path
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    raw_sources[source_name] = df
                    self.processing_metadata['sources_processed'].append(source_name)
                    logger.info(f"✅ Cargado {source_name}: {len(df)} registros")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {source_name}: {e}")
                    self.processing_metadata['data_quality_issues'].append(f"Error cargando {source_name}: {e}")
            else:
                logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
        
        logger.info(f"Total fuentes cargadas: {len(raw_sources)}")
        return raw_sources
    
    def _load_analysis_results(self) -> Dict[str, Any]:
        """
        Carga todos los resultados de análisis (clustering, descriptivo)
        
        Returns:
            Diccionario con resultados de análisis
        """
        logger.info("Cargando resultados de análisis...")
        
        analysis_results = {}
        
        # Clustering results
        clustering_files = {
            'kmeans_clusters': 'clustering_analysis/kmeans_clusters.csv',
            'dbscan_anomalies': 'clustering_analysis/dbscan_anomalies.csv',
            'cluster_interpretation': 'clustering_analysis/interpretacion_astronomica.csv'
        }
        
        # Descriptive analysis results
        descriptive_files = {
            'stats_by_type': 'descriptive_analysis/estadisticas_por_tipo.csv',
            'correlations': 'descriptive_analysis/matriz_correlaciones.csv',
            'type_comparison': 'descriptive_analysis/comparacion_tipos.csv'
        }
        
        all_analysis_files = {**clustering_files, **descriptive_files}
        
        for analysis_name, relative_path in all_analysis_files.items():
            file_path = self.results_dir / relative_path
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    analysis_results[analysis_name] = df
                    logger.info(f"✅ Cargado análisis {analysis_name}: {len(df)} registros")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando análisis {analysis_name}: {e}")
            else:
                logger.warning(f"⚠️ Archivo de análisis no encontrado: {file_path}")
        
        return analysis_results
    
    def _unify_and_deduplicate(self, raw_sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Unifica esquemas y elimina duplicados entre fuentes de datos
        
        Args:
            raw_sources: Diccionario con DataFrames de fuentes raw
            
        Returns:
            DataFrame unificado sin duplicados
        """
        logger.info("Unificando esquemas y eliminando duplicados...")
        
        unified_objects = []
        object_hashes = set()  # Para detectar duplicados
        
        # 1. Procesar OpenData (autoridad primaria para planetas/lunas)
        if 'opendata_all_bodies' in raw_sources:
            opendata_df = raw_sources['opendata_all_bodies'].copy()
            
            for _, row in opendata_df.iterrows():
                unified_obj = self._create_unified_object_from_opendata(row)
                obj_hash = self._calculate_object_hash(unified_obj)
                
                if obj_hash not in object_hashes:
                    unified_objects.append(unified_obj)
                    object_hashes.add(obj_hash)
                else:
                    self.processing_metadata['duplicates_removed'] += 1
        
        # 2. Procesar SBDB (autoridad primaria para asteroides/cometas)
        sbdb_sources = [k for k in raw_sources.keys() if k.startswith('sbdb_')]
        
        for sbdb_source in sbdb_sources:
            sbdb_df = raw_sources[sbdb_source].copy()
            
            for _, row in sbdb_df.iterrows():
                unified_obj = self._create_unified_object_from_sbdb(row, sbdb_source)
                obj_hash = self._calculate_object_hash(unified_obj)
                
                if obj_hash not in object_hashes:
                    unified_objects.append(unified_obj)
                    object_hashes.add(obj_hash)
                else:
                    self.processing_metadata['duplicates_removed'] += 1
        
        # 3. Procesar scraping data (datos complementarios)
        scraping_sources = [k for k in raw_sources.keys() if 'wikipedia' in k or 'johnstons' in k]
        
        for scraping_source in scraping_sources:
            try:
                scraping_df = raw_sources[scraping_source].copy()
                # Solo agregar si no existe ya (scraping es secundario)
                for _, row in scraping_df.iterrows():
                    unified_obj = self._create_unified_object_from_scraping(row, scraping_source)
                    obj_hash = self._calculate_object_hash(unified_obj)
                    
                    if obj_hash not in object_hashes:
                        unified_objects.append(unified_obj)
                        object_hashes.add(obj_hash)
                    else:
                        # Enriquecer objeto existente con datos de scraping
                        self._enrich_existing_object_with_scraping(unified_objects, unified_obj)
                        self.processing_metadata['duplicates_removed'] += 1
            except Exception as e:
                logger.warning(f"Error procesando scraping {scraping_source}: {e}")
        
        # Convertir a DataFrame
        unified_df = pd.DataFrame(unified_objects)
        
        self.processing_metadata['records_unified'] = len(unified_df)
        logger.info(f"✅ Objetos unificados: {len(unified_df)}")
        logger.info(f"✅ Duplicados eliminados: {self.processing_metadata['duplicates_removed']}")
        
        return unified_df
    
    def _create_unified_object_from_opendata(self, row: pd.Series) -> Dict[str, Any]:
        """
        Crea objeto unificado desde datos OpenData
        
        Args:
            row: Fila de DataFrame OpenData
            
        Returns:
            Diccionario con objeto unificado
        """
        return {
            # Identificación
            'id': row.get('id', ''),
            'name': row.get('englishName', row.get('name', '')),
            'alternative_names': [row.get('name', ''), row.get('englishName', '')],
            
            # Clasificación
            'object_type': row.get('bodyType', 'Unknown'),
            'is_planet': row.get('isPlanet', False),
            'data_source': 'OpenData',
            'data_quality': 'Primary',
            
            # Parámetros físicos
            'mean_radius_km': self._safe_float(row.get('meanRadius')),
            'mass_kg': self._safe_float(row.get('mass_kg')),
            'density_g_cm3': self._safe_float(row.get('density')),
            'gravity_m_s2': self._safe_float(row.get('gravity')),
            'escape_velocity_km_s': self._safe_float(row.get('escape')),
            'avg_temperature_k': self._safe_float(row.get('avgTemp')),
            
            # Parámetros orbitales (si disponibles)
            'semimajor_axis_km': self._safe_float(row.get('semimajorAxis')),
            'perihelion_km': self._safe_float(row.get('perihelion')),
            'aphelion_km': self._safe_float(row.get('aphelion')),
            'eccentricity': self._safe_float(row.get('eccentricity')),
            'inclination_deg': self._safe_float(row.get('inclination')),
            
            # Información descubrimiento
            'discovered_by': row.get('discoveredBy', ''),
            'discovery_date': row.get('discoveryDate', ''),
            
            # Metadatos
            'has_image': False,  # Se actualizará más tarde
            'clustering_enabled': False,  # Se actualizará con análisis
            'last_updated': datetime.now().isoformat()
        }
    
    def _create_unified_object_from_sbdb(self, row: pd.Series, source: str) -> Dict[str, Any]:
        """
        Crea objeto unificado desde datos SBDB
        
        Args:
            row: Fila de DataFrame SBDB
            source: Nombre de la fuente SBDB
            
        Returns:
            Diccionario con objeto unificado
        """
        # Mapear categoría SBDB a tipo de objeto
        category_mapping = {
            'sbdb_neos': 'NEO',
            'sbdb_main_belt': 'Asteroid',
            'sbdb_trojans': 'Trojan_Asteroid',
            'sbdb_comets_jfc': 'Comet',
            'sbdb_comets_htc': 'Comet', 
            'sbdb_phas': 'PHA',
            'sbdb_centaurs': 'Centaur'
        }
        
        return {
            # Identificación
            'id': str(row.get('spkid', '')),
            'name': row.get('full_name', '').strip(),
            'alternative_names': [row.get('pdes', ''), row.get('full_name', '')],
            
            # Clasificación
            'object_type': category_mapping.get(source, 'Small_Body'),
            'sbdb_class': row.get('class', ''),
            'is_neo': row.get('neo', 'N') == 'Y',
            'is_pha': row.get('pha', 'N') == 'Y',
            'data_source': 'SBDB',
            'data_quality': 'Primary',
            
            # Parámetros físicos (limitados en SBDB)
            'diameter_km': self._safe_float(row.get('diameter')),
            'absolute_magnitude_H': self._safe_float(row.get('H')),
            'albedo': self._safe_float(row.get('albedo')),
            'rotation_period_h': self._safe_float(row.get('rot_per')),
            
            # Parámetros orbitales (fuertes en SBDB)
            'semimajor_axis_au': self._safe_float(row.get('a')),
            'eccentricity': self._safe_float(row.get('e')),
            'inclination_deg': self._safe_float(row.get('i')),
            'orbital_period_days': self._safe_float(row.get('per')),
            'perihelion_distance_au': self._safe_float(row.get('q')),
            'aphelion_distance_au': self._safe_float(row.get('ad')),
            'argument_periapsis_deg': self._safe_float(row.get('w')),
            'longitude_ascending_node_deg': self._safe_float(row.get('om')),
            'mean_anomaly_deg': self._safe_float(row.get('ma')),
            
            # Metadatos
            'clustering_enabled': True,  # SBDB es ideal para clustering
            'has_orbital_data': True,
            'last_updated': datetime.now().isoformat()
        }
    
    def _create_unified_object_from_scraping(self, row: pd.Series, source: str) -> Dict[str, Any]:
        """
        Crea objeto unificado desde datos de scraping
        
        Args:
            row: Fila de DataFrame scraping
            source: Nombre de la fuente scraping
            
        Returns:
            Diccionario con objeto unificado
        """
        # Estructura básica para datos de scraping (complementarios)
        unified_obj = {
            'data_source': f'Scraping_{source}',
            'data_quality': 'Secondary',
            'last_updated': datetime.now().isoformat()
        }
        
        # Procesar según fuente específica
        if 'wikipedia' in source:
            unified_obj.update({
                'id': f"wiki_{row.get('Object', row.get('Name', ''))}", 
                'name': row.get('Object', row.get('Name', '')),
                'object_type': 'Wikipedia_Object',
                'diameter_km': self._safe_float(row.get('Diameter', row.get('Size'))),
                'has_image': True  # Wikipedia suele tener imágenes
            })
        
        elif 'johnstons' in source:
            unified_obj.update({
                'id': f"johnston_{row.get('Name', '')}",
                'name': row.get('Name', ''),
                'object_type': 'Physical_Data',
                'diameter_km': self._safe_float(row.get('Diameter')),
                'mass_kg': self._safe_float(row.get('Mass')),
                'density_g_cm3': self._safe_float(row.get('Density'))
            })
        
        return unified_obj
    
    def _enrich_with_analysis(self, unified_objects: pd.DataFrame, analysis_results: Dict[str, Any]) -> pd.DataFrame:
        """
        Enriquece objetos unificados con resultados de análisis ML
        
        Args:
            unified_objects: DataFrame con objetos unificados
            analysis_results: Resultados de análisis ML
            
        Returns:
            DataFrame enriquecido con análisis
        """
        logger.info("Enriqueciendo objetos con resultados de análisis...")
        
        enriched_df = unified_objects.copy()
        
        # Enriquecer con resultados de clustering
        if 'kmeans_clusters' in analysis_results:
            cluster_df = analysis_results['kmeans_clusters']
            
            # Crear mapping por nombre (más robusto que por ID)
            cluster_mapping = {}
            for _, row in cluster_df.iterrows():
                # Usar multiple identifiers para matching
                identifiers = [
                    str(row.get('spkid', '')),
                    row.get('full_name', '').strip(),
                    row.get('pdes', '').strip()
                ]
                
                cluster_info = {
                    'kmeans_cluster': int(row.get('kmeans_cluster', -1)),
                    'pca_1': float(row.get('pca_1', 0)),
                    'pca_2': float(row.get('pca_2', 0)),
                    'clustering_category': row.get('category', ''),
                    'has_clustering': True
                }
                
                for identifier in identifiers:
                    if identifier and identifier.strip():
                        cluster_mapping[identifier.strip()] = cluster_info
            
            # Aplicar clustering a objetos unificados
            for idx, row in enriched_df.iterrows():
                object_identifiers = [
                    str(row.get('id', '')),
                    str(row.get('name', '')).strip()
                ]
                alt_names = row.get('alternative_names', [])
                if isinstance(alt_names, list):
                    object_identifiers.extend(alt_names)
                elif alt_names and not pd.isna(alt_names):
                    object_identifiers.append(str(alt_names))
                
                for identifier in object_identifiers:
                    if identifier and str(identifier).strip() in cluster_mapping:
                        cluster_info = cluster_mapping[str(identifier).strip()]
                        for key, value in cluster_info.items():
                            enriched_df.loc[idx, key] = value
                        break
        
        # Enriquecer con anomalías DBSCAN
        if 'dbscan_anomalies' in analysis_results:
            anomaly_df = analysis_results['dbscan_anomalies']
            
            # Crear conjunto de parámetros orbitales anómalos para matching
            anomaly_signatures = set()
            
            for _, row in anomaly_df.iterrows():
                # Usar parámetros orbitales únicos como firma
                signature = f"{self._safe_float(row.get('a', 0)):.3f}_{self._safe_float(row.get('e', 0)):.3f}_{self._safe_float(row.get('i', 0)):.1f}"
                anomaly_signatures.add(signature)
            
            # Marcar anomalías usando matching orbital
            anomalies_found = 0
            for idx, row in enriched_df.iterrows():
                # Crear firma orbital del objeto actual
                object_signature = f"{self._safe_float(row.get('semimajor_axis_au', 0)) or 0:.3f}_{self._safe_float(row.get('eccentricity', 0)) or 0:.3f}_{self._safe_float(row.get('inclination_deg', 0)) or 0:.1f}"
                
                # Verificar si coincide con alguna anomalía
                is_anomaly = object_signature in anomaly_signatures
                
                if is_anomaly:
                    anomalies_found += 1
                
                enriched_df.loc[idx, 'is_anomaly'] = is_anomaly
                enriched_df.loc[idx, 'anomaly_type'] = 'DBSCAN_Outlier' if is_anomaly else None
            
            logger.info(f"✅ Anomalías DBSCAN detectadas: {anomalies_found}/{len(anomaly_df)}")
            
            # Si no se encontraron anomalías, usar método alternativo
            if anomalies_found == 0:
                logger.warning("⚠️ No se pudieron mapear anomalías por parámetros orbitales")
                logger.info("💡 Marcando objetos con dbscan_cluster = -1 como anomalías generales")
                
                # Marcar como anomalías objetos con características extremas
                for idx, row in enriched_df.iterrows():
                    is_extreme_anomaly = (
                        (self._safe_float(row.get('eccentricity', 0)) or 0) > 0.8 or  # Muy elíptico
                        (self._safe_float(row.get('inclination_deg', 0)) or 0) > 150 or  # Retrógrado extremo
                        (self._safe_float(row.get('perihelion_distance_au', 0)) or 10) < 0.1  # Sun grazer
                    )
                    
                    if is_extreme_anomaly:
                        enriched_df.loc[idx, 'is_anomaly'] = True
                        enriched_df.loc[idx, 'anomaly_type'] = 'Extreme_Orbital_Parameters'
                        anomalies_found += 1
                
                logger.info(f"✅ Anomalías por parámetros extremos: {anomalies_found}")
        
        logger.info(f"✅ Objetos enriquecidos con análisis: {len(enriched_df)}")
        return enriched_df
    
    def _create_web_tables(self, enriched_objects: pd.DataFrame, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea tablas especializadas para la aplicación web
        
        Args:
            enriched_objects: DataFrame con objetos enriquecidos
            analysis_results: Resultados de análisis
            
        Returns:
            Diccionario con tablas especializadas
        """
        logger.info("Creando tablas especializadas para web app...")
        
        web_tables = {}
        
        # 1. TABLA PRINCIPAL: Objetos para búsqueda general
        main_objects = enriched_objects.copy()
        
        # Limpiar y optimizar para búsqueda
        main_objects = main_objects.dropna(subset=['name'])
        main_objects = main_objects[main_objects['name'].str.strip() != '']
        
        # Añadir campos calculados para UI
        main_objects['display_name'] = main_objects['name'].str.title()
        main_objects['search_keywords'] = main_objects.apply(self._generate_search_keywords, axis=1)
        main_objects['ui_category'] = main_objects['object_type'].map(self._map_to_ui_category)
        
        web_tables['main_objects'] = main_objects
        
        # 2. TABLA CLUSTERING: Solo objetos con clustering válido
        if 'has_clustering' in main_objects.columns:
            clustering_objects = main_objects[main_objects['has_clustering'] == True].copy()
            
            # Añadir interpretación de clusters
            clustering_objects['cluster_description'] = clustering_objects['kmeans_cluster'].map(
                self._get_cluster_description
            )
            
            web_tables['clustering_objects'] = clustering_objects
        
        # 3. TABLA ANOMALÍAS: Solo objetos anómalos
        if 'is_anomaly' in main_objects.columns:
            anomaly_objects = main_objects[main_objects['is_anomaly'] == True].copy()
            
            # Añadir scoring de rareza
            anomaly_objects['rarity_score'] = anomaly_objects.apply(self._calculate_rarity_score, axis=1)
            
            web_tables['anomaly_objects'] = anomaly_objects
        
        # 4. TABLA ESTADÍSTICAS: Agregaciones para dashboard
        stats_table = self._create_dashboard_stats(main_objects, analysis_results)
        web_tables['dashboard_stats'] = stats_table
        
        # 5. TABLA COMPARACIÓN: Objetos principales para comparador
        comparison_objects = main_objects[
            (main_objects['object_type'].isin(['Planet', 'Asteroid', 'Comet', 'Moon'])) &
            (main_objects['data_quality'] == 'Primary')
        ].copy()
        
        web_tables['comparison_objects'] = comparison_objects
        
        # 6. TABLA IMÁGENES: Mapeo de objetos a imágenes disponibles
        image_mapping = self._create_image_mapping()
        web_tables['image_mapping'] = image_mapping
        
        self.processing_metadata['tables_created'] = list(web_tables.keys())
        logger.info(f"✅ Tablas web creadas: {list(web_tables.keys())}")
        
        return web_tables
    
    def _create_search_metadata(self, web_tables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea metadatos optimizados para búsquedas rápidas
        
        Args:
            web_tables: Tablas especializadas para web
            
        Returns:
            Diccionario con metadatos de búsqueda
        """
        logger.info("Creando metadatos de búsqueda...")
        
        search_metadata = {}
        
        if 'main_objects' in web_tables:
            main_df = web_tables['main_objects']
            
            # 1. Índice de nombres para autocompletado
            name_index = []
            for _, row in main_df.iterrows():
                name_entry = {
                    'id': row.get('id', ''),
                    'display_name': row.get('display_name', ''),
                    'object_type': row.get('ui_category', ''),
                    'keywords': row.get('search_keywords', '').split(',')
                }
                name_index.append(name_entry)
            
            search_metadata['name_index'] = name_index
            
            # 2. Estadísticas por categoría (CORREGIDO para manejar NaN)
            category_stats = {}
            for category in main_df['ui_category'].unique():
                if pd.isna(category):
                    continue
                    
                category_data = main_df[main_df['ui_category'] == category]
                
                # Calcular estadísticas seguras
                radius_values = category_data['mean_radius_km'].dropna()
                mass_values = category_data['mass_kg'].dropna()
                
                category_stats[category] = {
                    'id': len(category_data),  # count total
                    'mean_radius_km': float(radius_values.mean()) if len(radius_values) > 0 else None,
                    'mass_kg': float(mass_values.mean()) if len(mass_values) > 0 else None
                }
            
            search_metadata['category_stats'] = category_stats
            
            # 3. Rangos de valores para filtros
            numeric_columns = ['mean_radius_km', 'mass_kg', 'density_g_cm3', 'semimajor_axis_au']
            value_ranges = {}
            
            for col in numeric_columns:
                if col in main_df.columns:
                    valid_values = main_df[col].dropna()
                    if len(valid_values) > 0:
                        value_ranges[col] = {
                            'min': float(valid_values.min()),
                            'max': float(valid_values.max()),
                            'median': float(valid_values.median())
                        }
            
            search_metadata['value_ranges'] = value_ranges
        
        logger.info("✅ Metadatos de búsqueda creados")
        return search_metadata
    
    def _export_web_ready_data(self, web_tables: Dict[str, Any], search_metadata: Dict[str, Any]) -> None:
        """
        Exporta todas las tablas y metadatos en formatos optimizados para web
        
        Args:
            web_tables: Tablas especializadas
            search_metadata: Metadatos de búsqueda
        """
        import numpy as np
        
        logger.info("Exportando datos listos para web...")
        
        # Función para limpiar NaN antes de JSON
        def clean_for_json(obj):
            """Convierte valores NaN a None para JSON válido"""
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif pd.isna(obj):
                return None
            elif isinstance(obj, float) and (np.isnan(obj) or str(obj).lower() in ['nan', 'inf', '-inf']):
                return None
            elif isinstance(obj, str) and obj.lower() in ['nan', 'none', 'null']:
                return None
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return float(obj)
            else:
                return obj
        
        # Exportar tablas principales como CSV
        for table_name, table_data in web_tables.items():
            if isinstance(table_data, pd.DataFrame):
                output_path = self.output_dir / f"{table_name}.csv"
                table_data.to_csv(output_path, index=False)
                logger.info(f"✅ Exportado {table_name}: {len(table_data)} registros")
            else:
                # Datos no-DataFrame (stats, etc.)
                output_path = self.output_dir / f"{table_name}.json"
                cleaned_data = clean_for_json(table_data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Exportado {table_name} como JSON")
        
        # Exportar metadatos de búsqueda (LIMPIADO)
        metadata_path = self.output_dir / "search_metadata.json"
        cleaned_metadata = clean_for_json(search_metadata)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_metadata, f, indent=2, ensure_ascii=False)
        
        # Exportar resumen de procesamiento
        processing_path = self.output_dir / "processing_summary.json" 
        cleaned_processing = clean_for_json(self.processing_metadata)
        with open(processing_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_processing, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Datos exportados en: {self.output_dir}")
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Convierte valor a float de forma segura"""
        try:
            if pd.isna(value) or value == '' or value == '{}':
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _calculate_object_hash(self, obj: Dict[str, Any]) -> str:
        """Calcula hash único para detectar duplicados"""
        # Usar nombre + tipo como identificador único
        identifier = f"{obj.get('name', '')}{obj.get('object_type', '')}"
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def _enrich_existing_object_with_scraping(self, unified_objects: List[Dict], scraping_obj: Dict) -> None:
        """Enriquece objeto existente con datos de scraping"""
        # Buscar objeto existente por nombre similar
        scraping_name = scraping_obj.get('name', '').lower()
        
        for obj in unified_objects:
            existing_name = obj.get('name', '').lower()
            if scraping_name in existing_name or existing_name in scraping_name:
                # Enriquecer con datos adicionales de scraping
                if scraping_obj.get('has_image'):
                    obj['has_image'] = True
                if scraping_obj.get('diameter_km') and not obj.get('mean_radius_km'):
                    obj['mean_radius_km'] = scraping_obj['diameter_km'] / 2
                break
    
    def _generate_search_keywords(self, row: pd.Series) -> str:
        """Genera keywords para búsqueda de un objeto"""
        keywords = []
        
        # Nombre y aliases
        if row.get('name'):
            keywords.append(row['name'].lower())
        
        if row.get('alternative_names'):
            alt_names = row['alternative_names']
            if isinstance(alt_names, list):
                for alt_name in alt_names:
                    if alt_name and str(alt_name).strip():
                        keywords.append(str(alt_name).lower().strip())
            elif alt_names and not pd.isna(alt_names):
                keywords.append(str(alt_names).lower().strip())
        
        # Tipo y categoría
        if row.get('object_type'):
            keywords.append(row['object_type'].lower())
        
        if row.get('ui_category'):
            keywords.append(row['ui_category'].lower())
        
        # Características especiales
        if row.get('is_neo'):
            keywords.extend(['neo', 'near earth'])
        
        if row.get('is_pha'):
            keywords.extend(['pha', 'potentially hazardous'])
        
        if row.get('is_anomaly'):
            keywords.extend(['anomaly', 'unusual', 'rare'])
        
        return ','.join(set(keywords))
    
    def _map_to_ui_category(self, object_type: str) -> str:
        """Mapea tipo de objeto a categoría UI amigable"""
        ui_mapping = {
            'Planet': 'Planetas',
            'Moon': 'Lunas',
            'Asteroid': 'Asteroides', 
            'NEO': 'Objetos Cercanos',
            'PHA': 'Asteroides Peligrosos',
            'Trojan_Asteroid': 'Asteroides Troyanos',
            'Centaur': 'Centauros',
            'Comet': 'Cometas',
            'Dwarf_Planet': 'Planetas Enanos'
        }
        
        return ui_mapping.get(object_type, 'Otros Objetos')
    
    def _get_cluster_description(self, cluster_id: int) -> str:
        """Retorna descripción amigable del cluster"""
        cluster_descriptions = {
            0: "Población Principal - Dinámicamente estable",
            1: "Población Exterior - Dinámicamente excitada", 
            -1: "Anomalía - Características únicas"
        }
        
        return cluster_descriptions.get(cluster_id, f"Cluster {cluster_id}")
    
    def _calculate_rarity_score(self, row: pd.Series) -> float:
        """Calcula score de rareza para objetos anómalos"""
        score = 0.0
        
        # Factores de rareza
        if row.get('inclination_deg', 0) > 90:  # Retrógrado
            score += 0.4
        
        if row.get('eccentricity', 0) > 0.7:  # Muy elíptico
            score += 0.3
        
        if row.get('perihelion_distance_au', 10) < 0.1:  # Sun grazer
            score += 0.3
        
        return min(score, 1.0)  # Max score = 1.0
    
    def _create_dashboard_stats(self, main_objects: pd.DataFrame, analysis_results: Dict) -> Dict[str, Any]:
        """Crea estadísticas agregadas para dashboard"""
        stats = {
            'total_objects': len(main_objects),
            'by_category': main_objects['ui_category'].value_counts().to_dict() if 'ui_category' in main_objects.columns else {},
            'data_sources': main_objects['data_source'].value_counts().to_dict() if 'data_source' in main_objects.columns else {},
            'has_clustering': len(main_objects[main_objects['has_clustering'] == True]) if 'has_clustering' in main_objects.columns else 0,
            'anomalies_detected': len(main_objects[main_objects['is_anomaly'] == True]) if 'is_anomaly' in main_objects.columns else 0,
            'last_updated': datetime.now().isoformat()
        }
        
        return stats
    
    def _create_image_mapping(self) -> Dict[str, str]:
        """Crea mapeo de objetos a imágenes disponibles"""
        image_mapping = {}
        
        # Buscar imágenes en directorio wikipedia_images
        images_dir = self.raw_data_dir / "wikipedia_images"
        
        if images_dir.exists():
            for image_file in images_dir.glob("*.png"):
                # Extraer nombre del objeto desde nombre del archivo
                object_name = self._extract_object_name_from_image(image_file.name)
                if object_name:
                    image_mapping[object_name.lower()] = f"wikipedia_images/{image_file.name}"
        
        return image_mapping
    
    def _extract_object_name_from_image(self, filename: str) -> Optional[str]:
        """Extrae nombre del objeto desde nombre de archivo de imagen"""
        # Lógica para extraer nombres de objetos de nombres de archivo
        # Ej: "120px-Jupiter_OPAL_2024.png" -> "Jupiter"
        
        # Remover prefijos comunes
        clean_name = filename.replace('120px-', '').replace('60px-', '').replace('page1-50px-', '')
        
        # Remover extensión
        clean_name = clean_name.split('.')[0]
        
        # Extraer primera palabra (usualmente el nombre del objeto)
        object_name = clean_name.split('_')[0].split('-')[0]
        
        # Capitalizar apropiadamente
        return object_name.title() if object_name else None
    
    def _generate_processing_report(self) -> Dict[str, Any]:
        """Genera reporte final del procesamiento"""
        report = {
            'status': 'completed',
            'processing_metadata': self.processing_metadata,
            'output_directory': str(self.output_dir),
            'files_created': list(self.output_dir.glob("*")),
            'recommendations': [
                "Usar main_objects.csv como tabla principal para Flask",
                "Implementar búsqueda usando search_metadata.json",
                "Cargar clustering_objects.csv para visualizaciones interactivas",
                "Usar dashboard_stats.json para métricas del dashboard"
            ]
        }
        
        logger.info("✅ Reporte de procesamiento generado")
        return report


def main():
    """
    Función principal para ejecutar el filtrado completo
    """
    print("=== FILTRADO Y ORGANIZACIÓN DE DATOS DEL SISTEMA SOLAR ===")
    
    try:
        # Crear filtrador
        filter_processor = SolarSystemDataFilter()
        
        # Ejecutar filtrado completo
        report = filter_processor.run_complete_filtering()
        
        # Mostrar resultados
        print("\nPROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print(f"Total objetos procesados: {report['processing_metadata']['records_unified']}")
        print(f"Duplicados eliminados: {report['processing_metadata']['duplicates_removed']}")
        print(f"Tablas creadas: {len(report['processing_metadata']['tables_created'])}")
        print(f"Archivos exportados en: {report['output_directory']}")
        
        print("\nRECOMENDACIONES:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
            
        return True
        
    except Exception as e:
        print(f"ERROR EN PROCESAMIENTO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\nDatos listos para aplicacion web!")
    else:
        print("\nError en procesamiento. Revisar logs.")