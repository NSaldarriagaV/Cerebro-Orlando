#!/usr/bin/env python3
"""Verificación antes de publicar: con un solo FAIL no se despliega.

Revisa lago/raw/*/*.json (contrato) y lago/territorio/*.geojson (geometrías). Uso:
    python3 verificacion/verificar.py [--raiz CARPETA]
Termina con código 1 si algo falla. Las líneas WARN no hacen fallar, pero hay que leerlas."""
import argparse, datetime, glob, json, pathlib, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("--raiz", default=str(pathlib.Path(__file__).resolve().parents[1]))
RAIZ = pathlib.Path(ap.parse_args().raiz)

fallos = 0
PII = [re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}"),                                      # correos
       re.compile(r"(?<!\d)3\d{9}(?!\d)"),                                              # celulares colombianos
       re.compile(r"(?<![\d.])(?:\+?1[ .-]?)?\(?[2-9]\d{2}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")]   # teléfonos de EE. UU.
CAMPOS_PERSONALES = re.compile(r"cedula|documento_identidad|telefono|celular|correo|email|phone|owner|contractor|applicant|suspect|officer|name_?holder|commissionername", re.I)
BBOX = (-82.0, 28.0, -80.8, 29.0)        # lon_min, lat_min, lon_max, lat_max alrededor de Orlando
MAX_KB_GEOJSON = 5000
DIAS_MAX_PRUEBA = 400


def check(nombre, ok, detalle=""):
    global fallos
    print(("PASS " if ok else "FAIL ") + nombre + ("" if ok else f" <- {detalle}"))
    fallos += 0 if ok else 1


def warn(nombre):
    print("WARN " + nombre)


def recorre(x, clave=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from recorre(v, k)
    elif isinstance(x, list):
        for v in x:
            yield from recorre(v, clave)
    else:
        yield clave, x


def sin_datos_personales(etiqueta, dato):
    pares = list(recorre(dato))
    sospechosos = sorted({k for k, _ in pares if CAMPOS_PERSONALES.search(str(k))})
    check(f"{etiqueta}: ningún campo con nombre de dato personal", not sospechosos, sospechosos)
    hallado = next((v for _, v in pares if isinstance(v, str) and any(p.search(v) for p in PII)), None)
    check(f"{etiqueta}: ningún texto con correo o teléfono", hallado is None, hallado)


def valor(lago, nombre):
    return lago.get("cifras", {}).get(nombre, {}).get("valor")


def dominio(ruta, lago):
    """Comprobaciones de dominio para Orlando: que las cifras caigan en un rango sensato."""
    t = lago.get("tema")
    hoy = datetime.date.today()
    reglas = {
        "escucha":   [("vistas del último mes en rango sensato", lambda: 100 < valor(lago, "vistas_ultimo_mes") < 10_000_000)],
        "empleo":    [("índice de vacantes en rango sensato", lambda: 30 < valor(lago, "indice_ultimo_dia") < 300),
                      ("serie diaria ordenada y sin días repetidos", lambda: (lambda d: d == sorted(set(d)))([p[0] for p in lago["series"]["indice_diario"]["puntos"]]))],
        "vivienda":  [("índice de vivienda en rango sensato", lambda: 10 < valor(lago, "indice_ultimo_trimestre") < 2000),
                      ("último trimestre de hace menos de dos años", lambda: int(lago["cifras"]["indice_ultimo_trimestre"]["vigencia"][:4]) >= hoy.year - 2)],
        "clima":     [("temperatura actual en °F en rango sensato", lambda: 20 < valor(lago, "temperatura_actual") < 115),
                      ("pronóstico con al menos 6 periodos", lambda: len(lago["series"]["pronostico_temperatura"]["puntos"]) >= 6),
                      ("pronóstico en rango sensato", lambda: all(20 < p[1] < 115 for p in lago["series"]["pronostico_temperatura"]["puntos"]))],
        "permisos":  [("permisos del último año completo en rango sensato", lambda: 50 < valor(lago, "permisos_emitidos_ultimo_anio_completo") < 1_000_000),
                      ("umbral mínimo por barrio de al menos 5 permisos", lambda: valor(lago, "umbral_minimo_por_barrio") >= 5),
                      ("ningún barrio por debajo del umbral", lambda: all(p[1] >= valor(lago, "umbral_minimo_por_barrio") for p in lago["series"]["permisos_por_barrio_ultimo_anio"]["puntos"])),
                      ("los barrios mostrados no suman más que el total de la ciudad", lambda: sum(p[1] for p in lago["series"]["permisos_por_barrio_ultimo_anio"]["puntos"]) <= valor(lago, "permisos_emitidos_ultimo_anio_completo")),
                      ("serie anual ordenada y sin el año en curso", lambda: (lambda a: a == sorted(set(a)) and max(a) < hoy.year)([int(p[0]) for p in lago["series"]["permisos_por_anio"]["puntos"]]))],
        "territorio": [("hay al menos un polígono por capa", lambda: all(c["valor"] >= 1 for c in lago["cifras"].values()))],
    }
    for nombre, fn in reglas.get(t, []):
        try:
            ok = bool(fn())
        except Exception as e:
            ok = False
            nombre += f" (no se pudo evaluar: {type(e).__name__})"
        check(f"{ruta}: {nombre}", ok, "valor fuera de rango o estructura distinta")
    if t == "permisos":
        c = valor(lago, "coincidencia_nombres_con_capa_barrios")
        if c is not None and c < 80:
            warn(f"{ruta}: solo {c} % de los barrios coincide por nombre con la capa de barrios; el nombre no es una llave confiable")


# ---------- lago/raw/*/*.json
for ruta in sorted(glob.glob(str(RAIZ / "lago" / "raw" / "*" / "*.json"))):
    nombre_ruta = pathlib.Path(ruta).relative_to(RAIZ).as_posix()
    lago = json.load(open(ruta, encoding="utf-8"))
    fuentes = lago.get("fuentes", [])
    ids = {f.get("id") for f in fuentes}
    probado = str(lago.get("probado"))
    es_dia = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", probado))
    check(f"{nombre_ruta}: probado es un día", es_dia, probado)
    if es_dia:
        edad = (datetime.date.today() - datetime.date.fromisoformat(probado)).days
        check(f"{nombre_ruta}: probado no está en el futuro ni pasa de {DIAS_MAX_PRUEBA} días", 0 <= edad <= DIAS_MAX_PRUEBA, f"{edad} días")
    check(f"{nombre_ruta}: toda fuente con url y licencia", bool(fuentes) and all(f.get("url") and f.get("licencia") for f in fuentes))
    pendientes = [f.get("id") for f in fuentes if "por verificar" in str(f.get("licencia", "")).lower()]
    check(f"{nombre_ruta}: ninguna licencia pendiente de verificar", not pendientes, f"escribir la licencia en catalogo/fuentes_lago.json: {pendientes}")
    for f in fuentes:
        if str(f.get("licencia", "")).lower().startswith("no declara"):
            warn(f"{nombre_ruta}: la fuente {f.get('id')} no declara licencia; confirmar los términos del portal antes de publicar")
    for clave, c in lago.get("cifras", {}).items():
        completa = c.get("valor") is not None and c.get("unidad") and c.get("vigencia") and c.get("fuente") in ids
        check(f"{nombre_ruta}: {clave} con valor, unidad, vigencia y fuente conocida", completa, c)
    for clave, s in lago.get("series", {}).items():
        buenos = s.get("unidad") and s.get("fuente") in ids and s.get("puntos") and all(
            isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) and isinstance(p[1], (int, float)) for p in s["puntos"])
        check(f"{nombre_ruta}: serie {clave} con unidad, fuente conocida y puntos [etiqueta, número]", bool(buenos), str(s)[:120])
    sin_datos_personales(nombre_ruta, lago)
    dominio(nombre_ruta, lago)

# ---------- lago/territorio/*.geojson
for ruta in sorted(glob.glob(str(RAIZ / "lago" / "territorio" / "*.geojson"))):
    nombre_ruta = pathlib.Path(ruta).relative_to(RAIZ).as_posix()
    kb = pathlib.Path(ruta).stat().st_size // 1024
    check(f"{nombre_ruta}: pesa menos de {MAX_KB_GEOJSON} KB", kb <= MAX_KB_GEOJSON, f"{kb} KB: simplificar más o pasar a PMTiles")
    g = json.load(open(ruta, encoding="utf-8"))
    feats = g.get("features", [])
    check(f"{nombre_ruta}: es un FeatureCollection con polígonos", g.get("type") == "FeatureCollection" and feats and all(
        f.get("geometry", {}).get("type") in ("Polygon", "MultiPolygon") for f in feats))
    xs_ys = [c for _, c in recorre([f.get("geometry", {}).get("coordinates") for f in feats]) if isinstance(c, (int, float))]
    xs, ys = xs_ys[0::2], xs_ys[1::2]
    dentro = bool(xs) and BBOX[0] <= min(xs) and max(xs) <= BBOX[2] and BBOX[1] <= min(ys) and max(ys) <= BBOX[3]
    check(f"{nombre_ruta}: coordenadas WGS84 (lon, lat) dentro de la caja de Orlando", dentro,
          f"lon {min(xs, default=None)}..{max(xs, default=None)}, lat {min(ys, default=None)}..{max(ys, default=None)}")
    sin_datos_personales(nombre_ruta, [f.get("properties") for f in feats])

print(f"\n{fallos} fallos")
sys.exit(1 if fallos else 0)
