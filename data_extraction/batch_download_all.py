#!/usr/bin/env python3
"""
Script principal para extracción masiva de datos BATCH
====================================================

Este script ejecuta la descarga de todos los datos estáticos/semi-estáticos
que serán procesados offline para análisis de minería de datos.

Estrategia:
- OpenData: Semanal (datos físicos estables)
- SBDB: Quincenal (elementos orbitales semi-estáticos)
- Genera archivos CSV para análisis posterior
- No incluye datos real-time (Horizons) ni híbridos (NEO)
"""

import sys
import os
from datetime import datetime
import json

# Importar todos los clientes BATCH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_clients.opendata_client import get_solar_system_client
from api_clients.sbdb_client import get_sbdb_client

def ensure_data_directories():
    """Crea las estructuras de directorios necesarias"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    directories = [
        "data/raw/api_data",
        "data/raw/neo_cache", 
        "data/processed",
        "data/results"
    ]
    
    for directory in directories:
        full_path = os.path.join(base_dir, directory)
        os.makedirs(full_path, exist_ok=True)
        print(f"Directorio verificado: {directory}")

def extract_all_batch_data():
    """
    Función principal que ejecuta toda la extracción BATCH
    """
    print("*** INICIANDO EXTRACCION MASIVA DE DATOS ***")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Estrategia: BATCH PROCESSING")
    print("Proposito: Datos para analisis de mineria offline")
    print("=" * 60)

    # Crear directorios necesarios
    print("\nVERIFICANDO ESTRUCTURA DE DIRECTORIOS")
    print("-" * 40)
    ensure_data_directories()

    results = {}

    # 1. OPENDATA - Datos físicos de 366 cuerpos
    print("\nEXTRAYENDO DATOS FISICOS (OpenData)")
    print("-" * 40)
    try:
        opendata_client = get_solar_system_client()

        # Verificar si necesita actualización
        cache_status = opendata_client.check_cache_status()
        print(f"Cache existe: {cache_status['cache_exists']}")
        print(f"Necesita actualización: {cache_status['needs_update']}")

        if cache_status['needs_update']:
            print("Descargando datos fisicos y guardando en CSV...")
            opendata_files = opendata_client.batch_download_all()
            results['opendata'] = {
                'status': 'success',
                'files': list(opendata_files.keys()),
                'action': 'downloaded'
            }
            print(f"OK - {len(opendata_files)} archivos OpenData generados")
        else:
            print("OK - Cache OpenData actualizado, omitiendo descarga")
            results['opendata'] = {
                'status': 'cached',
                'records': cache_status.get('total_records', 0),
                'action': 'skipped'
            }

    except Exception as e:
        print(f"ERROR en OpenData: {e}")
        results['opendata'] = {'status': 'error', 'error': str(e)}

    # 2. SBDB - Elementos orbitales de asteroides/cometas
    print("\nEXTRAYENDO ELEMENTOS ORBITALES (SBDB)")
    print("-" * 40)
    try:
        sbdb_client = get_sbdb_client()

        # Verificar si necesita actualización
        cache_status = sbdb_client.check_cache_status()
        print(f"Cache existe: {cache_status['cache_exists']}")
        print(f"Necesita actualización: {cache_status['needs_update']}")

        if cache_status['needs_update']:
            print("Descargando elementos orbitales y guardando en CSV...")
            sbdb_files = sbdb_client.batch_download_all()
            results['sbdb'] = {
                'status': 'success',
                'files': len(sbdb_files),
                'action': 'downloaded'
            }
            print(f"OK - {len(sbdb_files)} archivos SBDB generados")
        else:
            print("OK - Cache SBDB actualizado, omitiendo descarga")
            results['sbdb'] = {
                'status': 'cached',
                'records': cache_status.get('total_records', 0),
                'action': 'skipped'
            }

    except Exception as e:
        print(f"ERROR en SBDB: {e}")
        results['sbdb'] = {'status': 'error', 'error': str(e)}

    # 3. Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE EXTRACCION BATCH")
    print("=" * 60)

    for source, result in results.items():
        status = result['status']
        action = result.get('action', 'unknown')

        if status == 'success':
            print(f"OK - {source.upper()}: Datos descargados exitosamente")
            if source == 'opendata':
                if 'all_bodies' in result:
                    print(f"   - {result['all_bodies']} cuerpos totales")
                    print(f"   - {result['planets']} planetas")
                    print(f"   - {result['moons']} lunas")
                else:
                    print(f"   - {len(result.get('files', []))} archivos generados")
            elif source == 'sbdb':
                if 'categories' in result:
                    for cat, count in result['categories'].items():
                        if isinstance(count, int):
                            print(f"   - {cat}: {count} objetos")
                        else:
                            print(f"   - {cat}: {count}")
                else:
                    print(f"   - {result.get('files', 0)} archivos generados")
        elif status == 'cached':
            records = result.get('records', 0)
            print(f"CACHE - {source.upper()}: Cache actualizado ({records} registros)")
        else:
            print(f"ERROR - {source.upper()}: Error - {result.get('error', 'Desconocido')}")

    # 4. Próximos pasos
    success_count = sum(1 for r in results.values() if r['status'] == 'success')

    if success_count == len(results):
        print(f"\nEXTRACCION COMPLETADA EXITOSAMENTE")
        print("Los datos estan listos para analisis de mineria de datos")
        print("\nArchivos generados en:")
        print("  data/raw/api_data/opendata_*.csv")
        print("  data/raw/api_data/sbdb_*.csv")
        print("\nProximo paso: ejecutar analisis descriptivo y clustering")
        
        # Guardar resumen de la extracción
        summary_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "raw", "api_data", "batch_extraction_summary.json"
        )
        
        summary = {
            'extraction_date': datetime.now().isoformat(),
            'strategy': 'BATCH_PROCESSING',
            'results': results
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Resumen guardado en: batch_extraction_summary.json")
        return True
    else:
        print(f"\nEXTRACCION PARCIAL: {success_count}/{len(results)} fuentes exitosas")
        print("Revisar errores antes de proceder con analisis")
        return False

if __name__ == "__main__":
    success = extract_all_batch_data()
    exit(0 if success else 1)