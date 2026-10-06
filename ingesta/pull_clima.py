#!/usr/bin/env python3
"""Ingesta · el clima de Orlando hoy y en los próximos días: National Weather Service (F57).

Lee:     api.weather.gov (sin llave; pide un User-Agent con contacto: variable CONTACTO).
Escribe: lago/raw/clima/clima.json con la forma del contrato.

OJO: es tiempo real. Este archivo cambia en cada corrida, así que no entra en la prueba de
reproducibilidad (git diff siempre lo mostrará distinto). Eso es esperado, no un error.
Unidad: todo en °F (la observación llega en °C y se convierte aquí)."""
from comun import get_json, hoy, fuente_lago, cifra, escribir_lago

LAT, LON = 28.5383, -81.3792          # centro de Orlando
BASE = "https://api.weather.gov"

punto = get_json(f"{BASE}/points/{LAT},{LON}")["properties"]
assert punto.get("gridId") == "MLB", f"El punto cae en la oficina {punto.get('gridId')}, no en Melbourne (MLB)"
assert punto["relativeLocation"]["properties"]["state"] == "FL"

periodos = get_json(punto["forecast"])["properties"]["periods"]
alertas = get_json(f"{BASE}/alerts/active?point={LAT},{LON}")["features"]

# Observación más reciente: la primera estación cercana que traiga temperatura
temp_f, dia_obs = None, None
for est in get_json(punto["observationStations"])["features"][:5]:
    obs = get_json(est["id"] + "/observations/latest")["properties"]
    t = (obs.get("temperature") or {}).get("value")
    if t is not None:
        temp_f, dia_obs = round(t * 9 / 5 + 32, 1), obs["timestamp"][:10]   # °C -> °F
        break
if temp_f is None:
    raise SystemExit("Ninguna de las cinco estaciones cercanas entregó temperatura.")


def en_f(p):
    t = p["temperature"]
    return round(t * 9 / 5 + 32, 1) if p.get("temperatureUnit") == "C" else t


pronostico = [[p["startTime"][:16], en_f(p)] for p in periodos]
lluvia = [[p["startTime"][:16], p["probabilityOfPrecipitation"]["value"]] for p in periodos
          if (p.get("probabilityOfPrecipitation") or {}).get("value") is not None]

series = {"pronostico_temperatura": {"unidad": "°F", "fuente": "nws_api", "puntos": pronostico}}
if lluvia:
    series["pronostico_lluvia"] = {"unidad": "% de probabilidad", "fuente": "nws_api", "puntos": lluvia}
cifras = {"temperatura_actual": cifra(temp_f, "°F", dia_obs, "nws_api"),
          "alertas_activas": cifra(len(alertas), "alertas vigentes", hoy(), "nws_api")}

ruta = escribir_lago("clima", [fuente_lago("nws_api", f"{BASE}/points/{LAT},{LON}")], cifras, series)
print(f"Orlando: {temp_f} °F el {dia_obs}, {len(pronostico)} periodos de pronóstico, {len(alertas)} alertas -> {ruta.name}")
