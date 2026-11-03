#!/usr/bin/env python3
"""Utilidades compartidas por los scripts de ingesta. Solo biblioteca estándar de Python.

Variable de entorno opcional: CONTACTO (un correo del grupo). Algunas fuentes, como el servicio
del clima de EE. UU., piden que el cliente se identifique."""
import datetime, hashlib, io, json, os, pathlib, sys, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import crudo

RAIZ = pathlib.Path(__file__).resolve().parents[1]
LAGO = RAIZ / "lago"
CATALOGO = RAIZ / "catalogo" / "fuentes_lago.json"
CONTACTO = os.environ.get("CONTACTO", "contacto-del-grupo@ejemplo.com")
UA = {"User-Agent": f"taller-sistemas-de-informacion/1.0 (curso universitario; {CONTACTO})"}


def _traer(url, timeout):
    """Pide la URL a la fuente; si el servidor dice 429 o 5xx, espera y reintenta (hasta 3 veces)."""
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and intento < 2:
                time.sleep(5 if e.code == 429 else 60)
                continue
            raise


def abrir(url, timeout=60):
    """Devuelve la respuesta de la URL como archivo en memoria y la deja guardada en la zona cruda del lago.

    Tres maneras de conseguirla (variables de entorno):
      CEREBRO_DESDE_CRUDO=AAAA-MM-DD  la lee de la zona cruda de esa fecha: reconstruir sin internet, idéntico.
      CEREBRO_CAPTURA=carpeta         la lee de una captura hecha con el navegador del equipo (un archivo por URL,
                                      con el sha1 de la URL como nombre); se anota «navegador del equipo».
      (ninguna)                       la pide directo a la fuente; se anota «script directo»."""
    desde = os.environ.get("CEREBRO_DESDE_CRUDO", "")
    if desde:
        return io.BytesIO(crudo.leer(url, desde))
    captura = os.environ.get("CEREBRO_CAPTURA", "")
    archivo = pathlib.Path(captura) / hashlib.sha1(url.encode()).hexdigest() if captura else None
    if archivo and archivo.exists():
        cuerpo = archivo.read_bytes()
        meta = archivo.with_suffix(".meta.json")
        como = json.loads(meta.read_text(encoding="utf-8"))["como"] if meta.exists() else "navegador del equipo"
    elif captura and not url.startswith("https://raw.githubusercontent.com/"):
        faltan = os.environ.get("CEREBRO_FALTAN", "")
        if faltan:
            with open(faltan, "a", encoding="utf-8") as f:
                f.write(url + "\n")
        raise SystemExit(f"FALTA {url}")
    else:
        cuerpo, como = _traer(url, timeout), "script directo"
    if os.environ.get("CEREBRO_GUARDAR_CRUDO", "1") != "0":
        crudo.guardar(url, cuerpo, hoy(), como)
    return io.BytesIO(cuerpo)


def get_json(url, timeout=60):
    with abrir(url, timeout) as r:
        return json.load(r)


def get_texto(url, timeout=60):
    with abrir(url, timeout) as r:
        return r.read().decode("utf-8")


def hoy():
    """El día de la prueba: AAAA-MM-DD, nunca con hora.
    Si se reconstruye desde una copia guardada de las respuestas, CEREBRO_FECHA_PRUEBA dice el día en que la fuente
    respondió de verdad (la prueba no cambia de fecha por volver a leer la misma copia)."""
    fija = os.environ.get("CEREBRO_FECHA_PRUEBA", "")
    if fija:
        datetime.date.fromisoformat(fija)                  # falla si no es AAAA-MM-DD
        return fija
    return datetime.date.today().isoformat()


def fecha_prueba():
    """hoy() como fecha: todo lo que depende del día (rangos de meses, año en curso) usa esto y no el reloj,
    para que reconstruir desde la zona cruda dé exactamente lo mismo."""
    return datetime.date.fromisoformat(hoy())


def variacion_pct(nuevo, viejo):
    return round((nuevo / viejo - 1) * 100, 1)


def ficha(id_fuente):
    """Lee la ficha de la fuente en catalogo/fuentes_lago.json (de ahí salen entidad y licencia)."""
    for f in json.loads(CATALOGO.read_text(encoding="utf-8")):
        if f["id"] == id_fuente:
            return f
    sys.exit(f"La fuente «{id_fuente}» no está en {CATALOGO}")


def fuente_lago(id_fuente, url):
    """Entrada de 'fuentes' del contrato. La licencia se copia de la ficha, no se escribe en el script."""
    f = ficha(id_fuente)
    if "por verificar" in f["licencia"].lower():
        print(f"AVISO {id_fuente}: licencia pendiente en el catálogo; verificar.py va a fallar hasta que se escriba.", file=sys.stderr)
    return {"id": id_fuente, "nombre": f["nombre"], "url": url, "estado": "vivo", "licencia": f["licencia"]}


def cifra(valor, unidad, vigencia, fuente):
    return {"valor": valor, "unidad": unidad, "vigencia": vigencia, "fuente": fuente}


def escribir_lago(tema, fuentes, cifras, series):
    """Escribe la zona curada: lago/curado/tema=<tema>/fecha=<día de la prueba>/<tema>.json con la forma del contrato.
    Cada fuente lleva en «crudo» las respuestas guardadas de las que salió (el linaje)."""
    carpeta = LAGO / "curado" / f"tema={tema}" / f"fecha={hoy()}"
    carpeta.mkdir(parents=True, exist_ok=True)
    lago = {"tema": tema, "probado": hoy(), "fuentes": crudo.linaje_por_fuente(fuentes), "cifras": cifras, "series": series}
    ruta = carpeta / f"{tema}.json"
    ruta.write_text(json.dumps(lago, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta


def ultimo_curado(tema, raiz=None):
    """La foto más reciente de un tema en la zona curada (None si no hay)."""
    fotos = sorted((pathlib.Path(raiz or RAIZ) / "lago" / "curado" / f"tema={tema}").glob("fecha=*/*.json"))
    return fotos[-1] if fotos else None


# ---------- utilidades para fuentes nuevas (v2) ----------
def fred(ids, desde=None):
    """Baja varias series de FRED en una sola consulta (fredgraph.csv acepta ids separados por coma, sin llave).
    Devuelve (url, {id: [[fecha AAAA-MM-DD, valor], ...]}), sin los valores vacíos ni los puntos «.»."""
    import csv, io
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + ",".join(ids)
    filas = list(csv.reader(io.StringIO(get_texto(url, timeout=120))))
    cab = filas[0]
    faltan = [i for i in ids if i not in cab]
    if faltan:
        raise SystemExit(f"FRED no devolvió las series {faltan}: ¿cambió el id o la descontinuaron?")
    series = {i: [] for i in ids}
    for f in filas[1:]:
        if desde and f[0] < desde:
            continue
        for j, i in enumerate(cab[1:], start=1):
            if j < len(f) and f[j] not in ("", "."):
                series[i].append([f[0], float(f[j])])
    for i, p in series.items():
        if not p:
            raise SystemExit(f"La serie {i} llegó vacía.")
    return url, series


def mes(fecha):
    """2026-08-01 -> 2026-08"""
    return fecha[:7]


def anio(fecha):
    return fecha[:4]


def suprimir(conteos, umbral):
    """Separa {barrio: n} en (mostrados, cuántos se suprimieron). Nunca se dice cuáles se suprimieron."""
    mostrados = {b: n for b, n in conteos.items() if b and n >= umbral}
    return mostrados, sum(1 for b, n in conteos.items() if b and n < umbral)


# ---------- geometría para cruzar capas con los barrios (v3) ----------
# Solo biblioteca estándar: en vez de recortar polígonos, se cubre el área con una rejilla de puntos y se cuenta en qué
# polígono cae cada punto. Con 120 m entre puntos, un barrio de 1 km² tiene unos 70 puntos: suficiente para repartir
# una población o medir qué parte de un barrio cae en una zona. Los puntos que caen en lagos no cuentan.
import math

KM_POR_GRADO_LAT = 110.57


def anillos(geom):
    """Lista de polígonos; cada polígono es una lista de anillos [(lon, lat), ...] (el primero es el borde)."""
    if not geom:
        return []
    polis = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"] if geom["type"] == "MultiPolygon" else []
    return [[[(float(p[0]), float(p[1])) for p in anillo] for anillo in poli] for poli in polis]


def desde_esri(geom):
    """Geometría de ArcGIS (rings, en 4326) a GeoJSON. ArcGIS no separa polígonos: cada anillo queda como su propio
    polígono y el par-impar del punto en polígono resuelve los huecos."""
    if not geom:
        return None
    if "rings" in geom:
        return {"type": "Polygon", "coordinates": geom["rings"]}
    if "paths" in geom:
        return {"type": "MultiLineString", "coordinates": geom["paths"]}
    if "x" in geom:
        return {"type": "Point", "coordinates": [geom["x"], geom["y"]]}
    return None


class Capa:
    """Polígonos con índice espacial simple (celdas de 0,01°) para preguntar «¿en cuál cae este punto?»."""
    CELDA = 0.01

    def __init__(self, items):
        # items: [(clave, geometría GeoJSON)]
        self.items, self.celdas = [], {}
        for clave, geom in items:
            anis = [a for poli in anillos(geom) for a in poli]
            if not anis:
                continue
            xs = [p[0] for a in anis for p in a]
            ys = [p[1] for a in anis for p in a]
            caja = (min(xs), min(ys), max(xs), max(ys))
            k = len(self.items)
            self.items.append((clave, anis, caja))
            for cx in range(int(caja[0] // self.CELDA), int(caja[2] // self.CELDA) + 1):
                for cy in range(int(caja[1] // self.CELDA), int(caja[3] // self.CELDA) + 1):
                    self.celdas.setdefault((cx, cy), []).append(k)

    @staticmethod
    def _dentro(x, y, anis):
        adentro = False
        for a in anis:
            j = len(a) - 1
            for i in range(len(a)):
                xi, yi = a[i]
                xj, yj = a[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    adentro = not adentro
                j = i
        return adentro

    def donde(self, x, y):
        """Clave del primer polígono que contiene el punto, o None."""
        for k in self.celdas.get((int(x // self.CELDA), int(y // self.CELDA)), ()):
            clave, anis, c = self.items[k]
            if c[0] <= x <= c[2] and c[1] <= y <= c[3] and self._dentro(x, y, anis):
                return clave
        return None

    def caja(self):
        cs = [c for _, _, c in self.items]
        return (min(c[0] for c in cs), min(c[1] for c in cs), max(c[2] for c in cs), max(c[3] for c in cs))


def rejilla(caja, paso_m=120):
    """Puntos (lon, lat) separados ~paso_m metros dentro de una caja (min_lon, min_lat, max_lon, max_lat)."""
    lat0 = (caja[1] + caja[3]) / 2
    dy = paso_m / 1000 / KM_POR_GRADO_LAT
    dx = paso_m / 1000 / (111.32 * math.cos(math.radians(lat0)))
    y = caja[1] + dy / 2
    while y < caja[3]:
        x = caja[0] + dx / 2
        while x < caja[2]:
            yield x, y
            x += dx
        y += dy


def leer_territorio(nombre):
    return json.loads((LAGO / "territorio" / f"{nombre}.geojson").read_text(encoding="utf-8"))["features"]


def simplificar_linea(puntos, tol=0.00005):
    """Douglas-Peucker en grados (0,00005 ≈ 5 m en Orlando), con 5 decimales y sin puntos repetidos."""
    pts = []
    for x, y in puntos:
        q = [round(float(x), 5), round(float(y), 5)]
        if not pts or q != pts[-1]:
            pts.append(q)
    if len(pts) <= 2:
        return pts
    def dp(a, b):
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** 0.5 or 1e-12
        lejos, k = 0.0, None
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
            if d > lejos:
                lejos, k = d, i
        return dp(a, k)[:-1] + dp(k, b) if k is not None and lejos > tol else [pts[a], pts[b]]
    return dp(0, len(pts) - 1)


def escribir_territorio(nombre, features):
    """Capa de referencia en lago/territorio/<nombre>.geojson (WGS84), compacta y siempre igual para los mismos datos."""
    ruta = LAGO / "territorio" / f"{nombre}.geojson"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return ruta


def capa_barrios():
    return Capa([(f["properties"]["nombre"], f["geometry"]) for f in leer_territorio("barrios")])


def capa_lagos():
    return Capa([(i, f["geometry"]) for i, f in enumerate(leer_territorio("lagos"))])


def reparto(capa_zonas, paso_m=120):
    """Qué parte de cada zona (tract, zona de tránsito…) cae en cada barrio, contando puntos de tierra firme.
    Devuelve ({zona: {barrio: fracción de la zona}}, {barrio: fracción del barrio cubierta por alguna zona})."""
    barrios, lagos = capa_barrios(), capa_lagos()
    cb = barrios.caja()
    # Solo interesan las zonas que tocan la caja de la ciudad, pero se cuentan enteras (también fuera de la ciudad)
    utiles = [it for it in capa_zonas.items if not (it[2][2] < cb[0] or it[2][0] > cb[2] or it[2][3] < cb[1] or it[2][1] > cb[3])]
    if not utiles:
        return {}, {}
    caja = (min(c[0] for _, _, c in utiles), min(c[1] for _, _, c in utiles), max(c[2] for _, _, c in utiles), max(c[3] for _, _, c in utiles))
    total_zona, cruce, tierra_barrio, cubierto = {}, {}, {}, {}
    for x, y in rejilla(caja, paso_m):
        if lagos.donde(x, y) is not None:
            continue
        z = capa_zonas.donde(x, y)
        b = barrios.donde(x, y) if cb[0] <= x <= cb[2] and cb[1] <= y <= cb[3] else None
        if b is not None:
            tierra_barrio[b] = tierra_barrio.get(b, 0) + 1
        if z is None:
            continue
        total_zona[z] = total_zona.get(z, 0) + 1
        if b is not None:
            cruce.setdefault(z, {})[b] = cruce.setdefault(z, {}).get(b, 0) + 1
            cubierto[b] = cubierto.get(b, 0) + 1
    pesos = {z: {b: n / total_zona[z] for b, n in bs.items()} for z, bs in cruce.items()}
    return pesos, {b: cubierto.get(b, 0) / n for b, n in tierra_barrio.items()}


def punto_en_barrio(barrios, lon, lat):
    return barrios.donde(float(lon), float(lat))


def cobertura_zona(capa_zona, paso_m=120):
    """Qué fracción de la tierra de cada barrio cae dentro de alguna zona de la capa (zona de oportunidad, CRA…).
    Devuelve {barrio: fracción} y {barrio: [claves de las zonas que lo tocan]}."""
    barrios, lagos = capa_barrios(), capa_lagos()
    total, dentro, cuales = {}, {}, {}
    for x, y in rejilla(barrios.caja(), paso_m):
        b = barrios.donde(x, y)
        if b is None or lagos.donde(x, y) is not None:
            continue
        total[b] = total.get(b, 0) + 1
        z = capa_zona.donde(x, y)
        if z is not None:
            dentro[b] = dentro.get(b, 0) + 1
            cuales.setdefault(b, set()).add(z)
    return {b: dentro.get(b, 0) / n for b, n in total.items()}, {b: sorted(map(str, z)) for b, z in cuales.items()}


def area_km2(geom):
    """Área aproximada (km²) de un polígono GeoJSON, en proyección plana local (bordes menos huecos por par-impar)."""
    total = 0.0
    for poli in anillos(geom):
        for k, a in enumerate(poli):
            lat0 = sum(p[1] for p in a) / len(a)
            kx = 111.32 * math.cos(math.radians(lat0))
            s = sum((a[i][0] * kx) * (a[(i + 1) % len(a)][1] * KM_POR_GRADO_LAT) - (a[(i + 1) % len(a)][0] * kx) * (a[i][1] * KM_POR_GRADO_LAT) for i in range(len(a)))
            total += abs(s) / 2 * (1 if k == 0 else -1)
    return total


def centro(geom):
    """Centro del anillo más grande (promedio de vértices): suficiente para decir en qué barrio cae un parque."""
    mayor = max((a for poli in anillos(geom) for a in poli[:1]), key=len, default=None)
    if not mayor:
        return None
    return sum(p[0] for p in mayor) / len(mayor), sum(p[1] for p in mayor) / len(mayor)


def largo_km(x1, y1, x2, y2):
    kx = 111.32 * math.cos(math.radians((y1 + y2) / 2))
    return math.hypot((x2 - x1) * kx, (y2 - y1) * KM_POR_GRADO_LAT)


def arcgis(capa, **partes):
    """URL de consulta a una capa de ArcGIS Server, con coordenadas en grados (4326)."""
    import urllib.parse
    base = {"where": "1=1", "outSR": "4326", "f": "json"}
    base.update(partes)
    return f"{capa}/query?" + urllib.parse.urlencode(base)
