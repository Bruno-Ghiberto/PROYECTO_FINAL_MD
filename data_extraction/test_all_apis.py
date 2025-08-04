"""
Script de prueba para todos los clientes API
===========================================

Este script prueba la conectividad y funcionalidad básica de todos los clientes API
implementados siguiendo la estrategia híbrida:

- BATCH: OpenData, SBDB (descarga masiva para análisis)
- REAL-TIME: Horizons (posiciones actuales)  
- HÍBRIDO: NEO (cache temporal para performance)

Uso: python test_all_apis.py
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar ruta de módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar todos los clientes
from api_clients.opendata_client import get_solar_system_client
from api_clients.sbdb_client import get_sbdb_client  
from api_clients.horizons_client import get_horizons_client
from api_clients.neo_client import get_neo_client


def test_opendata_client():
    """Prueba el cliente OpenData (estrategia BATCH)"""
    print("\n" + "="*60)
    print("🌍 TESTING OPENDATA CLIENT (BATCH)")
    print("="*60)
    
    try:
        client = get_solar_system_client()
        
        # Verificar estado del cache
        cache_status = client.check_cache_status()
        print(f"✓ Cliente creado exitosamente")
        print(f"  Cache existe: {cache_status['cache_exists']}")
        print(f"  Necesita actualización: {cache_status['needs_update']}")
        
        if cache_status['needs_update']:
            print("  🔄 Iniciando descarga masiva...")
            files = client.batch_download_all()
            print(f"  ✓ {len(files)} archivos generados: {list(files.keys())}")
        else:
            print(f"  ✓ Cache actualizado - {cache_status.get('total_records', 0)} registros")
        
        # Prueba individual: buscar la Tierra
        earth = client.get_by_name("Earth")
        if earth:
            mass = earth.get('mass', {})
            if isinstance(mass, dict):
                mass_val = mass.get('massValue', 'N/A')
            else:
                mass_val = mass
            print(f"  🌍 Tierra encontrada - Masa: {mass_val}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error en OpenData: {e}")
        return False


def test_sbdb_client():
    """Prueba el cliente SBDB (estrategia BATCH)"""
    print("\n" + "="*60)
    print("🌌 TESTING SBDB CLIENT (BATCH)")
    print("="*60)
    
    try:
        client = get_sbdb_client()
        
        # Verificar estado del cache
        cache_status = client.check_cache_status()
        print(f"✓ Cliente creado exitosamente")
        print(f"  Cache existe: {cache_status['cache_exists']}")
        print(f"  Necesita actualización: {cache_status['needs_update']}")
        
        if cache_status['needs_update']:
            print("  🔄 Iniciando descarga masiva...")
            files = client.batch_download_all()
            print(f"  ✓ {len(files)} archivos generados")
            for file_type in files.keys():
                if file_type != 'metadata':
                    print(f"    - {file_type}")
        else:
            print(f"  ✓ Cache actualizado - {cache_status.get('total_records', 0)} registros")
            print("  📋 Archivos disponibles:")
            for file_type, info in cache_status['files'].items():
                if info['exists']:
                    print(f"    - {file_type}: {info['records']} registros")
        
        # Prueba individual: algunos asteroides del cinturón principal
        print("  🪨 Probando consulta individual de asteroides MBA...")
        mba_sample = client.get_asteroids(asteroid_class='MBA', limit=5)
        if not mba_sample.empty:
            print(f"    ✓ {len(mba_sample)} asteroides MBA obtenidos")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error en SBDB: {e}")
        return False


def test_horizons_client():
    """Prueba el cliente Horizons (estrategia REAL-TIME)"""
    print("\n" + "="*60)
    print("🚀 TESTING HORIZONS CLIENT (REAL-TIME)")
    print("="*60)
    
    try:
        client = get_horizons_client()
        print(f"✓ Cliente creado exitosamente")
        
        # Prueba 1: Posiciones actuales de planetas interiores
        print("  🌍 Probando posiciones actuales de planetas interiores...")
        inner_planets = client.get_current_positions(['mercury', 'venus', 'earth', 'mars'])
        
        success_count = 0
        for planet, data in inner_planets.items():
            if data.get('status') == 'success':
                success_count += 1
                print(f"    ✓ {planet.capitalize()}: {data.get('data_points', 0)} puntos")
            else:
                print(f"    ⚠ {planet.capitalize()}: {data.get('error', 'Error')}")
        
        print(f"  📊 {success_count}/{len(inner_planets)} planetas procesados exitosamente")
        
        # Prueba 2: Datos orbitales de Júpiter
        print("  🪐 Probando datos orbitales de Júpiter (7 días)...")
        jupiter_orbit = client.get_orbital_period_data('jupiter', days_ahead=7)
        
        if jupiter_orbit.get('status') == 'success':
            print(f"    ✓ {jupiter_orbit['data_points']} puntos orbitales obtenidos")
        else:
            print(f"    ⚠ Error: {jupiter_orbit.get('error', 'Desconocido')}")
        
        return success_count > 0  # Al menos un planeta debe funcionar
        
    except Exception as e:
        print(f"  ❌ Error en Horizons: {e}")
        return False


def test_neo_client():
    """Prueba el cliente NEO (estrategia HÍBRIDA)"""
    print("\n" + "="*60)
    print("🌍 TESTING NEO CLIENT (HÍBRIDO)")
    print("="*60)
    
    try:
        client = get_neo_client()
        print(f"✓ Cliente creado exitosamente")
        
        # Verificar estado del cache
        cache_status = client.get_cache_status()
        print(f"  📦 Cache: {len(cache_status['files'])} archivos")
        print(f"  ⏱️ Duración del cache: {cache_status['cache_duration_hours']} horas")
        
        # Prueba 1: NEOs de la semana actual (híbrido)
        print("  🌍 Probando NEOs semana actual (estrategia híbrida)...")
        current_week = client.get_current_week_neos_cached(use_cache=True)
        
        if 'error' not in current_week:
            print(f"    ✓ Fuente: {current_week['data_source']}")
            print(f"    📊 {current_week.get('total_approaches', 0)} aproximaciones")
            
            if current_week['data_source'] == 'cache':
                cache_age = current_week.get('cache_age_hours', 0)
                print(f"    ⏰ Cache: {cache_age:.1f} horas de antigüedad")
        else:
            print(f"    ⚠ Error: {current_week['error']}")
        
        # Prueba 2: Asteroides potencialmente peligrosos
        print("  ⚠️ Probando asteroides potencialmente peligrosos...")
        phas = client.get_potentially_hazardous_cached()
        
        if 'error' not in phas:
            print(f"    ✓ Fuente: {phas['data_source']}")
            print(f"    ⚠️ PHAs: {phas.get('total_phas', 0)}")
            print(f"    📊 Total NEOs: {phas.get('total_all_neos', 0)}")
            
            if phas.get('total_phas', 0) > 0:
                percentage = phas.get('percentage_hazardous', 0)
                print(f"    📈 Porcentaje peligroso: {percentage:.1f}%")
        else:
            print(f"    ⚠ Error: {phas['error']}")
        
        # Prueba 3: Rango específico
        print("  📅 Probando rango específico (próximos 3 días)...")
        today = datetime.now().date()
        three_days = today + timedelta(days=3)
        
        range_data = client.get_neos_for_date_range(
            start_date=today.strftime('%Y-%m-%d'),
            end_date=three_days.strftime('%Y-%m-%d'),
            use_cache=True
        )
        
        if 'error' not in range_data:
            print(f"    ✓ Fuente: {range_data['data_source']}")
            print(f"    📊 {range_data.get('total_approaches', 0)} aproximaciones en 3 días")
        else:
            print(f"    ⚠ Error: {range_data['error']}")
        
        return 'total_approaches' in current_week or 'total_phas' in phas
        
    except Exception as e:
        print(f"  ❌ Error en NEO: {e}")
        if "DEMO_KEY" in str(e):
            print("  💡 Sugerencia: Configura NASA_API_KEY para mejor rendimiento")
        return False


def main():
    """Función principal que ejecuta todas las pruebas"""
    print("SISTEMA DE PRUEBAS - CLIENTES API")
    print("=" * 80)
    print("Probando estrategia hibrida de extraccion de datos:")
    print("  - BATCH: Descarga masiva para analisis (OpenData, SBDB)")  
    print("  - REAL-TIME: Consultas en vivo (Horizons)")
    print("  - HIBRIDO: Cache temporal + consultas (NEO)")
    print("=" * 80)
    
    results = {}
    
    # Ejecutar todas las pruebas
    results['opendata'] = test_opendata_client()
    results['sbdb'] = test_sbdb_client() 
    results['horizons'] = test_horizons_client()
    results['neo'] = test_neo_client()
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE PRUEBAS")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for client_name, passed in results.items():
        status = "PASO" if passed else "FALLO"
        strategy = {
            'opendata': 'BATCH',
            'sbdb': 'BATCH', 
            'horizons': 'REAL-TIME',
            'neo': 'HIBRIDO'
        }[client_name]
        print(f"  {client_name.upper():12} ({strategy:10}): {status}")
    
    print(f"\nRESULTADO FINAL: {passed_tests}/{total_tests} clientes funcionando")
    
    if passed_tests == total_tests:
        print("TODOS LOS CLIENTES FUNCIONAN CORRECTAMENTE!")
        print("El sistema de extraccion de datos esta listo para usar")
    elif passed_tests >= total_tests * 0.75:
        print("LA MAYORIA DE CLIENTES FUNCIONAN")
        print("Revisa los clientes que fallaron antes de continuar")
    else:
        print("MULTIPLES CLIENTES FALLARON")
        print("Se requiere revisar configuracion y conectividad")
    
    print("\nPROXIMOS PASOS:")
    print("   1. Si todo funciona: Proceder con analisis de datos")
    print("   2. Si hay fallos: Revisar conectividad y configuracion de APIs")
    print("   3. Para NEO: Configurar NASA_API_KEY para mejor rendimiento")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)