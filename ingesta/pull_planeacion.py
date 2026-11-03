#!/usr/bin/env python3
"""Ingesta · hacia dónde va la ciudad: proyecciones a 2045, zonas con incentivos y solicitudes de planeación
(F107, SIG de la Ciudad de Orlando; F86, Planning Applications; F96, anexiones).

Lee:     - Proyecciones de población y empleo 2017 → 2045 por zona de análisis de tránsito (TAZ) que publica la ciudad.
         - Zonas de Oportunidad federales, áreas de Main Street y Áreas de Redesarrollo Comunitario (CRA): dónde hay
           incentivos para invertir o abrir negocio.
         - Solicitudes de planeación (rezonificaciones, planes maestros, subdivisiones, reuniones previas…) agrupadas por
           barrio, tipo y año en el servidor; el nombre del solicitante nunca se pide.
         - Anexiones de la ciudad por año (cuánto ha crecido el territorio).
Escribe: lago/raw/planeacion/planeacion.json con la forma del contrato.

Cómo se lleva a barrios (derivado): rejilla de puntos cada 40 m (ver comun.reparto y pull_censo.py). La población y el empleo de cada
zona se reparten según la parte de la zona que cae en cada barrio; las zonas con incentivo se miden como «qué parte
del barrio está adentro». Las solicitudes ya traen el barrio. Barrio-año con menos de 5 solicitudes no se publica."""
import datetime, urllib.parse
from comun import (get_json, fuente_lago, cifra, escribir_lago, Capa, reparto, cobertura_zona, leer_territorio, desde_esri, fecha_prueba,
                   arcgis, suprimir)

SIG = "https://gis.orlando.gov/server/rest/services"
TAZ = f"{SIG}/Socrata_OpenData/OrlandoLandUsePlanning/MapServer/11"
ZONAS = {"zona_oportunidad": (f"{SIG}/Socrata_OpenData/OrlandoIncentivePrograms/MapServer/4", "NAME"),
         "main_street": (f"{SIG}/Socrata_OpenData/OrlandoIncentivePrograms/MapServer/2", "BUISNESSNE"),
         "cra": (f"{SIG}/Socrata_OpenData/OrlandoLandUsePlanning/MapServer/8", "CRAName")}
PORTAL = "https://data.cityoforlando.net"
SOLICITUDES, ANEXIONES = "bhxy-4rji", "jg52-dz4p"
UMBRAL = 5
TIPO_ES = {"HPB": "Patrimonio histórico", "MTG": "Reunión previa (proyecto en preparación)", "DET": "Determinación de uso",
           "ARB": "Revisión de apariencia", "VAR": "Variación de norma", "SUB": "Subdivisión o reloteo", "MPL": "Plan maestro",
           "MOD": "Modificación de aprobación", "GMP": "Cambio al plan de crecimiento", "ZON": "Rezonificación",
           "CUP": "Uso condicional", "ANX": "Anexión", "ABN": "Cesión de vía", "LDC": "Cambio al código", "DRI": "Desarrollo de impacto regional",
           "SNC": "Cambio de nombre de calle"}
GRANDES = ["MPL", "SUB", "ZON", "GMP", "ANX", "DRI"]                 # señales de proyectos de escala


def soql(ds, **partes):
    partes.setdefault("limit", "50000")
    return f"{PORTAL}/resource/{ds}.json?" + "&".join(f"${k}={urllib.parse.quote(v, safe='')}" for k, v in partes.items())


hoy = fecha_prueba()
nombres = [f["properties"]["nombre"] for f in leer_territorio("barrios")]
FS, FP, FA = "orlando_sig", "orlando_planeacion", "orlando_anexiones"
series, cifras = {}, {}

# ---------- 1. proyecciones 2017 -> 2045 ----------
url_taz = arcgis(TAZ, outFields="TrafficZoneNumber,ResPop2017,ResPop2045,EmpPop2017,EmpPop2045", returnGeometry="true",
                 maxAllowableOffset="0.0003", geometryPrecision="5")
zonas = get_json(url_taz, timeout=120)["features"]
capa = Capa([(i, desde_esri(z["geometry"])) for i, z in enumerate(zonas)])
pesos, _ = reparto(capa, paso_m=40)
acum = {}
for i, bs in pesos.items():
    a = zonas[i]["attributes"]
    for b, w in bs.items():
        s = acum.setdefault(b, [0.0, 0.0, 0.0, 0.0])
        for j, campo in enumerate(("ResPop2017", "ResPop2045", "EmpPop2017", "EmpPop2045")):
            s[j] += w * (a.get(campo) or 0)
for k, (j0, j1, u) in {"poblacion": (0, 1, "residentes"), "empleo": (2, 3, "empleos")}.items():
    series[f"{k}_2017_barrio"] = {"unidad": f"{u} en 2017 (base de la proyección de la ciudad) · por barrio", "fuente": FS,
                                  "puntos": sorted(([b, round(acum[b][j0])] for b in nombres if b in acum and acum[b][j0] >= 1), key=lambda p: -p[1])}
    series[f"{k}_2045_barrio"] = {"unidad": f"{u} proyectados a 2045 · por barrio", "fuente": FS,
                                  "puntos": sorted(([b, round(acum[b][j1])] for b in nombres if b in acum and acum[b][j1] >= 1), key=lambda p: -p[1])}
    # crecimiento solo donde la base es significativa (100 o más), para no publicar «+900 %» sobre 5 personas
    series[f"crecimiento_{k}_2045_barrio"] = {"unidad": f"% de cambio de {u} 2017 → 2045 (proyección) · por barrio", "fuente": FS,
                                              "puntos": sorted(([b, round((acum[b][j1] / acum[b][j0] - 1) * 100, 1)] for b in nombres
                                                                if b in acum and acum[b][j0] >= 100), key=lambda p: -p[1])}
    t0, t1 = sum(v[j0] for v in acum.values()), sum(v[j1] for v in acum.values())
    cifras[f"{k}_2017_ciudad"] = cifra(round(t0), f"{u} en 2017 (suma de barrios)", "2017", FS)
    cifras[f"{k}_2045_ciudad"] = cifra(round(t1), f"{u} proyectados a 2045 (suma de barrios)", "2045", FS)
    cifras[f"crecimiento_{k}_2045_ciudad"] = cifra(round((t1 / t0 - 1) * 100, 1), "% de cambio 2017 → 2045 (proyección de la ciudad)", "2045", FS)

# ---------- 2. zonas con incentivos ----------
urls_z = {}
for k, (capa_url, campo) in ZONAS.items():
    urls_z[k] = arcgis(capa_url, outFields=campo, returnGeometry="true", maxAllowableOffset="0.0002", geometryPrecision="5")
    feats = get_json(urls_z[k], timeout=120)["features"]
    frac, cuales = cobertura_zona(Capa([(f["attributes"].get(campo) or "sin nombre", desde_esri(f["geometry"])) for f in feats]), paso_m=40)
    series[f"{k}_barrio"] = {"unidad": "% de la tierra del barrio dentro de la zona", "fuente": FS,
                             "puntos": sorted(([b, round(frac[b] * 100)] for b in nombres if frac.get(b, 0) >= .05), key=lambda p: -p[1])}
    cifras[f"barrios_en_{k}"] = cifra(len(series[f"{k}_barrio"]["puntos"]), "barrios con al menos 5 % de su tierra en la zona", hoy.isoformat(), FS)

# ---------- 3. solicitudes de planeación por barrio, tipo y año ----------
url_s = soql(SOLICITUDES, select="neighborhood, substring(application_number,1,3) as tipo, date_extract_y(application_date) as anio, count(*) as n",
             group="neighborhood, tipo, anio")
filas = get_json(url_s, timeout=120)
ult = hoy.year - 1
anios = list(range(ult - 4, ult + 1))
por_ba, por_tipo, grandes = {}, {}, {}
for f in filas:
    if not f.get("anio"):
        continue
    a, b, t, n = int(float(f["anio"])), " ".join((f.get("neighborhood") or "").split()), f.get("tipo") or "", int(f["n"])
    por_ba.setdefault(a, {})[b] = por_ba.setdefault(a, {}).get(b, 0) + n
    por_tipo.setdefault(a, {})[t] = por_tipo.setdefault(a, {}).get(t, 0) + n
    if t in GRANDES and a >= ult - 1:
        grandes[b] = grandes.get(b, 0) + n
supr = 0
for a in anios:
    mostrados, s = suprimir(por_ba.get(a, {}), UMBRAL)
    supr = s if a == ult else supr
    series[f"solicitudes_barrio_{a}"] = {"unidad": f"solicitudes de planeación presentadas en {a}", "fuente": FP,
                                         "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
mostrados, _ = suprimir(grandes, UMBRAL)
series["proyectos_grandes_barrio"] = {"unidad": f"solicitudes de plan maestro, subdivisión, rezonificación, cambio de plan, anexión o DRI en {ult - 1}–{ult}",
                                      "fuente": FP, "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
series["solicitudes_por_anio"] = {"unidad": "solicitudes de planeación presentadas en el año (toda la ciudad)", "fuente": FP,
                                  "puntos": [[str(a), sum(por_ba.get(a, {}).values())] for a in anios]}
series[f"tipos_{ult}"] = {"unidad": f"solicitudes de planeación por tipo en {ult}", "fuente": FP,
                          "puntos": sorted(([TIPO_ES.get(t, t), n] for t, n in por_tipo.get(ult, {}).items() if n >= UMBRAL), key=lambda p: -p[1])}
url_ab = soql(SOLICITUDES, select="neighborhood, count(*) as n", where="application_status in('Open','Hold','Hardhold')", group="neighborhood")
abiertas = {" ".join((f.get("neighborhood") or "").split()): int(f["n"]) for f in get_json(url_ab, timeout=120)}
mostrados, _ = suprimir(abiertas, UMBRAL)
series["solicitudes_abiertas_barrio"] = {"unidad": "solicitudes de planeación abiertas o en espera hoy", "fuente": FP,
                                         "puntos": sorted(([b, n] for b, n in mostrados.items()), key=lambda p: -p[1])}
cifras |= {
    "solicitudes_ultimo_anio": cifra(sum(por_ba.get(ult, {}).values()), "solicitudes de planeación presentadas", str(ult), FP),
    "solicitudes_abiertas": cifra(sum(abiertas.values()), "solicitudes abiertas o en espera", hoy.isoformat(), FP),
    "barrios_suprimidos_solicitudes": cifra(supr, "barrios con menos solicitudes que el umbral en el último año", str(ult), FP),
    "umbral_minimo_por_barrio": cifra(UMBRAL, "solicitudes", str(ult), FP),
}

# ---------- 4. anexiones: cuánto ha crecido el territorio ----------
url_a = soql(ANEXIONES, select="year, count(*) as n, sum(legaldescriptionacres) as acres", group="year", order="year")
anex = [(int(float(f["year"])), int(f["n"]), float(f.get("acres") or 0)) for f in get_json(url_a, timeout=120) if f.get("year")]
decadas = {}
for y, n, ac in anex:
    d = y // 10 * 10
    decadas[d] = decadas.get(d, 0) + ac
series["anexiones_por_decada"] = {"unidad": "acres anexados a la ciudad en la década (según la descripción legal)", "fuente": FA,
                                  "puntos": [[f"{d}s", round(ac)] for d, ac in sorted(decadas.items())]}
diez = sum(ac for y, n, ac in anex if y > hoy.year - 11)
cifras["acres_anexados_10_anios"] = cifra(round(diez), "acres anexados en los últimos 10 años", f"{hoy.year - 10}-{hoy.year}", FA)
cifras["anexiones_10_anios"] = cifra(sum(n for y, n, ac in anex if y > hoy.year - 11), "anexiones en los últimos 10 años", f"{hoy.year - 10}-{hoy.year}", FA)

fuentes = [fuente_lago(FS, url_taz), fuente_lago(FP, url_s), fuente_lago(FA, url_a)]
ruta = escribir_lago("planeacion", fuentes, cifras, series)
print(f"Planeación: {cifras['poblacion_2017_ciudad']['valor']} → {cifras['poblacion_2045_ciudad']['valor']} residentes proyectados; "
      f"{cifras['solicitudes_ultimo_anio']['valor']} solicitudes en {ult}; {cifras['barrios_en_zona_oportunidad']['valor']} barrios en zona de oportunidad -> {ruta.name}")
