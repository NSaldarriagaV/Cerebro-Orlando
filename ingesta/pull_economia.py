#!/usr/bin/env python3
"""Ingesta · desempleo y empleo del área de Orlando, contra ciudades pares (F14, FRED).

Lee:     fredgraph.csv de FRED (sin llave), dos consultas:
         - tasa de desempleo (BLS, LAUS, sin ajuste estacional) de Orlando, Tampa, Miami, Jacksonville, Florida y EE. UU.;
         - empleo no agrícola total del área de Orlando (BLS, CES, ajustado por estacionalidad, en miles).
Escribe: lago/raw/economia/economia.json con la forma del contrato.

«Contra qué»: Orlando se compara con las otras tres áreas metropolitanas grandes de Florida y con el estado y el país,
en el mismo mes y con la misma medida (todas sin ajuste estacional). La licencia de cada serie se leyó en su ficha de FRED."""
from comun import fred, fuente_lago, cifra, escribir_lago, variacion_pct, mes

DESEMPLEO = {"ORLA712UR": "orlando", "TAMP312UR": "tampa", "MIAM112UR": "miami", "JACK212UR": "jacksonville",
             "FLURN": "florida", "UNRATENSA": "eeuu"}
METROS = ["orlando", "tampa", "miami", "jacksonville"]

url_d, d = fred(list(DESEMPLEO), desde="2000-01-01")
url_e, e = fred(["ORLA712NA"], desde="1990-01-01")
# v3: salario promedio por hora del sector privado (BLS, CES) y solicitudes de nuevos negocios (Census, BFS)
SALARIO = {"SMU12367400500000003": "orlando", "SMU12453000500000003": "tampa", "SMU12331000500000003": "miami",
           "SMU12272600500000003": "jacksonville"}
url_w, w = fred(list(SALARIO), desde="2011-01-01")
url_b, bfs = fred(["BABATOTALSAFL", "BABATOTALSAUS"], desde="2010-01-01")

series = {}
for sid, nombre in DESEMPLEO.items():
    series[f"desempleo_{nombre}"] = {"unidad": "% de la fuerza laboral", "fuente": "fred_laus",
                                     "puntos": [[mes(f), v] for f, v in d[sid]]}
empleo = [[mes(f), v] for f, v in e["ORLA712NA"]]
series["empleo_total"] = {"unidad": "miles de empleos (ajustado por estacionalidad)", "fuente": "fred_ces", "puntos": empleo}

for sid, n in SALARIO.items():
    series[f"salario_hora_{n}"] = {"unidad": "dólares por hora (promedio, sector privado)", "fuente": "fred_salarios",
                                   "puntos": [[mes(f), v] for f, v in w[sid]]}
series["solicitudes_negocio_florida"] = {"unidad": "solicitudes de nuevos negocios al mes (ajustado por estacionalidad)", "fuente": "fred_bfs",
                                         "puntos": [[mes(f), v] for f, v in bfs["BABATOTALSAFL"]]}
series["solicitudes_negocio_eeuu"] = {"unidad": "solicitudes de nuevos negocios al mes (ajustado por estacionalidad)", "fuente": "fred_bfs",
                                      "puntos": [[mes(f), v] for f, v in bfs["BABATOTALSAUS"]]}

# El último mes que tienen las cuatro áreas: así la comparación es del mismo mes
comunes = set.intersection(*({p[0] for p in series[f"desempleo_{m}"]["puntos"]} for m in METROS))
ultimo = max(comunes)
val = {m: dict(series[f"desempleo_{m}"]["puntos"])[ultimo] for m in METROS}
orden = sorted(METROS, key=lambda m: val[m])                     # puesto 1 = menor desempleo
hace_un_anio = f"{int(ultimo[:4]) - 1}{ultimo[4:]}"
orl = dict(series["desempleo_orlando"]["puntos"])
fl = dict(series["desempleo_florida"]["puntos"])

cifras = {
    "desempleo_ultimo_mes": cifra(orl[ultimo], "% de la fuerza laboral", ultimo, "fred_laus"),
    "desempleo_hace_un_anio": cifra(orl[hace_un_anio], "% de la fuerza laboral", hace_un_anio, "fred_laus"),
    "diferencia_con_florida": cifra(round(orl[ultimo] - fl[ultimo], 1), "puntos porcentuales", ultimo, "fred_laus"),
    "puesto_desempleo_entre_pares": cifra(orden.index("orlando") + 1, "puesto entre 4 áreas (1 = menor desempleo)", ultimo, "fred_laus"),
    "empleo_total_ultimo_mes": cifra(empleo[-1][1], "miles de empleos", empleo[-1][0], "fred_ces"),
    "variacion_empleo_12_meses": cifra(variacion_pct(empleo[-1][1], empleo[-13][1]), "%", empleo[-1][0], "fred_ces"),
}
ws_ = {n: dict(series[f"salario_hora_{n}"]["puntos"]) for n in SALARIO.values()}
ult_w = max(set.intersection(*(set(v) for v in ws_.values())))
sal = {n: ws_[n][ult_w] for n in ws_}
otros = [sal[n] for n in sal if n != "orlando"]
so = series["salario_hora_orlando"]["puntos"]
bf, bu = series["solicitudes_negocio_florida"]["puntos"], series["solicitudes_negocio_eeuu"]["puntos"]
doce = lambda pts: sum(v for _, v in pts[-12:])
cifras |= {
    "salario_hora_ultimo_mes": cifra(sal["orlando"], "dólares por hora", ult_w, "fred_salarios"),
    "variacion_salario_12_meses": cifra(variacion_pct(so[-1][1], so[-13][1]), "%", so[-1][0], "fred_salarios"),
    "puesto_salario_entre_pares": cifra(sorted(sal, key=lambda n: -sal[n]).index("orlando") + 1, "puesto entre 4 áreas (1 = mejor pagada)", ult_w, "fred_salarios"),
    "salario_frente_a_pares": cifra(variacion_pct(sal["orlando"], sum(otros) / len(otros)), "% frente al promedio de Tampa, Miami y Jacksonville", ult_w, "fred_salarios"),
    "solicitudes_negocio_florida_12_meses": cifra(round(doce(bf)), "solicitudes de nuevos negocios en Florida en 12 meses", bf[-1][0], "fred_bfs"),
    "variacion_solicitudes_negocio_florida": cifra(variacion_pct(doce(bf), sum(v for _, v in bf[-24:-12])), "% frente a los 12 meses anteriores", bf[-1][0], "fred_bfs"),
    "participacion_florida_en_negocios_eeuu": cifra(round(doce(bf) / doce(bu) * 100, 1), "% de las solicitudes de EE. UU. que son de Florida", bf[-1][0], "fred_bfs"),
}
ruta = escribir_lago("economia", [fuente_lago("fred_laus", url_d), fuente_lago("fred_ces", url_e), fuente_lago("fred_salarios", url_w),
                                  fuente_lago("fred_bfs", url_b)], cifras, series)
print(f"Desempleo {ultimo}: Orlando {orl[ultimo]} %, puesto {orden.index('orlando') + 1} de 4; empleo {empleo[-1][1]} mil -> {ruta.name}")
