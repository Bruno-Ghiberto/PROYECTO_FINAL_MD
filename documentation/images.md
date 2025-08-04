# API de Imágenes de NASA

## Descripción General

La API de **images.nasa.gov** está organizada en torno a **REST**. Nuestra API tiene URLs predecibles y orientadas a recursos, y utiliza códigos de respuesta HTTP para indicar errores de la API.

### Características principales:
- ✅ **Características HTTP integradas**: autenticación HTTP y verbos HTTP estándar
- ✅ **CORS habilitado**: intercambio de recursos de origen cruzado para aplicaciones web
- ✅ **Respuestas JSON**: todas las respuestas, incluidos los errores, devuelven JSON
- ✅ **Ejemplos incluidos**: fragmentos con curl, Unix pipes y Python

> **Nota**: Los ejemplos incluyen saltos de línea adicionales para legibilidad. Para ejecutarlos, elimina estos saltos de línea.

## URL Base

```
https://images-api.nasa.gov
```

## Endpoints Disponibles

| Endpoint | Descripción |
|----------|-------------|
| `/search` | Búsqueda de contenido multimedia |
| `/asset/{nasa_id}` | Manifiesto de un activo específico |
| `/metadata/{nasa_id}` | Metadatos de un activo |
| `/captions/{nasa_id}` | Subtítulos de videos |
| `/album/{album_name}` | Contenido de álbumes |

## ⚠️ Manejo de Errores

La API utiliza códigos de respuesta HTTP convencionales para indicar el éxito o fracaso de las solicitudes:

- **2xx**: Éxito ✅
- **4xx**: Error del cliente (parámetro faltante, búsqueda fallida, etc.) ❌
- **5xx**: Error del servidor (raros) 💥

> 💡 **Tip**: La mayoría de respuestas de error incluyen un atributo `reason` con detalles legibles.

### Códigos de Estado HTTP

| Código | Estado | Descripción |
|--------|--------|-------------|
| `200` | ✅ **OK** | Todo funcionó como se esperaba |
| `400` | ❌ **Bad Request** | Solicitud inaceptable (parámetro requerido faltante) |
| `404` | 🔍 **Not Found** | El recurso solicitado no existe |
| `500, 502, 503, 504` | 💥 **Server Errors** | Error del lado de la API (raros) |

### Recomendaciones

⚡ **Buenas prácticas**:
- Implementar manejo graceful de todos los códigos de estado HTTP
- Validar parámetros antes de enviar solicitudes
- Implementar reintentos para errores 5xx
- Verificar conectividad de red en caso de fallos

---

## 🔍 Endpoint: Búsqueda de Contenido

**Método**: `GET`  
**Ruta**: `/search?q={q}`

### Parámetros de Consulta

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `q` | `string` | ❌ | Términos de búsqueda de texto libre para comparar con metadatos |
| `center` | `string` | ❌ | Centro que publicó los medios |
| `description` | `string` | ❌ | Términos a buscar en los campos "Description" |
| `description_508` | `string` | ❌ | Términos a buscar en los campos "508 Description" |
| `keywords` | `string` | ❌ | Términos en "Keywords" (separar múltiples con comas) |
| `location` | `string` | ❌ | Términos a buscar en "Location" |
| `media_type` | `string` | ❌ | Tipos: `image`, `video`, `audio` (separar con comas) |
| `nasa_id` | `string` | ❌ | ID específico de NASA del activo |
| `page` | `integer` | ❌ | Número de página (inicio en 1) |
| `page_size` | `integer` | ❌ | Resultados por página (por defecto: 100) |
| `photographer` | `string` | ❌ | Nombre del fotógrafo principal |
| `secondary_creator` | `string` | ❌ | Nombre del fotógrafo/videógrafo secundario |
| `title` | `string` | ❌ | Términos a buscar en "Title" |
| `year_start` | `string` | ❌ | Año de inicio (formato: YYYY) |
| `year_end` | `string` | ❌ | Año de finalización (formato: YYYY) |

> ⚠️ **Importante**: Se requiere al menos un parámetro. Todos los valores deben estar codificados para URL.

### Ejemplos de Solicitud

#### Con curl y codificación automática:

```bash
curl -G https://images-api.nasa.gov/search \
  --data-urlencode "q=apollo 11" \
  --data-urlencode "description=moon landing" \
  --data-urlencode "media_type=image" | \
  python -m json.tool
```

#### URL pre-codificada:

```bash
curl "https://images-api.nasa.gov/search?q=apollo%2011&description=moon%20landing&media_type=image" | python -m json.tool
```

> 💡 **Tip**: La mayoría de bibliotecas HTTP manejan la codificación URL automáticamente.

### Respuesta de Ejemplo

Los resultados se devuelven en formato **Collection+JSON** con la siguiente estructura:

```json
{
  "collection": {
    "href": "https://images-api.nasa.gov/search?q=apollo%2011...",
    "items": [
      {
        "data": [
          {
            "center": "JSC",
            "date_created": "1969-07-21T00:00:00Z",
            "description": "AS11-40-5874 (20 July 1969)...",
            "keywords": [
              "APOLLO 11 FLIGHT",
              "MOON",
              "LUNAR SURFACE",
              "LUNAR BASES",
              "LUNAR MODULE",
              "ASTRONAUTS",
              "EXTRAVEHICULAR ACIVITY"
            ],
            "media_type": "image",
            "nasa_id": "as11-40-5874",
            "title": "Apollo 11 Mission image - Astronaut Edwin Aldrin poses beside..."
          }
        ],
        "href": "https://images-assets.nasa.gov/image/as11-40-5874/collection.json",
        "links": [
          {
            "href": "https://images-assets.nasa.gov/image/as11-40-5874/as11-40-5874~thumb.jpg",
            "rel": "preview",
            "render": "image"
          }
        ]
      }
      // ... 99 objetos más ...
    ],
    "links": [
      {
        "href": "https://images-api.nasa.gov/search?q=apollo+11...&page=2",
        "prompt": "Next",
        "rel": "next"
      }
    ],
    "metadata": {
      "total_hits": 336
    },
    "version": "1.0"
  }
}
```

#### Estructura de la Respuesta:

- **`collection.items[]`**: Array de resultados encontrados
- **`collection.metadata.total_hits`**: Total de elementos encontrados
- **`collection.links[]`**: Enlaces para paginación (siguiente, anterior)
- **`items[].data[]`**: Metadatos del elemento multimedia
- **`items[].links[]`**: Enlaces a diferentes tamaños de imagen

---

## 📄 Endpoint: Manifiesto de Activo

**Método**: `GET`  
**Ruta**: `/asset/{nasa_id}`

### Parámetros de Ruta

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `nasa_id` | `string` | ✅ | ID de NASA del activo de medios |

### Ejemplo de Solicitud

```bash
curl https://images-api.nasa.gov/asset/as11-40-5874 | python -m json.tool
```

### Respuesta de Ejemplo

Devuelve un manifiesto en formato **Collection+JSON** con todas las variantes disponibles:

```json
{
  "collection": {
    "href": "https://images-api.nasa.gov/asset/as11-40-5874",
    "items": [
      { "href": "https://images-assets.nasa.gov/image/as11-40-5874/as11-40-5874~orig.jpg" },
      { "href": "https://images-assets.nasa.gov/image/as11-40-5874/as11-40-5874~medium.jpg" },
      { "href": "https://images-assets.nasa.gov/image/as11-40-5874/as11-40-5874~small.jpg" },
      { "href": "https://images-assets.nasa.gov/image/as11-40-5874/as11-40-5874~thumb.jpg" },
      { "href": "https://images-assets.nasa.gov/image/as11-40-5874/metadata.json" }
    ],
    "version": "1.0"
  }
}
```

#### Tipos de Archivo Disponibles:

- **`~orig.jpg`**: Imagen original en máxima resolución
- **`~medium.jpg`**: Imagen en resolución media
- **`~small.jpg`**: Imagen en resolución pequeña  
- **`~thumb.jpg`**: Miniatura (thumbnail)
- **`metadata.json`**: Metadatos completos del activo

---

## 📋 Endpoint: Ubicación de Metadatos

**Método**: `GET`  
**Ruta**: `/metadata/{nasa_id}`

### Parámetros de Ruta

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `nasa_id` | `string` | ✅ | ID de NASA del activo de medios |

### Ejemplo de Solicitud

```bash
curl https://images-api.nasa.gov/metadata/as11-40-5874 | python -m json.tool
```

### Respuesta de Ejemplo

```json
{
  "location": "https://images-assets.nasa.gov/image/as11-40-5874/metadata.json"
}
```

> 📖 **Uso**: Descarga el archivo JSON desde la URL `location` para obtener los metadatos completos del activo.

---

## 🎬 Endpoint: Subtítulos de Video

**Método**: `GET`  
**Ruta**: `/captions/{nasa_id}`

### Parámetros de Ruta

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `nasa_id` | `string` | ✅ | ID de NASA del activo de video |

### Ejemplo de Solicitud

```bash
curl https://images-api.nasa.gov/captions/172_ISS-Slosh | python -m json.tool
```

### Respuesta de Ejemplo

```json
{
  "location": "https://images-assets.nasa.gov/video/172_ISS-Slosh/172_ISS-Slosh.srt"
}
```

> 📺 **Uso**: Descarga el archivo SRT o VTT desde la URL `location` para obtener los subtítulos del video.

#### Formatos Soportados:
- **`.srt`**: SubRip Subtitle (más común)
- **`.vtt`**: WebVTT (Web Video Text Tracks)

---

## 📁 Endpoint: Contenido de Álbum

**Método**: `GET`  
**Ruta**: `/album/{album_name}`

### Parámetros

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `album_name` | `string` | ✅ | Nombre del álbum (sensible a mayúsculas/minúsculas) |
| `page` | `integer` | ❌ | Número de página (inicio en 1) |

### Ejemplo de Solicitud

```bash
curl https://images-api.nasa.gov/album/apollo | python -m json.tool
```

### Respuesta de Ejemplo

Igual que las búsquedas, devuelve formato **Collection+JSON** con contenido del álbum:

```json
{
  "collection": {
    "href": "https://images-api.nasa.gov/album/apollo",
    "items": [
      {
        "data": [
          {
            "album": ["apollo"],
            "center": "GSFC",
            "date_created": "2017-11-06T00:00:00Z",
            "description": "A Black Brant IX suborbital sounding rocket is launched...",
            "keywords": [
              "NASA",
              "GSFC", 
              "Space Technology Demo at NASA Wallops"
            ],
            "media_type": "image",
            "nasa_id": "GSFC_20171102_Archive_e000579",
            "title": "Space Technology Demo at NASA Wallops"
          }
        ],
        "href": "https://images-assets.nasa.gov/image/GSFC_20171102_Archive_e000579/collection.json",
        "links": [
          {
            "href": "https://images-assets.nasa.gov/image/GSFC_20171102_Archive_e000579~thumb.jpg",
            "rel": "preview",
            "render": "image"
          }
        ]
      }
      // ... 99 objetos más ...
    ],
    "links": [
      {
        "href": "https://images-api.nasa.gov/album/apollo?page=2",
        "prompt": "Next",
        "rel": "next"
      }
    ],
    "metadata": {
      "total_hits": 302
    },
    "version": "1.0"
  }
}
```

#### Álbumes Populares:
- **`apollo`**: Misiones Apollo
- **`mars`**: Misiones y descubrimientos en Marte  
- **`hubble`**: Imágenes del Telescopio Hubble
- **`iss`**: Estación Espacial Internacional

---

## 🚀 ¡Comienza a Explorar!

### Enlaces Útiles:

- 🌐 **API Base**: https://images-api.nasa.gov
- 📚 **Documentación Oficial**: [NASA Images API](https://api.nasa.gov)
- 🎯 **Prueba la API**: [NASA API Portal](https://api.nasa.gov/#try-it-now)

### Tips de Uso:

💡 **Para desarrolladores**:
- Implementa cache local para mejorar rendimiento
- Usa `page_size` adecuado para tu aplicación
- Considera las limitaciones de rate limiting
- Maneja errores de red gracefully

---

*Documentación generada para el proyecto de Minería de Datos - NASA Images API*