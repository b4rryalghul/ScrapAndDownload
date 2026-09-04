# Web Scraping Tools

Colección de scripts en Python para extraer recursos de páginas web y localizar o descargar archivos de video.

## Contenido

### `scrapper.py`

Script de scraping general que:

- Extrae enlaces que contienen imágenes.
- Obtiene URLs absolutas de imágenes.
- Recupera metadatos básicos como `alt`, `title`, `width`, `height` y `srcset`.
- Guarda los resultados en formato JSON.

La URL objetivo se configura directamente en:

```python
URL = "https://example.com"
```

El resultado principal se guarda como:

```text
datos_completos.json
```

### `ScrapAndDownloadMP4.py`

Script orientado a localizar y descargar archivos de video.

Puede:

- Leer una lista de URLs desde un archivo `.txt`.
- Detectar archivos MP4 en etiquetas `<video>` y `<source>`.
- Buscar enlaces MP4 en atributos HTML y mediante expresiones regulares.
- Descargar archivos directamente mediante `requests`.
- Usar `yt-dlp` para algunos sitios que requieren extracción adicional.
- Reintentar descargas fallidas.
- Evitar descargar nuevamente archivos existentes.
- Generar un reporte CSV con los resultados.
- Generar un archivo de log de la ejecución.

## Requisitos

- Python 3.10 o superior recomendado.
- Acceso a Internet.
- Dependencias incluidas en `requirements.txt`.

Instalación:

```bash
pip install -r requirements.txt
```

## Uso

### 1. Scraping de enlaces e imágenes

Edita la variable `URL` en `scrapper.py`:

```python
URL = "https://example.com"
```

Después ejecuta:

```bash
python scrapper.py
```

El script generará `datos_completos.json` en el mismo directorio.

### 2. Búsqueda y descarga de MP4

En `ScrapAndDownloadMP4.py`, configura el archivo de entrada:

```python
INPUT_FILE = BASE_DIR / "links.txt"
```

Crea `links.txt` en la carpeta del proyecto y añade una URL por línea:

```text
https://example.com/page-1
https://example.com/page-2
```

Ejecuta:

```bash
python ScrapAndDownloadMP4.py
```

Los videos se guardarán en:

```text
Downloaded_videos/
```

También se generarán:

```text
mp4_files_report_YYYYMMDD_HHMMSS.csv
scraper_log_YYMMDD_HHMMSS.log
```

## Cookies y `yt-dlp`

El script de descarga está configurado para intentar utilizar las cookies de Chrome:

```python
"cookiesfrombrowser": ("chrome",)
```

También existe soporte previsto para un archivo `cookies.txt`. Si se utiliza, evita subirlo al repositorio porque puede contener información sensible de sesión.

Una entrada recomendable para `.gitignore` es:

```gitignore
cookies.txt
Downloaded_videos/
*.log
mp4_files_report_*.csv
datos_completos.json
__pycache__/
*.pyc
```

## Estructura sugerida

```text
web-scraping-tools/
├── README.md
├── LICENSE.md
├── requirements.txt
├── scrapper.py
├── ScrapAndDownloadMP4.py
└── .gitignore
```

## Uso responsable

Estos scripts deben utilizarse únicamente sobre contenido al que tengas derecho de acceso y de acuerdo con los términos de servicio, políticas del sitio web y legislación aplicable.

El scraping y la descarga automatizada pueden estar limitados o prohibidos por determinados sitios. El usuario es responsable de verificar las condiciones aplicables antes de ejecutar estas herramientas.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [`LICENSE.md`](LICENSE.md) para más información.
