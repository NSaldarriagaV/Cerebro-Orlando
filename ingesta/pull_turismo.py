#!/usr/bin/env python3
"""Ingesta · cuánto pesa el turismo: empleo en ocio y hotelería (F14, FRED) y alquileres de corto plazo con licencia (F85).

Lee:     - fredgraph.csv de FRED (sin llave): empleo en ocio y hotelería y empleo no agrícola total del área de Orlando
           (BLS, CES, ajustados por estacionalidad, en miles);
         - portal de datos abiertos de Orlando, «Short Term Rental Licenses» (ssrj-rbua), API SODA sin llave.
Escribe: lago/raw/turismo/turismo.json con la forma del contrato.

PRIVACIDAD: el dataset de alquileres trae nombre, teléfono, correo y dirección de titulares y propietarios. Aquí nunca se
descargan: la consulta agrupa en el servidor por estado de la licencia y por año de emisión, para toda la ciudad.
Los hospedajes por barrio salen de los negocios con licencia (F81) y están en el tema «negocios»."""
import datetime, urllib.parse
from comun import fred, get_json, fuente_lago, cifra, escribir_lago, variacion_pct, mes

PORTAL = "https://data.cityoforlando.net"
STR = "ssrj-rbua"


def soql(dataset, **partes):
    return f"{PORTAL}/resource/{dataset}.json?" + "&".join(f"${k}={urllib.parse.quote(v, safe='')}" for k, v in partes.items())


url_f, f = fred(["ORLA712LEIH", "ORLA712NA"], desde="1990-01-01")
# v3: el mismo cálculo para Tampa, Miami y Jacksonville, para saber si Orlando depende más del turismo que sus pares
PARES = {"tampa": ("TAMP312LEIH", "TAMP312NA"), "miami": ("MIAM112LEIH", "MIAM112NA"), "jacksonville": ("JACK212LEIH", "JACK212NA")}
url_fp, fp = fred([i for par in PARES.values() for i in par], desde="1990-01-01")
ocio = [[mes(d), round(v, 1)] for d, v in f["ORLA712LEIH"]]
total = dict((mes(d), v) for d, v in f["ORLA712NA"])
participacion = [[mes(d), round(v / total[mes(d)] * 100, 1)] for d, v in f["ORLA712LEIH"] if mes(d) in total]

estados = get_json(soql(STR, select="license_status, count(*) as n", group="license_status"))
por_estado = {(e.get("license_status") or "sin estado").strip(): int(e["n"]) for e in estados}
anios = get_json(soql(STR, select="date_extract_y(issued_date) as anio, count(*) as n", where="issued_date IS NOT NULL",
                      group="anio", order="anio"))
hoy = datetime.date.today()
emitidas = [[str(int(float(a["anio"]))), int(a["n"])] for a in anios if int(float(a["anio"])) < hoy.year]
ficha = get_json(f"{PORTAL}/api/views/{STR}.json")
actualizado = datetime.datetime.fromtimestamp(ficha["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()

series = {"empleo_ocio_hoteleria": {"unidad": "miles de empleos (ajustado por estacionalidad)", "fuente": "fred_ces", "puntos": ocio},
          "participacion_ocio_en_empleo": {"unidad": "% del empleo no agrícola", "fuente": "fred_ces", "puntos": participacion},
          "alquiler_corto_emitidas_por_anio": {"unidad": "licencias emitidas en el año", "fuente": "orlando_alquiler_corto", "puntos": emitidas}}
for c, (ocio_id, total_id) in PARES.items():
    tot_c = dict((mes(d), v) for d, v in fp[total_id])
    series[f"participacion_ocio_{c}"] = {"unidad": "% del empleo no agrícola", "fuente": "fred_ces",
                                         "puntos": [[mes(d), round(v / tot_c[mes(d)] * 100, 1)] for d, v in fp[ocio_id] if mes(d) in tot_c]}
ult_par = {c: series[f"participacion_ocio_{c}"]["puntos"][-1][1] for c in PARES} | {"orlando": participacion[-1][1]}
cifras = {"puesto_ocio_entre_pares": cifra(sorted(ult_par, key=lambda c: -ult_par[c]).index("orlando") + 1,
                                           "puesto entre 4 áreas por peso del ocio en el empleo (1 = el que más depende)", participacion[-1][0], "fred_ces"),
          "empleo_ocio_ultimo_mes": cifra(ocio[-1][1], "miles de empleos", ocio[-1][0], "fred_ces"),
          "variacion_empleo_ocio_12_meses": cifra(variacion_pct(ocio[-1][1], ocio[-13][1]), "%", ocio[-1][0], "fred_ces"),
          "participacion_ocio_ultimo_mes": cifra(participacion[-1][1], "% del empleo no agrícola", participacion[-1][0], "fred_ces"),
          "alquiler_corto_activas": cifra(por_estado.get("Active", 0), "licencias activas", actualizado, "orlando_alquiler_corto"),
          "alquiler_corto_total_historico": cifra(sum(por_estado.values()), "licencias registradas (todas)", actualizado, "orlando_alquiler_corto")}
url_str = f"{PORTAL}/resource/{STR}.json"
ruta = escribir_lago("turismo", [fuente_lago("fred_ces", url_f), fuente_lago("orlando_alquiler_corto", url_str)], cifras, series)
print(f"Ocio y hotelería {ocio[-1][0]}: {ocio[-1][1]} mil ({participacion[-1][1]} %); alquileres activos {por_estado.get('Active', 0)} -> {ruta.name}")
