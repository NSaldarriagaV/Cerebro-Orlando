#!/usr/bin/env python3
"""Ingesta · pulso del mercado laboral de Orlando: Indeed Hiring Lab (F70).

Lee:     CSV de GitHub (hiring-lab/job_postings_tracker), todas las áreas metropolitanas de EE. UU.
         (unos 60 MB). Se lee en flujo y solo se guarda Orlando. Sin llave.
Escribe: lago/raw/empleo/empleo.json con la forma del contrato.

Cruce por código territorial, no por nombre: CBSA 36740 = Orlando-Kissimmee-Sanford, FL."""
import calendar, csv, datetime, io
from comun import abrir, fuente_lago, cifra, escribir_lago, variacion_pct

URL = "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/US/metro_job_postings_us.csv"
CBSA = "36740"
UNIDAD = "índice (base 100 = 2020-02-01, ajustado por estacionalidad)"

puntos, nombre = [], None
with abrir(URL, timeout=180) as r:
    for f in csv.DictReader(io.TextIOWrapper(r, encoding="utf-8", newline="")):
        if f["cbsa_code"] == CBSA:
            nombre = f["metro"]
            puntos.append([f["date"], float(f["indeed_job_postings_index"])])
if not puntos:
    raise SystemExit(f"El CBSA {CBSA} no aparece en el archivo: ¿cambió la estructura?")
assert "Orlando" in nombre, f"El CBSA {CBSA} ahora es «{nombre}»"
puntos.sort()

por_dia = dict(puntos)
ultimo_dia, ultimo_valor = puntos[-1]
cifras = {"indice_ultimo_dia": cifra(ultimo_valor, UNIDAD, ultimo_dia, "indeed_hiring_lab")}
hace_un_anio = (datetime.date.fromisoformat(ultimo_dia) - datetime.timedelta(days=365)).isoformat()
if hace_un_anio in por_dia:
    cifras["variacion_12_meses"] = cifra(variacion_pct(ultimo_valor, por_dia[hace_un_anio]), "%", ultimo_dia, "indeed_hiring_lab")

# Promedio mensual: solo meses completos (un mes a medias engaña)
meses = {}
for dia, v in puntos:
    meses.setdefault(dia[:7], []).append(v)
mensual = [[m, round(sum(v) / len(v), 2)] for m, v in sorted(meses.items())
           if len(v) == calendar.monthrange(int(m[:4]), int(m[5:]))[1]]

ruta = escribir_lago("empleo", [fuente_lago("indeed_hiring_lab", URL)], cifras, {
    "indice_diario": {"unidad": UNIDAD, "fuente": "indeed_hiring_lab", "puntos": puntos},
    "indice_mensual": {"unidad": UNIDAD + ", promedio del mes", "fuente": "indeed_hiring_lab", "puntos": mensual}})
print(f"{nombre}: {len(puntos)} días, último {ultimo_dia} con índice {ultimo_valor} -> {ruta.name}")
