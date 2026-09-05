import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parámetros configurables
URL = "ejemplo.com"          # Cambia por la URL deseada
TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def scrape_page(url):
    """ Realiza el scraping de enlaces e imagenes de una pagina """
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error al obtener la pagina: {e}")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extraer enlaces con imagen dentro
    links_with_images = []
    for a_tag in soup.find_all('a', href=True):   # solo <a> con href
        href = a_tag['href']
        img_tag = a_tag.find('img')
        if not img_tag:
            continue   # Solo enlaces que contienen una imagen (cambia a 'if img_tag' para excluirlos)

        # Obtener src de la imagen (con fallback a data-src)
        img_src = img_tag.get('src') or img_tag.get('data-src')
        if not img_src:
            continue   # Si no hay fuente de imagen, saltamos

        img_abs = urljoin(url, img_src)

        # Texto del enlace (prioriza span si existe)
        span = a_tag.find('span')
        texto = span.get_text(strip=True) if span else a_tag.get_text(strip=True)
        texto = texto or None

        links_with_images.append({
            'url': urljoin(url, href),
            'img': img_abs,
            'texto': texto
        })

    return links_with_images

"""
    # Extraer todas las imágenes de la página
    all_images = []
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if not src:
            continue
        src_abs = urljoin(url, src)

        all_images.append({
            'src': src_abs,
            'alt': img.get('alt', '').strip() or None,
            'title': img.get('title', '').strip() or None,
            'width': img.get('width'),
            'height': img.get('height'),
            'srcset': img.get('srcset')   # opcional
        })

    return links_with_images #, all_images
"""
def save_to_json(data, filename):
    """ Guarda los datos en un archivo JSON en el directorio del script """
    output_path = Path(__file__).parent / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info(f"Datos guardados en {output_path}")


def save_to_text(data, filename):
    """ Guarda los url en un .txt """
    output_path = Path(__file__).parent / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(item['url'] + '\n')

if __name__ == "__main__":
    enlaces = scrape_page(URL)
    imagenes = scrape_page(URL)

    if enlaces is None:
        logging.error("No se pudo realizar el scraping.")
        exit(1)

    # Guardar en un solo archivo
    datos_completos = {
        "enlaces_con_imagen": enlaces,
        "todas_las_imagenes": imagenes
    }
    save_to_json(datos_completos, "datos_completos.json")
    save_to_text(enlaces, "enlaces.txt")

    # También puedes guardar por separado si lo prefieres
    # save_to_json(enlaces, "enlaces_con_imagen.json")
    # save_to_json(imagenes, "imagenes.json")

    logging.info(f"Se extrajeron {len(enlaces)} enlaces con imagen y {len(imagenes)} imagenes totales.")
    logging.info(f"Se extrajeron {len(enlaces)} enlaces con imagen.")
    logging.info(f"Se guardaron {len(enlaces)} URLs en .txt")
