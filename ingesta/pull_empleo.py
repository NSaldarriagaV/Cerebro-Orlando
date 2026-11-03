#!/usr/bin/env python3
"""Ingesta · pulso del mercado laboral de Orlando: Indeed Hiring Lab (F70).

Lee:     CSV de GitHub (hiring-lab/job_postings_tracker), todas las áreas metropolitanas de EE. UU.
         (unos 60 MB). Se lee en flujo y solo se guarda Orlando. Sin llave.
Escribe: lago/raw/empleo/empleo.json con la forma del contrato.

Cruce por código territorial, no por nombre: CBSA 36740 = Orlando-Kissimmee-Sanford, FL.
«Contra qué»: del mismo archivo salen Tampa (45300), Miami (33100) y Jacksonville (27260), con la misma base 100."""
import calendar, csv, datetime, io
from comun import abrir, fuente_lago, cifra, escribir_lago, variacion_pct

URL = "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/US/metro_job_postings_us.csv"
CBSA = "36740"
PARES = {"45300": "tampa", "33100": "miami", "27260": "jacksonville"}
UNIDAD = "índice (base 100 = 2020-02-01, ajustado por estacionalidad)"

puntos, nombre = [], None
pares = {c: [] for c in PARES}
with abrir(URL, timeout=180) as r:
    for f in csv.DictReader(io.TextIOWrapper(r, encoding="utf-8", newline="")):
        if f["cbsa_code"] == CBSA:
            nombre = f["metro"]
            puntos.append([f["date"], float(f["indeed_job_postings_index"])])
        elif f["cbsa_code"] in pares:
            pares[f["cbsa_code"]].append([f["date"], float(f["indeed_job_postings_index"])])
for c, p in pares.items():
    if not p:
        raise SystemExit(f"El CBSA {c} ({PARES[c]}) no aparece en el archivo.")
    p.sort()
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
def promedio_mensual(pts):
    meses = {}
    for dia, v in pts:
        meses.setdefault(dia[:7], []).append(v)
    return [[m, round(sum(v) / len(v), 2)] for m, v in sorted(meses.items())
            if len(v) == calendar.monthrange(int(m[:4]), int(m[5:]))[1]]


mensual = promedio_mensual(puntos)
series = {"indice_diario": {"unidad": UNIDAD, "fuente": "indeed_hiring_lab", "puntos": puntos},
          "indice_mensual": {"unidad": UNIDAD + ", promedio del mes", "fuente": "indeed_hiring_lab", "puntos": mensual}}
ult_mes = {}
for c, ciudad in PARES.items():
    m = promedio_mensual(pares[c])
    series[f"indice_mensual_{ciudad}"] = {"unidad": UNIDAD + ", promedio del mes", "fuente": "indeed_hiring_lab", "puntos": m}
    ult_mes[ciudad] = dict(m).get(mensual[-1][0])
ult_mes["orlando"] = mensual[-1][1]
if all(v is not None for v in ult_mes.values()):
    orden = sorted(ult_mes, key=lambda k: -ult_mes[k])
    cifras["puesto_entre_pares"] = cifra(orden.index("orlando") + 1, "puesto entre 4 áreas (1 = más avisos frente a feb 2020)",
                                         mensual[-1][0], "indeed_hiring_lab")

ruta = escribir_lago("empleo", [fuente_lago("indeed_hiring_lab", URL)], cifras, series)
print(f"{nombre}: {len(puntos)} días, último {ultimo_dia} con índice {ultimo_valor} -> {ruta.name}")
