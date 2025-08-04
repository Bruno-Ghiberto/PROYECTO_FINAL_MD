# Integración Avanzada de APIs de la NASA: Una Guía Técnica para la Fusión de Datos de JPL Horizons y la Biblioteca de Imágenes para Proyectos de Minería de Datos

## Sección 1: Análisis Profundo de la API JPL Horizons del NASA/JPL

Esta sección proporciona una deconstrucción exhaustiva de la API JPL Horizons, avanzando desde conceptos fundamentales hasta las técnicas prácticas avanzadas requeridas para el proyecto del usuario. El enfoque se centra en la extracción robusta de datos y en la comprensión de las características únicas de esta interfaz de programación.

### 1.1. Fundamentos del Sistema Horizons: Más Allá de una API REST Típica

Para integrar eficazmente la API JPL Horizons, es fundamental comprender que no se trata de una API REST convencional diseñada desde cero, sino de una interfaz moderna para un sistema de cómputo de efemérides de alta precisión con una larga y respetada historia.¹ 

Antes de la existencia de la API web, introducida formalmente alrededor de 2021, el sistema Horizons se accedía principalmente a través de interfaces de línea de comandos (vía Telnet), correo electrónico y una interfaz web interactiva.¹

Esta herencia arquitectónica tiene una implicación directa y crítica para el desarrollador. La API actúa como un "envoltorio" (wrapper) que traduce una solicitud HTTP GET en un comando para el sistema subyacente. Como resultado, la respuesta de la API, aunque encapsulada en formato JSON, a menudo contiene en su campo principal (`result`) un bloque de texto preformateado. Este texto es, en esencia, la salida directa que el sistema heredado habría generado. 

Por lo tanto, el proceso de extracción de datos no se limita a un simple análisis de un objeto JSON estructurado; requiere un paso adicional y robusto de análisis de cadenas de texto (string parsing) para extraer los valores numéricos de este bloque de texto.

El sistema Horizons puede proporcionar una vasta gama de datos de alta precisión para prácticamente todos los cuerpos conocidos del Sistema Solar, incluyendo más de 1.2 millones de asteroides, miles de cometas, satélites naturales, planetas y naves espaciales.² Los tipos de datos disponibles incluyen:

- **Efemérides del Observador**: Cantidades como la ascensión recta (A.R.), declinación (DEC), ángulos y tasas de plano de cielo, visibilidad y aspecto físico.²
- **Elementos Orbitales Osculantes**: Parámetros que definen la órbita de un objeto en un instante específico.²
- **Vectores de Estado Cartesianos**: Posición (x,y,z) y velocidad (vx​,vy​,vz​) del objeto en un sistema de coordenadas específico.²
- **Datos Físicos**: Cuando están disponibles, se pueden obtener parámetros como magnitud, diámetro y período de rotación.

Comprender que la API es una puerta de entrada a un motor de cálculo explica por qué la solicitud es altamente personalizable y por qué la respuesta requiere un tratamiento especial, un tema que se abordará en detalle en la subsección 1.5.

### 1.2. Identificación Precisa de Cuerpos Celestes: La Estrategia de Dos Pasos

Un desafío fundamental en cualquier sistema automatizado que trate con cuerpos celestes es la ambigüedad de los nombres. Un nombre común como "Patroclus" podría referirse al baricentro del sistema troyano (asteroide 617), al cuerpo primario del sistema, o a otras designaciones, cada una con un identificador único en el sistema Horizons.⁴ 

Realizar una consulta con un nombre ambiguo puede devolver una lista de coincidencias o, peor aún, un resultado incorrecto. Para un proyecto de minería de datos que requiere precisión y robustez, este enfoque no es viable.

La solución es un flujo de trabajo de dos pasos que utiliza una API auxiliar específica para la resolución de nombres: `horizons_lookup.api`. Esta herramienta está diseñada para correlacionar las diversas etiquetas de un objeto (nombre, designación, número IAU) con su identificador primario y único, el SPK-ID.⁴

El flujo de trabajo recomendado es el siguiente:

1. **Consulta de Búsqueda (Lookup)**: Realizar una primera llamada a la API `horizons_lookup.api`. El objetivo es buscar un objeto utilizando su nombre más común. Por ejemplo, para el asteroide Apophis, la consulta se realizaría al endpoint `https://ssd-api.jpl.nasa.gov/api/horizons_lookup.api` con el parámetro `sstr=Apophis`. Se puede añadir un parámetro opcional `group` (por ejemplo, `group=ast`) para limitar la búsqueda a asteroides y mejorar la precisión.⁴

2. **Extracción del Identificador Único**: La respuesta de esta API, en formato JSON, contendrá el nombre oficial, el tipo de objeto, el SPK-ID primario (`spkid`) y una lista de alias (`alias`).⁴ Para Apophis, el `spkid` devuelto es "20099942". Este es el identificador definitivo que se debe usar en las consultas posteriores.

3. **Consulta de Datos Principales**: Utilizar el `spkid` extraído en el parámetro `COMMAND` de la consulta principal a `horizons.api` para solicitar las efemérides y los datos físicos.

Este proceso de dos pasos garantiza que cada consulta de datos se dirija a un objeto inequívocamente identificado. Además, este enfoque revela una oportunidad estratégica para la fusión de datos. La respuesta de la API de búsqueda (`horizons_lookup.api`) incluye un campo `alias` que contiene designaciones alternativas, como "2004 MN4" para Apophis.⁴ 

Si una búsqueda del nombre primario ("99942 Apophis") en la API de Imágenes de la NASA (Sección 2) no produce resultados relevantes, estos alias pueden utilizarse como términos de búsqueda de respaldo. Almacenar estos alias junto con el nombre primario crea un mecanismo de recuperación de imágenes mucho más resiliente y aumenta significativamente la probabilidad de encontrar un activo visual correspondiente para cada objeto.

### 1.3. Construcción de Consultas a la API Principal (horizons.api)

Una vez obtenido el SPK-ID único del objeto, el siguiente paso es construir la solicitud a la API principal de Horizons para obtener los datos científicos. Esta se realiza mediante una solicitud HTTP GET a la URL base `https://ssd.jpl.nasa.gov/api/horizons.api`.⁵ La personalización de los datos devueltos se controla a través de una serie de parámetros en la URL.

A continuación, se presenta una tabla con los parámetros más relevantes para este proyecto, extraídos de la documentación oficial.⁵

#### Tabla 1: Parámetros Clave de la API JPL Horizons (GET Request)

| Parámetro | Valor de Ejemplo | Descripción |
|-----------|------------------|-------------|
| `format` | `json` | Especifica el formato de salida. Se recomienda `json` para facilitar el manejo inicial de la respuesta. |
| `COMMAND` | `'20099942'` | El identificador del cuerpo celeste. Debe ser el `spkid` obtenido de la API de búsqueda. |
| `OBJ_DATA` | `'YES'` | Incluye un resumen de datos del objeto (página de información) en la respuesta. |
| `MAKE_EPHEM` | `'YES'` | Instruye al sistema para que genere la tabla de efemérides. |
| `EPHEM_TYPE` | `'OBSERVER'` | Genera efemérides tal como se verían desde una ubicación específica (el observador). |
| `CENTER` | `'500@399'` | Define la ubicación del observador. '500@399' corresponde al centro de la Tierra. |
| `START_TIME` | `'2024-01-01'` | Fecha y hora de inicio para el cálculo de las efemérides. |
| `STOP_TIME` | `'2024-01-02'` | Fecha y hora de finalización para el cálculo. |
| `STEP_SIZE` | `'1d'` | El intervalo de tiempo entre cada registro de la efeméride (e.g., '1d' para un día, '1h' para una hora). |
| `QUANTITIES` | `'1,9,20,23,24'` | Una lista de códigos numéricos separados por comas que especifica qué datos se deben incluir en la tabla. |

El parámetro `QUANTITIES` es especialmente poderoso, ya que permite al desarrollador solicitar únicamente los datos necesarios para las "cartas de presentación", optimizando así la respuesta. La siguiente tabla desmitifica algunos de los códigos más útiles.⁵

#### Tabla 2: Parámetros QUANTITIES de Horizons Seleccionados y Recomendados

| Código | Descripción de Datos | Unidad |
|--------|---------------------|--------|
| 1 | Ascensión Recta y Declinación Astrométricas (A.R. & DEC) | Grados |
| 9 | Magnitud Aparente y Brillo Superficial | mag, mag/arcsec² |
| 19 | Distancia al Sol y al Observador (Range) | Unidades Astronómicas (AU) |
| 20 | Tasa de cambio de la distancia (Range-Rate) | km/s |
| 23 | Longitud y Latitud Eclíptica Verdadera del Objeto | Grados |
| 24 | Velocidad angular en el plano del cielo | arcsec/hora |
| 29 | Constelación en la que se encuentra el objeto | N/A |

Al combinar estos parámetros, se puede construir una URL de consulta precisa. Por ejemplo, para obtener la magnitud y la distancia de Apophis para una fecha específica, la URL sería similar a:

    https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='20099942'&EPHEM_TYPE='OBSERVER'&CENTER='500@399'&START_TIME='2029-04-13'&STOP_TIME='2029-04-14'&STEP_SIZE='1d'&QUANTITIES='9,19'


### 1.4. Aclaración de Conceptos: Propiedades Físicas en Horizons

Durante la investigación de APIs, es posible encontrar referencias a "propiedades físicas" en contextos tecnológicos que pueden generar confusión. Documentación de plataformas como Meta Horizon Worlds o VMware Horizon menciona conceptos como colisionadores, gravedad, masa en kilogramos y motores de física para simulaciones en tiempo real.⁶ Es crucial entender que estos conceptos no tienen ninguna relación con el sistema JPL Horizons.

En el contexto de la astronomía y la API JPL Horizons, las "propiedades físicas" se refieren a los datos astronómicos y orbitales del cuerpo celeste.² Esto incluye:

- Parámetros orbitales (excentricidad, inclinación)
- Vectores de estado (posición y velocidad)
- Características rotacionales
- Magnitud absoluta (H)
- Parámetro de pendiente (G)
- Diámetro, albedo y taxonomía espectral, cuando se conocen

Esta distinción es vital para enfocar correctamente los esfuerzos de desarrollo en la extracción de datos astronómicos relevantes para el proyecto, en lugar de buscar APIs o parámetros relacionados con la física de los videojuegos.

### 1.5. El Reto Crítico: Parseo de la Respuesta de Horizons

Como se mencionó anteriormente, el mayor desafío técnico al trabajar con la API de Horizons es el análisis de su respuesta. Una consulta con `format=json` devuelve un objeto JSON que contiene una clave `result`. El valor asociado a esta clave no es otro objeto JSON anidado, sino una única y larga cadena de texto que contiene toda la información generada por el sistema backend de Horizons.⁵

Esta cadena de texto está formateada para la lectura humana, con encabezados, tablas y notas al pie. Para utilizar estos datos en una aplicación, es necesario analizarlos y convertirlos en una estructura de datos manejable, como una lista de diccionarios o un DataFrame de Pandas.

La estrategia de análisis recomendada es la siguiente:

1. **Aislar la Cadena de Texto**: Extraer el contenido de la clave `result` del objeto JSON principal.

2. **Identificar la Tabla de Efemérides**: La tabla de datos principal está delimitada por marcadores específicos. El inicio de la tabla se indica con la cadena `$$SOE` (Start of Ephemeris) y el final con `$$EOE` (End of Ephemeris). Todo el texto entre estos dos marcadores corresponde a los datos de la efeméride.

3. **Extraer Encabezados y Datos**: Una vez aislada la sección de la tabla, se pueden usar expresiones regulares (regex) para procesarla.
   - La línea inmediatamente anterior a `$$SOE` suele contener los encabezados de las columnas. Se puede analizar para determinar el nombre y el orden de cada columna.
   - Cada línea entre `$$SOE` y `$$EOE` representa un registro de datos en un instante de tiempo. Se puede dividir cada línea y asignar cada valor a su encabezado correspondiente.

4. **Manejar Datos Adicionales**: La información de la página de resumen del objeto (`OBJ_DATA='YES'`) aparece antes de la sección de efemérides. También se puede analizar con expresiones regulares para extraer datos clave como el nombre completo del objeto, su tipo y otros parámetros físicos que no están en la tabla de efemérides.

A continuación se muestra un ejemplo conceptual en Python que ilustra esta lógica de análisis:

```python
import re
import json

def parse_horizons_result(response_text):
    """
    Analiza la respuesta de texto de la API de Horizons y la convierte
    en una estructura de datos utilizable.
    """
    try:
        data = json.loads(response_text)
        if "result" not in data:
            # Manejar posible error devuelto por la API
            return {"error": data.get("error", "Respuesta inesperada de Horizons")}
        
        result_text = data["result"]
        
        # Extraer la tabla de efemérides usando los marcadores
        match = re.search(r'\$\$SOE(.*?)\$\$EOE', result_text, re.DOTALL)
        if not match:
            return {"error": "No se encontró la tabla de efemérides (marcadores $$SOE/$$EOE)."}
            
        ephemeris_block = match.group(1).strip()
        
        # Un enfoque simple es dividir por líneas y luego por comas (el formato real puede variar)
        lines = ephemeris_block.split('\n')
        
        # Suponiendo que los encabezados están definidos en la documentación de QUANTITIES
        # Por ejemplo, para QUANTITIES='9,19' podríamos esperar: 'Date', 'APmag', 'S-O-T', 'r', 'rdot'
        # Aquí se necesitaría una lógica más robusta para mapear los encabezados reales
        
        parsed_data = []
        for line in lines:
            # La salida de Horizons está alineada por columnas, no separada por comas.
            # Se requiere un análisis más sofisticado basado en anchos de columna fijos o regex.
            # Este es un ejemplo simplificado.
            # Ejemplo de línea: 2029-Apr-13 00:00 * -1.95 0.00021234 0.00021156 -42.34...
            
            # Una expresión regular podría ser más efectiva aquí para capturar cada campo.
            # Ejemplo (debe ajustarse a las QUANTITIES exactas solicitadas):
            data_match = re.match(r'^\s*(\d{4}-\w{3}-\d{2}\s\d{2}:\d{2})\s+([a-zA-Z*tn ]+)\s+([-\d.]+)\s+([-\d.]+)', line)
            if data_match:
                record = {
                    "timestamp": data_match.group(1).strip(),
                    "flags": data_match.group(2).strip(),
                    "apparent_magnitude": float(data_match.group(3)),
                    "distance_au": float(data_match.group(4)),
                    #... más campos según las QUANTITIES
                }
                parsed_data.append(record)

        return {"ephemeris": parsed_data}

    except json.JSONDecodeError:
        return {"error": "La respuesta no es un JSON válido."}
    except Exception as e:
        return {"error": f"Error durante el parseo: {str(e)}"}
```

Este código de ejemplo demuestra la necesidad de un analizador personalizado. Un enfoque robusto implicaría definir las expresiones regulares basándose en las `QUANTITIES` solicitadas para garantizar una extracción precisa de los datos de la tabla.

---

## Sección 2: Dominio de la API de la Biblioteca de Imágenes y Vídeos de la NASA

A diferencia de la API de Horizons, la API de la Biblioteca de Imágenes y Vídeos de la NASA (`images-api.nasa.gov`) sigue un patrón REST más convencional. Su propósito es proporcionar acceso a la vasta colección de más de 140,000 imágenes, vídeos y archivos de audio de la NASA.¹¹

### 2.1. Autenticación, Claves API y Límites de Tasa

El primer paso para utilizar esta API es obtener una clave de API. Este proceso es sencillo y se realiza a través del portal de APIs de la NASA en `api.nasa.gov`.¹³ Tras un breve registro, se proporciona una clave única.

Esta clave debe incluirse en cada solicitud a la API como un parámetro de consulta en la URL, por ejemplo: `&api_key=SU_CLAVE_API`. Aunque es posible realizar consultas de prueba con la clave genérica `DEMO_KEY`, esta tiene límites de tasa muy estrictos (e.g., 30 solicitudes por hora) y no es adecuada para un proyecto de desarrollo o minería de datos.¹³

Una clave de API registrada ofrece un límite de tasa mucho más generoso, típicamente de 1,000 solicitudes por hora por dirección IP.¹⁴ Es crucial gestionar este límite de forma responsable. La API devuelve encabezados HTTP en cada respuesta que ayudan a monitorear el uso:

- `X-RateLimit-Limit`: El número total de solicitudes permitidas en el período de tiempo.
- `X-RateLimit-Remaining`: El número de solicitudes restantes en el período actual.

Un sistema de minería de datos debe verificar estos encabezados para evitar exceder los límites, lo que podría resultar en un bloqueo temporal del acceso.

### 2.2. El Endpoint /search: Búsqueda Efectiva de Activos Visuales

El endpoint principal para encontrar imágenes es `/search`. La URL base para las consultas de búsqueda es `https://images-api.nasa.gov/search`.¹³ La efectividad de la búsqueda depende directamente de la calidad y especificidad de los parámetros de consulta utilizados.

#### Tabla 3: Parámetros Clave de la API NASA Image Library (/search)

| Parámetro | Valor de Ejemplo | Descripción |
|-----------|------------------|-------------|
| `q` | `"Europa" "Jupiter"` | La consulta de texto libre. Es el parámetro más importante. Se pueden usar comillas para frases exactas. |
| `media_type` | `image` | Filtra los resultados para devolver solo imágenes. Esencial para este proyecto. |
| `nasa_id` | `PIA19048` | Busca un activo específico por su NASA ID. |
| `keywords` | `europa,moon,jupiter` | Busca dentro de los metadatos de palabras clave. Puede ser una lista separada por comas. |
| `year_start` | `2015` | Filtra los resultados para incluir solo los creados a partir de este año. |
| `year_end` | `2020` | Filtra los resultados para incluir solo los creados hasta este año. |

El éxito de la fusión de datos entre Horizons y la Biblioteca de Imágenes depende en gran medida de la construcción de una consulta de búsqueda (`q`) inteligente. Una consulta simple como `q=Io` es demasiado genérica y probablemente devolverá imágenes de conceptos no relacionados.

Una estrategia mucho más robusta, que aprovecha los datos ya obtenidos de Horizons, es construir una consulta compuesta. Por ejemplo, si Horizons identifica un objeto como "Europa", una luna de Júpiter, la consulta a la API de imágenes debería ser `q="Europa" "Jupiter" moon`. Esta combinación de nombre, cuerpo padre y tipo de objeto reduce drásticamente la ambigüedad y aumenta la relevancia de los resultados. Este es un punto clave de la estrategia de fusión que se detallará en la Sección 3.

### 2.3. Navegación de la Estructura de Respuesta JSON

La respuesta del endpoint `/search` es un objeto JSON bien estructurado, lo que facilita su análisis en comparación con la respuesta de Horizons. La estructura general contiene una clave `collection` que, a su vez, contiene una clave `items`, que es una lista de los resultados encontrados.

Cada elemento (`item`) en la lista `items` representa un activo visual y contiene dos claves principales: `data` y `links`.

- **`data`**: Es una lista que contiene un objeto con los metadatos descriptivos.
  - Título: `response['collection']['items'][i]['data'][0]['title']`
  - Descripción: `response['collection']['items'][i]['data'][0]['description']`
  - Palabras Clave: `response['collection']['items'][i]['data'][0]['keywords']` (una lista de strings)
  - NASA ID: `response['collection']['items'][i]['data'][0]['nasa_id']`

- **`links`**: Es una lista que contiene objetos, cada uno representando una versión o un archivo asociado al activo.

Un punto crucial es que la matriz `links` puede contener múltiples URLs para un solo activo: diferentes resoluciones de imagen, miniaturas, o incluso archivos de audio o subtítulos asociados.¹³ Por lo tanto, el código no debe simplemente tomar la primera URL que encuentre. Es necesario iterar a través de la lista `links` e inspeccionar las propiedades de cada enlace para tomar una decisión informada. 

Cada objeto de enlace tiene una propiedad `rel` (relación, e.g., 'preview', 'original') y `render` (tipo de medio, e.g., 'image', 'audio').

Para obtener la URL de una imagen en miniatura adecuada para una "carta de presentación", la lógica de programación debería buscar un objeto de enlace donde `render` sea 'image' y `rel` sea 'preview'. Para una imagen de mayor calidad, se buscaría `rel` como 'original'.

```json
// Ejemplo de la estructura de un 'item' en la respuesta
{
  "href": "https://images-api.nasa.gov/asset/PIA19048",
  "data": [{
      "nasa_id": "PIA19048",
      "title": "Europa: Chaotic Terrain",
      "keywords": ["Europa", "Jupiter", "moon", "satellite"],
      "description": "This image of Jupiter's moon Europa shows a region of chaotic terrain..."
    }
  ],
  "links": [
    {
      "href": "https://images-assets.nasa.gov/image/PIA19048/PIA19048~thumb.jpg",
      "rel": "preview",
      "render": "image"
    },
    {
      "href": "https://images-assets.nasa.gov/image/PIA19048/PIA19048.tif",
      "rel": "original",
      "render": "image"
    }
  ]
}
```

En el ejemplo anterior, `links[0]['href']` proporcionaría la URL de la miniatura, ideal para la vista de la tarjeta.

---

## Sección 3: Estrategia de Fusión de Datos y Flujo de Trabajo para Minería

Esta sección constituye el núcleo del informe, presentando un flujo de trabajo completo, robusto y escalable que integra las dos APIs para lograr el objetivo del proyecto: generar "cartas de presentación" de objetos del Sistema Solar combinando datos científicos e imágenes.

### 3.1. Arquitectura del Flujo de Trabajo Unificado

El siguiente algoritmo detalla una arquitectura de proceso de datos paso a paso, diseñada para ser automatizada y escalable, incorporando todas las técnicas y consideraciones discutidas en las secciones anteriores.

**Entrada**: Una lista de nombres de cuerpos celestes a procesar (e.g., `['Mars', 'Ceres', 'Halley']`).

**Iteración**: Para cada nombre en la lista de entrada:

#### Paso A (Validación y Enriquecimiento):
- Llamar al endpoint `horizons_lookup.api` con el nombre del objeto (`sstr={nombre}`).
- Si no se encuentra el objeto o la respuesta es ambigua, registrar el error y continuar con el siguiente objeto.
- Si tiene éxito, extraer y almacenar el `spkid` definitivo, el nombre canónico (`name`) y la lista de alias (`alias`).

#### Paso B (Obtención de Datos Científicos):
- Construir y ejecutar una consulta a `horizons.api` utilizando el `spkid` obtenido.
- Solicitar los datos físicos (`OBJ_DATA='YES'`) y las efemérides (`MAKE_EPHEM='YES'`) con las `QUANTITIES` deseadas.

#### Paso C (Análisis de Datos Científicos):
- Recibir la respuesta JSON de Horizons.
- Aplicar la función de análisis de texto personalizada (descrita en 1.5) al campo `result` para extraer los datos científicos en una estructura de datos limpia (e.g., un diccionario de Python).

#### Paso D (Construcción de Consulta de Imagen):
- Construir una consulta de búsqueda principal y optimizada para la API de Imágenes. 
- Utilizar el nombre canónico y el tipo de objeto extraído de Horizons. 
- Ejemplo: `q="{nombre_canónico}" {tipo_objeto}` (e.g., `q="Ceres" "dwarf planet"`).

#### Paso E (Recuperación y Validación de Imagen):
- Ejecutar la consulta contra el endpoint `/search` de la API de Imágenes, asegurándose de filtrar por `media_type=image`.
- Iterar a través de los resultados. Para cada resultado, realizar una validación de relevancia: comprobar si las `keywords` o la `description` del resultado contienen términos de contexto (e.g., si se busca Titán, verificar la presencia de "Saturn").
- Seleccionar la URL de la primera imagen que pase la validación. Extraer la URL de la miniatura (`rel: 'preview'`) y el título de la imagen.

#### Paso F (Estrategia de Respaldo - Fallback):
- Si la búsqueda principal del Paso E no devuelve resultados válidos, repetir el proceso utilizando los alias obtenidos en el Paso A como términos de búsqueda.
- Si todas las búsquedas fallan, asignar una URL de imagen de marcador de posición (placeholder) predeterminada para indicar que no se encontró una imagen.

#### Paso G (Combinación Final):
- Fusionar los datos científicos estructurados del Paso C y la información de la imagen (URL y título) del Paso E/F en un único objeto JSON.

#### Paso H (Almacenamiento):
- Guardar el objeto JSON combinado en un sistema de almacenamiento persistente (e.g., una base de datos, un archivo JSON en disco) para su uso posterior por parte de la aplicación web.

### 3.2. Implementación de Referencia Completa en Python

El siguiente script en Python proporciona una implementación de referencia modular y comentada del flujo de trabajo descrito anteriormente. Sirve como un plano de construcción directo y accionable para el proyecto.

```python
import requests
import json
import time
import re

# --- CONFIGURACIÓN ---
NASA_API_KEY = "SU_CLAVE_API_AQUI"  # Reemplazar con su clave API real
HORIZONS_API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
LOOKUP_API_URL = "https://ssd-api.jpl.nasa.gov/api/horizons_lookup.api"
IMAGE_API_URL = "https://images-api.nasa.gov/search"

def get_horizons_id(object_name):
    """Obtiene el SPK-ID y los alias de un objeto desde la API de lookup."""
    params = {'sstr': object_name, 'format': 'json'}
    try:
        response = requests.get(LOOKUP_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('count', 0) > 0 and 'result' in data:
            # Tomar el primer resultado para simplicidad
            first_result = data['result'][0]
            return {
                "spkid": first_result.get("spkid"),
                "name": first_result.get("name"),
                "aliases": first_result.get("alias", []),
                "type": first_result.get("type")
            }
    except requests.exceptions.RequestException as e:
        print(f"Error en la API de lookup para '{object_name}': {e}")
    return None

def get_horizons_data(spkid):
    """Obtiene datos de efemérides y físicos de la API principal de Horizons."""
    params = {
        'format': 'json',
        'COMMAND': f"'{spkid}'",
        'OBJ_DATA': 'YES',
        'MAKE_EPHEM': 'YES',
        'EPHEM_TYPE': 'OBSERVER',
        'CENTER': "'500@399'",
        'START_TIME': "'2025-01-01'",
        'STOP_TIME': "'2025-01-02'",
        'STEP_SIZE': "'1d'",
        'QUANTITIES': "'1,9,20'"
    }
    try:
        response = requests.get(HORIZONS_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error en la API de Horizons para SPK-ID '{spkid}': {e}")
    return None

def parse_horizons_result(horizons_response):
    """Analiza la cadena de texto 'result' de la respuesta de Horizons."""
    if not horizons_response or 'result' not in horizons_response:
        return {"error": "Respuesta de Horizons inválida o vacía."}
    
    result_text = horizons_response['result']
    parsed_data = {}
    
    # Ejemplo de extracción de un dato físico (Magnitud absoluta H)
    h_match = re.search(r'Absolute\s+magnitude,\s+H\s+=\s+([\d.]+)', result_text)
    if h_match:
        parsed_data['absolute_magnitude_H'] = float(h_match.group(1))

    # Ejemplo de análisis de la tabla de efemérides
    ephem_match = re.search(r'\$\$SOE(.*?)\$\$EOE', result_text, re.DOTALL)
    if ephem_match:
        ephem_block = ephem_match.group(1).strip()
        first_line = ephem_block.split('\n')[0]
        # Aquí iría una lógica de parseo más robusta
        parsed_data['ephemeris_first_line'] = first_line

    return parsed_data

def find_object_image(object_info):
    """Busca una imagen relevante en la NASA Image Library."""
    search_terms = [object_info['name']] + object_info.get('aliases', [])
    
    for term in search_terms:
        # Construir una consulta más específica
        query = f'"{term}" {object_info.get("type", "")}'
        params = {
            'q': query,
            'media_type': 'image'
        }
        try:
            response = requests.get(IMAGE_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['collection']['metadata']['total_hits'] > 0:
                # Tomar la primera imagen y su miniatura
                first_item = data['collection']['items'][0]
                image_data = {
                    "title": first_item['data'][0].get('title'),
                    "url": first_item['links'][0].get('href') if first_item.get('links') else None
                }
                return image_data
        except requests.exceptions.RequestException as e:
            print(f"Error en la API de Imágenes para la búsqueda '{query}': {e}")
        
        time.sleep(1)  # Respetar los límites de la API

    return {"title": "No se encontró imagen", "url": "url_placeholder.jpg"}

def main():
    """Función principal para orquestar el flujo de trabajo."""
    object_list = ['Vesta', '99942 Apophis', '1P/Halley']
    final_data = []

    for name in object_list:
        print(f"--- Procesando: {name} ---")
        
        # Paso A: Validar
        object_info = get_horizons_id(name)
        if not object_info or not object_info.get('spkid'):
            print(f"No se pudo encontrar un ID único para {name}. Saltando.")
            continue
        
        time.sleep(1)  # Pausa entre llamadas a APIs

        # Pasos B y C: Obtener y analizar datos de Horizons
        horizons_raw_data = get_horizons_data(object_info['spkid'])
        scientific_data = parse_horizons_result(horizons_raw_data)
        
        time.sleep(1)

        # Pasos D, E, F: Encontrar imagen
        image_data = find_object_image(object_info)
        
        # Paso G: Combinar
        combined_object = {
            "id": object_info['spkid'],
            "name": object_info['name'],
            "type": object_info['type'],
            "image": image_data,
            "scientific_data": scientific_data
        }
        final_data.append(combined_object)
        
        print(f"Datos combinados para {object_info['name']} generados.")
        
    # Paso H: Guardar
    with open('solar_system_data.json', 'w') as f:
        json.dump(final_data, f, indent=2)
    
    print("\nProceso completado. Datos guardados en 'solar_system_data.json'.")

if __name__ == "__main__":
    main()
```

### 3.3. Consideraciones para la Escalabilidad y Minería de Datos

El objetivo de "minería de datos" implica procesar potencialmente cientos o miles de objetos. Un bucle simple, como el del ejemplo, se encontraría rápidamente con los límites de tasa de las APIs.¹⁴ Para construir un sistema robusto y escalable, se deben implementar dos estrategias clave: **caching** y **throttling**.

#### Estrategia de Caching (Almacenamiento en Caché)
Antes de realizar cualquier llamada a una API para un objeto determinado, el sistema debe verificar si los datos de ese objeto ya han sido recuperados y almacenados localmente. Se puede implementar una caché simple usando archivos JSON nombrados con el SPK-ID del objeto, o una solución más robusta como una base de datos SQLite. 

Si los datos existen en la caché y no son demasiado antiguos (e.g., más de 30 días), se utilizan directamente, evitando una llamada innecesaria a la API. Esto reduce drásticamente el número de solicitudes y acelera las ejecuciones posteriores.

#### Estrategia de Throttling (Regulación)
Para respetar los límites de tasa de las APIs (e.g., 1,000 solicitudes/hora), es fundamental introducir una pequeña pausa entre solicitudes consecutivas. Una simple llamada a `time.sleep(1)` en Python entre cada llamada a la API, como se muestra en el script de ejemplo, es una forma efectiva de asegurar que no se exceda el límite y se eviten bloqueos.

Finalmente, para almacenar los datos combinados de manera eficiente, se propone el siguiente esquema de datos. Este esquema puede servir como modelo para una tabla en una base de datos relacional (como PostgreSQL) o un documento en una base de datos NoSQL (como MongoDB).

#### Tabla 4: Esquema de Datos Combinados Sugerido para Almacenamiento

| Campo | Tipo de Dato | Descripción |
|-------|--------------|-------------|
| `object_id` | VARCHAR (Clave Primaria) | El SPK-ID único del objeto, obtenido de Horizons. |
| `primary_name` | TEXT | El nombre canónico del objeto (e.g., "4 Vesta"). |
| `object_type` | TEXT | El tipo de objeto (e.g., "asteroid", "comet", "planetary satellite"). |
| `image_url` | TEXT | La URL de la imagen seleccionada de la Biblioteca de Imágenes. |
| `image_title` | TEXT | El título asociado a la imagen. |
| `horizons_data` | JSONB o TEXT | Un campo JSON que contiene todos los datos científicos parseados de Horizons. |
| `last_updated` | TIMESTAMP | La fecha y hora de la última actualización del registro, para gestionar la caché. |

Este esquema proporciona una base sólida para el backend de la aplicación web, permitiendo consultas eficientes para recuperar los datos necesarios para construir las "cartas de presentación".

---

## Sección 4: Diseño de la "Carta de Presentación" y Recomendaciones para el Frontend

Esta sección final sirve de puente entre el pipeline de datos del backend y la aplicación web orientada al usuario, ofreciendo recomendaciones sobre cómo estructurar y presentar la información combinada de manera efectiva.

### 4.1. Estructura de Datos Óptima para el Consumo Web (API del Lado del Servidor)

Aunque la base de datos almacena una gran cantidad de información detallada, no es eficiente ni práctico enviar todo el objeto de datos crudos al cliente (navegador web). El backend del proyecto debería exponer su propia API que sirva una versión curada y simplificada de los datos, optimizada para el renderizado de una "carta de presentación".

Esta API interna debería tomar el objeto de datos combinado de la base de datos y transformarlo en una estructura limpia y fácil de consumir para el frontend. A continuación se muestra un ejemplo de la estructura JSON ideal que la API del servidor podría devolver para un solo objeto:

```json
{
  "name": "4 Vesta",
  "type": "Asteroide",
  "imageUrl": "https://images-assets.nasa.gov/image/PIA15678/PIA15678~thumb.jpg",
  "summary": "Vesta es uno de los objetos más grandes del cinturón de asteroides, con un diámetro medio de unos 525 kilómetros. Es el segundo asteroide más masivo después del planeta enano Ceres.",
  "dataPoints": [
    {"label": "Diámetro", "value": "525", "unit": "km"},
    {"label": "Distancia del Sol", "value": "2.36", "unit": "AU"},
    {"label": "Magnitud Absoluta", "value": "3.20", "unit": "mag"}
  ],
  "sourceLink": "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=Vesta"
}
```

Esta estructura es ideal porque:

- Es ligera y contiene solo la información necesaria para la vista.
- Los `dataPoints` están en un formato de lista de objetos (`label`, `value`, `unit`), lo que permite al frontend iterar y renderizarlos fácilmente sin necesidad de lógica compleja.
- Incluye un `summary` pre-generado y un `sourceLink` para más información.

### 4.2. Mejores Prácticas y Consideraciones Finales

Para completar el proyecto y asegurar una experiencia de usuario de alta calidad y un uso responsable de los datos, se deben tener en cuenta las siguientes consideraciones:

#### Atribución
Es un requisito legal y ético proporcionar una atribución clara a las fuentes de los datos y las imágenes. Las directrices de la NASA estipulan que se debe acreditar a "NASA" o, más específicamente, a "NASA/JPL" para los datos de Horizons.¹⁷ Esta atribución debe ser visible en cada "carta de presentación" o en un pie de página general en la aplicación.

#### Manejo de Datos Faltantes
El flujo de trabajo debe anticipar que no siempre se encontrarán todos los datos. La interfaz de usuario (UI) debe manejar estos casos con elegancia.

- Si no se encuentra una imagen (`image_url` es el marcador de posición), la tarjeta debería mostrar un gráfico genérico del tipo de objeto (e.g., un icono de asteroide) o un mensaje claro de "Imagen no disponible".
- Si un punto de dato científico específico no está disponible en la respuesta de Horizons, ese campo simplemente no debería mostrarse en la tarjeta, en lugar de mostrar "N/A" o un error.

#### Enlaces Profundos (Deep Linking)
Para potenciar el aspecto de "exploración científica" del proyecto, cada tarjeta debería incluir enlaces que dirijan al usuario a las fuentes originales. El campo `sourceLink` en el JSON de ejemplo podría apuntar al JPL Small-Body Database Browser para el objeto específico, y la propia imagen podría ser un enlace a su página en la NASA Image and Video Library. Esto añade valor y credibilidad al proyecto, permitiendo a los usuarios curiosos profundizar en la información.

---

## Referencias

1. NASA JPL Horizons System Documentation
2. JPL Horizons API Documentation
3. NASA API Portal
4. Horizons Lookup API Documentation
5. NASA Images and Video Library API Documentation

---
