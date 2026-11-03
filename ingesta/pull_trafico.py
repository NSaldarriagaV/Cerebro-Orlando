#!/usr/bin/env python3
"""Ingesta · tráfico: cuántos vehículos pasan por las vías de Orlando (FDOT) y los choques con muertos (NHTSA FARS).

Lee (todo sin llave):
  FDOT, Transportation Data and Analytics (ArcGIS Online):
    - Annual_Average_Daily_Traffic_TDA: cada tramo de vía con su tráfico promedio diario del último año (AADT) y su línea.
    - Annual_Average_Daily_Traffic_Historical_TDA: el mismo conteo de los años anteriores, por estación (COSITE).
    - RCI_Layers, capa «Roadways with Local Names»: el nombre de cada vía (I-4, SR-408…), que el AADT no trae.
  NHTSA, Fatality Analysis Reporting System (servicio de mapas del Departamento de Transporte de EE. UU.): choques
    con al menos un muerto. Solo se piden ESTADÍSTICAS al servidor (conteos por año y por vía): nunca se baja un choque.
Escribe: lago/curado/tema=trafico/fecha=<día>/trafico.json y lago/territorio/vias_trafico.geojson (cada tramo con su
         línea y su tráfico, para el mapa de carreteras de la pestaña Movilidad)

PRIVACIDAD: el AADT cuenta vehículos por tramo de vía; no trae personas. FARS registra cada choque mortal con fecha,
hora y punto; aquí no se piden esos campos. El servidor devuelve cuántos choques y muertos hubo por año en la ciudad y
por vía en los últimos cinco años, y las vías con menos de UMBRAL choques no se publican."""
import json, statistics, urllib.parse
from comun import (get_json, fuente_lago, cifra, escribir_lago, variacion_pct, fecha_prueba, arcgis, capa_barrios, punto_en_barrio,
                   simplificar_linea, escribir_territorio)

AADT = "https://services1.arcgis.com/O1JpcwDW8sjYuddV/ArcGIS/rest/services/Annual_Average_Daily_Traffic_TDA/FeatureServer/0"
AADT_HIST = "https://services1.arcgis.com/O1JpcwDW8sjYuddV/ArcGIS/rest/services/Annual_Average_Daily_Traffic_Historical_TDA/FeatureServer/0"
NOMBRES = "https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/FeatureServer/13"
FARS = "https://geo.dot.gov/server/rest/services/NHTSA/FQAcc/MapServer"
CIUDAD_FARS = 2360           # código GSA de la ciudad de Orlando en FARS (CITYNAME = ORLANDO)
UMBRAL = 5
ANIOS_FARS = 10              # serie de choques mortales: los últimos diez años publicados
ANIOS_VIAS = 5               # vías con más choques mortales: suma de los últimos cinco años


def paginas(capa, **partes):
    """Todas las filas de una consulta de ArcGIS, de a 2000 (el máximo de estas capas)."""
    filas, desde = [], 0
    while True:
        r = get_json(arcgis(capa, resultOffset=desde, resultRecordCount=2000, **partes), timeout=120)
        if "error" in r:
            raise SystemExit(f"{capa}: el servidor respondió con error: {r['error']}")
        filas += r.get("features", [])
        if not r.get("exceededTransferLimit"):
            return filas
        desde += 2000


def estadistica(lid, where, agrupar, stats):
    r = get_json(f"{FARS}/{lid}/query?" + urllib.parse.urlencode({"where": where, "groupByFieldsForStatistics": agrupar,
                 "outStatistics": json.dumps(stats, separators=(",", ":")), "f": "json"}, quote_via=urllib.parse.quote), timeout=120)
    if "error" in r:
        raise SystemExit(f"FARS respondió con error: {r['error']}")
    return [f["attributes"] for f in r["features"]]


hoy = fecha_prueba()
barrios = capa_barrios()
x0, y0, x1, y1 = barrios.caja()

# ---------- 1. AADT del último año: tramos que tocan algún barrio de la ciudad
tramos = paginas(AADT, where="COUNTY = 'Orange'", geometry=f"{x0},{y0},{x1},{y1}", geometryType="esriGeometryEnvelope", inSR="4326",
                 spatialRel="esriSpatialRelIntersects", outFields="COSITE,ROADWAY,BEGIN_POST,END_POST,AADT,YEAR_",
                 returnGeometry="true", geometryPrecision="5", orderByFields="FID")
nombres = {}
for f in paginas(NOMBRES, where="COUNTYDOT = '75'", outFields="ROADWAY,NAME,BEGIN_POST,END_POST", returnGeometry="false", orderByFields="OBJECTID"):
    a = f["attributes"]
    nombres.setdefault(a["ROADWAY"], []).append((a["BEGIN_POST"] or 0, a["END_POST"] or 0, " ".join(str(a["NAME"] or "").split())))


def nombre_via(roadway, ini, fin):
    """El nombre local que más se solapa con el tramo (por kilometraje de FDOT)."""
    mejor, solape = None, -1
    for b, e, n in nombres.get(roadway, []):
        s = min(fin, e) - max(ini, b)
        if n and s > solape:
            mejor, solape = n, s
    return mejor or f"Vía {roadway}"


en_ciudad, max_barrio, lineas = [], {}, []
for f in tramos:
    a, g = f["attributes"], f.get("geometry") or {}
    if not a.get("AADT"):
        continue
    tocados = set()
    for camino in g.get("paths", []):
        puntos = list(camino) + [[(p[0] + q[0]) / 2, (p[1] + q[1]) / 2] for p, q in zip(camino, camino[1:])]
        for x, y in puntos:
            b = punto_en_barrio(barrios, x, y)
            if b:
                tocados.add(b)
    if not tocados:
        continue
    via = nombre_via(a["ROADWAY"], a["BEGIN_POST"] or 0, a["END_POST"] or 0)
    en_ciudad.append({"cosite": a["COSITE"], "via": via, "aadt": int(a["AADT"]), "anio": int(a["YEAR_"])})
    caminos = [c for c in (simplificar_linea(c) for c in g.get("paths", [])) if len(c) >= 2]
    if caminos:
        lineas.append({"type": "Feature", "properties": {"via": via, "aadt": int(a["AADT"]), "anio": int(a["YEAR_"]), "fuente": "fdot_aadt"},
                       "geometry": {"type": "LineString", "coordinates": caminos[0]} if len(caminos) == 1 else {"type": "MultiLineString", "coordinates": caminos}})
    for b in tocados:
        max_barrio[b] = max(max_barrio.get(b, 0), int(a["AADT"]))
if len(en_ciudad) < 50:
    raise SystemExit(f"Solo {len(en_ciudad)} tramos con AADT en la ciudad: algo cambió en la capa de FDOT.")
anio_aadt = max(t["anio"] for t in en_ciudad)
por_via = {}
for t in en_ciudad:
    por_via[t["via"]] = max(por_via.get(t["via"], 0), t["aadt"])
top_vias = sorted(((v, n) for v, n in por_via.items() if not v.startswith("Vía ")), key=lambda p: (-p[1], p[0]))[:12]   # solo vías con nombre

# ---------- 2. AADT de años anteriores, en las mismas estaciones
sitios = {t["cosite"] for t in en_ciudad}
hist = {}
for f in paginas(AADT_HIST, where="COUNTY = 'Orange'", outFields="COSITE,YEAR_,AADT", returnGeometry="false", orderByFields="FID"):
    a = f["attributes"]
    if a["COSITE"] in sitios and a.get("AADT"):
        hist.setdefault(int(a["YEAR_"]), []).append(int(a["AADT"]))
mediana_anio = [[str(y), round(statistics.median(v))] for y, v in sorted(hist.items()) if len(v) >= 0.5 * len(sitios)]

# ---------- 3. FARS: choques mortales en la ciudad, por año y por vía
capas = {}
for l in get_json(f"{FARS}?f=json")["layers"]:
    if l["name"].startswith("ACC") and l["name"][3:].isdigit():
        capas[int(l["name"][3:])] = l["id"]
anios_fars = sorted(capas)[-ANIOS_FARS:]
donde = f"STATE = 12 AND CITY = {CIUDAD_FARS}"
choques, muertos, con_peaton = {}, {}, {}
for y in anios_fars:
    for f in estadistica(capas[y], donde, "A_PED", [{"statisticType": "count", "onStatisticField": "ST_CASE", "outStatisticFieldName": "n"},
                                                    {"statisticType": "sum", "onStatisticField": "FATALS", "outStatisticFieldName": "m"}]):
        choques[y] = choques.get(y, 0) + int(f["n"])
        muertos[y] = muertos.get(y, 0) + int(f["m"] or 0)
        if f["A_PED"] == 1:                     # 1 = con peatón involucrado (Analytical User's Manual de FARS)
            con_peaton[y] = con_peaton.get(y, 0) + int(f["n"])
vias_fars = {}
for y in anios_fars[-ANIOS_VIAS:]:
    for f in estadistica(capas[y], donde, "TWAY_ID", [{"statisticType": "count", "onStatisticField": "ST_CASE", "outStatisticFieldName": "n"}]):
        via = " ".join(str(f["TWAY_ID"] or "").split())
        vias_fars[via] = vias_fars.get(via, 0) + int(f["n"])
vias_mostradas = sorted(([v, n] for v, n in vias_fars.items() if v and n >= UMBRAL), key=lambda p: (-p[1], p[0]))
ult, ant = anios_fars[-1], anios_fars[-2]
cinco = anios_fars[-ANIOS_VIAS:]
rango5 = f"{cinco[0]}-{cinco[-1]}"

FA, FH, FN, FF = "fdot_aadt", "fdot_aadt_historico", "fdot_nombres_vias", "nhtsa_fars"
cifras = {
    "anio_conteo": cifra(anio_aadt, "año del conteo de FDOT", str(anio_aadt), FA),
    "tramos_medidos": cifra(len(en_ciudad), "tramos de vía con conteo que tocan la ciudad", str(anio_aadt), FA),
    "via_mas_cargada_aadt": cifra(top_vias[0][1], f"vehículos al día en su tramo más cargado ({top_vias[0][0]})", str(anio_aadt), FA),
    "tramos_mas_de_100_mil": cifra(sum(1 for t in en_ciudad if t["aadt"] >= 100_000), "tramos con 100.000 vehículos al día o más", str(anio_aadt), FA),
    "choques_mortales_ultimo_anio": cifra(choques.get(ult, 0), "choques con al menos un muerto en la ciudad", str(ult), FF),
    "muertes_ultimo_anio": cifra(muertos.get(ult, 0), "personas muertas en choques de tránsito en la ciudad", str(ult), FF),
    "variacion_muertes_ultimo_anio": cifra(variacion_pct(muertos.get(ult, 0), muertos.get(ant, 0)) if muertos.get(ant) else 0.0, "%", str(ult), FF),
    "muertes_cinco_anios": cifra(sum(muertos.get(y, 0) for y in cinco), "personas muertas en choques de tránsito", rango5, FF),
    "pct_choques_mortales_con_peaton": cifra(round(sum(con_peaton.get(y, 0) for y in cinco) / max(1, sum(choques.get(y, 0) for y in cinco)) * 100, 1),
                                             "% de los choques mortales con un peatón involucrado", rango5, FF),
    "umbral_minimo_por_via": cifra(UMBRAL, "choques mortales en cinco años", rango5, FF),
    "vias_suprimidas": cifra(sum(1 for v, n in vias_fars.items() if v and n < UMBRAL), "vías con menos choques que el umbral", rango5, FF),
}
if len(mediana_anio) >= 2:
    cifras["mediana_aadt_ultimo_anio"] = cifra(mediana_anio[-1][1], "vehículos al día (mediana de las estaciones de conteo de la ciudad)", mediana_anio[-1][0], FH)
    cifras["variacion_mediana_aadt"] = cifra(variacion_pct(mediana_anio[-1][1], mediana_anio[-2][1]), "%", mediana_anio[-1][0], FH)
series = {
    "vias_mas_cargadas": {"unidad": f"vehículos al día en el tramo más cargado de cada vía ({anio_aadt})", "fuente": FA, "puntos": [[v, n] for v, n in top_vias]},
    "trafico_max_barrio": {"unidad": f"vehículos al día en la vía más cargada que cruza el barrio ({anio_aadt})", "fuente": FA,
                           "puntos": sorted(([b, n] for b, n in max_barrio.items()), key=lambda p: (-p[1], p[0]))},
    "mediana_aadt_por_anio": {"unidad": "vehículos al día (mediana de las mismas estaciones de conteo)", "fuente": FH, "puntos": mediana_anio},
    "choques_mortales_por_anio": {"unidad": "choques con al menos un muerto en la ciudad", "fuente": FF, "puntos": [[str(y), choques.get(y, 0)] for y in anios_fars]},
    "muertes_por_anio": {"unidad": "personas muertas en choques de tránsito en la ciudad", "fuente": FF, "puntos": [[str(y), muertos.get(y, 0)] for y in anios_fars]},
    "choques_con_peaton_por_anio": {"unidad": "choques mortales con un peatón involucrado", "fuente": FF, "puntos": [[str(y), con_peaton.get(y, 0)] for y in anios_fars]},
    "vias_con_mas_choques_mortales": {"unidad": f"choques mortales {rango5} (vías con {UMBRAL} o más)", "fuente": FF, "puntos": vias_mostradas},
}
capa = escribir_territorio("vias_trafico", sorted(lineas, key=lambda f: (f["properties"]["aadt"], f["properties"]["via"], json.dumps(f["geometry"]))))
ruta = escribir_lago("trafico", [fuente_lago(FA, f"{AADT}/query"), fuente_lago(FH, f"{AADT_HIST}/query"), fuente_lago(FN, f"{NOMBRES}/query"),
                                 fuente_lago(FF, f"{FARS}")], cifras, series)
print(f"Tráfico {anio_aadt}: {len(en_ciudad)} tramos, más cargado {top_vias[0]}; FARS {ult}: {choques.get(ult)} choques, {muertos.get(ult)} muertos; "
      f"{len(vias_mostradas)} vías con {UMBRAL}+ choques en {rango5} -> {ruta}; {len(lineas)} tramos en {capa.name} ({capa.stat().st_size // 1024} KB)")
