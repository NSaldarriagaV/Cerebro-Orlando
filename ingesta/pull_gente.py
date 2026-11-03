#!/usr/bin/env python3
"""Ingesta · cuánta gente vive en Orlando y cómo le va: población, ingreso y pobreza (F14, FRED).

Lee:     fredgraph.csv de FRED (sin llave):
         - población residente del condado de Orange (1970 en adelante) y del área metropolitana (2000 en adelante), en miles
           (U.S. Census Bureau, estimaciones de población);
         - ingreso mediano de los hogares y porcentaje de personas en pobreza (U.S. Census Bureau, SAIPE) del condado de
           Orange y de sus pares: Hillsborough (Tampa), Duval (Jacksonville), Miami-Dade, y Florida.
Escribe: lago/raw/gente/gente.json con la forma del contrato.

Escala: la ciudad de Orlando no tiene series de población por año en FRED; el condado de Orange (que la contiene) sí.
Se dice así en cada cifra. La población por barrio exige la API del Census con llave: queda como hueco declarado."""
from comun import fred, fuente_lago, cifra, escribir_lago, variacion_pct, anio

CONDADOS = {"12095": "orange", "12057": "hillsborough", "12031": "duval", "12086": "miami_dade", "12000": "florida"}

url_p, p = fred(["FLORAN0POP", "ORLPOP"])
# v3: los condados pares también, para comparar el crecimiento (mismos ids de la Oficina del Censo en FRED)
POB_PARES = {"FLHILL7POP": "hillsborough", "FLDUVA0POP": "duval", "FLMIAM6POP": "miami_dade", "FLPOP": "florida"}
url_pp, pp = fred(list(POB_PARES), desde="1970-01-01")
# Ingreso personal por habitante (BEA): todo el ingreso del condado dividido por su gente (no solo el de los hogares)
PCPI = {"PCPI12095": "orange", "PCPI12057": "hillsborough", "PCPI12031": "duval", "PCPI12086": "miami_dade", "FLPCPI": "florida"}
url_pc, pcpi = fred(list(PCPI), desde="2000-01-01")
# Inflación: IPC de la región Sur (BLS). Orlando no tiene IPC propio; el Sur es la región que lo contiene
url_ipc, ipc = fred(["CUUR0300SA0"], desde="2000-01-01")
ids_s = [f"MHIFL{c}A052NCEN" for c in CONDADOS] + [f"PPAAFL{c}A156NCEN" for c in CONDADOS]
url_s, s = fred(ids_s)

series = {
    "poblacion_condado": {"unidad": "miles de personas", "fuente": "fred_poblacion", "puntos": [[anio(f), v] for f, v in p["FLORAN0POP"]]},
    "poblacion_area_metro": {"unidad": "miles de personas", "fuente": "fred_poblacion", "puntos": [[anio(f), v] for f, v in p["ORLPOP"]]},
}
for c, nombre in CONDADOS.items():
    series[f"ingreso_mediano_{nombre}"] = {"unidad": "dólares corrientes por hogar al año", "fuente": "fred_saipe",
                                           "puntos": [[anio(f), v] for f, v in s[f"MHIFL{c}A052NCEN"]]}
    series[f"pobreza_{nombre}"] = {"unidad": "% de las personas", "fuente": "fred_saipe",
                                   "puntos": [[anio(f), v] for f, v in s[f"PPAAFL{c}A156NCEN"]]}

for sid, n in POB_PARES.items():
    series[f"poblacion_{n}"] = {"unidad": "miles de personas", "fuente": "fred_poblacion", "puntos": [[anio(f), v] for f, v in pp[sid]]}
series["poblacion_orange"] = {"unidad": "miles de personas", "fuente": "fred_poblacion", "puntos": [[anio(f), v] for f, v in p["FLORAN0POP"]]}
for sid, n in PCPI.items():
    series[f"ingreso_por_persona_{n}"] = {"unidad": "dólares corrientes por persona al año", "fuente": "fred_bea", "puntos": [[anio(f), v] for f, v in pcpi[sid]]}
ipc_anual = {}
for f, v in ipc["CUUR0300SA0"]:
    ipc_anual.setdefault(anio(f), []).append(v)
ipc_anual = {a: sum(v) / len(v) for a, v in ipc_anual.items() if len(v) == 12}
series["ipc_sur_anual"] = {"unidad": "índice (1982-84 = 100), promedio del año", "fuente": "fred_ipc", "puntos": [[a, round(v, 2)] for a, v in sorted(ipc_anual.items())]}

pc, pm = series["poblacion_condado"]["puntos"], series["poblacion_area_metro"]["puntos"]
ing = {n: series[f"ingreso_mediano_{n}"]["puntos"][-1] for n in CONDADOS.values()}
pob = {n: series[f"pobreza_{n}"]["puntos"][-1] for n in CONDADOS.values()}
ult_s = ing["orange"][0]
assert all(v[0] == ult_s for v in list(ing.values()) + list(pob.values())), "Los condados no tienen el mismo último año"
pares = ["orange", "hillsborough", "duval", "miami_dade"]
diez = dict(pc).get(str(int(pc[-1][0]) - 10))
crec = {}
for n in ["orange", "hillsborough", "duval", "miami_dade", "florida"]:
    s_ = series[f"poblacion_{n}"]["puntos"]
    crec[n] = variacion_pct(s_[-1][1], dict(s_)[str(int(s_[-1][0]) - 10)])
series["crecimiento_10_anios_condados"] = {"unidad": "% de cambio de la población en 10 años", "fuente": "fred_poblacion",
                                           "puntos": [[n, v] for n, v in crec.items()]}
ppp = {n: series[f"ingreso_por_persona_{n}"]["puntos"][-1] for n in PCPI.values()}
# Ingreso real: cuánto creció el ingreso mediano de los hogares de Orange en 10 años, descontada la inflación del Sur
ing_o = dict(series["ingreso_mediano_orange"]["puntos"])
a1 = series["ingreso_mediano_orange"]["puntos"][-1][0]
a0 = str(int(a1) - 10)
real_10 = round(((ing_o[a1] / ing_o[a0]) / (ipc_anual[a1] / ipc_anual[a0]) - 1) * 100, 1) if a0 in ing_o and a0 in ipc_anual and a1 in ipc_anual else None

cifras = {
    "poblacion_condado_ultimo_anio": cifra(pc[-1][1], "miles de personas (condado de Orange)", pc[-1][0], "fred_poblacion"),
    "crecimiento_condado_10_anios": cifra(variacion_pct(pc[-1][1], diez), "%", pc[-1][0], "fred_poblacion"),
    "poblacion_area_metro_ultimo_anio": cifra(pm[-1][1], "miles de personas (área metropolitana)", pm[-1][0], "fred_poblacion"),
    "ingreso_mediano_condado": cifra(ing["orange"][1], "dólares por hogar al año", ult_s, "fred_saipe"),
    "ingreso_frente_a_florida": cifra(variacion_pct(ing["orange"][1], ing["florida"][1]), "% frente al de Florida", ult_s, "fred_saipe"),
    "pobreza_condado": cifra(pob["orange"][1], "% de las personas", ult_s, "fred_saipe"),
    "puesto_ingreso_entre_pares": cifra(sorted(pares, key=lambda n: -ing[n][1]).index("orange") + 1,
                                        "puesto entre 4 condados (1 = mayor ingreso)", ult_s, "fred_saipe"),
    "ingreso_por_persona_condado": cifra(ppp["orange"][1], "dólares por persona al año", ppp["orange"][0], "fred_bea"),
    "puesto_ingreso_por_persona": cifra(sorted(pares, key=lambda n: -ppp[n][1]).index("orange") + 1,
                                        "puesto entre 4 condados (1 = mayor ingreso por persona)", ppp["orange"][0], "fred_bea"),
    "puesto_crecimiento_entre_pares": cifra(sorted(pares, key=lambda n: -crec[n]).index("orange") + 1,
                                            "puesto entre 4 condados por crecimiento de la población en 10 años (1 = el que más creció)", pc[-1][0], "fred_poblacion"),
}
if real_10 is not None:
    cifras["ingreso_real_10_anios"] = cifra(real_10, f"% de cambio del ingreso mediano de los hogares {a0}–{a1}, descontada la inflación del Sur", f"{a0}-{a1}", "fred_ipc")
ruta = escribir_lago("gente", [fuente_lago("fred_poblacion", url_p), fuente_lago("fred_saipe", url_s), fuente_lago("fred_bea", url_pc),
                              fuente_lago("fred_ipc", url_ipc)], cifras, series)
print(f"Condado de Orange {pc[-1][0]}: {pc[-1][1]} mil personas; ingreso mediano {ult_s}: {ing['orange'][1]} -> {ruta.name}")
