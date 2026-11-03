#!/usr/bin/env python3
"""Ingesta · qué tiene cerca cada barrio: parques, colegios, estaciones de SunRail y ciclovías (F107, SIG de la Ciudad de Orlando).

Lee:     cinco capas del servidor de mapas de la ciudad (gis.orlando.gov, ArcGIS Server, sin llave):
         parques (OrlandoParks), colegios públicos y chárter (capas de Orange County Public Schools que la ciudad
         republica), estaciones de SunRail y ciclovías existentes.
Escribe: lago/raw/servicios/servicios.json con la forma del contrato.

Cómo se asigna a barrios (derivado): un parque cuenta en el barrio donde cae su centro; un colegio o una estación, en el
barrio donde está su punto; una ciclovía se parte en tramos y cada tramo suma su largo al barrio de su punto medio.
Lo que queda fuera de los barrios de la ciudad no cuenta (las capas de colegios cubren todo el condado).

Datos de personas: no hay. Los colegios traen nombre del director y teléfono: esos campos no se piden."""
from comun import get_json, fuente_lago, cifra, escribir_lago, capa_barrios, leer_territorio, desde_esri, centro, area_km2, largo_km, arcgis

SIG = "https://gis.orlando.gov/server/rest/services"
CAPAS = {
    "parques": (f"{SIG}/Socrata_OpenData/OrlandoParks/MapServer/0", {"outFields": "TYPE", "maxAllowableOffset": "0.0002", "geometryPrecision": "5"}),
    "colegios": (f"{SIG}/Epic_Simplify_i3/Schools/MapServer/3", {"outFields": "FAC_TYPE", "geometryPrecision": "5"}),
    "charter": (f"{SIG}/Epic_Simplify_i3/Schools/MapServer/1", {"outFields": "TYPE", "geometryPrecision": "5"}),
    "sunrail": (f"{SIG}/Epic_Simplify_i3/Transportation/MapServer/27", {"outFields": "StationNameAlt", "geometryPrecision": "5"}),
    "ciclovias": (f"{SIG}/Socrata_OpenData/OrlandoBikeRoutes/MapServer/0", {"outFields": "Type", "maxAllowableOffset": "0.0001", "geometryPrecision": "5"}),
}
F = "orlando_sig"
barrios = capa_barrios()
nombres = [f["properties"]["nombre"] for f in leer_territorio("barrios")]
urls, conteo, fuera = {}, {}, {}


def sumar(clave, barrio, v=1):
    if barrio is None:
        fuera[clave] = fuera.get(clave, 0) + v
        return
    conteo.setdefault(clave, {})[barrio] = conteo.setdefault(clave, {}).get(barrio, 0) + v


for clave, (capa, partes) in CAPAS.items():
    urls[clave] = arcgis(capa, returnGeometry="true", **partes)
    r = get_json(urls[clave], timeout=120)
    if "error" in r:
        raise SystemExit(f"El SIG de la ciudad respondió con error en {clave}: {r['error']}")
    for f in r["features"]:
        g = desde_esri(f.get("geometry"))
        if not g:
            continue
        if clave == "parques":
            c = centro(g)
            b = barrios.donde(*c) if c else None
            sumar("parques", b)
            sumar("parques_km2", b, area_km2(g))
        elif clave == "ciclovias":
            for linea in g["coordinates"]:
                for (x1, y1), (x2, y2) in zip(linea, linea[1:]):
                    sumar("ciclovias_km", barrios.donde((x1 + x2) / 2, (y1 + y2) / 2), largo_km(x1, y1, x2, y2))
        else:
            x, y = g["coordinates"]
            sumar(clave, barrios.donde(x, y))

UNIDAD = {"parques": "parques de la ciudad (por su centro)", "parques_km2": "km² de parque (por el centro del parque)",
          "colegios": "colegios públicos de OCPS", "charter": "escuelas chárter de OCPS", "sunrail": "estaciones de SunRail",
          "ciclovias_km": "km de ciclovía existente"}
series = {}
for k, u in UNIDAD.items():
    d = conteo.get(k, {})
    pts = sorted(([b, round(d[b], 2) if isinstance(d[b], float) else d[b]] for b in nombres if d.get(b)), key=lambda p: -p[1])
    series[f"{k}_barrio"] = {"unidad": u + " · por barrio", "fuente": F, "puntos": pts}
hoy_ = __import__("comun").hoy()
cifras = {f"{k}_ciudad": cifra(round(sum(conteo.get(k, {}).values()), 1), u + " en los barrios de la ciudad", hoy_, F) for k, u in UNIDAD.items()}
cifras["barrios_sin_parque"] = cifra(sum(1 for b in nombres if not conteo.get("parques", {}).get(b)), "barrios sin un parque de la ciudad adentro", hoy_, F)
cifras["barrios_sin_colegio_publico"] = cifra(sum(1 for b in nombres if not conteo.get("colegios", {}).get(b)), "barrios sin colegio público adentro", hoy_, F)
cifras["colegios_fuera_de_la_ciudad"] = cifra(fuera.get("colegios", 0), "colegios públicos de la capa que quedan fuera de los barrios (la capa cubre el condado)", hoy_, F)
fuentes = [fuente_lago(F, urls["parques"])]
ruta = escribir_lago("servicios", fuentes, cifras, series)
print(f"Servicios: {cifras['parques_ciudad']['valor']} parques, {cifras['colegios_ciudad']['valor']} colegios públicos, "
      f"{cifras['sunrail_ciudad']['valor']} estaciones de SunRail, {cifras['ciclovias_km_ciudad']['valor']} km de ciclovía -> {ruta.name}")
