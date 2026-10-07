#!/usr/bin/env python3
"""Ingesta · permisos de construcción de Orlando por barrio y año (F79, dataset ryhf-m453 «Permit Applications»).

Lee:     portal de datos abiertos de Orlando (API SODA, sin llave).
Escribe: lago/raw/permisos/permisos.json con la forma del contrato.

PRIVACIDAD (por qué este tema es el del dato delicado):
- El dataset original trae nombres de propietarios, nombre y teléfono del contratista y la dirección de cada permiso.
  Aquí NUNCA se descargan: la consulta (SoQL) agrupa en el servidor y solo pide el barrio, el año y un conteo.
- Se suprimen los barrios con menos de UMBRAL permisos en el año: un barrio con uno o dos permisos señala a una persona.
- El umbral queda escrito en el lago (cifra «umbral_minimo_por_barrio») y verificar.py comprueba que se respete.
- Límite conocido: como el total de la ciudad y los barrios mostrados se publican, la suma de lo suprimido puede deducirse.
  Cada barrio suprimido tiene menos de UMBRAL permisos y no hay nombres, por eso se acepta.

SUPUESTO A CONFIRMAR con una fila real: «Issue Permit Date» (issue_permit_date) con fecha = permiso emitido.
Las solicitudes sin esa fecha todavía no se cuentan.

Cruce con la capa de barrios: los nombres del campo «neighborhood» se comparan con los de la capa de barrios del portal y el
porcentaje que coincide queda en el lago; si es bajo, el nombre no es una llave confiable."""
import datetime, urllib.parse
from comun import get_json, fuente_lago, cifra, escribir_lago, variacion_pct

PORTAL = "https://data.cityoforlando.net"
DATASET = "ryhf-m453"
UMBRAL = 5                       # mínimo de permisos por barrio y año para mostrarlo
UNIDAD = "permisos emitidos (solicitudes con fecha de emisión)"


def soql(select, where, group, order):
    partes = {"$select": select, "$where": where, "$group": group, "$order": order, "$limit": "50000"}
    return f"{PORTAL}/resource/{DATASET}.json?" + "&".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in partes.items())


def limpio(txt):
    return " ".join(str(txt or "").split())


hoy = datetime.date.today()
filas = get_json(soql("neighborhood, date_extract_y(issue_permit_date) as anio, count(*) as permisos",
                      "issue_permit_date IS NOT NULL", "neighborhood, anio", "anio"), timeout=120)
if not filas:
    raise SystemExit("La consulta de permisos volvió vacía: ¿cambió el nombre de algún campo?")

por_anio_barrio, fuera_de_rango = {}, 0
for f in filas:
    anio, n = int(float(f["anio"])), int(float(f["permisos"]))
    if not 2000 <= anio <= hoy.year:
        fuera_de_rango += n
        continue
    barrio = limpio(f.get("neighborhood"))
    por_anio_barrio.setdefault(anio, {})
    por_anio_barrio[anio][barrio] = por_anio_barrio[anio].get(barrio, 0) + n
if fuera_de_rango:
    print(f"AVISO: {fuera_de_rango} permisos con año fuera de 2000..{hoy.year} no se cuentan.")

total = {a: sum(b.values()) for a, b in por_anio_barrio.items()}
completos = sorted(a for a in total if a < hoy.year)        # un año a medias engaña: el año en curso va aparte
if not completos:
    raise SystemExit("No hay ningún año completo en los datos.")
ultimo = completos[-1]

# Barrios del último año completo, con supresión de celdas pequeñas
barrios = {b: n for b, n in por_anio_barrio[ultimo].items() if b}
sin_barrio = por_anio_barrio[ultimo].get("", 0)
mostrados = {b: n for b, n in barrios.items() if n >= UMBRAL}
suprimidos = len(barrios) - len(mostrados)

# ¿Los nombres coinciden con la capa de barrios? (el cruce por nombre se mide, no se supone)
capa = {limpio(r.get("neighborhoodname")).casefold() for r in get_json(f"{PORTAL}/resource/yskk-n7cw.json?$select=neighborhoodname&$limit=5000")}
coinciden = sum(1 for b in mostrados if b.casefold() in capa)
pct_coincide = round(100 * coinciden / len(mostrados), 1) if mostrados else 0.0

ficha = get_json(f"{PORTAL}/api/views/{DATASET}.json")
actualizado = datetime.datetime.fromtimestamp(ficha["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()

F = "orlando_permisos"
cifras = {
    "permisos_emitidos_ultimo_anio_completo": cifra(total[ultimo], UNIDAD, str(ultimo), F),
    "permisos_emitidos_anio_en_curso": cifra(total.get(hoy.year, 0), UNIDAD + ", año en curso a la fecha", actualizado, F),
    "barrios_mostrados_ultimo_anio": cifra(len(mostrados), "barrios", str(ultimo), F),
    "barrios_suprimidos_ultimo_anio": cifra(suprimidos, "barrios con menos permisos que el umbral", str(ultimo), F),
    "permisos_sin_barrio_ultimo_anio": cifra(sin_barrio, UNIDAD + ", sin barrio asignado", str(ultimo), F),
    "umbral_minimo_por_barrio": cifra(UMBRAL, "permisos", str(ultimo), F),
    "coincidencia_nombres_con_capa_barrios": cifra(pct_coincide, "% de los barrios mostrados", actualizado, F),
}
if len(completos) >= 2 and total[completos[-2]]:
    cifras["variacion_ultimo_anio"] = cifra(variacion_pct(total[ultimo], total[completos[-2]]), "%", str(ultimo), F)

series = {
    "permisos_por_anio": {"unidad": UNIDAD, "fuente": F, "puntos": [[str(a), total[a]] for a in completos]},
    "permisos_por_barrio_ultimo_anio": {"unidad": UNIDAD, "fuente": F,
                                        "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])},
}
url = f"{PORTAL}/resource/{DATASET}.json"
ruta = escribir_lago("permisos", [fuente_lago(F, url)], cifras, series)
print(f"Permisos {ultimo}: {total[ultimo]} en la ciudad; {len(mostrados)} barrios mostrados, {suprimidos} suprimidos (< {UMBRAL}), "
      f"{sin_barrio} sin barrio; nombres que coinciden con la capa: {pct_coincide} % -> {ruta.name}")
