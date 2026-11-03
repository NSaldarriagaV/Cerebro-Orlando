#!/usr/bin/env python3
"""Ingesta · cuánta gente busca Orlando en Wikipedia (F71).

Lee:     es.wikipedia.org (resumen del artículo) y la API de vistas de Wikimedia. Sin llave.
Escribe: lago/raw/escucha/escucha.json con la forma del contrato.

«Un título que coincide no es la cosa»: se exige que el título sea un artículo (no una página de
desambiguación) y que hable de Florida, y se usa el título canónico para pedir las vistas.
«Contra qué»: las mismas vistas para Tampa, Miami y Jacksonville, con la misma regla de título y el mismo periodo."""
import datetime, urllib.parse
from comun import get_json, hoy, fuente_lago, cifra, escribir_lago, variacion_pct, fecha_prueba

TITULOS = ["Orlando (Florida)", "Orlando"]   # candidatos, en orden de preferencia
PARES = {"tampa": ["Tampa"], "miami": ["Miami"], "jacksonville": ["Jacksonville (Florida)", "Jacksonville"]}
MESES = 20                                   # meses completos hacia atrás


def rango_meses(n):
    """(desde, hasta) como AAAAMMDD: del primer día de hace n meses al último día del mes pasado."""
    hasta = fecha_prueba().replace(day=1) - datetime.timedelta(days=1)
    y, m = hasta.year, hasta.month - (n - 1)
    while m <= 0:
        m, y = m + 12, y - 1
    return datetime.date(y, m, 1).strftime("%Y%m%d"), hasta.strftime("%Y%m%d")


def canonico(titulos, lang="es"):
    for t in titulos:
        r = get_json(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(t.replace(" ", "_"), safe="()_,"))
        texto = (r.get("description") or "") + " " + (r.get("extract") or "")
        if r.get("type") == "standard" and "Florida" in texto:
            return r["titles"]["canonical"]
        print(f"«{t}» descartado: tipo {r.get('type')}, no menciona Florida")
    raise SystemExit(f"Ningún título candidato de {titulos} es el artículo de la ciudad: elíjanlo a mano.")


def vistas(canon, lang="es"):
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/all-access/user/"
           f"{urllib.parse.quote(canon, safe='()_,')}/monthly/{desde}/{hasta}")
    return url, [[i["timestamp"][:4] + "-" + i["timestamp"][4:6], i["views"]] for i in get_json(url)["items"]]


canon = canonico(TITULOS)

desde, hasta = rango_meses(MESES)
url, puntos = vistas(canon)
ultimo = puntos[-1]
pares = {c: vistas(canonico(t))[1] for c, t in PARES.items()}
# v3: la misma medida en Wikipedia en inglés, que es donde busca la mayoría de los visitantes
EN = {"orlando": ["Orlando, Florida"], "tampa": ["Tampa, Florida"], "miami": ["Miami"], "jacksonville": ["Jacksonville, Florida"]}
ingles = {c: vistas(canonico(t, "en"), "en")[1] for c, t in EN.items()}

cifras = {"vistas_ultimo_mes": cifra(ultimo[1], "vistas de personas", ultimo[0], "wikimedia_pageviews")}
if len(puntos) >= 13:   # mismo mes del año anterior
    cifras["variacion_anual"] = cifra(variacion_pct(ultimo[1], puntos[-13][1]), "%", ultimo[0], "wikimedia_pageviews")

series = {"vistas_mensuales": {"unidad": "vistas de personas", "fuente": "wikimedia_pageviews", "puntos": puntos}}
for c, pts in pares.items():
    series[f"vistas_mensuales_{c}"] = {"unidad": "vistas de personas", "fuente": "wikimedia_pageviews", "puntos": pts}
# Atención frente a los pares: suma de los últimos 12 meses de Orlando sobre el promedio de los pares
doce = {c: sum(v for _, v in pts[-12:]) for c, pts in list(pares.items()) + [("orlando", puntos)]}
prom_pares = sum(doce[c] for c in PARES) / len(PARES)
cifras["atencion_frente_a_pares"] = cifra(round(doce["orlando"] / prom_pares, 2), "veces el promedio de Tampa, Miami y Jacksonville (12 meses)", ultimo[0], "wikimedia_pageviews")
for c, pts in ingles.items():
    series[f"vistas_ingles_{c}"] = {"unidad": "vistas de personas (Wikipedia en inglés)", "fuente": "wikimedia_pageviews", "puntos": pts}
doce_en = {c: sum(v for _, v in pts[-12:]) for c, pts in ingles.items()}
cifras["vistas_ingles_12_meses"] = cifra(doce_en["orlando"], "vistas de personas en Wikipedia en inglés (12 meses)", ultimo[0], "wikimedia_pageviews")
cifras["puesto_ingles_entre_pares"] = cifra(sorted(doce_en, key=lambda c: -doce_en[c]).index("orlando") + 1, "puesto entre 4 ciudades en Wikipedia en inglés (12 meses)", ultimo[0], "wikimedia_pageviews")
cifras["puesto_entre_pares"] = cifra(sorted(doce, key=lambda c: -doce[c]).index("orlando") + 1, "puesto entre 4 ciudades (1 = más vistas en 12 meses)", ultimo[0], "wikimedia_pageviews")
ruta = escribir_lago("escucha", [fuente_lago("wikimedia_pageviews", url)], cifras, series)
print(f"Orlando ({canon}): {len(puntos)} meses, último {ultimo[0]} con {ultimo[1]} vistas -> {ruta.name}")
