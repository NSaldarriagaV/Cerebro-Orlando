#!/usr/bin/env python3
"""Ingesta · precio de la vivienda en Orlando en el largo plazo: FRED (F14).

Lee:     fredgraph.csv de la serie ATNHPIUS36740Q (índice de precios de vivienda, área de Orlando), trimestral.
         Sin llave (la API oficial sí pide llave gratuita; el CSV por serie no).
Escribe: lago/raw/vivienda/vivienda.json con la forma del contrato.

La licencia de FRED varía por serie: se copia a catalogo/fuentes_lago.json tal como la declara la página
de la serie. Mientras diga «por verificar», verificar.py falla."""
import csv, io
from comun import get_texto, fuente_lago, cifra, escribir_lago, variacion_pct

SERIE = "ATNHPIUS36740Q"
URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIE}"
UNIDAD = "índice (1995-Q1 = 100, sin ajuste estacional)"

filas = list(csv.reader(io.StringIO(get_texto(URL))))
assert filas[0][1] == SERIE, f"La columna es «{filas[0][1]}», se esperaba {SERIE}"


def trimestre(fecha):          # 1978-04-01 -> 1978-Q2
    return f"{fecha[:4]}-Q{(int(fecha[5:7]) - 1) // 3 + 1}"


puntos = [[trimestre(f[0]), float(f[1])] for f in filas[1:] if len(f) > 1 and f[1] not in ("", ".")]
if len(puntos) < 8:
    raise SystemExit("La serie llegó casi vacía: no se escribe el lago.")
ultimo = puntos[-1]

cifras = {"indice_ultimo_trimestre": cifra(ultimo[1], UNIDAD, ultimo[0], "fred_ihv_orlando"),
          "variacion_4_trimestres": cifra(variacion_pct(ultimo[1], puntos[-5][1]), "%", ultimo[0], "fred_ihv_orlando")}
ruta = escribir_lago("vivienda", [fuente_lago("fred_ihv_orlando", URL)], cifras,
                     {"indice_trimestral": {"unidad": UNIDAD, "fuente": "fred_ihv_orlando", "puntos": puntos}})
print(f"FRED {SERIE}: {len(puntos)} trimestres, último {ultimo[0]} con {ultimo[1]} -> {ruta.name}")
