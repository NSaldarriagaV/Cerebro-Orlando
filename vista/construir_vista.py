#!/usr/bin/env python3
"""Construye la vista pública del Cerebro Orlando.

Lee:     la foto más reciente de cada tema en lago/curado/ (17 temas), la anterior (para «qué cambió»), lago/territorio/*.geojson,
         el manifiesto de lo crudo, el inventario del lago y catalogo/*.json.
Escribe: lago/consumo/tablero/tablero.json   lo que lee el tablero publicado (zona de consumo del lago)
         publico/                            el sitio que publica Vercel: index.html lee lago/consumo/tablero/tablero.json
         vista/index.html                    la misma página en un solo archivo, con los datos adentro (sirve sin servidor)

Uso (solo biblioteca estándar de Python 3.9+):
    python3 vista/construir_vista.py                 # corre verificar.py antes; con un solo FAIL no construye
    python3 vista/construir_vista.py --sin-verificar # solo para probar el diseño, nunca para publicar

Qué agrega la vista (todo queda marcado como «derivado» en la página):
- Cada barrio se asigna al distrito de comisionado que contiene su centro (cruce espacial, no viene de la fuente).
- Área aproximada de cada barrio en km² (proyección plana local) para el indicador «permisos por km²».
- Las geometrías se proyectan aquí a coordenadas de pantalla (mapas planos SVG) y se incrustan como GeoJSON para el mapa 3D
  (MapLibre GL desde cdnjs, sin teselas ni llaves: solo las capas del lago).
Nada de esto agrega datos de personas: la vista solo usa conteos por barrio que ya pasaron el umbral del lago."""
import argparse, datetime, gzip, hashlib, json, math, pathlib, shutil, subprocess, sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
VISTA = RAIZ / "vista"
TEMAS = ["gente", "economia", "empleo", "vivienda", "escucha", "permisos", "seguridad", "codigo", "negocios", "turismo",
         "clima", "clima_historico", "territorio", "censo", "riesgo", "servicios", "planeacion", "trafico", "transporte"]
ANCHO = 1000                      # ancho del mapa en unidades de pantalla (viewBox)
REPO = "https://github.com/TeoVH/Cerebro-Orlando"         # fork del repo del equipo (NSaldarriagaV/Cerebro-Orlando) con la v4
WEB = "https://cerebro-orlando.vercel.app"          # la copia publicada (Vercel), con el lago en /lago/

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


def fotos(tema):
    return sorted((RAIZ / "lago" / "curado" / f"tema={tema}").glob("fecha=*/*.json"))


lago, anterior = {}, {}
for t in TEMAS:
    fs = fotos(t)
    if not fs:
        sys.exit(f"Falta lago/curado/tema={t}/: corran reconstruir.py antes de construir la vista.")
    lago[t] = leer(fs[-1])
    if len(fs) > 1:
        anterior[t] = leer(fs[-2])

# Qué cambió entre la foto anterior y la actual de cada tema (cifras con otro valor o con otra vigencia)
cambios = []
for t, viejo in anterior.items():
    for k, c in lago[t]["cifras"].items():
        a = viejo["cifras"].get(k)
        if a and (a["valor"] != c["valor"] or str(a["vigencia"]) != str(c["vigencia"])):
            cambios.append({"tema": t, "clave": k, "antes": a["valor"], "ahora": c["valor"], "unidad": c["unidad"],
                            "vig_antes": str(a["vigencia"]), "vig_ahora": str(c["vigencia"]), "fuente": c["fuente"],
                            "foto_antes": viejo["probado"], "foto_ahora": lago[t]["probado"]})

# El manifiesto de lo crudo, compacto (lo que muestra el explorador del lago)
MANIF = RAIZ / "lago" / "catalogo" / "manifiesto_crudo" / "manifiesto.jsonl"
manifiesto = [json.loads(l) for l in MANIF.read_text(encoding="utf-8").splitlines() if l.strip()] if MANIF.exists() else []
# A qué temas del lago alimenta cada respuesta cruda: lo dice el linaje de la zona curada (un script puede escribir dos temas)
temas_de = {}
for ruta in sorted((RAIZ / "lago" / "curado").glob("tema=*/fecha=*/*.json")):
    cur = leer(ruta)
    for f in cur["fuentes"]:
        for a in f.get("crudo", []):
            temas_de.setdefault(a, set()).add(cur["tema"])
crudo_vista = [{"f": m["fecha"], "s": m["sitio"], "u": m["url"], "t": ",".join(sorted(temas_de.get(m.get("archivo"), {m["tema"]}))), "c": m["como"], "fo": m.get("formato"), "e": m["estado"],
                "a": m.get("archivo"), "bo": m["bytes_original"], "bg": m.get("bytes_guardado"), "h": (m.get("sha256_guardado") or "")[:16],
                "ho": m["sha256_original"][:16], "r": m.get("retirado") or {}} for m in manifiesto]
CAT_LAGO = RAIZ / "lago" / "catalogo" / "catalogo_lago.json"
cat_lago = leer(CAT_LAGO) if CAT_LAGO.exists() else {"zonas": {}, "fechas": [], "crudo": {}, "archivos": []}

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

# Vías (FDOT, con su tráfico) y recorridos de bus (LYNX) como líneas del mapa plano; de la más chica a la más grande, para
# que las cargadas queden encima
def linea_svg(geom):
    caminos = [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]
    return "".join("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in (xy(p) for p in c)) for c in caminos)


def capa_lineas(nombre, valor, etiqueta):
    ruta = RAIZ / "lago" / "territorio" / f"{nombre}.geojson"
    if not ruta.exists():
        return []
    fs = leer(ruta)["features"]
    return [[linea_svg(f["geometry"]), f["properties"][valor], f["properties"][etiqueta]] for f in sorted(fs, key=lambda f: (f["properties"][valor], f["properties"][etiqueta]))]


# La copia del lago en AWS (CloudFront delante del bucket), si ya se montó con aws/crear_infra.py
NUBE = json.loads((RAIZ / "publicar" / "nube.json").read_text(encoding="utf-8")) if (RAIZ / "publicar" / "nube.json").exists() else {}
# Versión de la vista: el tablero que arme la Lambda en AWS solo se usa si salió del mismo código que esta página
VERSION = hashlib.sha1(b"".join((VISTA / f).read_bytes() for f in ("app.js", "plantilla.html", "construir_vista.py"))).hexdigest()[:12]
datos = {
    "generado": max(l["probado"] for l in lago.values()),          # el día más reciente en que una fuente respondió
    "version_vista": VERSION,
    "repo": REPO,
    "web": WEB,
    "nube": NUBE.get("cloudfront", ""),
    "lago": lago,
    "fuentes_lago": leer(RAIZ / "catalogo" / "fuentes_lago.json"),
    "catalogo": leer(RAIZ / "catalogo" / "catalogo_completo.json"),
    "diccionario": leer(RAIZ / "catalogo" / "diccionario.json"),
    "bitacora": leer(RAIZ / "catalogo" / "bitacora_ia.json"),
    "mapa": {"ancho": ANCHO, "alto": ALTO, "km_por_unidad": round(1 / ESCALA, 5), "limite": limite, "lagos": lagos,
             "barrios": barrios, "distritos": distritos, "sin_poligono": sin_poligono,
             "vias": capa_lineas("vias_trafico", "aadt", "via"), "rutas": capa_lineas("rutas_bus", "paradas_dia", "ruta"),
             "caja": [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)],
             "geo": {"barrios": geo(barrios_geo, ["i", "nombre"]), "distritos": geo(distritos_geo, ["distrito"]),
                     "limite": geo(limite_geo, []), "lagos": geo(lagos_geo, ["nombre"])}},
}

datos["verificacion"] = verificacion
# Resumen por zona sin el propio archivo del tablero (si no, cada construcción cambiaría el tamaño de la siguiente)
zonas = {}
for a in cat_lago["archivos"]:
    if a["ruta"].startswith("consumo/tablero/"):
        continue
    z = zonas.setdefault(a["zona"], {"archivos": 0, "bytes": 0, "descripcion": cat_lago["zonas"].get(a["zona"], {}).get("descripcion", "")})
    z["archivos"] += 1; z["bytes"] += a["bytes"]
datos["lago_info"] = {"fechas": cat_lago["fechas"], "zonas": zonas, "crudo_resumen": cat_lago["crudo"], "crudo": crudo_vista,
                      "cambios": cambios, "curado": sorted(a["ruta"] for a in cat_lago["archivos"] if a["zona"] == "curado"),
                      "consumo": sorted(a["ruta"] for a in cat_lago["archivos"] if a["zona"] == "consumo" and "tablero" not in a["ruta"]),
                      "s3": "cerebro-orlando-lago-eafit"}

plantilla = (VISTA / "plantilla.html").read_text(encoding="utf-8")
json_datos = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
incrustado = json_datos.replace("</", "<\\/")
for marca in ("__DATOS__", "<!--CUERPO-->", "/*__ESTILOS__*/", "/*__APP__*/"):
    if marca not in plantilla:
        sys.exit(f"La plantilla no tiene el marcador {marca}.")
estilos = (VISTA / "estilos.css").read_text(encoding="utf-8").replace("</", "<\\/")
app_txt = (VISTA / "app.js").read_text(encoding="utf-8")
app = app_txt.replace("</script", "<\\/script")
CAB = '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'


def pagina(plant):
    cabeza, cuerpo = plant.split("<!--CUERPO-->", 1)
    return cabeza, cuerpo, f'{CAB}{cabeza}</head>\n<body>\n{cuerpo}</body>\n</html>\n'


# 1) vista/index.html: un solo archivo con estilos, código y datos adentro (funciona sin servidor, también en el artefacto)
unico = plantilla.replace("/*__ESTILOS__*/", estilos).replace("/*__APP__*/", app).replace("__DATOS__", incrustado)
cabeza, cuerpo, html = pagina(unico)
salida = VISTA / "index.html"
salida.write_text(html, encoding="utf-8")
if args.fragmento:   # copia sin <html>/<head>/<body>, para plataformas que ponen el esqueleto ellas mismas
    pathlib.Path(args.fragmento).write_text(cabeza + cuerpo, encoding="utf-8")

# 2) zona de consumo: el archivo que lee el tablero publicado
TABLERO = RAIZ / "lago" / "consumo" / "tablero" / "tablero.json"
TABLERO.parent.mkdir(parents=True, exist_ok=True)
TABLERO.write_text(json_datos, encoding="utf-8")

# 3) publico/: el sitio de Vercel. La página no trae los datos: los lee del lago publicado al abrirse
PUB = RAIZ / "publico"
PUB.mkdir(exist_ok=True)
CARGADOR = """const leer = u => fetch(u, {cache: "no-cache"}).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
const NUBE = "__NUBE__", VERSION = "__VERSION__";
// Primero la última foto que publicó la actualización semanal en AWS (CloudFront); si no responde o salió de otra versión
// del código, la copia que viene con esta página
(NUBE ? leer(NUBE + "/consumo/tablero/tablero.json").then(d => { if (d.version_vista !== VERSION) throw new Error("otra versión"); window.__LAGO = NUBE + "/"; return d; }) : Promise.reject())
  .catch(() => leer("lago/consumo/tablero/tablero.json").then(d => { window.__LAGO = "lago/"; return d; }))
  .then(d => { window.__D = d; const s = document.createElement("script"); s.src = "app.js?v=" + encodeURIComponent(d.generado); document.body.append(s); })
  .catch(e => { document.querySelector("main").insertAdjacentHTML("afterbegin", '<div class="wrap" style="padding:40px 0"><h2>No se pudo leer el lago</h2><p>La página lee sus datos de lago/consumo/tablero/tablero.json y no respondió (' + e.message + '). Pruebe recargar.</p></div>'); });"""
CARGADOR = CARGADOR.replace("__NUBE__", NUBE.get("cloudfront", "")).replace("__VERSION__", VERSION)
web = plantilla.replace("/*__ESTILOS__*/", estilos).replace("__DATOS__", "").replace("<script>/*__APP__*/</script>", f"<script>{CARGADOR}</script>")
(PUB / "index.html").write_text(pagina(web)[2], encoding="utf-8")
(PUB / "app.js").write_text(app_txt, encoding="utf-8")
# Para probar en local se copia el lago adentro (en Vercel lo copia el paso de build: ver vercel.json). No va al repositorio.
if (PUB / "lago").exists():
    shutil.rmtree(PUB / "lago")
shutil.copytree(RAIZ / "lago", PUB / "lago")

# 4) el inventario del lago incluye ahora el archivo del tablero
sys.path.insert(0, str(RAIZ / "publicar"))
import consumo
consumo.catalogar()
# Después de escribir el tablero: lo que lee la página tiene que ser la última foto del lago (verificacion/consistencia.py)
if not args.sin_verificar:
    r = subprocess.run([sys.executable, str(RAIZ / "verificacion" / "consistencia.py")], capture_output=True, text=True)
    print("consistencia entre pestañas:", (r.stdout.strip().splitlines() or ["sin salida"])[-1])
    if r.returncode:
        sys.exit("consistencia.py falló después de construir:\n" + "\n".join(l for l in r.stdout.splitlines() if l.startswith("FAIL")))
shutil.copy2(RAIZ / "lago" / "catalogo" / "catalogo_lago.json", PUB / "lago" / "catalogo" / "catalogo_lago.json")
asignados = sum(1 for b in barrios if b["distrito"])
print(f"vista/index.html: {salida.stat().st_size // 1024} KB · tablero.json: {TABLERO.stat().st_size // 1024} KB · {len(cambios)} cifras cambiaron · {len(barrios)} barrios ({asignados} con distrito) · "
      f"{len(distritos)} distritos · {len(datos['catalogo'])} fichas del catálogo · sin polígono: {sin_poligono}")
