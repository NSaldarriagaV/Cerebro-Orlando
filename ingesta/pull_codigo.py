#!/usr/bin/env python3
"""Ingesta · mantenimiento urbano: casos de código (Code Enforcement) por barrio y por año (F83).

Lee:     portal de datos abiertos de Orlando, «Code Enforcement Cases» (k6e8-nw6w), API SODA sin llave.
Escribe: lago/raw/codigo/codigo.json con la forma del contrato.

Qué es: un caso de código se abre cuando un predio incumple normas de la ciudad (lote enmontado, vivienda insegura,
avisos, zonificación). Puede abrirlo un funcionario o una queja ciudadana (campo «src» = Citizen). Las quejas ciudadanas son
lo más cercano que hay abierto a «qué reclaman los vecinos» (el 311 no está publicado), pero no lo reemplazan.

PRIVACIDAD: «Case Name», «Case Comments», «Add By» y la dirección pueden traer nombres. Nunca se descargan: la consulta
agrupa en el servidor por barrio, año y tipo. Celdas barrio-año con menos de UMBRAL casos se suprimen.
El sistema de casos arranca en 2016-2017 (antes hay pocos registros migrados): la serie anual empieza en 2017."""
import datetime, urllib.parse
from comun import get_json, fuente_lago, cifra, escribir_lago, variacion_pct

PORTAL = "https://data.cityoforlando.net"
DATASET = "k6e8-nw6w"
UMBRAL = 5
DESDE = 2017
ANIOS_BARRIO = 5
TIPO_ES = {"Zoning": "Zonificación", "Lot": "Lote (maleza, basura)", "Housing": "Vivienda", "Ticket": "Multa", "Business Tax Receipt": "Licencia de negocio",
           "Sign": "Avisos", "Certificate of Use": "Certificado de uso", "Towing and Zoning Endpoints": "Grúas y zonificación",
           "Commercial": "Comercial", "Abatement": "Saneamiento ordenado", "Tree": "Árboles", "Pool": "Piscinas",
           "After Midnight Alcohol Sales": "Alcohol después de medianoche"}


def soql(**partes):
    partes.setdefault("limit", "50000")
    return f"{PORTAL}/resource/{DATASET}.json?" + "&".join(f"${k}={urllib.parse.quote(v, safe='')}" for k, v in partes.items())


def limpio(txt):
    return " ".join(str(txt or "").split())


hoy = datetime.date.today()
anios_fila = get_json(soql(select="case_open_year, count(*) as n", group="case_open_year", order="case_open_year"))
por_anio = {int(f["case_open_year"]): int(f["n"]) for f in anios_fila if f.get("case_open_year", "").strip().isdigit()}
completos = [a for a in sorted(por_anio) if DESDE <= a < hoy.year]
ultimo = completos[-1]
quejas_fila = get_json(soql(select="case_open_year, count(*) as n", where="src = 'Citizen'", group="case_open_year", order="case_open_year"))
quejas_anio = {int(f["case_open_year"]): int(f["n"]) for f in quejas_fila if f.get("case_open_year", "").strip().isdigit()}

desde_b = completos[-ANIOS_BARRIO]
filas = get_json(soql(select="nbrhd_descript, case_open_year, count(*) as n",
                      where=f"case_open_year >= '{desde_b}' AND case_open_year <= '{ultimo}'", group="nbrhd_descript, case_open_year"))
filas_q = get_json(soql(select="nbrhd_descript, count(*) as n", where=f"src = 'Citizen' AND case_open_year = '{ultimo}'", group="nbrhd_descript"))
tipos = get_json(soql(select="case_type, count(*) as n", where=f"case_open_year = '{ultimo}'", group="case_type", order="n DESC"))

capa = {limpio(r.get("neighborhoodname")).casefold() for r in get_json(f"{PORTAL}/resource/yskk-n7cw.json?$select=neighborhoodname&$limit=5000")}

series = {"casos_por_anio": {"unidad": "casos de código abiertos en el año", "fuente": "orlando_codigo",
                             "puntos": [[str(a), por_anio[a]] for a in completos]},
          # El origen del caso («src») casi no se registraba antes de 2020 (2 y 10 quejas en 2018 y 2019): esos años no
          # dicen que no hubo quejas, dicen que no se anotaba. Se publican los años en que al menos 5 % de los casos lo trae.
          "quejas_por_anio": {"unidad": "casos abiertos por queja ciudadana en el año", "fuente": "orlando_codigo",
                              "puntos": [[str(a), quejas_anio[a]] for a in completos if quejas_anio.get(a, 0) >= 0.05 * por_anio[a]]}}
suprimidos = sin_barrio = 0
coinciden = mostrados_ult = 0
for a in range(desde_b, ultimo + 1):
    conteo = {}
    for f in filas:
        if f.get("case_open_year") == str(a):
            b = limpio(f.get("nbrhd_descript"))
            conteo[b] = conteo.get(b, 0) + int(f["n"])
    mostrados = {b: n for b, n in conteo.items() if b and n >= UMBRAL}
    series[f"casos_barrio_{a}"] = {"unidad": f"casos de código abiertos en {a}", "fuente": "orlando_codigo",
                                   "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
    if a == ultimo:
        suprimidos = sum(1 for b, n in conteo.items() if b and n < UMBRAL)
        sin_barrio = conteo.get("", 0)
        mostrados_ult = len(mostrados)
        coinciden = sum(1 for b in mostrados if b.casefold() in capa)
q = {}
for f in filas_q:
    b = limpio(f.get("nbrhd_descript"))
    q[b] = q.get(b, 0) + int(f["n"])
series[f"quejas_barrio_{ultimo}"] = {"unidad": f"casos abiertos por queja ciudadana en {ultimo}", "fuente": "orlando_codigo",
                                     "puntos": sorted(([b, n] for b, n in q.items() if b and n >= UMBRAL), key=lambda p: -p[1])}
series[f"tipos_{ultimo}"] = {"unidad": f"casos de código en {ultimo}", "fuente": "orlando_codigo",
                             "puntos": [[TIPO_ES.get(limpio(t.get("case_type")), limpio(t.get("case_type")) or "Sin tipo"), int(t["n"])] for t in tipos]}

F = "orlando_codigo"
cifras = {
    "casos_ultimo_anio": cifra(por_anio[ultimo], "casos de código abiertos", str(ultimo), F),
    "variacion_ultimo_anio": cifra(variacion_pct(por_anio[ultimo], por_anio[completos[-2]]), "%", str(ultimo), F),
    "quejas_ultimo_anio": cifra(quejas_anio.get(ultimo, 0), "casos abiertos por queja ciudadana", str(ultimo), F),
    "casos_anio_en_curso": cifra(por_anio.get(hoy.year, 0), "casos abiertos en lo que va del año", hoy.isoformat(), F),
    "barrios_suprimidos_ultimo_anio": cifra(suprimidos, "barrios con menos casos que el umbral", str(ultimo), F),
    "casos_sin_barrio_ultimo_anio": cifra(sin_barrio, "casos sin barrio asignado", str(ultimo), F),
    "umbral_minimo_por_barrio": cifra(UMBRAL, "casos", str(ultimo), F),
    "coincidencia_nombres_con_capa_barrios": cifra(round(100 * coinciden / mostrados_ult, 1) if mostrados_ult else 0.0,
                                                   "% de los barrios mostrados", str(ultimo), F),
}
ruta = escribir_lago("codigo", [fuente_lago(F, f"{PORTAL}/resource/{DATASET}.json")], cifras, series)
print(f"Código {ultimo}: {por_anio[ultimo]} casos ({quejas_anio.get(ultimo, 0)} por queja); {mostrados_ult} barrios, {suprimidos} suprimidos, "
      f"{sin_barrio} sin barrio; coincidencia {cifras['coincidencia_nombres_con_capa_barrios']['valor']} % -> {ruta.name}")
