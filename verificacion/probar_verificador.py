#!/usr/bin/env python3
"""Prueba que el verificador sepa fallar: «una verificación que nunca falla no está verificando».

Arma carpetas temporales. En la buena pone un lago correcto (zona cruda con su manifiesto y zona curada con su linaje) y
espera código 0. En las malas rompe el lago a propósito (cifra sin fuente, licencia pendiente, hora en 'probado', un correo
y dos teléfonos; una respuesta cruda con un correo, una que cambió después de guardarse y una fuente sin respuestas
crudas) y espera código 1 con cada falla nombrada. Al final hace lo mismo con la consistencia entre pestañas
(consistencia.py) sobre una copia del lago real."""
import gzip, hashlib, json, os, pathlib, subprocess, sys, tempfile, datetime

VERIFICAR = pathlib.Path(__file__).resolve().parent / "verificar.py"
CATALOGO = (pathlib.Path(__file__).resolve().parents[1] / "catalogo" / "fuentes_lago.json").read_text(encoding="utf-8")
HOY = datetime.date.today().isoformat()
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


CRUDO_BUENO = json.dumps({"datos": [{"barrio": "Barrio A", "n": 40}]}).encode()


def correr(lago, cuerpo=CRUDO_BUENO, alterar=False, sin_linaje=False):
    """Escribe el lago de prueba en una carpeta temporal y corre el verificador sobre ella."""
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        rel = f"crudo/sitio=ejemplo.org/fecha={HOY}/datos-0000000000.json.gz"
        (t / "lago" / rel).parent.mkdir(parents=True)
        (t / "lago" / rel).write_bytes(gzip.compress(cuerpo + (b" " if alterar else b""), mtime=0))
        fila = {"fecha": HOY, "sitio": "ejemplo.org", "url": "https://ejemplo.org/datos", "tema": "prueba", "como": "script directo",
                "formato": "json", "estado": "guardado", "archivo": rel, "retirado": {}, "bytes_original": len(cuerpo),
                "sha256_original": hashlib.sha256(cuerpo).hexdigest(), "sha256_guardado": hashlib.sha256(cuerpo).hexdigest()}
        (t / "lago" / "catalogo" / "manifiesto_crudo").mkdir(parents=True)
        (t / "lago" / "catalogo" / "manifiesto_crudo" / "manifiesto.jsonl").write_text(json.dumps(fila) + "\n", encoding="utf-8")
        lago = json.loads(json.dumps(lago))
        for f in lago["fuentes"]:
            f["crudo"] = [] if sin_linaje else [rel]
        tema = lago["tema"]
        carpeta = t / "lago" / "curado" / f"tema={tema}" / f"fecha={str(lago['probado'])[:10]}"
        carpeta.mkdir(parents=True)
        (carpeta / f"{tema}.json").write_text(json.dumps(lago, ensure_ascii=False), encoding="utf-8")
        # el verificador lee del catálogo qué fuentes traen personas («solo agregados»)
        (t / "catalogo").mkdir()
        (t / "catalogo" / "fuentes_lago.json").write_text(CATALOGO, encoding="utf-8")
        r = subprocess.run([sys.executable, str(VERIFICAR), "--raiz", str(t)], capture_output=True, text=True, encoding="utf-8", env=ENV)
        return r.returncode, r.stdout


fuente = {"id": "f", "nombre": "f", "url": "https://ejemplo.org", "estado": "vivo", "licencia": "CC0"}
bueno = {"tema": "prueba", "probado": HOY, "fuentes": [fuente],
         "cifras": {"x": {"valor": 1, "unidad": "u", "vigencia": "2026-09", "fuente": "f"}}, "series": {}}
malo = {"tema": "prueba", "probado": HOY + "T10:00:00", "fuentes": [dict(fuente, licencia="por verificar: leer")],
        "cifras": {"sin_fuente": {"valor": 12, "unidad": "personas", "vigencia": "2026"}},
        "series": {}, "nota": "escribir a nombre@ejemplo.com, al 3000000000 o al 407-555-0123"}

F = "orlando_permisos"
def lago_permisos(puntos_barrio):
    c = lambda v, u="permisos": {"valor": v, "unidad": u, "vigencia": "2025", "fuente": F}
    return {"tema": "permisos", "probado": HOY, "fuentes": [dict(fuente, id=F)],
            "cifras": {"permisos_emitidos_ultimo_anio_completo": c(1000), "umbral_minimo_por_barrio": c(5)},
            "series": {"permisos_por_barrio_ultimo_anio": {"unidad": "permisos", "fuente": F, "puntos": puntos_barrio},
                       "permisos_por_anio": {"unidad": "permisos", "fuente": F, "puntos": [["2024", 900], ["2025", 1000]]}}}

codigo, _ = correr(bueno)
print("lago correcto ->", "PASA (código 0)" if codigo == 0 else f"FALLA, código {codigo}: el verificador es demasiado estricto")
ok = codigo == 0
codigo, salida = correr(malo)
esperadas = ["probado es un día", "ninguna licencia pendiente", "sin_fuente con valor", "ningún texto con correo o teléfono"]
atrapadas = [e for e in esperadas if any(l.startswith("FAIL") and e in l for l in salida.splitlines())]
print(f"lago roto -> código {codigo}; atrapó {len(atrapadas)} de {len(esperadas)} fallos esperados")
for e in esperadas:
    print("   ", "OK " if e in atrapadas else "NO ", e)
# Caso de privacidad: un barrio con 2 permisos (por debajo del umbral de 5) no se puede publicar
cod_ok, _ = correr(lago_permisos([["Barrio A", 40], ["Barrio B", 12]]))
cod_mal, salida_mal = correr(lago_permisos([["Barrio A", 40], ["Barrio B", 2]]))
atrapo = cod_mal == 1 and any(l.startswith("FAIL") and "ningún barrio por debajo del umbral" in l for l in salida_mal.splitlines())
print("permisos con todos los barrios sobre el umbral ->", "PASA" if cod_ok == 0 else f"FALLA (código {cod_ok})")
print("permisos con un barrio de 2 permisos ->", "ATRAPADO" if atrapo else "NO LO ATRAPÓ")
# Caso de seguridad: una categoría que decidimos no publicar (Baker Act) y una celda barrio-año de 3 casos
S = "opd_casos"
def lago_seguridad(tipos, barrio):
    c = lambda v: {"valor": v, "unidad": "casos", "vigencia": "2025", "fuente": S}
    return {"tema": "seguridad", "probado": HOY, "fuentes": [dict(fuente, id=S)],
            "cifras": {"delitos_ultimo_anio": c(1000), "umbral_minimo_por_barrio": c(5)},
            "series": {"tipos_2025": {"unidad": "casos", "fuente": S, "puntos": tipos},
                       "delitos_barrio_2025": {"unidad": "casos", "fuente": S, "puntos": barrio}}}
s_ok, _ = correr(lago_seguridad([["Hurto menor", 500]], [["Barrio A", 40]]))
s_cat, sal_cat = correr(lago_seguridad([["Hurto menor", 500], ["Baker Act", 30]], [["Barrio A", 40]]))
s_bar, sal_bar = correr(lago_seguridad([["Hurto menor", 500]], [["Barrio A", 40], ["Barrio B", 3]]))
atrapo_cat = s_cat == 1 and any(l.startswith("FAIL") and "ninguna categoría excluida" in l for l in sal_cat.splitlines())
atrapo_bar = s_bar == 1 and any(l.startswith("FAIL") and "ninguna celda por barrio bajo el umbral" in l for l in sal_bar.splitlines())
print("seguridad correcta ->", "PASA" if s_ok == 0 else f"FALLA (código {s_ok})")
print("seguridad con «Baker Act» ->", "ATRAPADO" if atrapo_cat else "NO LO ATRAPÓ")
print("seguridad con un barrio de 3 casos ->", "ATRAPADO" if atrapo_bar else "NO LO ATRAPÓ")
# Caso del censo: un barrio con 80 habitantes estimados no puede publicar porcentajes (la estimación no dice nada)
CE = "censo_acs"
def lago_censo(pct):
    c = lambda v, u="personas": {"valor": v, "unidad": u, "vigencia": "2020-2024", "fuente": CE}
    s = lambda pts, u="%": {"unidad": u, "fuente": CE, "puntos": pts}
    return {"tema": "censo", "probado": HOY, "fuentes": [dict(fuente, id=CE)],
            "cifras": {"poblacion_ciudad": c(300000), "diferencia_con_cifra_oficial": c(-2, "%"), "minimo_habitantes_por_barrio": c(200)},
            "series": {"poblacion_barrio": s([["Barrio A", 5000], ["Barrio B", 80]], "personas"), "pct_sin_carro_barrio": s(pct),
                       "ingreso_mediano_barrio": s([["Barrio A", 60000]], "dólares"), "ingreso_mediano_ciudades": s([["orlando", 70000]], "dólares"),
                       "arriendo_mediano_barrio": s([["Barrio A", 1500]], "dólares"), "arriendo_mediano_ciudades": s([["orlando", 1700]], "dólares")}}
c_ok, _ = correr(lago_censo([["Barrio A", 7.5]]))
c_mal, sal_c = correr(lago_censo([["Barrio A", 7.5], ["Barrio B", 30.0]]))
atrapo_censo = c_mal == 1 and any(l.startswith("FAIL") and "mínimo de habitantes" in l for l in sal_c.splitlines())
print("censo correcto ->", "PASA" if c_ok == 0 else f"FALLA (código {c_ok})")
print("censo con porcentaje de un barrio de 80 habitantes ->", "ATRAPADO" if atrapo_censo else "NO LO ATRAPÓ")
# La zona cruda: un correo que se coló, un archivo que cambió después de guardarse y una fuente sin respuestas crudas
def atrapa(salida, codigo, texto):
    return codigo == 1 and any(l.startswith("FAIL") and texto in l for l in salida.splitlines())
k1, s1 = correr(bueno, cuerpo=json.dumps({"contacto": "Escribir a alguien", "nota": "vecino@correo.com"}).encode())
k2, s2 = correr(bueno, alterar=True)
k3, s3 = correr(bueno, sin_linaje=True)
crudos = [("respuesta cruda con un correo", atrapa(s1, k1, "sin datos de personas")),
          ("respuesta cruda que cambió después de guardarse", atrapa(s2, k2, "huella")),
          ("fuente curada sin respuestas crudas (linaje roto)", atrapa(s3, k3, "linaje"))]
for nombre, ok_c in crudos:
    print(nombre, "->", "ATRAPADO" if ok_c else "NO LO ATRAPÓ")
# Un lago vacío (por ejemplo, rutas mal después de reorganizar carpetas) tiene que fallar, no pasar sin revisar nada
with tempfile.TemporaryDirectory() as t:
    (pathlib.Path(t) / "lago" / "curado").mkdir(parents=True)
    (pathlib.Path(t) / "catalogo").mkdir()
    (pathlib.Path(t) / "catalogo" / "fuentes_lago.json").write_text(CATALOGO, encoding="utf-8")
    vacio = subprocess.run([sys.executable, str(VERIFICAR), "--raiz", t], capture_output=True, text=True, encoding="utf-8", env=ENV).returncode
print("lago vacío ->", "ATRAPADO" if vacio == 1 else "NO LO ATRAPÓ: pasa sin revisar nada")
# Consistencia entre pestañas: la copia real del lago pasa; con la tarjeta y el gráfico en desacuerdo, tiene que fallar
CONSISTENCIA = pathlib.Path(__file__).resolve().parent / "consistencia.py"
RAIZ_REAL = pathlib.Path(__file__).resolve().parents[1]
cons = []
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    import shutil
    for parte in ("lago/curado", "lago/consumo"):
        if (RAIZ_REAL / parte).exists():
            shutil.copytree(RAIZ_REAL / parte, t / parte)
    (t / "vista").mkdir()
    for f in ("plantilla.html", "app.js"):
        shutil.copy(RAIZ_REAL / "vista" / f, t / "vista" / f)
    correr_c = lambda: subprocess.run([sys.executable, str(CONSISTENCIA), "--raiz", str(t)], capture_output=True, text=True, encoding="utf-8", env=ENV)
    r0 = correr_c()
    cons.append(("lago real, todo consistente", r0.returncode == 0))
    ruta = sorted((t / "lago" / "curado").glob("tema=permisos/fecha=*/permisos.json"))[-1]
    d = json.loads(ruta.read_text(encoding="utf-8"))
    d["cifras"]["permisos_emitidos_ultimo_anio_completo"]["valor"] += 50
    ruta.write_text(json.dumps(d), encoding="utf-8")
    r1 = correr_c()
    cons.append(("tarjeta de permisos distinta del gráfico", atrapa(r1.stdout, r1.returncode, "punto 2025 de la serie permisos_por_anio")))
    cons.append(("total de la ciudad que no cuadra con la suma por barrio", atrapa(r1.stdout, r1.returncode, "cuadra con la suma por barrio")))
for nombre, ok_c in cons:
    print("consistencia:", nombre, "->", ("PASA" if ok_c else "FALLA") if nombre.startswith("lago real") else ("ATRAPADO" if ok_c else "NO LO ATRAPÓ"))
sys.exit(0 if all(c for _, c in crudos) and all(c for _, c in cons) and vacio == 1 and ok and codigo == 1 and c_ok == 0 and atrapo_censo and len(atrapadas) == len(esperadas) and cod_ok == 0 and atrapo
         and s_ok == 0 and atrapo_cat and atrapo_bar else 1)
