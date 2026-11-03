#!/usr/bin/env python3
"""Ingesta · negocios con licencia vigente por barrio, y hospedajes y restaurantes (F81, «Business Tax Receipts»).

Lee:     portal de datos abiertos de Orlando, «Business Tax Receipts» (7388-4re5), API SODA sin llave.
Escribe: lago/raw/negocios/negocios.json con la forma del contrato.

Qué cuenta: licencias de negocio (Business Tax Receipt) con estado «Open». Un negocio con varias actividades puede tener
más de una licencia: es un conteo de licencias, no de empresas. Las categorías son códigos de la ciudad (PROFES, RESTAU,
LODGES…); el nombre en español es nuestra lectura del código y se marca así en la vista.

PRIVACIDAD: el dataset trae el nombre del dueño, teléfono y correo del negocio. Nunca se descargan: la consulta agrupa en el
servidor por barrio y categoría. Celdas con menos de UMBRAL licencias se suprimen (un negocio solo en su categoría y barrio
se reconoce)."""
import datetime, urllib.parse
from comun import get_json, fuente_lago, cifra, escribir_lago

PORTAL = "https://data.cityoforlando.net"
DATASET = "7388-4re5"
UMBRAL = 5
ABIERTO = "license_status = 'Open'"
CATEGORIA_ES = {"PROFES": "Servicios profesionales", "SERREP": "Servicios y reparaciones", "CONTRA": "Contratistas",
                "MERCNT": "Comercio", "BUSOFF": "Oficinas", "PEDDLE": "Venta ambulante", "RESTAU": "Restaurantes",
                "PARLOR": "Salones de belleza", "JANSER": "Aseo y limpieza", "INSURE": "Seguros", "MASSEU": "Masajes",
                "FINANC": "Servicios financieros", "MANUFA": "Manufactura", "LODGES": "Hospedaje", "WARHSE": "Bodegas",
                "LAWNMT": "Jardinería", "DISTRI": "Distribución", "AUTOMO": "Automotor", "SCHOOL": "Escuelas",
                "LAUNDR": "Lavanderías", "PHOTOG": "Fotografía", "VENDNG": "Máquinas expendedoras", "TRAVEL": "Agencias de viaje",
                "CHILDC": "Cuidado infantil", "AMUSEM": "Entretenimiento", "CATERE": "Banquetes", "ARTIST": "Artistas",
                "ADVERT": "Publicidad", "TOURSV": "Servicios turísticos", "INSTRU": "Instructores y academias",
                "MAILOD": "Ventas por correo o internet", "SERSTA": "Estaciones de servicio", "HELSPA": "Spas y gimnasios",
                "WRECKR": "Grúas", "DETECT": "Seguridad privada", "LANDSC": "Paisajismo", "MANICU": "Manicura",
                "DANCEH": "Salones de baile", "DECORA": "Decoración", "LABORT": "Laboratorios"}
# v3: categorías que la sección «Decidir» compara por barrio (demanda contra competencia)
GIROS = {"comercio": "MERCNT", "belleza": "PARLOR", "profesionales": "PROFES", "cuidado_infantil": "CHILDC", "automotor": "AUTOMO"}


def soql(**partes):
    partes.setdefault("limit", "50000")
    return f"{PORTAL}/resource/{DATASET}.json?" + "&".join(f"${k}={urllib.parse.quote(v, safe='')}" for k, v in partes.items())


def limpio(txt):
    return " ".join(str(txt or "").split())


def por_barrio(where):
    conteo = {}
    for f in get_json(soql(select="neighborhood_name, count(*) as n", where=where, group="neighborhood_name")):
        b = limpio(f.get("neighborhood_name"))
        conteo[b] = conteo.get(b, 0) + int(f["n"])
    return conteo


hoy = datetime.date.today()
ficha = get_json(f"{PORTAL}/api/views/{DATASET}.json")
actualizado = datetime.datetime.fromtimestamp(ficha["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()

total = por_barrio(ABIERTO)
rest = por_barrio(ABIERTO + " AND license_category = 'RESTAU'")
hosp = por_barrio(ABIERTO + " AND license_category = 'LODGES'")
giros = {g: por_barrio(ABIERTO + f" AND license_category = '{c}'") for g, c in GIROS.items()}
# Negocios que abrieron el último año completo, por barrio (vigentes o no): dónde se está abriendo negocio
ult_anio = datetime.date.today().year - 1
nuevos = por_barrio(f"business_open_date >= '{ult_anio}-01-01T00:00:00' AND business_open_date < '{ult_anio + 1}-01-01T00:00:00'")
cats = get_json(soql(select="license_category, count(*) as n", where=ABIERTO, group="license_category", order="n DESC"))
aperturas = get_json(soql(select="date_extract_y(business_open_date) as anio, count(*) as n",
                          where="business_open_date IS NOT NULL", group="anio", order="anio"))

F = "orlando_negocios"
series = {}
supr = {}
for nombre, conteo, unidad in (("negocios_barrio", total, "licencias de negocio vigentes"),
                               ("restaurantes_barrio", rest, "licencias de restaurante vigentes"),
                               ("hospedajes_barrio", hosp, "licencias de hospedaje vigentes"),
                               (f"aperturas_barrio_{ult_anio}", nuevos, f"licencias con fecha de apertura en {ult_anio}"),
                               *((f"{g}_barrio", giros[g], f"licencias vigentes de la categoría {CATEGORIA_ES[c]}") for g, c in GIROS.items())):
    mostrados = {b: n for b, n in conteo.items() if b and n >= UMBRAL}
    supr[nombre] = sum(1 for b, n in conteo.items() if b and n < UMBRAL)
    series[nombre] = {"unidad": unidad, "fuente": F, "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
cat_pts = [[CATEGORIA_ES.get(limpio(c.get("license_category")), limpio(c.get("license_category")) or "Sin categoría"), int(c["n"])]
           for c in cats if int(c["n"]) >= UMBRAL]
series["categorias_ciudad"] = {"unidad": "licencias de negocio vigentes en toda la ciudad", "fuente": F, "puntos": cat_pts}
series["aperturas_por_anio"] = {"unidad": "licencias con fecha de apertura en el año (vigentes o cerradas)", "fuente": F,
                                "puntos": [[str(int(float(a["anio"]))), int(a["n"])] for a in aperturas
                                           if 2000 <= int(float(a["anio"])) < hoy.year]}
cifras = {
    "negocios_vigentes": cifra(sum(total.values()), "licencias de negocio vigentes", actualizado, F),
    "restaurantes_vigentes": cifra(sum(rest.values()), "licencias de restaurante vigentes", actualizado, F),
    "hospedajes_vigentes": cifra(sum(hosp.values()), "licencias de hospedaje vigentes", actualizado, F),
    "negocios_sin_barrio": cifra(total.get("", 0), "licencias vigentes sin barrio asignado", actualizado, F),
    "barrios_suprimidos_negocios": cifra(supr["negocios_barrio"], "barrios con menos licencias que el umbral", actualizado, F),
    "barrios_suprimidos_hospedajes": cifra(supr["hospedajes_barrio"], "barrios con menos licencias de hospedaje que el umbral", actualizado, F),
    "umbral_minimo_por_barrio": cifra(UMBRAL, "licencias", actualizado, F),
}
ruta = escribir_lago("negocios", [fuente_lago(F, f"{PORTAL}/resource/{DATASET}.json")], cifras, series)
print(f"Negocios vigentes {actualizado}: {sum(total.values())} ({sum(rest.values())} restaurantes, {sum(hosp.values())} hospedajes); "
      f"{len(series['negocios_barrio']['puntos'])} barrios -> {ruta.name}")
