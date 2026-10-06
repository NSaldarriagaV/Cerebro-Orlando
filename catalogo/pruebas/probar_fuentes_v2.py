"""Prueba las URL de la hoja '1. Fuentes' y guarda el resultado en pruebas_fuentes.csv.
Uso:  python probar_fuentes_v2.py Diccionario_de_datos_TallerDatos_v2.xlsx
Solo usa la biblioteca estándar + openpyxl. Correrlo desde una red sin restricciones.
La columna 'fecha_prueba' es la fecha real de la respuesta: úsenla en «Fecha en que la probaron»
solo si la respuesta fue una descarga o una API de verdad (no una página de aviso o de login)."""
import csv, sys, datetime, urllib.request, urllib.error
from openpyxl import load_workbook

ws = load_workbook(sys.argv[1], data_only=True)["1. Fuentes"]
rows = [(r[0].value, r[4].value) for r in ws.iter_rows(min_row=5, max_row=110) if r[0].value and r[4].value]
hoy = datetime.date.today().isoformat()

with open("pruebas_fuentes_v2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "url", "http", "tipo_contenido", "url_final", "fecha_prueba", "error"])
    for fid, url in rows:
        req = urllib.request.Request(url, headers={"User-Agent": "TallerDatos-EAFIT/1.0 (contacto del grupo)"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                w.writerow([fid, url, r.status, r.headers.get("Content-Type", ""), r.geturl(), hoy, ""])
        except urllib.error.HTTPError as e:
            w.writerow([fid, url, e.code, "", "", hoy, e.reason])
        except Exception as e:
            w.writerow([fid, url, "", "", "", hoy, str(e)[:120]])
        print(fid, url)
