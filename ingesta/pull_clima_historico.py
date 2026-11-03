#!/usr/bin/env python3
"""Ingesta · cómo está cambiando el clima de Orlando: temperatura media y lluvia de cada año desde 1953 (F58, NOAA NCEI).

Lee:     servicio de acceso a datos de NOAA NCEI (sin token), conjunto «Global Summary of the Year», estación
         USW00012815 = Orlando International Airport. Unidades estándar: °F y pulgadas.
Escribe: lago/raw/clima_historico/clima_historico.json con la forma del contrato.

Decisiones:
- Se usan los años con dato publicado por NOAA; un año sin TAVG (por meses faltantes) queda fuera, no se rellena.
- La comparación es entre dos periodos de 30 años (el primero y el último completos), no año contra año, porque un
  solo año caliente no dice nada del clima. Es una diferencia de promedios, no una tendencia ajustada."""
import datetime
from comun import get_json, fuente_lago, cifra, escribir_lago

ESTACION = "USW00012815"
hoy = datetime.date.today()
URL = ("https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-summary-of-the-year"
       f"&stations={ESTACION}&dataTypes=TAVG,PRCP&startDate=1940-01-01&endDate={hoy.year - 1}-12-31&format=json&units=standard")

filas = get_json(URL, timeout=120)
assert filas and all(f.get("STATION") == ESTACION for f in filas), "La respuesta no es de la estación esperada"
temp = [[f["DATE"], float(f["TAVG"])] for f in filas if f.get("TAVG", "").strip()]
lluvia = [[f["DATE"], float(f["PRCP"])] for f in filas if f.get("PRCP", "").strip()]
if len(temp) < 60:
    raise SystemExit(f"Solo {len(temp)} años con temperatura: no alcanza para dos periodos de 30 años.")

prim, ult = temp[:30], temp[-30:]
m1 = round(sum(v for _, v in prim) / 30, 2)
m2 = round(sum(v for _, v in ult) / 30, 2)
mas_caliente = max(temp, key=lambda p: p[1])
F = "noaa_gsoy"
cifras = {
    "temperatura_media_ultimo_anio": cifra(temp[-1][1], "°F (media del año)", temp[-1][0], F),
    "promedio_primeros_30": cifra(m1, f"°F (media {prim[0][0]}–{prim[-1][0]})", f"{prim[0][0]}-{prim[-1][0]}", F),
    "promedio_ultimos_30": cifra(m2, f"°F (media {ult[0][0]}–{ult[-1][0]})", f"{ult[0][0]}-{ult[-1][0]}", F),
    "diferencia_entre_periodos": cifra(round(m2 - m1, 2), "°F", f"{ult[0][0]}-{ult[-1][0]}", F),
    "anio_mas_caliente": cifra(int(mas_caliente[0]), f"año (media de {mas_caliente[1]} °F)", mas_caliente[0], F),
    "lluvia_ultimo_anio": cifra(lluvia[-1][1], "pulgadas en el año", lluvia[-1][0], F),
}
series = {"temperatura_anual": {"unidad": "°F (media del año)", "fuente": F, "puntos": temp},
          "lluvia_anual": {"unidad": "pulgadas en el año", "fuente": F, "puntos": lluvia}}
ruta = escribir_lago("clima_historico", [fuente_lago(F, URL)], cifras, series)
print(f"NOAA {ESTACION}: {len(temp)} años ({temp[0][0]}–{temp[-1][0]}); {m1} °F -> {m2} °F; más caliente {mas_caliente} -> {ruta.name}")
