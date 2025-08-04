# 📊 Estrategias de Extracción de Datos por API - Documentación Técnica

## 🗂️ Tabla Detallada de Datos por API y Estrategia de Consulta

| API Cliente | Estrategia | Datos Extraídos | Frecuencia de Consulta | Almacenamiento | Uso en Web App |
|-------------|------------|-----------------|------------------------|----------------|----------------|
| OpenData | 📦 BATCH | • Datos físicos de 366 cuerpos<br>• Masa, radio, densidad, gravedad<br>• Parámetros orbitales básicos<br>• Información de lunas<br>• Datos de descubrimiento | Una vez por semana<br>(Datos muy estables) | CSV Locales:<br>• opendata_all_bodies.csv<br>• opendata_planets.csv<br>• opendata_moons.csv | • Consulta Local<br>• Búsquedas instantáneas<br>• Comparaciones<br>• Análisis estadístico |
| SBDB | 📦 BATCH | • Elementos orbitales completos<br>• Asteroides del cinturón principal<br>• NEOs (Near-Earth Objects)<br>• Cometas JFC/HTC<br>• Asteroides Troyanos<br>• PHAs (Potencialmente peligrosos) | Una vez cada 15 días<br>(Elementos orbitales semi-estáticos) | CSV por Categoría:<br>• sbdb_neos.csv<br>• sbdb_main_belt.csv<br>• sbdb_trojans.csv<br>• sbdb_comets_jfc.csv<br>• sbdb_phas.csv | • Consulta Local<br>• Clustering<br>• Clasificación orbital<br>• Análisis predictivo |
| Horizons | 🔴 REAL-TIME | • Posiciones planetarias actuales<br>• Efemérides específicas<br>• Vectores posición/velocidad<br>• Coordenadas RA/DEC<br>• Distancias y magnitudes | Cada consulta de usuario<br>(Posiciones cambian constantemente) | Sin almacenamiento<br>(Respuesta directa) | • Consulta Online<br>• Mapa orbital dinámico<br>• Posiciones "ahora"<br>• Trayectorias futuras |
| NEO | 🔄 HÍBRIDO | • Aproximaciones de la semana<br>• Objetos potencialmente peligrosos<br>• Datos de aproximación<br>• Velocidades relativas<br>• Distancias mínimas | Cache 6-12 horas<br>(Balance performance/actualización) | Cache JSON Temporal:<br>• current_week_*.json<br>• potentially_hazardous_current.json<br>• Auto-renovación | • Consulta Cache + API<br>• Monitor de aproximaciones<br>• Alertas PHAs<br>• Calendario eventos |

---

## 📊 Detalle de Datos por Estrategia

### 📦 BATCH PROCESSING (Ejecutar → Guardar → Usar Local)

#### OpenData Client - Datos Físicos Estables

**Lo que se descarga UNA VEZ por semana:**

366 cuerpos del sistema solar con:
- Información básica: nombre, tipo, descubrimiento
- Parámetros físicos: masa (kg), radio (km), densidad (g/cm³)
- Parámetros orbitales: semieje mayor, excentricidad, período
- Datos térmicos: temperatura promedio
- Relaciones: planeta padre (para lunas), número de lunas

**Archivos generados:**
- `opendata_all_bodies.csv` → Todos los 366 cuerpos
- `opendata_planets.csv` → Solo planetas y enanos
- `opendata_moons.csv` → Solo lunas con datos del planeta padre

#### SBDB Client - Elementos Orbitales Semi-estáticos

**Lo que se descarga cada 15 días por categoría:**
- NEOs (~5000): Asteroides cercanos a la Tierra
- MBA (~8000): Asteroides del cinturón principal
- Troyanos (~3000): Asteroides en puntos de Lagrange de Júpiter
- Cometas JFC (~2000): Cometas de período corto
- Cometas HTC (~1000): Cometas de período largo
- PHAs (~3000): Asteroides potencialmente peligrosos

**Datos por objeto:**
- Elementos orbitales: a, e, i, w, om, ma, per, q, ad
- Parámetros físicos: diámetro, albedo, período rotación
- Clasificación: clase dinámica, tipo espectral
- Magnitudes: H (absoluta), G (parámetro pendiente)

### 🔴 REAL-TIME PROCESSING (Consultar Online Cada Vez)

#### Horizons Client - Posiciones Dinámicas

**Lo que se consulta EN VIVO cada vez que el usuario lo solicita:**
- Posición actual de planetas (ahora mismo)
- Efemérides para fechas específicas del usuario
- Trayectorias orbitales para rangos de tiempo
- Coordenadas celestes (RA/DEC) observacionales
- Vectores posición/velocidad en tiempo específico

**Casos de uso en Web App:**
- "¿Dónde está Marte ahora?" → Consulta inmediata
- Mapa orbital con slider de tiempo → Consulta por fecha
- "Mostrar órbita de Júpiter próximos 30 días" → Consulta rango

### 🔄 HYBRID PROCESSING (Cache Inteligente + API)

#### NEO Client - Balance Performance/Actualización

**Cache 6 horas para datos frecuentes:**
- NEOs de la semana actual (se actualiza 4 veces/día)
- Lista de aproximaciones próximas
- Estadísticas generales de actividad

**Cache 12 horas para datos menos frecuentes:**
- Lista completa de PHAs actuales
- Análisis de peligrosidad
- Tendencias de aproximación

**Lógica del cache:**
```python
if cache_age < 6_hours:
    return cached_data
else:
    new_data = api_call()
    save_to_cache(new_data)
    return new_data
```

---

## 🐍 Archivo Python Principal de Extracción de Datos

### Script Principal: `data_extraction/batch_download_all.py` (A crear)

```python
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

# Importar todos los clientes BATCH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_clients.opendata_client import get_solar_system_client
from api_clients.sbdb_client import get_sbdb_client

def extract_all_batch_data():
    """
    Función principal que ejecuta toda la extracción BATCH
    """
    print("🚀 INICIANDO EXTRACCIÓN MASIVA DE DATOS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Estrategia: BATCH PROCESSING")
    print("Propósito: Datos para análisis de minería offline")
    print("=" * 60)

    results = {}

    # 1. OPENDATA - Datos físicos de 366 cuerpos
    print("\n📊 EXTRAYENDO DATOS FÍSICOS (OpenData)")
    print("-" * 40)
    try:
        opendata_client = get_solar_system_client()

        # Verificar si necesita actualización
        cache_status = opendata_client.check_cache_status()
        print(f"Cache existe: {cache_status['cache_exists']}")
        print(f"Necesita actualización: {cache_status['needs_update']}")

        if cache_status['needs_update']:
            print("🔄 Descargando datos físicos...")
            opendata_files = opendata_client.batch_download_all()
            results['opendata'] = {
                'status': 'success',
                'files': list(opendata_files.keys()),
                'action': 'downloaded'
            }
            print(f"✅ {len(opendata_files)} archivos OpenData generados")
        else:
            print("✅ Cache OpenData actualizado, omitiendo descarga")
            results['opendata'] = {
                'status': 'cached',
                'records': cache_status.get('total_records', 0),
                'action': 'skipped'
            }

    except Exception as e:
        print(f"❌ Error en OpenData: {e}")
        results['opendata'] = {'status': 'error', 'error': str(e)}

    # 2. SBDB - Elementos orbitales de asteroides/cometas
    print("\n🌌 EXTRAYENDO ELEMENTOS ORBITALES (SBDB)")
    print("-" * 40)
    try:
        sbdb_client = get_sbdb_client()

        # Verificar si necesita actualización
        cache_status = sbdb_client.check_cache_status()
        print(f"Cache existe: {cache_status['cache_exists']}")
        print(f"Necesita actualización: {cache_status['needs_update']}")

        if cache_status['needs_update']:
            print("🔄 Descargando elementos orbitales...")
            sbdb_files = sbdb_client.batch_download_all()
            results['sbdb'] = {
                'status': 'success',
                'files': len(sbdb_files),
                'action': 'downloaded'
            }
            print(f"✅ {len(sbdb_files)} archivos SBDB generados")
        else:
            print("✅ Cache SBDB actualizado, omitiendo descarga")
            results['sbdb'] = {
                'status': 'cached',
                'records': cache_status.get('total_records', 0),
                'action': 'skipped'
            }

    except Exception as e:
        print(f"❌ Error en SBDB: {e}")
        results['sbdb'] = {'status': 'error', 'error': str(e)}

    # 3. Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE EXTRACCIÓN BATCH")
    print("=" * 60)

    for source, result in results.items():
        status = result['status']
        action = result.get('action', 'unknown')

        if status == 'success':
            print(f"✅ {source.upper()}: Datos descargados exitosamente")
        elif status == 'cached':
            records = result.get('records', 0)
            print(f"📦 {source.upper()}: Cache actualizado ({records} registros)")
        else:
            print(f"❌ {source.upper()}: Error - {result.get('error', 'Desconocido')}")

    # 4. Próximos pasos
    success_count = sum(1 for r in results.values() if r['status'] in ['success', 'cached'])

    if success_count == len(results):
        print(f"\n🎉 EXTRACCIÓN COMPLETADA EXITOSAMENTE")
        print("Los datos están listos para análisis de minería de datos")
        print("\nArchivos generados en:")
        print("  📁 data/raw/api_data/opendata_*.csv")
        print("  📁 data/raw/api_data/sbdb_*.csv")
        print("\nPróximo paso: ejecutar análisis descriptivo y clustering")
        return True
    else:
        print(f"\n⚠️ EXTRACCIÓN PARCIAL: {success_count}/{len(results)} fuentes exitosas")
        print("Revisar errores antes de proceder con análisis")
        return False

if __name__ == "__main__":
    success = extract_all_batch_data()
    exit(0 if success else 1)
```

### Scripts de Datos Real-Time y Híbridos

#### Para la Web App: `web_app/api_handlers.py` (A crear)

```python
"""
Manejadores de APIs para datos en tiempo real en la web app
"""

from api_clients.horizons_client import get_horizons_client
from api_clients.neo_client import get_neo_client

class RealTimeDataHandler:
    """Maneja consultas real-time para la web app"""

    def get_planet_position_now(self, planet_name):
        """Obtiene posición actual de un planeta"""
        horizons = get_horizons_client()
        return horizons.get_current_positions([planet_name])

    def get_current_neos(self):
        """Obtiene NEOs actuales (usa cache híbrido)"""
        neo = get_neo_client()
        return neo.get_current_week_neos_cached(use_cache=True)
```

---

## 🔄 Flujo de Trabajo Completo

### 1. Extracción Inicial (Una vez)

```bash
# Descargar todos los datos BATCH para análisis
cd data_extraction
python batch_download_all.py
```

**Resultado:**
- ✅ Genera archivos CSV con 366 cuerpos (OpenData)
- ✅ Genera archivos CSV con asteroides/cometas por categoría (SBDB)
- ✅ Datos listos para análisis offline

### 2. Procesamiento de Datos (Análisis de Minería)

```bash
# Procesar datos descargados
cd data_analysis
python descriptive_analysis.py    # Usa archivos CSV locales
python clustering_analysis.py     # Usa archivos CSV locales
```

**Resultado:**
- 📊 Análisis descriptivo de 366 cuerpos
- 🎯 Clustering de asteroides y cometas
- 📈 Visualizaciones y resultados

### 3. Web App (Uso Mixto)

```bash
# En la web app:
- Datos BATCH: Consulta archivos CSV locales (instantáneo)
- Datos REAL-TIME: Consulta Horizons online (2-3 segundos)
- Datos HÍBRIDOS: Consulta cache NEO o API según edad (< 1 segundo)
```

**Resultado:**
- ⚡ Búsquedas instantáneas en datos locales
- 🔴 Posiciones planetarias en tiempo real
- 🔄 Aproximaciones NEO actualizadas automáticamente

---

## 📁 Estructura de Archivos Generados

    data/raw/api_data/
    ├── 📦 BATCH (Descarga periódica)
    │ ├── opendata_all_bodies.csv # 366 cuerpos físicos
    │ ├── opendata_planets.csv # Solo planetas
    │ ├── opendata_moons.csv # Solo lunas
    │ ├── sbdb_neos.csv # Near-Earth Objects
    │ ├── sbdb_main_belt.csv # Asteroides cinturón principal
    │ ├── sbdb_trojans.csv # Asteroides Troyanos
    │ ├── sbdb_comets_jfc.csv # Cometas período corto
    │ ├── sbdb_comets_htc.csv # Cometas período largo
    │ └── sbdb_phas.csv # Potencialmente peligrosos
    ├── 🔄 CACHE (Renovación automática)
    │ └── neo_cache/
    │ ├── current_week_.json # NEOs semana actual
    │ └── potentially_hazardous_current.json
    └── 🔴 REAL-TIME (Sin almacenamiento)
    └── (Consultas directas a Horizons)


---

## 🎯 Ventajas de Esta Arquitectura

### ⚡ Performance

- **Datos BATCH**: Consultas instantáneas (archivos locales)
- **Cache Híbrido**: Balance perfecto actualización/velocidad
- **Real-Time**: Solo cuando es necesario

### 🔒 Robustez

- **Offline Capability**: Análisis funciona sin internet
- **Cache Fallback**: NEO funciona aunque API falle temporalmente
- **Degradación Elegante**: Web app funciona parcialmente sin Horizons

### 📊 Análisis Optimizado

- **Datos Estables**: Perfectos para clustering y estadísticas
- **Elementos Orbitales**: Completos para clasificación astronómica
- **Tiempo Real**: Experiencia interactiva en web app

Esta arquitectura te da lo mejor de ambos mundos: análisis rápido offline con datos estables, y funcionalidad en tiempo real para la experiencia de usuario interactiva.