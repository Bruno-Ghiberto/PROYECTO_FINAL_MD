"""
scrape_objects.py
-------------------

Este módulo contiene dos funciones principales para realizar web scraping de
dos sitios distintos que ofrecen datos relacionados con el Sistema Solar. En
ambos casos se emplean buenas prácticas de scraping: se utiliza un agente
de usuario personalizado, se respetan tiempos de espera entre peticiones
y se documenta cuidadosamente el proceso para que cualquier usuario pueda
adaptarlo a sus necesidades.  

Funciones:

* ``scrape_wikipedia_objects_by_size`` – Extrae las tablas de la página de
  Wikipedia “List of Solar System objects by size” para varias secciones de
  interés (objetos con radios mayores de 400 km, de 200 a 399 km, etc.) y
  descarga las imágenes asociadas en una carpeta local.

* ``scrape_johnstons_physical_data`` – Descarga la página de Johnston’s Archive
  que contiene una tabla de datos físicos para planetas y satélites y
  convierte dicha tabla de texto en un ``pandas.DataFrame``.

Dependencias:
``requests``, ``beautifulsoup4``, ``pandas``, ``lxml``.

Para ejecutar este módulo como script se incluyen ejemplos al final
en un ``if __name__ == '__main__'``.
"""

from __future__ import annotations

import os
import re
import time
import csv
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup
import pandas as pd


def _clean_text(text: str) -> str:
    """Elimina referencias de notas [1], [2] y espacios redundantes.

    Wikipedia incluye referencias en la forma ``[n]`` después de muchos
    valores (por ejemplo ``6 371±1[15]``). Estas notas no son parte del
    dato en sí y pueden eliminarse para simplificar el análisis posterior.

    Args:
        text: cadena de texto original extraída de una celda HTML.

    Returns:
        Cadena de texto limpia sin notas y espacios extra.
    """
    # Eliminar notas [1], [2], [a], etc. Las notas suelen estar dentro
    # de corchetes. Utilizamos una expresión regular que elimina todo
    # bloque entre corchetes cuadrados incluyendo las referencias de
    # notas y los números de parámetro (p. ej., [15], [a]).
    text_no_refs = re.sub(r"\[[^\]]*\]", "", text)
    # Sustituir múltiples espacios consecutivos por un solo espacio y recortar
    return re.sub(r"\s+", " ", text_no_refs).strip()


def scrape_wikipedia_objects_by_size(
    output_csv: str = "../../data/raw/scraping_data/wikipedia_objects_by_size.csv",
    images_dir: str = "../../data/raw/wikipedia_images",
    delay: float = 1.0,
) -> pd.DataFrame:
    """Descarga tablas de la página de Wikipedia 'List of Solar System objects by size'.

    Esta función navega por la estructura HTML de Wikipedia para localizar
    las secciones especificadas en la consigna: "Objects with radii over
    400 km", "From 200 to 399 km", "From 100 to 199 km", "From 50 to
    99 km", "From 20 to 49 km", "From 1 to 19 km" y "Below 1 km". Para cada
    sección localiza la tabla inmediatamente posterior al título y extrae
    todas las filas. Además descarga las imágenes de la primera columna y
    las guarda en un directorio local.  

    Args:
        output_csv: ruta del fichero CSV donde guardar la tabla resultante.
        images_dir: carpeta donde se guardarán las imágenes descargadas.
        delay: tiempo (en segundos) a esperar entre descargas de imágenes
            para respetar el ``crawl-delay`` de Wikipedia.

    Returns:
        ``pandas.DataFrame`` con todas las filas de las tablas concatenadas.

    Raises:
        ``requests.HTTPError`` si la página de Wikipedia no se puede
        descargar (por ejemplo, por cambios en la URL o conectividad).
    """
    url = "https://en.wikipedia.org/wiki/List_of_Solar_System_objects_by_size"
    headers = {
        # User‑Agent personalizado para identificar este scraper.  
        # Wikipedia recomienda utilizar un UA descriptivo.
        "User-Agent": "SolarSystemScraper/1.0 (+https://example.com)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  # Lanza excepción si la respuesta no es 200

    soup = BeautifulSoup(response.content, "lxml")

    # Lista de ids de las secciones que se van a procesar.  
    # Los ids de los titulares de Wikipedia sustituyen espacios por guiones bajos.
    section_ids = [
        "Objects_with_radii_over_400_km",
        "From_200_to_399_km",
        "From_100_to_199_km",
        "From_50_to_99_km",
        "From_20_to_49_km",
        "From_1_to_19_km",
        "Below_1_km",
    ]

    # Crear directorios si no existen
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    all_rows: List[Dict[str, str]] = []

    for sec_id in section_ids:
        # Buscar el span con id=sec_id y clase mw-headline
        heading = soup.find(id=sec_id)
        if not heading:
            print(f"No se encontró la sección con id '{sec_id}'.")
            continue

        # La tabla más cercana después del título
        # Nos movemos al siguiente elemento hermano hasta encontrar una tabla
        next_el = heading.parent.find_next_sibling()
        table = None
        while next_el:
            if next_el.name == "table" and "wikitable" in next_el.get("class", []):
                table = next_el
                break
            next_el = next_el.find_next_sibling()
        if table is None:
            print(f"No se encontró tabla para la sección '{sec_id}'.")
            continue

        # Procesar cabecera de la tabla para obtener los nombres de las columnas
        header_cells = table.find("tr").find_all(["th", "td"])
        colnames = [_clean_text(cell.get_text(separator=" ")) for cell in header_cells]

        # Las tablas siempre deberían comenzar con 'Body' o similar
        # Si la primera columna es 'Body[ note 1 ]' o tiene alguna nota, limpiar
        # colnames ahora contiene nombres limpios sin referencias.

        # Procesar filas de datos
        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["th", "td"])
            if not cells:
                continue
            # Iniciar diccionario con el nombre de la sección actual
            row_data: Dict[str, str] = {"section": sec_id}

            for idx, colname in enumerate(colnames):
                # Si hay menos celdas que cabeceras es porque la tabla puede
                # contener celdas combinadas. Asegurar índice válido.
                if idx >= len(cells):
                    row_data[colname] = ""
                    continue

                cell = cells[idx]
                # Si la columna es la de la imagen (normalmente la segunda),
                # descargar la imagen y devolver su ruta
                if colname.lower().startswith("image"):
                    img_tag = cell.find("img")
                    if img_tag and img_tag.get("src"):
                        # Completar URL relativa (comienza con //)
                        img_url = img_tag["src"]
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        # Nombre de archivo basado en el texto del primer campo
                        # (nombre del objeto) o índice único si no existe.
                        # Extraemos el nombre de la imagen de la URL
                        img_name = os.path.basename(img_url.split("/")[-1])
                        img_path = os.path.join(images_dir, img_name)
                        # Verificar si la imagen ya existe antes de descargar
                        if os.path.exists(img_path):
                            print(f"[SKIP] Imagen ya existe: {img_name}")
                        else:
                            try:
                                print(f"[DOWNLOAD] Descargando: {img_name}")
                                img_resp = requests.get(img_url, headers=headers, timeout=10)
                                img_resp.raise_for_status()
                                with open(img_path, "wb") as img_file:
                                    img_file.write(img_resp.content)
                                print(f"[OK] Descargada: {img_name}")
                                # Respetar retraso entre descargas
                                time.sleep(delay)
                            except Exception as e:
                                print(f"[ERROR] No se pudo descargar {img_name}: {type(e).__name__}")
                        row_data[colname] = img_path
                    else:
                        row_data[colname] = ""
                else:
                    # Obtener texto de la celda y limpiar notas
                    text = cell.get_text(separator=" ")
                    row_data[colname] = _clean_text(text)

            all_rows.append(row_data)

    # Convertir a DataFrame. Pandas ajustará automáticamente los tipos.
    df = pd.DataFrame(all_rows)
    # Guardar CSV (encoding='utf-8' para caracteres especiales)
    if output_csv:
        df.to_csv(output_csv, index=False, encoding="utf-8")

    return df


def scrape_johnstons_physical_data(
    output_csv: str = "../../data/raw/scraping_data/johnstons_physical_data.csv",
) -> pd.DataFrame:
    """Extrae la tabla de datos físicos del sitio de Johnston’s Archive.

    La página de Johnston contiene una tabla en formato de texto preformateado
    (no está en una etiqueta ``<table>`` estándar). Cada fila está separada
    por líneas de guiones y los valores están alineados mediante espacios.

    Esta función descarga la página, localiza el bloque de líneas que
    corresponde a la tabla y utiliza ``pandas.read_fwf`` (Fixed Width File)
    para inferir las columnas automáticamente. Aunque ``read_fwf`` no
    siempre acierta al 100 % con formatos muy complejos, proporciona un
    punto de partida razonable que puede refinarse ajustando las anchuras
    de las columnas si es necesario.

    Args:
        output_csv: ruta del fichero CSV donde guardar la tabla resultante.

    Returns:
        ``pandas.DataFrame`` con los datos extraídos de la tabla.
    """
    url = "https://www.johnstonsarchive.net/astro/solar_system_phys_data.html"
    headers = {
        "User-Agent": "SolarSystemScraper/1.0 (+https://example.com)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    html = response.text

    soup = BeautifulSoup(html, "lxml")

    # El contenido de la tabla se encuentra después de la explicación de las
    # columnas y antes de la sección de referencias o fuentes. Analizaremos
    # todas las líneas de texto dentro del documento y buscaremos la fila
    # que contiene 'number      name' y a partir de ahí recopilaremos
    # las líneas hasta que aparezcan múltiples guiones consecutivos.
    text = soup.get_text("\n")
    lines = text.splitlines()
    # Buscar el índice de inicio de la tabla. Usamos una expresión regular
    # que detecta una línea que comienza con espacios opcionales, seguida
    # de la palabra 'number' y luego 'name' separados por espacios.
    start_idx = None
    for i, line in enumerate(lines):
        if re.search(r"\bnumber\s+name\b", line):
            start_idx = i
            break
    if start_idx is None:
        raise ValueError("No se encontró el inicio de la tabla en la página.")
    # Recopilar líneas hasta la próxima línea vacía después de que la tabla
    # termine. La tabla se compone de bloques separados por líneas de
    # guiones ('-' repetidos). Continuaremos recopilando hasta que haya
    # más de 5 líneas consecutivas sin datos (como una heurística sencilla).
    table_lines: List[str] = []
    # A contadores para decidir cuándo parar. Consideramos que una línea es
    # vacía o separador si contiene solo guiones y espacios.
    empty_count = 0
    for line in lines[start_idx:]:
        # Línea con guiones o vacía
        if re.fullmatch(r"[\-\s]*", line):
            empty_count += 1
        else:
            empty_count = 0
        # Añadir la línea siempre; se eliminarán separadores más adelante
        table_lines.append(line)
        # Si alcanzamos 8 líneas consecutivas vacías o separadores, asumimos
        # que la tabla ha terminado.
        if empty_count >= 8:
            break

    # Filtrar líneas que son separadores (guiones) o están vacías
    data_lines = [ln for ln in table_lines if not re.fullmatch(r"[\-\s]*", ln)]

    # Unir las líneas en un único bloque de texto separado por saltos de línea
    table_text = "\n".join(data_lines)

    # Intentar inferir automáticamente las posiciones de las columnas
    # mediante read_fwf. Pandas buscará columnas basándose en espacios.
    from io import StringIO
    df = pd.read_fwf(StringIO(table_text))
    # Crear directorio para CSV si no existe
    if output_csv:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding="utf-8")
    return df


if __name__ == "__main__":
    print("=== Iniciando scraping de datos del Sistema Solar ===")
    
    try:
        print("Descargando tablas de Wikipedia...")
        df_wiki = scrape_wikipedia_objects_by_size()
        print(f"[OK] Se han extraido {len(df_wiki)} filas de Wikipedia y guardado en CSV.")
        print(f"[INFO] Archivo guardado: data/raw/scraping_data/wikipedia_objects_by_size.csv")
        print(f"[INFO] Imagenes guardadas en: data/raw/wikipedia_images/")
    except Exception as e:
        print(f"[ERROR] Error con Wikipedia: {e}")
    
    try:
        print("\nDescargando tabla de Johnston's Archive...")
        df_john = scrape_johnstons_physical_data()
        print(f"[OK] Tabla de Johnston contiene {len(df_john)} filas.")
        print(f"[INFO] Archivo guardado: data/raw/scraping_data/johnstons_physical_data.csv")
    except Exception as e:
        print(f"[ERROR] Error con Johnston's Archive: {e}")
    
    print("\n=== Scraping completado ===")