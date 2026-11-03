#!/usr/bin/env python3
"""Ingesta · transporte público: las paradas, rutas y salidas de los buses de LYNX en cada barrio (GTFS).

Lee:     el GTFS de LYNX (Central Florida Regional Transit Authority): un ZIP con paradas, rutas, viajes y horarios.
         Primero la dirección oficial de LYNX; si no responde (o no está en la captura), la copia que guarda
         Mobility Database del mismo feed. La zona cruda anota cuál de las dos respondió.
Escribe: lago/curado/tema=transporte/fecha=<día>/transporte.json y lago/territorio/rutas_bus.geojson (el recorrido más
         usado de cada ruta que para en la ciudad, para el mapa de la pestaña Movilidad)

Cómo se cuenta: se toma un miércoles normal dentro de la vigencia del feed (el primero que no tenga excepciones) y se
cuenta cuántas veces para un bus en cada parada ese día («salidas»). Cada parada se ubica en su barrio con su punto.
No trae personas: son horarios publicados."""
import csv, datetime, io, statistics, zipfile
from comun import abrir, fuente_lago, cifra, escribir_lago, capa_barrios, punto_en_barrio, leer_territorio, simplificar_linea, escribir_territorio

OFICIAL = "http://gtfsrt.golynx.com/gtfsrt/google_transit.zip"
COPIA = "https://files.mobilitydatabase.org/mdb-347/latest.zip"


def traer():
    try:
        return abrir(OFICIAL, timeout=120).read(), OFICIAL
    except (Exception, SystemExit):
        return abrir(COPIA, timeout=120).read(), COPIA


cuerpo, usada = traer()
z = zipfile.ZipFile(io.BytesIO(cuerpo))
leer = lambda n: list(csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))) if n in z.namelist() else []
stops, routes, trips = leer("stops.txt"), leer("routes.txt"), leer("trips.txt")
calendar, fechas = leer("calendar.txt"), leer("calendar_dates.txt")
if not (stops and routes and trips):
    raise SystemExit("El GTFS no trae stops, routes o trips.")

# Un miércoles normal: el primero dentro de la vigencia que no tenga excepciones en calendar_dates
d = lambda s: datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
inicio = min(d(c["start_date"]) for c in calendar) if calendar else min(d(f["date"]) for f in fechas)
fin = max(d(c["end_date"]) for c in calendar) if calendar else max(d(f["date"]) for f in fechas)
excepciones = {}
for f in fechas:
    excepciones.setdefault(d(f["date"]), []).append((f["service_id"], f["exception_type"]))
dia = inicio + datetime.timedelta(days=(2 - inicio.weekday()) % 7)
while dia in excepciones and dia <= fin:
    dia += datetime.timedelta(days=7)
activos = {c["service_id"] for c in calendar if c["wednesday"] == "1" and d(c["start_date"]) <= dia <= d(c["end_date"])}
for sid, tipo in excepciones.get(dia, []):
    (activos.add if tipo == "1" else activos.discard)(sid)
viajes = {t["trip_id"]: t["route_id"] for t in trips if t["service_id"] in activos}

barrios = capa_barrios()
nombres_b = [f["properties"]["nombre"] for f in leer_territorio("barrios")]
barrio_de = {}
for s in stops:
    if s.get("location_type", "0") in ("", "0") and s.get("stop_lat") and s.get("stop_lon"):
        barrio_de[s["stop_id"]] = punto_en_barrio(barrios, s["stop_lon"], s["stop_lat"])

salidas, rutas_b, salidas_ruta, rutas_ciudad = {}, {}, {}, set()
with io.TextIOWrapper(z.open("stop_times.txt"), encoding="utf-8-sig") as fh:
    for st in csv.DictReader(fh):
        r = viajes.get(st["trip_id"])
        b = barrio_de.get(st["stop_id"])
        if r is None or b is None:
            continue
        salidas[b] = salidas.get(b, 0) + 1
        rutas_b.setdefault(b, set()).add(r)
        salidas_ruta[r] = salidas_ruta.get(r, 0) + 1
        rutas_ciudad.add(r)
paradas = {}
for sid, b in barrio_de.items():
    if b:
        paradas[b] = paradas.get(b, 0) + 1
nombre_ruta = {r["route_id"]: " ".join(f"{r.get('route_short_name', '')} {r.get('route_long_name', '')}".split()) for r in routes}
top_rutas = sorted(((nombre_ruta.get(r, r), n) for r, n in salidas_ruta.items()), key=lambda p: (-p[1], p[0]))[:12]

vig = dia.isoformat()
F = "lynx_gtfs"
sin_parada = [b for b in nombres_b if not paradas.get(b)]
cifras = {
    "rutas_en_la_ciudad": cifra(len(rutas_ciudad), "rutas de bus que paran en la ciudad", vig, F),
    "rutas_lynx": cifra(len(routes), "rutas en el horario de LYNX", vig, F),
    "paradas_en_la_ciudad": cifra(sum(paradas.values()), "paradas de bus dentro de la ciudad", vig, F),
    "salidas_dia_habil_ciudad": cifra(sum(salidas.values()), "veces que para un bus en la ciudad en un día hábil", vig, F),
    "barrios_sin_parada": cifra(len(sin_parada), "barrios sin ninguna parada de bus", vig, F),
    "mediana_salidas_barrio": cifra(round(statistics.median([salidas.get(b, 0) for b in nombres_b])), "paradas de bus por barrio en un día hábil (mediana)", vig, F),
}
ordenar = lambda dic: sorted(([b, n] for b, n in dic.items() if n), key=lambda p: (-p[1], p[0]))
series = {
    "paradas_barrio": {"unidad": "paradas de bus", "fuente": F, "puntos": ordenar(paradas)},
    "rutas_barrio": {"unidad": "rutas de bus que paran en el barrio", "fuente": F, "puntos": ordenar({b: len(r) for b, r in rutas_b.items()})},
    "salidas_barrio": {"unidad": "veces que para un bus en un día hábil", "fuente": F, "puntos": ordenar(salidas)},
    "rutas_mas_frecuentes": {"unidad": "paradas que hace la ruta dentro de la ciudad en un día hábil", "fuente": F, "puntos": [[n, v] for n, v in top_rutas]},
}
# El recorrido de cada ruta: la forma (shape) que más viajes usa ese miércoles
usos = {}
for t in trips:
    r = viajes.get(t["trip_id"])
    if r in rutas_ciudad and (t.get("shape_id") or "").strip():
        usos.setdefault(r, {}).setdefault(t["shape_id"].strip(), 0)
        usos[r][t["shape_id"].strip()] += 1
forma_de = {r: sorted(c.items(), key=lambda p: (-p[1], p[0]))[0][0] for r, c in usos.items()}
puntos_forma = {}
if "shapes.txt" in z.namelist():
    with io.TextIOWrapper(z.open("shapes.txt"), encoding="utf-8-sig") as fh:
        quiero = set(forma_de.values())
        for p in csv.DictReader(fh):
            if p["shape_id"].strip() in quiero:
                puntos_forma.setdefault(p["shape_id"].strip(), []).append((int(p["shape_pt_sequence"]), float(p["shape_pt_lon"]), float(p["shape_pt_lat"])))
recorridos = []
for r, sid in forma_de.items():
    pts = simplificar_linea([(x, y) for _, x, y in sorted(puntos_forma.get(sid, []))], tol=0.0001)
    if len(pts) >= 2:
        recorridos.append({"type": "Feature", "properties": {"ruta": nombre_ruta.get(r, r), "paradas_dia": salidas_ruta[r], "fuente": F},
                           "geometry": {"type": "LineString", "coordinates": pts}})
capa = escribir_territorio("rutas_bus", sorted(recorridos, key=lambda f: (f["properties"]["paradas_dia"], f["properties"]["ruta"])))
ruta = escribir_lago("transporte", [fuente_lago(F, usada)], cifras, series)
print(f"Transporte (GTFS de {'LYNX' if usada == OFICIAL else 'Mobility Database'}, día {vig}): {len(rutas_ciudad)} rutas, "
      f"{sum(paradas.values())} paradas, {sum(salidas.values())} salidas; {len(sin_parada)} barrios sin parada -> {ruta}; "
      f"{len(recorridos)} recorridos en {capa.name} ({capa.stat().st_size // 1024} KB)")
