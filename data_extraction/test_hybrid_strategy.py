#!/usr/bin/env python3
"""
Test de la estrategia híbrida implementada según nn.md
=====================================================

Este script prueba todos los componentes de la arquitectura híbrida:
- BATCH: Descarga y consulta de datos locales
- REAL-TIME: Posiciones planetarias en tiempo real
- HÍBRIDO: Cache inteligente de NEOs

Propósito: Verificar que la implementación funciona según la especificación
"""

import sys
import os
from datetime import datetime

# Añadir directorios al path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'data_extraction'))
sys.path.append(os.path.join(project_root, 'web_app'))

def test_batch_strategy():
    """
    Prueba la estrategia BATCH: descarga y consulta local
    """
    print("🧪 PROBANDO ESTRATEGIA BATCH")
    print("=" * 50)
    
    try:
        from batch_download_all import extract_all_batch_data
        
        print("1. Ejecutando descarga BATCH...")
        success = extract_all_batch_data()
        
        if success:
            print("✅ Descarga BATCH exitosa")
            return True
        else:
            print("❌ Error en descarga BATCH")
            return False
            
    except Exception as e:
        print(f"❌ Error importando/ejecutando BATCH: {e}")
        return False

def test_batch_local_queries():
    """
    Prueba consultas a datos BATCH locales
    """
    print("\n🧪 PROBANDO CONSULTAS BATCH LOCALES")
    print("=" * 50)
    
    try:
        from api_handlers import get_batch_handler
        
        batch_handler = get_batch_handler()
        
        # Probar obtener todos los cuerpos
        print("1. Obteniendo todos los cuerpos del sistema solar...")
        all_bodies = batch_handler.get_all_solar_system_bodies()
        
        if all_bodies is not None and len(all_bodies) > 0:
            print(f"✅ Cargados {len(all_bodies)} cuerpos desde cache local")
        else:
            print("❌ No se pudieron cargar datos locales")
            return False
        
        # Probar búsqueda por nombre
        print("2. Buscando 'Jupiter' en datos locales...")
        jupiter = batch_handler.search_body_by_name('Jupiter')
        
        if jupiter:
            jupiter_data = jupiter['body']
            print(f"✅ Encontrado: {jupiter_data.get('englishName', 'N/A')}")
            print(f"   - Radio: {jupiter_data.get('meanRadius', 'N/A')} km")
            print(f"   - Estrategia: {jupiter['strategy']}")
        else:
            print("❌ No se encontró Jupiter en datos locales")
            return False
        
        # Probar obtener asteroides
        print("3. Obteniendo NEOs desde datos locales...")
        neos = batch_handler.get_asteroids_by_category('neos')
        
        if neos is not None and len(neos) > 0:
            print(f"✅ Cargados {len(neos)} NEOs desde cache local")
        else:
            print("⚠️ NEOs no disponibles localmente (puede ser normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en consultas BATCH locales: {e}")
        return False

def test_realtime_strategy():
    """
    Prueba la estrategia REAL-TIME: Horizons
    """
    print("\n🧪 PROBANDO ESTRATEGIA REAL-TIME")
    print("=" * 50)
    
    try:
        from api_handlers import get_realtime_handler
        
        realtime_handler = get_realtime_handler()
        
        # Probar obtener posición actual
        print("1. Obteniendo posición actual de Júpiter...")
        jupiter_pos = realtime_handler.get_planet_position_now('Jupiter')
        
        if jupiter_pos:
            print(f"✅ Posición de Júpiter obtenida:")
            print(f"   - Fecha: {jupiter_pos['date']}")
            print(f"   - Fuente: {jupiter_pos['source']}")
            print(f"   - Estrategia: {jupiter_pos['strategy']}")
        else:
            print("❌ No se pudo obtener posición de Júpiter")
            return False
        
        # Probar trayectoria futura
        print("2. Obteniendo trayectoria de Marte (10 días)...")
        mars_trajectory = realtime_handler.get_planet_trajectory('Mars', days_ahead=10)
        
        if mars_trajectory and len(mars_trajectory) > 0:
            print(f"✅ Trayectoria de Marte obtenida:")
            print(f"   - Puntos: {len(mars_trajectory)}")
            print(f"   - Rango: {mars_trajectory[0]['date']} a {mars_trajectory[-1]['date']}")
        else:
            print("❌ No se pudo obtener trayectoria de Marte")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estrategia REAL-TIME: {e}")
        return False

def test_hybrid_strategy():
    """
    Prueba la estrategia HÍBRIDA: NEO con cache
    """
    print("\n🧪 PROBANDO ESTRATEGIA HÍBRIDA")
    print("=" * 50)
    
    try:
        from api_handlers import get_realtime_handler
        
        realtime_handler = get_realtime_handler()
        
        # Probar NEOs actuales con cache
        print("1. Obteniendo NEOs actuales (con cache)...")
        neos_data = realtime_handler.get_current_neos(use_cache=True)
        
        if neos_data:
            print(f"✅ NEOs actuales obtenidos:")
            print(f"   - Cantidad: {neos_data['count']}")
            print(f"   - Fuente: {neos_data['source']}")
            print(f"   - Estrategia: {neos_data['strategy']}")
            print(f"   - Cache usado: {neos_data['cache_used']}")
        else:
            print("❌ No se pudieron obtener NEOs actuales")
            return False
        
        # Probar PHAs
        print("2. Obteniendo asteroides potencialmente peligrosos...")
        phas_data = realtime_handler.get_potentially_hazardous_asteroids()
        
        if phas_data:
            print(f"✅ PHAs obtenidos:")
            print(f"   - Cantidad: {phas_data['count']}")
            print(f"   - Estrategia: {phas_data['strategy']}")
        else:
            print("❌ No se pudieron obtener PHAs")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estrategia HÍBRIDA: {e}")
        return False

def test_unified_system():
    """
    Prueba el sistema unificado completo
    """
    print("\n🧪 PROBANDO SISTEMA UNIFICADO")
    print("=" * 50)
    
    try:
        from api_handlers import get_unified_manager
        
        manager = get_unified_manager()
        
        # Obtener estado completo del sistema
        print("1. Verificando estado completo del sistema...")
        system_status = manager.get_system_status()
        
        if 'error' in system_status:
            print(f"❌ Error en sistema unificado: {system_status['error']}")
            return False
        
        # Mostrar estado BATCH
        batch_status = system_status['batch_data']
        print(f"📦 Estado BATCH:")
        print(f"   - OpenData: {batch_status['opendata']['records']} registros")
        print(f"   - SBDB: {batch_status['sbdb']['records']} registros")
        
        # Mostrar estado REAL-TIME
        realtime_status = system_status['realtime_apis']
        print(f"🔴 Estado REAL-TIME:")
        print(f"   - Horizons: {'✅ Disponible' if realtime_status['horizons_available'] else '❌ No disponible'}")
        print(f"   - NEO: {'✅ Disponible' if realtime_status['neo_available'] else '❌ No disponible'}")
        
        # Mostrar recomendaciones
        print(f"💡 Recomendaciones del sistema:")
        for rec in system_status['recommendations']:
            print(f"   - {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en sistema unificado: {e}")
        return False

def main():
    """
    Función principal de pruebas
    """
    print("🚀 INICIANDO PRUEBAS DE ESTRATEGIA HÍBRIDA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Basado en especificaciones de nn.md")
    print("=" * 60)
    
    # Resultados de pruebas
    results = {}
    
    # 1. Probar estrategia BATCH
    results['batch_download'] = test_batch_strategy()
    results['batch_queries'] = test_batch_local_queries()
    
    # 2. Probar estrategia REAL-TIME
    results['realtime'] = test_realtime_strategy()
    
    # 3. Probar estrategia HÍBRIDA
    results['hybrid'] = test_hybrid_strategy()
    
    # 4. Probar sistema unificado
    results['unified'] = test_unified_system()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, passed in results.items():
        status = "✅ EXITOSO" if passed else "❌ FALLIDO"
        description = {
            'batch_download': 'Descarga BATCH',
            'batch_queries': 'Consultas BATCH locales',
            'realtime': 'Estrategia REAL-TIME',
            'hybrid': 'Estrategia HÍBRIDA',
            'unified': 'Sistema unificado'
        }.get(test_name, test_name)
        
        print(f"   {description}: {status}")
    
    print(f"\n🎯 RESULTADO GLOBAL: {passed_tests}/{total_tests} pruebas exitosas ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 ¡IMPLEMENTACIÓN COMPLETADA EXITOSAMENTE!")
        print("La estrategia híbrida según nn.md está funcionando correctamente")
    elif success_rate >= 80:
        print("⚠️ Implementación mayormente funcional con algunos problemas menores")
    else:
        print("❌ Implementación requiere correcciones importantes")
    
    print("\n💡 Próximos pasos recomendados:")
    if results['batch_download'] and results['batch_queries']:
        print("   ✅ Datos BATCH listos para análisis de minería de datos")
    else:
        print("   🔧 Verificar y corregir sistema de datos BATCH")
    
    if results['realtime']:
        print("   ✅ APIs real-time listas para web app interactiva")
    else:
        print("   🔧 Verificar conectividad con APIs de NASA")
    
    if results['hybrid']:
        print("   ✅ Sistema híbrido listo para experiencia balanceada")
    else:
        print("   🔧 Verificar configuración de cache híbrido")
    
    return success_rate == 100

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)