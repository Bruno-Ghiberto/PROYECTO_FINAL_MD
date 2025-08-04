A continuación se detalla una estrategia de scraping para cada sitio seleccionado y se adjunta el código en Python que implementa dicha estrategia.  Se explica en detalle cómo se ha analizado la estructura de cada página y cómo se procesan los datos, de modo que puedas aprender y adaptarlo a tus necesidades.

## 1. Wikipedia – “List of Solar System objects by size”

### Análisis del sitio

El artículo de Wikipedia contiene varias secciones con títulos como “Objects with radii over 400 km”, “From 200 to 399 km”, etc. Cada título va seguido de una tabla con columnas como **Body**, **Image**, **Radius**, **Volume**, **Mass**, etc.  La primera columna suele incluir el nombre del cuerpo y un enlace a su artículo; la segunda contiene una miniatura de una imagen, y las demás columnas incluyen valores numéricos.

Las tablas están marcadas con la clase `wikitable` y el encabezado de cada sección está contenido en un elemento `<span>` cuyo atributo `id` coincide con el título con espacios sustituidos por guiones bajos (por ejemplo `Objects_with_radii_over_400_km`). Esto nos permite localizar rápidamente la tabla que sigue a cada título.

### Estrategia de scraping

1. **Descarga de la página**: Se utiliza `requests.get` con un *User‑Agent* descriptivo para evitar que Wikipedia interprete la solicitud como un bot anónimo.
2. **Identificación de secciones**: Se define una lista de IDs de las secciones de interés (por ejemplo `Objects_with_radii_over_400_km`). Con `BeautifulSoup` se busca el elemento con ese ID y a partir de su elemento padre se avanza hasta encontrar la siguiente tabla con clase `wikitable`.
3. **Extracción de datos**:

   * Se obtiene el encabezado (`<th>` o `<td>`) para conocer las columnas. Se limpia el texto eliminando referencias entre corchetes (como `[15]`) y espacios redundantes.
   * Cada fila de la tabla se recorre y se construye un diccionario con las columnas.
   * En la columna **Image** se localiza la etiqueta `<img>` y se forma la URL completa (suelen empezar por `//upload.wikimedia.org/`). Se descarga el fichero con `requests` y se guarda en un directorio local; la ruta del fichero guardado se incluye en la fila.
4. **Construcción de la tabla final**: Todas las filas se almacenan en una lista y luego se convierten en un `pandas.DataFrame`. Opcionalmente se guarda en un CSV.

En el código se incluye un retraso configurable (`delay`) entre descargas de imágenes para respetar el `crawl-delay` de Wikipedia.

## 2. Johnston’s Archive – “Physical data for solar system planets and satellites”

### Análisis del sitio

En Johnston’s Archive, los datos no están en una tabla HTML sino en texto preformateado. El contenido empieza con una explicación de las columnas y, a continuación, aparece una tabla donde cada fila se muestra como una línea de texto alineada con espacios. Las líneas se separan mediante filas de guiones.

Para extraer los datos es necesario tratar ese bloque de texto como un archivo de ancho fijo: los valores de cada columna están separados por grupos de espacios y las filas no están encapsuladas en etiquetas `<tr>` o `<td>`.

### Estrategia de scraping

1. **Descarga de la página**: Al igual que en el caso anterior se usa `requests.get` con un *User‑Agent* personalizado.
2. **Localización del bloque de datos**: Se extrae todo el texto de la página y se identifica la línea que contiene los encabezados (“number name prov des …”). A partir de esa línea se recopilan las líneas siguientes hasta que se detectan varias líneas consecutivas formadas únicamente por guiones o espacios; esto indica el final de la tabla.
3. **Limpieza del texto**: Se eliminan las líneas de separación (guiones) para quedarse solo con las líneas que contienen datos.
4. **Parseo de ancho fijo**: Se emplea `pandas.read_fwf` (read fixed width file) para dejar que `pandas` infiera las posiciones de las columnas. Dado que el formato es complejo, esto da un primer esquema de columnas que después se puede ajustar manualmente si fuera necesario.

Al finalizar, los datos se escriben en un CSV y también se devuelven como `pandas.DataFrame`.

## Código de scraping

Puedes descargar el script completo para ambos sitios con el siguiente enlace:

{{file\:file-5Fpa6oSFzeCve2mYNfujLd}}

El código contiene comentarios detallados en español que explican cada paso, por lo que te resultará útil para aprender o modificarlo.  A grandes rasgos:

* La función `scrape_wikipedia_objects_by_size` define una lista de IDs de secciones, descarga la página de Wikipedia, localiza cada sección y su tabla asociada, extrae los valores, descarga las imágenes y construye un `DataFrame`.
* La función `scrape_johnstons_physical_data` descarga la página de Johnston, identifica el bloque de datos mediante una heurística simple, filtra las líneas relevantes y utiliza `pandas.read_fwf` para parsear las columnas.

Puedes ejecutar estas funciones en tu entorno así:

```python
from scrape_objects import scrape_wikipedia_objects_by_size, scrape_johnstons_physical_data

# Extraer tablas de Wikipedia (guarda imágenes en 'wikipedia_images')
df_wiki = scrape_wikipedia_objects_by_size(
    output_csv='wikipedia_objects_by_size.csv',
    images_dir='wikipedia_images',
    delay=1.5  # segundos entre descargas para respetar robots
)

# Extraer la tabla de Johnston’s Archive
df_john = scrape_johnstons_physical_data(
    output_csv='johnstons_physical_data.csv'
)
```

Esto generará los CSV con los datos de cada fuente y descargará las imágenes asociadas en la carpeta indicada.
