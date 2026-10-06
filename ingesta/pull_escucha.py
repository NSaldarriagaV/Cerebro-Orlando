#!/usr/bin/env python3
"""Ingesta · cuánta gente busca Orlando en Wikipedia (F71).

Lee:     es.wikipedia.org (resumen del artículo) y la API de vistas de Wikimedia. Sin llave.
Escribe: lago/escucha.json con la forma del contrato.

«Un título que coincide no es la cosa»: se exige que el título sea un artículo (no una página de
desambiguación) y que hable de Florida, y se usa el título canónico para pedir las vistas."""
import datetime, urllib.parse
from comun import get_json, hoy, fuente_lago, cifra, escribir_lago, variacion_pct

TITULOS = ["Orlando (Florida)", "Orlando"]   # candidatos, en orden de preferencia
MESES = 20                                   # meses completos hacia atrás


def rango_meses(n):
    """(desde, hasta) como AAAAMMDD: del primer día de hace n meses al último día del mes pasado."""
    hasta = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    y, m = hasta.year, hasta.month - (n - 1)
    while m <= 0:
        m, y = m + 12, y - 1
    return datetime.date(y, m, 1).strftime("%Y%m%d"), hasta.strftime("%Y%m%d")


canon = None
for t in TITULOS:
    r = get_json("https://es.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(t.replace(" ", "_"), safe="()_,"))
    texto = (r.get("description") or "") + " " + (r.get("extract") or "")
    if r.get("type") == "standard" and "Florida" in texto:
        canon = r["titles"]["canonical"]
        break
    print(f"«{t}» descartado: tipo {r.get('type')}, no menciona Florida")
if canon is None:
    raise SystemExit("Ningún título candidato es el artículo de la ciudad: elijan el título a mano en TITULOS.")

desde, hasta = rango_meses(MESES)
url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/es.wikipedia/all-access/user/"
       f"{urllib.parse.quote(canon, safe='()_,')}/monthly/{desde}/{hasta}")
puntos = [[i["timestamp"][:4] + "-" + i["timestamp"][4:6], i["views"]] for i in get_json(url)["items"]]
ultimo = puntos[-1]

cifras = {"vistas_ultimo_mes": cifra(ultimo[1], "vistas de personas", ultimo[0], "wikimedia_pageviews")}
if len(puntos) >= 13:   # mismo mes del año anterior
    cifras["variacion_anual"] = cifra(variacion_pct(ultimo[1], puntos[-13][1]), "%", ultimo[0], "wikimedia_pageviews")

ruta = escribir_lago("escucha", [fuente_lago("wikimedia_pageviews", url)], cifras,
                     {"vistas_mensuales": {"unidad": "vistas de personas", "fuente": "wikimedia_pageviews", "puntos": puntos}})
print(f"Orlando ({canon}): {len(puntos)} meses, último {ultimo[0]} con {ultimo[1]} vistas -> {ruta.name}")
