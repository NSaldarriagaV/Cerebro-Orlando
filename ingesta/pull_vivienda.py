#!/usr/bin/env python3
"""Ingesta · precio de la vivienda en Orlando: largo plazo, mercado de hoy y ciudades pares (F14, FRED).

Lee:     fredgraph.csv de FRED (sin llave; la API oficial sí pide llave gratuita, el CSV no):
         - ATNHPIUS36740Q: índice de precios de vivienda del área de Orlando (FHFA), trimestral, desde 1978;
         - índices de Tampa, Jacksonville y Miami-Miami Beach-Kendall (FHFA), para comparar;
         - precio mediano de lista, casas en venta y días en el mercado del área (Realtor.com), mensual, desde 2016;
         - viviendas nuevas autorizadas por permisos en el área (Census, BPS), mensual, ajustado por estacionalidad.
Escribe: lago/raw/vivienda/vivienda.json con la forma del contrato.

La licencia de FRED varía por serie: se copió a catalogo/fuentes_lago.json tal como la declara la ficha de cada serie.
Las series de Realtor.com dicen «Copyrighted: Citation Required»: la vista las cita en el mismo bloque donde aparecen."""
import csv, io
from comun import get_texto, fred, fuente_lago, cifra, escribir_lago, variacion_pct, mes

SERIE = "ATNHPIUS36740Q"
URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIE}"
UNIDAD = "índice (1995-Q1 = 100, sin ajuste estacional)"
PARES = {"ATNHPIUS45300Q": "tampa", "ATNHPIUS27260Q": "jacksonville", "ATNHPIUS33124Q": "miami"}
REALTOR = {"MEDLISPRI36740": ("precio_mediano_lista", "dólares"), "ACTLISCOU36740": ("casas_en_venta", "viviendas en venta"),
           "MEDDAYONMAR36740": ("dias_en_mercado", "días (mediana)")}

filas = list(csv.reader(io.StringIO(get_texto(URL))))
assert filas[0][1] == SERIE, f"La columna es «{filas[0][1]}», se esperaba {SERIE}"


def trimestre(fecha):          # 1978-04-01 -> 1978-Q2
    return f"{fecha[:4]}-Q{(int(fecha[5:7]) - 1) // 3 + 1}"


puntos = [[trimestre(f[0]), float(f[1])] for f in filas[1:] if len(f) > 1 and f[1] not in ("", ".")]
if len(puntos) < 8:
    raise SystemExit("La serie llegó casi vacía: no se escribe el lago.")
ultimo = puntos[-1]

url_p, p = fred(list(PARES))
url_r, r = fred(list(REALTOR))
url_b, b = fred(["ORLA712BPPRIVSA"], desde="2000-01-01")
# v3: el mercado de hoy de las áreas pares (Realtor.com), y cuántas viviendas de Orlando bajaron de precio
CBSA = {"45300": "tampa", "33100": "miami", "27260": "jacksonville"}
REALTOR_PARES = {f"{pre}{c}": (base, ciudad) for c, ciudad in CBSA.items()
                 for pre, base in (("MEDLISPRI", "precio_mediano_lista"), ("MEDDAYONMAR", "dias_en_mercado"),
                                   ("ACTLISCOU", "casas_en_venta"), ("PRIREDCOU", "rebajas"))}
url_rp, rp = fred(list(REALTOR_PARES))
# fredgraph.csv devuelve como máximo 12 series por consulta: las dos de Orlando van aparte
REALTOR_ORL = {"PRIREDCOU36740": ("rebajas", "orlando"), "MEDLISPRIPERSQUFEE36740": ("precio_pie2", "orlando")}
url_ro, ro = fred(list(REALTOR_ORL))
REALTOR_PARES |= REALTOR_ORL
rp |= ro
# Zillow: arriendo típico (ZORI) y valor típico de vivienda (ZHVI) de las cuatro áreas y de EE. UU.
ZILLOW = {"zori": "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
          "zhvi": "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"}
AREAS_Z = {"Orlando, FL": "orlando", "Tampa, FL": "tampa", "Miami, FL": "miami", "Jacksonville, FL": "jacksonville", "United States": "eeuu"}


def zillow(url, desde):
    filas = list(csv.reader(io.StringIO(get_texto(url, timeout=180))))
    cab = filas[0]
    fechas = [(j, c[:7]) for j, c in enumerate(cab) if len(c) == 10 and c[4] == "-" and c[:7] >= desde]
    salida = {}
    for f in filas[1:]:
        nombre = f[cab.index("RegionName")]
        if nombre in AREAS_Z and (nombre == "United States" or f[cab.index("StateName")] == "FL"):
            salida[AREAS_Z[nombre]] = [[m, round(float(f[j]))] for j, m in fechas if j < len(f) and f[j] not in ("", None)]
    falta = set(AREAS_Z.values()) - set(salida)
    if falta:
        raise SystemExit(f"Zillow no trajo {falta}: ¿cambió el archivo?")
    return salida


zori = zillow(ZILLOW["zori"], "2015-01")
zhvi = zillow(ZILLOW["zhvi"], "2005-01")

series = {"indice_trimestral": {"unidad": UNIDAD, "fuente": "fred_ihv_orlando", "puntos": puntos}}
for sid, ciudad in PARES.items():
    series[f"indice_trimestral_{ciudad}"] = {"unidad": UNIDAD.replace("1995-Q1", "1995-Q1 de cada área"), "fuente": "fred_ihv_pares",
                                             "puntos": [[trimestre(f), v] for f, v in p[sid]]}
for sid, (nombre, unidad) in REALTOR.items():
    series[nombre] = {"unidad": unidad, "fuente": "fred_realtor", "puntos": [[mes(f), v] for f, v in r[sid]]}
series["viviendas_autorizadas"] = {"unidad": "viviendas nuevas autorizadas al mes (ajustado por estacionalidad)", "fuente": "fred_bps",
                                   "puntos": [[mes(f), round(v, 1)] for f, v in b["ORLA712BPPRIVSA"]]}

for sid, (base, ciudad) in REALTOR_PARES.items():
    if base == "rebajas" and ciudad == "orlando":
        nombre = "rebajas"
    elif base == "precio_pie2":
        nombre = "precio_pie2"
    else:
        nombre = f"{base}_{ciudad}"
    series[nombre] = {"unidad": {"precio_mediano_lista": "dólares", "dias_en_mercado": "días (mediana)", "casas_en_venta": "viviendas en venta",
                                 "rebajas": "viviendas en venta que bajaron de precio en el mes", "precio_pie2": "dólares por pie cuadrado (mediana de lista)"}[base],
                      "fuente": "fred_realtor", "puntos": [[mes(f), v] for f, v in rp[sid]]}
for c, pts in zori.items():
    series[f"arriendo_tipico_{c}"] = {"unidad": "dólares al mes (arriendo típico observado, ZORI)", "fuente": "zillow_research", "puntos": pts}
for c, pts in zhvi.items():
    series[f"valor_tipico_{c}"] = {"unidad": "dólares (valor típico de vivienda, ZHVI)", "fuente": "zillow_research", "puntos": pts}

lista = series["precio_mediano_lista"]["puntos"]
inv = series["casas_en_venta"]["puntos"]
aut = series["viviendas_autorizadas"]["puntos"]
ult12 = sum(v for _, v in aut[-12:])
prev12 = sum(v for _, v in aut[-24:-12])
cifras = {"indice_ultimo_trimestre": cifra(ultimo[1], UNIDAD, ultimo[0], "fred_ihv_orlando"),
          "variacion_4_trimestres": cifra(variacion_pct(ultimo[1], puntos[-5][1]), "%", ultimo[0], "fred_ihv_orlando"),
          "precio_mediano_lista_ultimo_mes": cifra(lista[-1][1], "dólares", lista[-1][0], "fred_realtor"),
          "variacion_precio_lista_12_meses": cifra(variacion_pct(lista[-1][1], lista[-13][1]), "%", lista[-1][0], "fred_realtor"),
          "casas_en_venta_ultimo_mes": cifra(inv[-1][1], "viviendas en venta", inv[-1][0], "fred_realtor"),
          "variacion_casas_en_venta_12_meses": cifra(variacion_pct(inv[-1][1], inv[-13][1]), "%", inv[-1][0], "fred_realtor"),
          "dias_en_mercado_ultimo_mes": cifra(series["dias_en_mercado"]["puntos"][-1][1], "días (mediana)", lista[-1][0], "fred_realtor"),
          "viviendas_autorizadas_12_meses": cifra(round(ult12), "viviendas nuevas autorizadas en 12 meses", aut[-1][0], "fred_bps"),
          "variacion_viviendas_autorizadas": cifra(variacion_pct(ult12, prev12), "% frente a los 12 meses anteriores", aut[-1][0], "fred_bps")}
# Señal de mercado: qué parte de las viviendas en venta bajó de precio, y cuánto tarda en venderse
reb = dict(series["rebajas"]["puntos"]); act = dict(inv)
m_ = inv[-1][0]
zo, zh = series["arriendo_tipico_orlando"]["puntos"], series["valor_tipico_orlando"]["puntos"]
cifras |= {
    "pct_con_rebaja_ultimo_mes": cifra(round(reb[m_] / act[m_] * 100, 1), "% de las viviendas en venta que bajaron de precio", m_, "fred_realtor"),
    "pct_con_rebaja_hace_un_anio": cifra(round(reb[inv[-13][0]] / act[inv[-13][0]] * 100, 1), "% de las viviendas en venta que bajaron de precio", inv[-13][0], "fred_realtor"),
    "arriendo_tipico_ultimo_mes": cifra(zo[-1][1], "dólares al mes (ZORI)", zo[-1][0], "zillow_research"),
    "variacion_arriendo_12_meses": cifra(variacion_pct(zo[-1][1], zo[-13][1]), "%", zo[-1][0], "zillow_research"),
    "valor_tipico_ultimo_mes": cifra(zh[-1][1], "dólares (ZHVI)", zh[-1][0], "zillow_research"),
    "variacion_valor_12_meses": cifra(variacion_pct(zh[-1][1], zh[-13][1]), "%", zh[-1][0], "zillow_research"),
    "rentabilidad_bruta_arriendo": cifra(round(zo[-1][1] * 12 / zh[-1][1] * 100, 1), "% al año (arriendo típico × 12 ÷ valor típico; antes de gastos e impuestos)", zo[-1][0], "zillow_research"),
}
ruta = escribir_lago("vivienda", [fuente_lago("fred_ihv_orlando", URL), fuente_lago("fred_ihv_pares", url_p),
                                  fuente_lago("fred_realtor", url_r), fuente_lago("fred_bps", url_b),
                                  fuente_lago("zillow_research", ZILLOW["zori"])], cifras, series)
print(f"FRED {SERIE}: {len(puntos)} trimestres, último {ultimo[0]} con {ultimo[1]}; lista {lista[-1]}; autorizadas 12 m {round(ult12)} -> {ruta.name}")
