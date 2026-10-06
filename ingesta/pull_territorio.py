#!/usr/bin/env python3
"""Ingesta · límites de Orlando: ciudad, barrios y distritos de comisionados (F88, F90, F94).

Lee:     portal de datos abiertos de Orlando (API SODA, sin llave), formato JSON con la geometría en 'the_geom'.
Escribe: territorio/*.geojson (WGS84, simplificado) y lago/territorio.json con el contrato.

Decisiones:
- Solo se copian los campos de la lista blanca de cada capa. En la capa de distritos se descarta a propósito
  «commissionername» (nombre de una persona): se conserva el número de distrito.
- Las geometrías se simplifican (Douglas-Peucker, unos 10 m) y se redondean a 5 decimales para que pesen poco.
- La vigencia de cada capa es la fecha de la última actualización de sus filas, que da la ficha del portal."""
import datetime, json, math, pathlib
from comun import RAIZ, get_json, fuente_lago, cifra, escribir_lago

PORTAL = "https://data.cityoforlando.net"
TOLERANCIA = 0.0001                      # grados (~10 m)
CAPAS = [
    {"fuente": "orlando_limites",   "dataset": "adpi-29a3", "archivo": "limite_ciudad",          "campos": {"areaname": "nombre"}},
    {"fuente": "orlando_barrios",   "dataset": "yskk-n7cw", "archivo": "barrios",                "campos": {"neighborhoodname": "nombre", "neighborhoodid": "id"}},
    {"fuente": "orlando_distritos", "dataset": "iy8d-dzv4", "archivo": "distritos_comisionados", "campos": {"commissionerdistrictid": "distrito"}},
]


def _distancia(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def douglas_peucker(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        i, j = pila.pop()
        dmax, k = 0.0, None
        for m in range(i + 1, j):
            d = _distancia(pts[m], pts[i], pts[j])
            if d > dmax:
                dmax, k = d, m
        if k is not None and dmax > tol:
            keep[k] = True
            pila += [(i, k), (k, j)]
    return [p for p, c in zip(pts, keep) if c]


def anillo(pts):
    redondo = [[round(x, 5), round(y, 5)] for x, y in pts]
    simple = douglas_peucker(redondo, TOLERANCIA)
    return simple if len(simple) >= 4 else redondo       # un anillo necesita 4 puntos (el último repite el primero)


def simplificar(geom):
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [anillo(r) for r in geom["coordinates"]]}
    if geom["type"] == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": [[anillo(r) for r in poli] for poli in geom["coordinates"]]}
    return None


def puntos(geom):
    return sum(len(r) for c in ([geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]) for r in c)


pathlib.Path(RAIZ / "territorio").mkdir(exist_ok=True)
fuentes, cifras = [], {}
for capa in CAPAS:
    filas = get_json(f"{PORTAL}/resource/{capa['dataset']}.json?$limit=5000", timeout=120)
    ficha_portal = get_json(f"{PORTAL}/api/views/{capa['dataset']}.json")
    vigencia = datetime.datetime.fromtimestamp(ficha_portal["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    if (ficha_portal.get("license") or {}).get("name"):
        print(f"AVISO {capa['dataset']}: la ficha ahora declara licencia «{ficha_portal['license']['name']}»: actualicen catalogo/fuentes_lago.json")

    features, antes, despues, sin_geom = [], 0, 0, 0
    for fila in filas:
        g = fila.get("the_geom")
        if not g:
            sin_geom += 1
            continue
        simple = simplificar(g)
        if simple is None:
            sin_geom += 1
            continue
        antes, despues = antes + puntos(g), despues + puntos(simple)
        props = {nuevo: fila.get(viejo) for viejo, nuevo in capa["campos"].items()}
        props["fuente"] = capa["fuente"]
        features.append({"type": "Feature", "properties": props, "geometry": simple})
    if not features:
        raise SystemExit(f"{capa['dataset']}: ninguna fila con geometría; no se escribe la capa.")

    ruta = RAIZ / "territorio" / f"{capa['archivo']}.geojson"
    ruta.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    url = f"{PORTAL}/resource/{capa['dataset']}.json"
    fuentes.append(fuente_lago(capa["fuente"], url))
    cifras[f"poligonos_{capa['archivo']}"] = cifra(len(features), "polígonos", vigencia, capa["fuente"])
    print(f"{capa['archivo']}: {len(features)} polígonos, {antes} -> {despues} puntos, {ruta.stat().st_size // 1024} KB (actualizado {vigencia}, sin geometría: {sin_geom})")

ruta = escribir_lago("territorio", fuentes, cifras, {})
print(f"-> {ruta.name}")
