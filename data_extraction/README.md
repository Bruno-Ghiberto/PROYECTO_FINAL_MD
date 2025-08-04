# Módulo de Extracción de Datos - Sistema Solar Explorer

Este módulo contiene todos los clientes API y scrapers necesarios para obtener datos sobre el Sistema Solar de múltiples fuentes oficiales.

## Estructura del módulo

```
data_extraction/
├── api_clients/          # Clientes para APIs REST
│   ├── horizons_client.py    # JPL Horizons (efemérides)
│   ├── sbdb_client.py        # Small-Body Database (asteroides/cometas)
│   ├── neo_client.py         # Near-Earth Objects
│   ├── opendata_client.py    # Solar System OpenData
│   └── image_client.py       # APOD y NASA Image Library
├── scrapers/            # Web scrapers éticos
│   ├── planetary_facts.py    # NASA Planetary Fact Sheet
│   └── moon_facts.py         # NASA Moon Fact Sheet
├── base_client.py       # Clases base con funcionalidad común
└── test_apis.py         # Script de prueba de conectividad
```

## Configuración inicial

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# NASA API Key (obtener en https://api.nasa.gov/)
NASA_API_KEY=tu_api_key_aqui

# Email para identificación (opcional)
EMAIL_ADDRESS=tu_email@ejemplo.com
```

### 3. Verificar conectividad

```bash
python data_extraction/test_apis.py
```

## Uso de los clientes API

### JPL Horizons - Efemérides y posiciones

```python
from data_extraction.api_clients.horizons_client import get_horizons_client

# Crear cliente
client = get_horizons_client()

# Obtener posición de la Tierra
df = client.get_ephemeris(
    body='earth',              # Nombre o código NAIF
    start_date='2024-01-01',   # Fecha inicio
    stop_date='2024-01-07',    # Fecha fin
    step_size='1d',            # Intervalo
    center='@sun'              # Centro de referencia
)
```

### SBDB - Asteroides y cometas

```python
from data_extraction.api_clients.sbdb_client import get_sbdb_client

client = get_sbdb_client()

# Obtener asteroides del cinturón principal
asteroids = client.get_asteroids(
    asteroid_class='MBA',      # Main Belt Asteroids
    min_diameter=100,          # Diámetro mínimo en km
    limit=100
)

# Obtener cometas de período corto
comets = client.get_comets(
    comet_class='JFC',         # Jupiter Family Comets
    max_period=7300            # ~20 años
)
```

### NEO - Objetos cercanos a la Tierra

```python
from data_extraction.api_clients.neo_client import get_neo_client

client = get_neo_client()  # Usa NASA_API_KEY del .env

# Obtener NEOs de la próxima semana
df = client.get_feed(
    start_date='2024-01-01',
    end_date='2024-01-07'      # Máximo 7 días
)

# Analizar aproximaciones
stats = client.analyze_approaches(df)
```

### Solar System OpenData

```python
from data_extraction.api_clients.opendata_client import get_solar_system_client

client = get_solar_system_client()

# Obtener todos los planetas
planets = client.get_planets(include_dwarf=True)

# Obtener lunas de Júpiter
moons = client.get_moons('jupiter')

# Comparar planetas terrestres
comparison = client.get_body_comparison(
    ['mercury', 'venus', 'terre', 'mars']
)
```

### APIs de imágenes

```python
from data_extraction.api_clients.image_client import (
    get_apod_client, 
    get_nasa_image_client
)

# APOD - Imagen astronómica del día
apod_client = get_apod_client()
today_apod = apod_client.get_apod()

# NASA Image Library
nasa_client = get_nasa_image_client()
mars_images, metadata = nasa_client.search(
    "Mars rover",
    media_type='image',
    year_start=2020
)
```

## Uso de los scrapers

### Planetary Fact Sheet

```python
from data_extraction.scrapers.planetary_facts import get_planetary_facts_scraper

scraper = get_planetary_facts_scraper()

# Obtener tabla de datos planetarios
df = scraper.scrape_planetary_facts()

# Convertir a unidades SI
df_si = scraper.convert_to_standard_units(df)
```

### Moon Fact Sheet

```python
from data_extraction.scrapers.moon_facts import get_moon_facts_scraper

scraper = get_moon_facts_scraper()

# Obtener datos de la Luna
moon_data = scraper.scrape_moon_facts()

# Comparar con la Tierra
comparison = scraper.get_lunar_comparison()
```

### Jovian Satellite Fact Sheet

```python
from data_extraction.scrapers.jovian_sats import get_jovian_satellite_scraper

scraper = get_jovian_satellite_scraper()

# Obtener todas las lunas de Júpiter
all_moons = scraper.scrape_jovian_satellites()
print(f"Total de lunas: {len(all_moons)}")

# Obtener solo las lunas galileanas
galilean = scraper.get_galilean_moons()
print(galilean[['name', 'mean_radius_km', 'orbital_period_days']])

# Comparar con la Luna terrestre
comparison = scraper.compare_with_moon()
print(comparison[['name', 'radius_vs_moon', 'mass_vs_moon']].head())
```

## Características principales

### Manejo robusto de errores

- Reintentos automáticos con backoff exponencial
- Timeouts configurables
- Logging detallado de errores

### Scraping ético

- Verificación de robots.txt
- Delays entre peticiones (2 segundos)
- Headers de identificación

### Procesamiento de datos

- Conversión automática a DataFrames de pandas
- Normalización de unidades
- Limpieza de valores numéricos

## Límites y consideraciones

### Límites de APIs

- **NASA APIs**: 1000 peticiones/hora con API key, 30/hora con DEMO_KEY
- **JPL Horizons**: Sin límite estricto, usar con moderación
- **NEO API**: Máximo 7 días por petición
- **SBDB**: Sin límite documentado

### Buenas prácticas

1. **Cache los resultados** cuando sea posible
2. **No hagas peticiones innecesarias** - los datos planetarios no cambian frecuentemente
3. **Respeta los delays** en el scraping
4. **Identifícate apropiadamente** con email en Horizons

## Solución de problemas

### Error "DEMO_KEY rate limit exceeded"

Obtén una API key gratuita en https://api.nasa.gov/

### Error de conexión en SBDB

La API SBDB usa HTTP (no HTTPS). Algunos firewalls pueden bloquearlo.

### Scraping devuelve datos vacíos

1. Verifica tu conexión a internet
2. El sitio puede haber cambiado su estructura HTML
3. Revisa los logs para más detalles

## Ejemplos avanzados

### Obtener efemérides de múltiples cuerpos

```python
bodies = ['mercury', 'venus', 'earth', 'mars']
all_ephemerides = []

for body in bodies:
    df = client.get_ephemeris(
        body=body,
        start_date='2024-01-01',
        stop_date='2024-12-31',
        step_size='7d'
    )
    df['body'] = body
    all_ephemerides.append(df)

combined_df = pd.concat(all_ephemerides)
```

### Análisis temporal de NEOs

```python
# Obtener NEOs para múltiples semanas
all_neos = []
start = datetime(2024, 1, 1)

for week in range(4):
    week_start = start + timedelta(weeks=week)
    week_end = week_start + timedelta(days=6)
    
    df = neo_client.get_feed(
        start_date=week_start.strftime('%Y-%m-%d'),
        end_date=week_end.strftime('%Y-%m-%d')
    )
    all_neos.append(df)

# Analizar tendencias
full_df = pd.concat(all_neos)
```

## Contribuciones

Para reportar errores o sugerir mejoras, por favor abre un issue en el repositorio del proyecto.