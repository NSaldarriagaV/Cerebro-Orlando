#!/usr/bin/env python3
"""Utilidades compartidas por los scripts de ingesta. Solo biblioteca estándar de Python.

Variable de entorno opcional: CONTACTO (un correo del grupo). Algunas fuentes, como el servicio
del clima de EE. UU., piden que el cliente se identifique."""
import datetime, json, os, pathlib, sys, time, urllib.error, urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[1]
LAGO = RAIZ / "lago"
CATALOGO = RAIZ / "catalogo" / "fuentes_lago.json"
CONTACTO = os.environ.get("CONTACTO", "contacto-del-grupo@ejemplo.com")
UA = {"User-Agent": f"taller-sistemas-de-informacion/1.0 (curso universitario; {CONTACTO})"}


def abrir(url, timeout=60):
    """Abre una URL; si el servidor dice 429 o 5xx, espera y reintenta (hasta 3 veces)."""
    for intento in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and intento < 2:
                time.sleep(5 * (intento + 1))
                continue
            raise


def get_json(url, timeout=60):
    with abrir(url, timeout) as r:
        return json.load(r)


def get_texto(url, timeout=60):
    with abrir(url, timeout) as r:
        return r.read().decode("utf-8")


def hoy():
    """El día de la prueba: AAAA-MM-DD, nunca con hora."""
    return datetime.date.today().isoformat()


def variacion_pct(nuevo, viejo):
    return round((nuevo / viejo - 1) * 100, 1)


def ficha(id_fuente):
    """Lee la ficha de la fuente en catalogo/fuentes_lago.json (de ahí salen entidad y licencia)."""
    for f in json.loads(CATALOGO.read_text(encoding="utf-8")):
        if f["id"] == id_fuente:
            return f
    sys.exit(f"La fuente «{id_fuente}» no está en {CATALOGO}")


def fuente_lago(id_fuente, url):
    """Entrada de 'fuentes' del contrato. La licencia se copia de la ficha, no se escribe en el script."""
    f = ficha(id_fuente)
    if "por verificar" in f["licencia"].lower():
        print(f"AVISO {id_fuente}: licencia pendiente en el catálogo; verificar.py va a fallar hasta que se escriba.", file=sys.stderr)
    return {"id": id_fuente, "nombre": f["nombre"], "url": url, "estado": "vivo", "licencia": f["licencia"]}


def cifra(valor, unidad, vigencia, fuente):
    return {"valor": valor, "unidad": unidad, "vigencia": vigencia, "fuente": fuente}


def escribir_lago(tema, fuentes, cifras, series):
    """Escribe lago/<tema>.json con la forma del contrato."""
    LAGO.mkdir(exist_ok=True)
    lago = {"tema": tema, "probado": hoy(), "fuentes": fuentes, "cifras": cifras, "series": series}
    ruta = LAGO / f"{tema}.json"
    ruta.write_text(json.dumps(lago, ensure_ascii=False, indent=1), encoding="utf-8")
    return ruta
