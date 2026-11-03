#!/usr/bin/env python3
"""Ingesta · quién vive en cada barrio y qué riesgos tiene: censo por sector censal (F12) y Índice Nacional de Riesgo (F108).

Lee:     - American Community Survey 2020-2024 (5 años) por sector censal («tract») del condado de Orange y por ciudad
           (Orlando, Tampa, Miami, Jacksonville), con Florida y EE. UU. Se consulta por Census Reporter, que sirve las mismas
           tablas del Census Bureau sin llave (la API oficial, api.census.gov, ahora exige llave).
         - Los contornos de esos sectores (TIGER 2024, misma fuente).
         - El National Risk Index de FEMA por sector (huracán, inundación, calor, tornado, vulnerabilidad social).
Escribe: lago/raw/censo/censo.json y lago/raw/riesgo/riesgo.json con la forma del contrato.

Cómo se pasa de sectores a barrios (derivado, y así se dice en la vista): se cubre el área con una rejilla de puntos de
tierra firme cada 40 m (sin lagos) y se cuenta qué parte de cada sector cae en cada barrio. Con 150 m un barrio de
0,12 km² (Camellia Gardens) recibía 4 puntos y su población salía casi el doble; a 40 m los barrios cambian en promedio
menos de 3 % frente a 75 m, así que la estimación ya no depende de dónde caiga la rejilla. Los conteos (personas,
hogares, arrendatarios…) se reparten con esa fracción, suponiendo que la gente se reparte parejo dentro del sector.
Las medianas (ingreso, arriendo, valor) no se pueden sumar: se promedian ponderando por los hogares que aporta cada
sector, y por eso se llaman «aproximadas». Un barrio con menos de 200 habitantes estimados no tiene porcentajes ni
medianas: con tan poca gente la estimación no dice nada.

Datos de personas: no hay. Son tablas agregadas que el Census Bureau publica ya protegidas."""
import urllib.parse
from comun import get_json, fuente_lago, cifra, escribir_lago, Capa, reparto, leer_territorio

API = "https://api.censusreporter.org/1.0"
CONDADO = "05000US12095"                                     # condado de Orange, Florida (Orlando está entero adentro)
LUGARES = {"orlando": "16000US1253000", "tampa": "16000US1271000", "miami": "16000US1245000",
           "jacksonville": "16000US1235000", "florida": "04000US12", "eeuu": "01000US"}
GRUPOS = ["B01003,B19013,B25064,B25003,B25070,B01002,B25077,B25002", "B08201,B08013,B08303,C17002", "B15003,C16001"]
NRI = "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/National_Risk_Index_Census_Tracts/FeatureServer/0"
NRI_CAMPOS = ["TRACTFIPS", "POPULATION", "RISK_SCORE", "EAL_VALT", "SOVI_SCORE", "RESL_SCORE", "HRCN_RISKS", "IFLD_RISKS",
              "HWAV_RISKS", "TRND_RISKS", "HRCN_EALT", "IFLD_EALT", "NRI_VER"]
PASO_M = 40                                                    # rejilla fina: los barrios pequeños necesitan puntos
MIN_HAB = 200                                                 # bajo esto un barrio no tiene porcentajes ni medianas


def datos(geos, edicion_pedida="latest"):
    """{geoid: {columna: estimado}} para todas las tablas de GRUPOS, y la edición (p. ej. ACS 2024 5-year).
    «latest» para los sectores da la última de 5 años; las ciudades se piden con esa misma edición, porque «latest»
    les daría la de 1 año y no serían comparables con los barrios."""
    todo, edicion, urls = {}, None, []
    for g in GRUPOS:
        url = f"{API}/data/show/{edicion_pedida}?table_ids={g}&geo_ids={geos}"
        urls.append(url)
        r = get_json(url, timeout=180)
        edicion = r["release"]
        for geo, tablas in r["data"].items():
            fila = todo.setdefault(geo, {})
            for t in tablas.values():
                for col, v in t["estimate"].items():
                    fila[col] = v
    return todo, edicion, urls


def medidas(E):
    """Conteos y bases de una geografía a partir de las columnas del ACS (None si la columna falta)."""
    g = lambda c: E.get(c)
    suma = lambda *cs: sum(E.get(c) or 0 for c in cs)
    return {
        "poblacion": g("B01003001"), "hogares": g("B25003001"), "propietarios": g("B25003002"), "arrendatarios": g("B25003003"),
        "ingreso": g("B19013001"), "arriendo": g("B25064001"), "valor": g("B25077001"), "edad": g("B01002001"),
        "carga": suma("B25070007", "B25070008", "B25070009", "B25070010"), "base_carga": (g("B25070001") or 0) - (g("B25070011") or 0),
        "viviendas": g("B25002001"), "vacantes": g("B25002003"),
        "sin_carro": g("B08201002"), "base_carro": g("B08201001"),
        "minutos": g("B08013001"), "trabajadores": g("B08303001"),
        "pobres": suma("C17002002", "C17002003"), "base_pobreza": g("C17002001"),
        "universitarios": suma("B15003022", "B15003023", "B15003024", "B15003025"), "base_educ": g("B15003001"),
        "espanol": g("C16001003"), "base_idioma": g("C16001001"),
    }


def pct(a, b):
    return round(a / b * 100, 1) if a is not None and b else None


def indicadores(m):
    """Lo que se publica de una geografía (ciudad o barrio)."""
    return {
        "poblacion": round(m["poblacion"]) if m["poblacion"] is not None else None,
        "ingreso_mediano": round(m["ingreso"]) if m["ingreso"] else None,
        "arriendo_mediano": round(m["arriendo"]) if m["arriendo"] else None,
        "valor_vivienda": round(m["valor"]) if m["valor"] else None,
        "edad_mediana": round(m["edad"], 1) if m["edad"] else None,
        "pct_arrendatarios": pct(m["arrendatarios"], m["hogares"]),
        "pct_carga_arriendo": pct(m["carga"], m["base_carga"]),
        "pct_sin_carro": pct(m["sin_carro"], m["base_carro"]),
        "minutos_al_trabajo": round(m["minutos"] / m["trabajadores"], 1) if m["minutos"] and m["trabajadores"] else None,
        "pct_pobreza": pct(m["pobres"], m["base_pobreza"]),
        "pct_universitarios": pct(m["universitarios"], m["base_educ"]),
        "pct_espanol": pct(m["espanol"], m["base_idioma"]),
        "pct_vacantes": pct(m["vacantes"], m["viviendas"]),
    }


UNIDAD = {"poblacion": "personas", "ingreso_mediano": "dólares por hogar al año", "arriendo_mediano": "dólares al mes (arriendo bruto)",
          "valor_vivienda": "dólares (valor declarado por el dueño)", "edad_mediana": "años",
          "pct_arrendatarios": "% de los hogares que arriendan", "pct_carga_arriendo": "% de los hogares arrendatarios que gastan 30 % o más del ingreso en arriendo",
          "pct_sin_carro": "% de los hogares sin carro", "minutos_al_trabajo": "minutos de viaje al trabajo (promedio)",
          "pct_pobreza": "% de las personas bajo la línea de pobreza", "pct_universitarios": "% de los mayores de 25 con título universitario",
          "pct_espanol": "% de los mayores de 5 años que hablan español en casa", "pct_vacantes": "% de las viviendas desocupadas"}

# ---------- 1. sectores censales del condado (la última edición de 5 años) ----------
tracts, edicion, urls_tr = datos(f"140|{CONDADO}")
vig_txt = edicion.get("years", edicion["name"])

# ---------- 2. ciudades comparables, con la misma edición ----------
lugares, ed_lug, urls_lug = datos(",".join(LUGARES.values()), edicion["id"])
assert ed_lug["id"] == edicion["id"], "Las ciudades y los sectores no vienen de la misma edición del ACS"
por_lugar = {k: indicadores(medidas(lugares[g])) for k, g in LUGARES.items() if g in lugares}
anio_geo = edicion["id"][3:7]                                  # acs2024_5yr -> 2024
url_geo = f"{API}/geo/show/tiger{anio_geo}?geo_ids=140|{CONDADO}"
geo = get_json(url_geo, timeout=180)
capa = Capa([(f["properties"]["geoid"], f["geometry"]) for f in geo["features"]])
pesos, cobertura = reparto(capa, paso_m=PASO_M)

CONTEOS = ["poblacion", "hogares", "propietarios", "arrendatarios", "carga", "base_carga", "viviendas", "vacantes", "sin_carro",
           "base_carro", "minutos", "trabajadores", "pobres", "base_pobreza", "universitarios", "base_educ", "espanol", "base_idioma"]
MEDIANAS = {"ingreso": "hogares", "arriendo": "arrendatarios", "valor": "propietarios", "edad": "poblacion"}
acum = {}
for tr, bs in pesos.items():
    m = medidas(tracts.get(tr, {}))
    for b, w in bs.items():
        a = acum.setdefault(b, {k: 0.0 for k in CONTEOS} | {f"_{k}": [0.0, 0.0] for k in MEDIANAS})
        for k in CONTEOS:
            a[k] += w * (m[k] or 0)
        for k, base in MEDIANAS.items():
            if m[k] and m[base]:
                a[f"_{k}"][0] += w * m[base] * m[k]
                a[f"_{k}"][1] += w * m[base]
por_barrio = {}
for b, a in acum.items():
    m = {k: a[k] for k in CONTEOS} | {k: (a[f"_{k}"][0] / a[f"_{k}"][1] if a[f"_{k}"][1] else None) for k in MEDIANAS}
    ind = indicadores(m)
    if (ind["poblacion"] or 0) < MIN_HAB:                        # muy poca gente: solo se publica el conteo
        ind = {k: (v if k == "poblacion" else None) for k, v in ind.items()}
    por_barrio[b] = ind

nombres = [f["properties"]["nombre"] for f in leer_territorio("barrios")]
F, FG = "censo_acs", "censo_tiger"
series = {}
for k in UNIDAD:
    pts = sorted(([b, por_barrio[b][k]] for b in nombres if b in por_barrio and por_barrio[b][k] is not None), key=lambda p: -p[1])
    series[f"{k}_barrio"] = {"unidad": UNIDAD[k] + " · estimación por barrio", "fuente": F, "puntos": pts}
    series[f"{k}_ciudades"] = {"unidad": UNIDAD[k], "fuente": F,
                               "puntos": [[c, por_lugar[c][k]] for c in LUGARES if c in por_lugar and por_lugar[c][k] is not None]}
series["cobertura_barrio"] = {"unidad": "% de la tierra del barrio cubierta por sectores censales", "fuente": FG,
                              "puntos": [[b, round(v * 100, 1)] for b, v in sorted(cobertura.items())]}

orl = por_lugar["orlando"]
estimada = sum(v["poblacion"] or 0 for v in por_barrio.values())
cifras = {f"{k}_ciudad": cifra(orl[k], UNIDAD[k], vig_txt, F) for k in UNIDAD if orl.get(k) is not None}
cifras |= {
    "poblacion_estimada_en_barrios": cifra(round(estimada), "personas (suma de las estimaciones por barrio)", vig_txt, F),
    "diferencia_con_cifra_oficial": cifra(round((estimada / orl["poblacion"] - 1) * 100, 1), "% (suma de barrios frente a la población oficial de la ciudad)", vig_txt, F),
    "barrios_con_estimacion": cifra(sum(1 for v in por_barrio.values() if v["pct_arrendatarios"] is not None), "barrios con 200 habitantes o más", vig_txt, F),
    "sectores_usados": cifra(len(pesos), "sectores censales que tocan algún barrio", vig_txt, FG),
    "minimo_habitantes_por_barrio": cifra(MIN_HAB, "habitantes estimados para publicar porcentajes y medianas", vig_txt, F),
}
r1 = escribir_lago("censo", [fuente_lago(F, urls_tr[0]), fuente_lago(FG, url_geo)], cifras, series)

# ---------- 3. Índice Nacional de Riesgo de FEMA por sector, llevado a barrios ----------
url_nri = NRI + "/query?" + urllib.parse.urlencode({"where": f"STCOFIPS='{CONDADO[-5:]}'", "outFields": ",".join(NRI_CAMPOS),
                                                     "returnGeometry": "false", "orderByFields": "TRACTFIPS", "f": "json"})
nri = {f["attributes"]["TRACTFIPS"]: f["attributes"] for f in get_json(url_nri, timeout=180)["features"]}
version = next(iter(nri.values()))["NRI_VER"]
RIESGOS = {"RISK_SCORE": "riesgo_total", "HRCN_RISKS": "riesgo_huracan", "IFLD_RISKS": "riesgo_inundacion", "HWAV_RISKS": "riesgo_calor",
           "TRND_RISKS": "riesgo_tornado", "SOVI_SCORE": "vulnerabilidad_social"}
racum = {}
for tr, bs in pesos.items():
    a = nri.get(tr.replace("14000US", ""))
    if not a:
        continue
    pob = (medidas(tracts.get(tr, {}))["poblacion"] or 0) + 1   # +1: un sector sin gente igual cuenta un poco
    for b, w in bs.items():
        r = racum.setdefault(b, {k: [0.0, 0.0] for k in RIESGOS} | {"perdida": 0.0})
        for campo in RIESGOS:
            if a.get(campo) is not None:
                r[campo][0] += w * pob * a[campo]
                r[campo][1] += w * pob
        r["perdida"] += w * (a.get("EAL_VALT") or 0)
FR = "fema_nri"
rseries = {}
for campo, k in RIESGOS.items():
    pts = [[b, round(racum[b][campo][0] / racum[b][campo][1], 1)] for b in nombres if b in racum and racum[b][campo][1]]
    rseries[f"{k}_barrio"] = {"unidad": "puntaje de 0 a 100 (percentil nacional; más alto, más riesgo) · promedio ponderado por población",
                              "fuente": FR, "puntos": sorted(pts, key=lambda p: -p[1])}
rseries["perdida_anual_esperada_barrio"] = {"unidad": "dólares al año (pérdida esperada por todos los peligros, repartida por área)", "fuente": FR,
                                            "puntos": sorted(([b, round(racum[b]["perdida"])] for b in nombres if b in racum), key=lambda p: -p[1])}
prom = lambda k: round(sum(p[1] for p in rseries[f"{k}_barrio"]["puntos"]) / max(1, len(rseries[f"{k}_barrio"]["puntos"])), 1)
rcifras = {f"{k}_promedio_barrios": cifra(prom(k), "puntaje de 0 a 100 (promedio simple de los barrios)", version, FR) for k in RIESGOS.values()}
rcifras["perdida_anual_esperada_ciudad"] = cifra(round(sum(p[1] for p in rseries["perdida_anual_esperada_barrio"]["puntos"])),
                                                 "dólares al año (suma de los barrios)", version, FR)
r2 = escribir_lago("riesgo", [fuente_lago(FR, url_nri), fuente_lago(FG, url_geo)], rcifras, rseries)
print(f"Censo {vig_txt}: Orlando {orl['poblacion']} hab. oficiales, {round(estimada)} estimados en {len(por_barrio)} barrios "
      f"({len(pesos)} sectores) -> {r1.name}; riesgo FEMA {version} -> {r2.name}")
