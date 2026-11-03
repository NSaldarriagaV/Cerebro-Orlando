#!/usr/bin/env python3
"""Ingesta · qué pasa con la seguridad: casos de la Policía de Orlando por barrio y por año (F106).

Lee:     servicio de mapas público de la ciudad (ArcGIS REST, capa OPD_Cases_Viewing), sin llave.
         Todas las consultas piden ESTADÍSTICAS al servidor (outStatistics + groupByFieldsForStatistics): nunca se baja un caso.
Escribe: lago/raw/seguridad/seguridad.json con la forma del contrato.

PRIVACIDAD (este es el tema más delicado del lago):
- La capa trae el número de caso, la fecha y el punto exacto de cada hecho: con eso se puede llegar a una víctima o a un
  domicilio. Aquí no se pide ninguno de esos campos; el servidor devuelve conteos por barrio, por tipo y por año.
- Solo entran tres grupos de delitos (hurtos y robos a la propiedad, violencia contra personas, drogas). No entran al lago
  los casos de salud mental (Baker Act), suicidios, muertes, personas desaparecidas, disputas de custodia, órdenes de
  alejamiento ni reportes administrativos: no son delitos y señalarían a personas vulnerables.
- Cada celda barrio-año con menos de UMBRAL casos se suprime (no se publica cuál).
- Límite conocido: «caso» no es «delito comprobado»; es un reporte que la policía abrió. Y no hay población por barrio,
  así que no se calculan tasas por habitante: solo totales y casos por km² (en la vista)."""
import datetime, json, urllib.parse
from comun import get_json, fuente_lago, cifra, escribir_lago, variacion_pct

CAPA = "https://gis.orlando.gov/server/rest/services/OPD_Cases_Viewing/FeatureServer/0"
UMBRAL = 5
GRUPOS = {
    "hurtos": ["Petit Theft", "Grand Theft", "Vehicle Burglary", "Residential Burglary", "Commercial Burglary", "Motor Vehicle Theft",
               "Attempted Motor Vehicle Theft", "Pickpocket Theft", "Distraction Theft"],
    "violencia": ["Battery", "Aggravated Assault", "Aggravated Battery", "Assault", "Homicide", "Attempted Homicide",
                  "Shooting at/within/in struc/veh", "Person Robbery", "Armed Robbery", "Commercial Robbery", "Home Invasion Robbery",
                  "Carjacking", "Kidnapping", "Attempted Kidnapping", "Battery on LEO/Firefighter", "Vehicular Homicide"],
    "drogas": ["Drug Violation", "Possession of Controlled Subst", "Trafficking Controlled Substance", "Sale and Delivery/Controlled Sub"],
}
NOMBRE_GRUPO = {"hurtos": "hurtos y robos a la propiedad", "violencia": "violencia contra personas", "drogas": "drogas"}
TIPO_ES = {"Petit Theft": "Hurto menor", "Grand Theft": "Hurto mayor", "Vehicle Burglary": "Robo en vehículo",
           "Residential Burglary": "Robo en vivienda", "Commercial Burglary": "Robo en comercio", "Motor Vehicle Theft": "Robo de vehículo",
           "Attempted Motor Vehicle Theft": "Intento de robo de vehículo", "Pickpocket Theft": "Carterismo", "Distraction Theft": "Hurto por distracción",
           "Battery": "Agresión física", "Aggravated Assault": "Amenaza con arma", "Aggravated Battery": "Agresión con lesiones graves",
           "Assault": "Amenaza de agresión", "Homicide": "Homicidio", "Attempted Homicide": "Intento de homicidio",
           "Shooting at/within/in struc/veh": "Disparos contra vivienda o vehículo", "Person Robbery": "Atraco a persona",
           "Armed Robbery": "Atraco con arma", "Commercial Robbery": "Atraco a comercio", "Home Invasion Robbery": "Atraco en vivienda",
           "Carjacking": "Robo de vehículo con violencia", "Kidnapping": "Secuestro", "Attempted Kidnapping": "Intento de secuestro",
           "Battery on LEO/Firefighter": "Agresión a policía o bombero", "Vehicular Homicide": "Homicidio con vehículo",
           "Drug Violation": "Infracción de drogas", "Possession of Controlled Subst": "Posesión de sustancias controladas",
           "Trafficking Controlled Substance": "Tráfico de sustancias controladas", "Sale and Delivery/Controlled Sub": "Venta de sustancias controladas"}


def consulta(where, agrupar):
    stats = json.dumps([{"statisticType": "count", "onStatisticField": "CaseNumber", "outStatisticFieldName": "n"}], separators=(",", ":"))
    partes = {"where": where, "groupByFieldsForStatistics": agrupar, "outStatistics": stats, "f": "json"}
    r = get_json(f"{CAPA}/query?" + urllib.parse.urlencode(partes, quote_via=urllib.parse.quote), timeout=120)
    if "error" in r:
        raise SystemExit(f"El servidor respondió con error: {r['error']}")
    return [f["attributes"] for f in r["features"]]


def donde(tipos, a):
    lista = ",".join("'" + t.replace("'", "''") + "'" for t in tipos)
    return f"CaseType IN ({lista}) AND CaseDate >= DATE '{a}-01-01' AND CaseDate < DATE '{a + 1}-01-01'"


def limpio(txt):
    return " ".join(str(txt or "").split())


hoy = datetime.date.today()
# El primer caso de la capa es de febrero de 2021: 2021 está incompleto y no se usa
rango = get_json(f"{CAPA}/query?" + urllib.parse.urlencode({"where": "1=1", "f": "json", "outStatistics": json.dumps(
    [{"statisticType": "min", "onStatisticField": "CaseDate", "outStatisticFieldName": "mn"}])}, quote_via=urllib.parse.quote))
primero = datetime.datetime.fromtimestamp(rango["features"][0]["attributes"]["mn"] / 1000, datetime.timezone.utc).date()
anios = [a for a in range(primero.year + (0 if primero <= datetime.date(primero.year, 1, 7) else 1), hoy.year)]
if len(anios) < 2:
    raise SystemExit("La capa no tiene dos años completos.")
ultimo = anios[-1]

por_anio = {g: {} for g in GRUPOS}             # ciudad: grupo -> año -> n
barrio = {}                                     # (grupo, año) -> {barrio: n}
for a in anios:
    for g, tipos in GRUPOS.items():
        filas = consulta(donde(tipos, a), "NeighborhoodName")
        conteo = {}
        for f in filas:
            nombre = limpio(f["NeighborhoodName"])
            conteo[nombre] = conteo.get(nombre, 0) + int(f["n"])
        barrio[(g, a)] = conteo
        por_anio[g][a] = sum(conteo.values())

# Tipos del último año completo, para toda la ciudad
tipos_ult = {}
for f in consulta(donde([t for ts in GRUPOS.values() for t in ts], ultimo), "CaseType"):
    tipos_ult[TIPO_ES.get(f["CaseType"], f["CaseType"])] = int(f["n"])

# Año en curso, para toda la ciudad (no se grafica: está incompleto)
en_curso = sum(int(f["n"]) for f in consulta(donde([t for ts in GRUPOS.values() for t in ts], hoy.year), "CaseType"))

series, cifras = {}, {}
for g in GRUPOS:
    series[f"{g}_por_anio"] = {"unidad": f"casos de {NOMBRE_GRUPO[g]} en el año", "fuente": "opd_casos",
                               "puntos": [[str(a), por_anio[g][a]] for a in anios]}
suprimidos_ult = sin_barrio_ult = 0
for a in anios:
    total = {}
    for g in GRUPOS:
        for b, n in barrio[(g, a)].items():
            total[b] = total.get(b, 0) + n
    mostrados = {b: n for b, n in total.items() if b and n >= UMBRAL}
    series[f"delitos_barrio_{a}"] = {"unidad": "casos de los tres grupos en el año", "fuente": "opd_casos",
                                     "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
    if a == ultimo:
        suprimidos_ult = sum(1 for b, n in total.items() if b and n < UMBRAL)
        sin_barrio_ult = total.get("", 0)
        total_ult = sum(total.values())
for g in GRUPOS:
    mostrados = {b: n for b, n in barrio[(g, ultimo)].items() if b and n >= UMBRAL}
    series[f"{g}_barrio_{ultimo}"] = {"unidad": f"casos de {NOMBRE_GRUPO[g]} en {ultimo}", "fuente": "opd_casos",
                                      "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
series[f"tipos_{ultimo}"] = {"unidad": f"casos en toda la ciudad en {ultimo}", "fuente": "opd_casos",
                             "puntos": sorted(([t, n] for t, n in tipos_ult.items() if n >= UMBRAL), key=lambda p: -p[1])}

anterior = anios[-2]
total_ant = sum(por_anio[g][anterior] for g in GRUPOS)
F = "opd_casos"
cifras = {
    "delitos_ultimo_anio": cifra(total_ult, "casos de hurtos, violencia y drogas", str(ultimo), F),
    "variacion_ultimo_anio": cifra(variacion_pct(total_ult, total_ant), "%", str(ultimo), F),
    "hurtos_ultimo_anio": cifra(por_anio["hurtos"][ultimo], "casos", str(ultimo), F),
    "violencia_ultimo_anio": cifra(por_anio["violencia"][ultimo], "casos", str(ultimo), F),
    "drogas_ultimo_anio": cifra(por_anio["drogas"][ultimo], "casos", str(ultimo), F),
    "delitos_anio_en_curso": cifra(en_curso, "casos de los tres grupos, año en curso a la fecha", hoy.isoformat(), F),
    "barrios_suprimidos_ultimo_anio": cifra(suprimidos_ult, "barrios con menos casos que el umbral", str(ultimo), F),
    "casos_sin_barrio_ultimo_anio": cifra(sin_barrio_ult, "casos sin barrio asignado", str(ultimo), F),
    "umbral_minimo_por_barrio": cifra(UMBRAL, "casos", str(ultimo), F),
}
ruta = escribir_lago("seguridad", [fuente_lago(F, f"{CAPA}/query")], cifras, series)
print(f"Seguridad {ultimo}: {total_ult} casos ({por_anio['hurtos'][ultimo]} hurtos, {por_anio['violencia'][ultimo]} violencia, "
      f"{por_anio['drogas'][ultimo]} drogas); {suprimidos_ult} barrios suprimidos; años {anios} -> {ruta.name}")
