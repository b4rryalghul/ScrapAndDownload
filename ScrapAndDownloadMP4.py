import requests
import re
from bs4 import BeautifulSoup as bsp
from urllib.parse import urljoin
from urllib.parse import urlparse
import os
import time
import csv
import datetime as dt
from pathlib import Path
import logging as lg
import yt_dlp as yp

# CONFIG 
BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "***.txt" # Specify the file with the links
CSV_OUTPUT = BASE_DIR / f"mp4_files_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
REQUEST_DELAY = 1.5
TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
DL_FOLDER = BASE_DIR / "Downloaded_videos"
MAX_RETRIES = 2 # NUMERO MAXIMO DE INTENTOS
COOKIES_FILE = BASE_DIR / "cookies.txt"  # Opcional


# configurar el logging (tambien guarda archivo)
LOG_FILE = BASE_DIR / f"scraper_log_{dt.datetime.now().strftime('%y%m%d_%H%M%S')}.log"
lg.basicConfig(
    level=lg.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        lg.FileHandler(LOG_FILE, encoding="utf-8"),
        lg.StreamHandler()
    ]
)


os.makedirs(DL_FOLDER, exist_ok=True)

def is_url_valid(url):
    # Validar si la url tiene esquema http,https
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
    
def get_mp4_url(url):
    """ Devuelve lista de MP4s y posible error """
    headers = {"User-Agent": USER_AGENT}
    mp4_encontrados = []
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=headers)
        resp.raise_for_status()
        html = resp.text
        final_url = resp.url

        sopa = bsp(html, 'html.parser')

        # 1. <video src="...">
        for tag in sopa.find_all("video"):
            src = tag.get("src")
            if src and src.strip():
                mp4_encontrados.append(urljoin(final_url, src))

        # 2. <source src="...">
        for tag in sopa.find_all("source"):
            src = tag.get("src")
            if src and src.strip():
                mp4_encontrados.append(urljoin(final_url, src))

        # 3. Cualquier etiqueta con href/src/data-src/data-url que termine en .mp4
        for tag in sopa.find_all(["a", "img", "div", "section", "video", "source"]):
            for attr in ["href", "src", "data-src", "data-url"]:
                val = tag.get(attr)
                if val and isinstance(val, str) and val.strip().lower().endswith(".mp4"):
                    mp4_encontrados.append(urljoin(final_url, val))

        # 4. Regex en todo el HTML
        regex_pattern = r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*'
        matches = re.findall(regex_pattern, html, re.IGNORECASE)
        mp4_encontrados.extend(matches)

        # 5. Eliminar duplicados (preservando orden)
        seen = set()
        unique = []
        for link in mp4_encontrados:
            if link not in seen:
                seen.add(link)
                unique.append(link)

        return unique, None

    except requests.exceptions.Timeout:
        return [], "Timeout"
    except requests.exceptions.ConnectionError:
        return [], "Connection Error"
    except requests.exceptions.HTTPError as e:
        return [], f"HTTP {e.response.status_code}"
    except Exception as e:
        return [], f"Other error: {str(e)}"

def complex_download(url, folder):
    """ Usa yt-dlp para obtener la URL directa del video de sitios como VK """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "cookiesfrombrowser": ("chrome",),  # Usa cookies de Chrome
        # Si prefieres usar cookies.txt, descomenta la siguiente línea:
        # "cookiefile": str(COOKIES_FILE),
    }

    try:
        with yp.YoutubeDL(ydl_opts) as ydl:
            # Extrae la información del video sin descargarlo
            info = ydl.extract_info(url, download=False)
            
            # Busca la URL directa del video
            # Puede estar en 'url' o dentro de la lista 'formats'
            direct_url = info.get('url')
            if not direct_url and 'formats' in info:
                # Si hay varios formatos, elige el de mejor calidad
                # (normalmente el último de la lista)
                direct_url = info['formats'][-1]['url']
            
            if not direct_url:
                return "ERROR: No se pudo obtener la URL directa"

            print(f"   URL directa obtenida: {direct_url[:100]}...")
            # Una vez obtenida la URL directa, usa la función de descarga normal
            return download_file(direct_url, folder)

    except Exception as e:
        print(f"    Error con yt-dlp: {e}")
        return f"ERROR: yt-dlp - {str(e)}"

def download_file(url, folder, retries=MAX_RETRIES):
    """ caso 1 - Descarga de sitios complicados """
    complex_sites = ["vk.com", "vkvideo.ru", "youtube.com", "youtu.be", "x.com"]

    if any(site in url for site in complex_sites):
        print(f" Downlading using yt-dlp: {url}")
        return complex_download(url, folder)



    """ caso 2 - Otherwise, descarga directa """
    filename = url.split("/")[-1].split("?")[0]
    if not filename.endswith(".mp4"):
        filename = f"video_{hash(url)}.mp4"

    filepath = os.path.join(folder, filename)

    # Saltar si ya existe
    if os.path.exists(filepath):
        lg.info(f" Saltado (ya existe): {filename}")
        return "SKIPPED"

    # Intentar descargar, se agregan intentos
    for intento in range(retries + 1):
        try:
            lg.info(f" Descargando: {filename} (intento {intento+1}/{retries+1})")
            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()

            with open(filepath, "wb") as f:
                for parte in r.iter_content(chunk_size=8192):
                    f.write(parte)

            lg.info(f" Guardado: {filename}")
            return "DOWNLOADED"

        except Exception as e:
            if intento < retries:
                lg.warning(f" Intento {intento+1} fallo: {str(e)}. Reintentando...")
                time.sleep(2 ** intento)

            else:
                lg.error(f" Error after {retries+1} intentos: {url} - {e}")
                return f"Error: {str(e)}"


def main():
    # 1 - Leer URLs del archivo
    try:
        with open(INPUT_FILE, 'r', encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        lg.error(f" Error: Archivo no encontrado '{INPUT_FILE}'")
        return

    if not urls:
        lg.warning("El archivo está vacío.")
        return

    lg.info(f"Escaneando {len(urls)} websites...\n")
    resultado = []

    for idx, url in enumerate(urls, start=1):
        lg.info(f"[{idx}/{len(urls)}] Escaneando: {url}")

        # 2. Obtener lista de MP4s de esta página
        lista_mp4, error = get_mp4_url(url)

        # 3. Si hay error, guardar y pasar a la siguiente URL
        if error:
            lg.error(f"    Error: {error}")
            resultado.append({
                "url": url,
                "mp4_count": 0,
                "download_status": "N/A",
                "mp4_links": "",
                "status": f"ERROR: {error}"
            })
            # delay antes de pasar a la siguiente pag
            if idx < len(urls):
                time.sleep(REQUEST_DELAY)
            continue

        # 4. Si no hay MP4s, guardar y pasar a la siguiente
        if not lista_mp4:
            lg.info("    No MP4s found")
            resultado.append({
                "url": url,
                "mp4_count": 0,
                "download_status": "N/A",
                "mp4_links": "",
                "status": "OK (none found)"
            })
            # Delay
            if idx < len(urls):
                time.sleep(REQUEST_DELAY)
            continue

        # 5. Descarga mp4 encontrados
        lg.info(f"    Found {len(lista_mp4)} MP4(s). Downloading...")
        download_status_list = []
        for mp4 in lista_mp4:
            lg.info(f"       {mp4}")
            status = download_file(mp4, DL_FOLDER)
            download_status_list.append(f"{mp4} [{status}]")
            time.sleep(0.5)  # Pausa entre descargas

        # 6. Guardar resultado de esta página en el CSV
        resultado.append({
            "url": url,
            "mp4_count": len(lista_mp4),
            "download_status": " | ".join(download_status_list),
            "mp4_links": " | ".join(lista_mp4),
            "status": "OK"
        })

        # Pausa entre sitios web, a menos que sea la ultima
        if idx < len(urls):
            time.sleep(REQUEST_DELAY)

    # 7. Escribir el CSV final
    
    try:
        with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "mp4_count", "download_status", "mp4_links", "status"])
            writer.writeheader()
            writer.writerows(resultado)
        lg.info(f"\n CSV Report saved: {CSV_OUTPUT}")
    except Exception as e:
        lg.error(f"Error trying to save CSV: {e}")

    # 8. Estadisticas finales
    total_pages = len(resultado)
    total_mp4 = sum(r["mp4_count"] for r in resultado)
    lg.info(f"\n{'='*60}")
    lg.info(f"Process Complete")
    lg.info(f"Downloads: {DL_FOLDER}")
    lg.info(f"Report: {CSV_OUTPUT}")
    lg.info(f"Resumen: {total_pages} pages, {total_mp4} MP4s found")
    lg.info(f"Log: {LOG_FILE}")
    lg.info(f"="*60)

if __name__ == "__main__":
    main()