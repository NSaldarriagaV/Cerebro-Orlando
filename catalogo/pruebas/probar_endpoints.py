"""Prueba endpoints de datos (no páginas principales) y guarda pruebas_endpoints.csv.
Uso:  python probar_endpoints.py
ATENCIÓN: estas URL las propuso la IA de memoria y NO se han probado. Un 404 aquí significa
que la IA se equivocó con la ruta, no que la fuente no sirva: en ese caso busquen la ruta correcta
en la documentación de la fuente.
Cambien CONTACTO por un correo del grupo (algunas fuentes, como BLS o NWS, piden identificar al cliente).
La «fecha_prueba» solo vale para la columna M del Excel si http=200 y el contenido es de datos (CSV/JSON/TSV), no HTML."""
import csv, datetime, urllib.request, urllib.error

CONTACTO = "correo-del-grupo@ejemplo.com"
ENDPOINTS = [
 ("F01", "https://api.us.socrata.com/api/catalog/v1?domains=data.cityoforlando.net&limit=100",
  "Catálogo de datasets del portal de Orlando (si el portal es Socrata). Cada dataset trae su licencia en el JSON."),
 ("F12", "https://api.census.gov/data/2023/acs/acs5?get=NAME,B19013_001E&for=place:53000&in=state:12",
  "ACS 5 años 2023: ingreso mediano del hogar, ciudad de Orlando (place 53000, estado 12)."),
 ("F14", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ATNHPIUS36740Q",
  "FRED: índice de precios de vivienda del área de Orlando (CSV directo, sin llave). Verificar el ID de la serie."),
 ("F41", "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
  "Zillow ZHVI por área metropolitana (el nombre del archivo puede cambiar)."),
 ("F42", "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/redfin_metro_market_tracker.tsv000.gz",
  "Redfin: mercado por área metropolitana (archivo grande; el script solo lee los primeros bytes)."),
 ("F57", "https://api.weather.gov/points/28.5383,-81.3792",
  "NWS: punto de Orlando; la respuesta trae los enlaces al pronóstico y a las alertas."),
 ("F58", "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=USW00012815&startDate=2025-01-01&endDate=2025-12-31&format=csv",
  "NOAA: resumen diario del año 2025 en la estación que debería ser Orlando Intl (verificar el ID)."),
 ("F70", "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/US/metro_job_postings_us.csv",
  "Indeed Hiring Lab: probada por Claude el 2026-10-02; repetirla desde su red."),
]
hoy = datetime.date.today().isoformat()
with open("pruebas_endpoints.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "url", "http", "tipo_contenido", "bytes_declarados", "primeros_200_caracteres", "fecha_prueba", "error", "nota"])
    for fid, url, nota in ENDPOINTS:
        req = urllib.request.Request(url, headers={"User-Agent": f"TallerDatos-EAFIT/1.0 ({CONTACTO})"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                cuerpo = r.read(2048)
                texto = cuerpo[:200].decode("utf-8", errors="replace").replace("\n", " ") if r.headers.get("Content-Encoding") != "gzip" and not url.endswith(".gz") else "(archivo comprimido)"
                w.writerow([fid, url, r.status, r.headers.get("Content-Type", ""), r.headers.get("Content-Length", ""), texto, hoy, "", nota])
                print(fid, r.status, r.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as e:
            w.writerow([fid, url, e.code, "", "", "", hoy, e.reason, nota]); print(fid, e.code, e.reason)
        except Exception as e:
            w.writerow([fid, url, "", "", "", "", hoy, str(e)[:120], nota]); print(fid, "ERROR", str(e)[:80])
