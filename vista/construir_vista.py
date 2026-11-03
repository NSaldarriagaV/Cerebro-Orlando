#!/usr/bin/env python3
"""Construye la vista pública del Cerebro Orlando: vista/index.html, una sola página sin servidor.

Lee:     lago/raw/<tema>/<tema>.json (17 temas), lago/territorio/*.geojson y catalogo/*.json.
Escribe: vista/index.html = vista/plantilla.html + estilos.css + app.js + los datos incrustados en un <script type="application/json">.

Uso (solo biblioteca estándar de Python 3.9+):
    python3 vista/construir_vista.py                 # corre verificar.py antes; con un solo FAIL no construye
    python3 vista/construir_vista.py --sin-verificar # solo para probar el diseño, nunca para publicar

Qué agrega la vista (todo queda marcado como «derivado» en la página):
- Cada barrio se asigna al distrito de comisionado que contiene su centro (cruce espacial, no viene de la fuente).
- Área aproximada de cada barrio en km² (proyección plana local) para el indicador «permisos por km²».
- Las geometrías se proyectan aquí a coordenadas de pantalla (mapas planos SVG) y se incrustan como GeoJSON para el mapa 3D
  (MapLibre GL desde cdnjs, sin teselas ni llaves: solo las capas del lago).
Nada de esto agrega datos de personas: la vista solo usa conteos por barrio que ya pasaron el umbral del lago."""
import argparse, datetime, json, math, pathlib, subprocess, sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
VISTA = RAIZ / "vista"
TEMAS = ["gente", "economia", "empleo", "vivienda", "escucha", "permisos", "seguridad", "codigo", "negocios", "turismo",
         "clima", "clima_historico", "territorio", "censo", "riesgo", "servicios", "planeacion"]
ANCHO = 1000                      # ancho del mapa en unidades de pantalla (viewBox)
REPO = "https://github.com/NSaldarriagaV/Cerebro-Orlando"

ap = argparse.ArgumentParser()
ap.add_argument("--sin-verificar", action="store_true")
ap.add_argument("--fragmento", help="ruta opcional para una copia sin <html>, <head> ni <body>")
args = ap.parse_args()

verificacion = "sin verificar (solo prueba de diseño)"
if not args.sin_verificar:
    r = subprocess.run([sys.executable, str(RAIZ / "verificacion" / "verificar.py")], capture_output=True, text=True)
    lineas = r.stdout.strip().splitlines()
    print(lineas[-1] if lineas else "verificar.py no imprimió nada")
    if r.returncode != 0:
        print(r.stdout)
        sys.exit("verificar.py falló: no se construye la vista.")
    verificacion = {"pasan": sum(l.startswith("PASS") for l in lineas), "avisos": sum(l.startswith("WARN") for l in lineas),
                    "fallos": 0, "avisos_texto": [l[5:] for l in lineas if l.startswith("WARN")]}


def leer(ruta):
    return json.loads(pathlib.Path(ruta).read_text(encoding="utf-8"))


lago = {}
for t in TEMAS:
    ruta = RAIZ / "lago" / "raw" / t / f"{t}.json"
    if not ruta.exists():
        sys.exit(f"Falta {ruta.relative_to(RAIZ)}: corran reconstruir.py antes de construir la vista.")
    lago[t] = leer(ruta)

barrios_geo = leer(RAIZ / "lago" / "territorio" / "barrios.geojson")["features"]
distritos_geo = leer(RAIZ / "lago" / "territorio" / "distritos_comisionados.geojson")["features"]
limite_geo = leer(RAIZ / "lago" / "territorio" / "limite_ciudad.geojson")["features"]
lagos_ruta = RAIZ / "lago" / "territorio" / "lagos.geojson"
lagos_geo = leer(lagos_ruta)["features"] if lagos_ruta.exists() else []


# ---------- geometría ----------
def anillos(geom):
    polis = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [poli for poli in polis]


todos = [p for f in barrios_geo + distritos_geo + limite_geo for poli in anillos(f["geometry"]) for anillo in poli for p in anillo]
min_lon, max_lon = min(p[0] for p in todos), max(p[0] for p in todos)
min_lat, max_lat = min(p[1] for p in todos), max(p[1] for p in todos)
lat0 = (min_lat + max_lat) / 2
KX, KY = 111.32 * math.cos(math.radians(lat0)), 110.57          # km por grado en Orlando
ESCALA = ANCHO / ((max_lon - min_lon) * KX)                      # unidades de pantalla por km
ALTO = round((max_lat - min_lat) * KY * ESCALA)


def xy(p):
    return ((p[0] - min_lon) * KX * ESCALA, (max_lat - p[1]) * KY * ESCALA)


def ruta_svg(geom):
    partes = []
    for poli in anillos(geom):
        for anillo in poli:
            pts = [xy(p) for p in anillo]
            partes.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(partes)


def area_centro(anillo):
    """Área (km², con signo) y centroide en coordenadas lon/lat de un anillo."""
    a = cx = cy = 0.0
    pts = [((p[0] - min_lon) * KX, (p[1] - min_lat) * KY) for p in anillo]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    a /= 2
    if abs(a) < 1e-12:
        return 0.0, anillo[0]
    return a, [cx / (6 * a) / KX + min_lon, cy / (6 * a) / KY + min_lat]


def medir(geom):
    """Área total (km², exteriores menos huecos) y centro del polígono más grande."""
    total, mayor, centro = 0.0, -1, None
    for poli in anillos(geom):
        a_ext, c = area_centro(poli[0])
        a_ext = abs(a_ext)
        huecos = sum(abs(area_centro(h)[0]) for h in poli[1:])
        total += a_ext - huecos
        if a_ext > mayor:
            mayor, centro = a_ext, c
    return total, centro


def dentro(p, geom):
    x, y, adentro = p[0], p[1], False
    for poli in anillos(geom):
        for anillo in poli:
            for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    adentro = not adentro
    return adentro


def distrito_de(geom, centro):
    for d in distritos_geo:
        if dentro(centro, d["geometry"]):
            return d["properties"]["distrito"]
    # El centro cae fuera (barrio en forma de C): gana el distrito que contiene más vértices del barrio
    votos = {}
    for poli in anillos(geom):
        for p in poli[0]:
            for d in distritos_geo:
                if dentro(p, d["geometry"]):
                    votos[d["properties"]["distrito"]] = votos.get(d["properties"]["distrito"], 0) + 1
    return max(votos, key=votos.get) if votos else None


# ---------- permisos por barrio ----------
serie = lago["permisos"]["series"]["permisos_por_barrio_ultimo_anio"]["puntos"]
por_nombre = {b.casefold(): n for b, n in serie}
ranking = {b.casefold(): i + 1 for i, (b, _) in enumerate(sorted(serie, key=lambda p: -p[1]))}

barrios, nombres_capa = [], set()
for f in barrios_geo:
    nombre = f["properties"]["nombre"]
    nombres_capa.add(nombre.casefold())
    area, centro = medir(f["geometry"])
    cx, cy = xy(centro)
    barrios.append({"id": f["properties"]["id"], "nombre": nombre, "d": ruta_svg(f["geometry"]),
                    "cx": round(cx, 1), "cy": round(cy, 1), "km2": round(area, 2), "lon": round(centro[0], 5), "lat": round(centro[1], 5),
                    "distrito": distrito_de(f["geometry"], centro),
                    "permisos": por_nombre.get(nombre.casefold()), "puesto": ranking.get(nombre.casefold())})
sin_poligono = [[b, n] for b, n in serie if b.casefold() not in nombres_capa]

distritos = []
for d in sorted(distritos_geo, key=lambda f: int(f["properties"]["distrito"])):
    num = d["properties"]["distrito"]
    area, centro = medir(d["geometry"])
    cx, cy = xy(centro)
    suyos = [b for b in barrios if b["distrito"] == num]
    distritos.append({"distrito": num, "d": ruta_svg(d["geometry"]), "cx": round(cx, 1), "cy": round(cy, 1),
                      "lon": round(centro[0], 5), "lat": round(centro[1], 5),
                      "km2": round(area, 1), "barrios": len(suyos),
                      "permisos": sum(b["permisos"] or 0 for b in suyos)})

limite = "".join(ruta_svg(f["geometry"]) for f in limite_geo)
# Lagos dentro del recuadro de la ciudad, para el mapa plano (el 3D usa el GeoJSON)
lagos = "".join(ruta_svg(f["geometry"]) for f in lagos_geo)


def geo(features, campos):
    """GeoJSON compacto para MapLibre: solo los campos que usa la vista; el índice del barrio va en «i»."""
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {k: (i if k == "i" else f["properties"].get(k)) for k in campos}, "geometry": f["geometry"]}
        for i, f in enumerate(features)]}

datos = {
    "generado": datetime.date.today().isoformat(),
    "repo": REPO,
    "lago": lago,
    "fuentes_lago": leer(RAIZ / "catalogo" / "fuentes_lago.json"),
    "catalogo": leer(RAIZ / "catalogo" / "catalogo_completo.json"),
    "diccionario": leer(RAIZ / "catalogo" / "diccionario.json"),
    "bitacora": leer(RAIZ / "catalogo" / "bitacora_ia.json"),
    "mapa": {"ancho": ANCHO, "alto": ALTO, "km_por_unidad": round(1 / ESCALA, 5), "limite": limite, "lagos": lagos,
             "barrios": barrios, "distritos": distritos, "sin_poligono": sin_poligono,
             "caja": [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)],
             "geo": {"barrios": geo(barrios_geo, ["i", "nombre"]), "distritos": geo(distritos_geo, ["distrito"]),
                     "limite": geo(limite_geo, []), "lagos": geo(lagos_geo, ["nombre"])}},
}

datos["verificacion"] = verificacion

plantilla = (VISTA / "plantilla.html").read_text(encoding="utf-8")
incrustado = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
for marca in ("__DATOS__", "<!--CUERPO-->", "/*__ESTILOS__*/", "/*__APP__*/"):
    if marca not in plantilla:
        sys.exit(f"La plantilla no tiene el marcador {marca}.")
estilos = (VISTA / "estilos.css").read_text(encoding="utf-8").replace("</", "<\\/")
app = (VISTA / "app.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
# Estilos y código viven en archivos aparte para poder leerlos; la página final los lleva adentro (un solo archivo)
plantilla = plantilla.replace("/*__ESTILOS__*/", estilos).replace("/*__APP__*/", app)
cabeza, cuerpo = plantilla.replace("__DATOS__", incrustado).split("<!--CUERPO-->", 1)
salida = VISTA / "index.html"
salida.write_text('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
                  '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                  f'{cabeza}</head>\n<body>\n{cuerpo}</body>\n</html>\n', encoding="utf-8")
if args.fragmento:   # copia sin <html>/<head>/<body>, para plataformas que ponen el esqueleto ellas mismas
    pathlib.Path(args.fragmento).write_text(cabeza + cuerpo, encoding="utf-8")
asignados = sum(1 for b in barrios if b["distrito"])
print(f"vista/index.html: {salida.stat().st_size // 1024} KB · {len(barrios)} barrios ({asignados} con distrito) · "
      f"{len(distritos)} distritos · {len(datos['catalogo'])} fichas del catálogo · sin polígono: {sin_poligono}")
