#!/usr/bin/env python3
"""Prueba que el verificador sepa fallar: «una verificación que nunca falla no está verificando».

Arma dos carpetas temporales. En la buena pone un lago correcto y espera código 0. En la mala rompe el lago a
propósito (cifra sin fuente, licencia pendiente, hora en 'probado', un correo y dos teléfonos) y espera código 1
con cada falla nombrada."""
import json, os, pathlib, subprocess, sys, tempfile, datetime

VERIFICAR = pathlib.Path(__file__).resolve().parent / "verificar.py"
CATALOGO = (pathlib.Path(__file__).resolve().parents[1] / "catalogo" / "fuentes_lago.json").read_text(encoding="utf-8")
HOY = datetime.date.today().isoformat()
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def correr(lago):
    with tempfile.TemporaryDirectory() as t:
        (pathlib.Path(t) / "lago" / "raw" / "prueba").mkdir(parents=True)
        (pathlib.Path(t) / "lago" / "raw" / "prueba" / "prueba.json").write_text(json.dumps(lago, ensure_ascii=False), encoding="utf-8")
        # el verificador lee del catálogo qué fuentes traen personas («solo agregados»)
        (pathlib.Path(t) / "catalogo").mkdir()
        (pathlib.Path(t) / "catalogo" / "fuentes_lago.json").write_text(CATALOGO, encoding="utf-8")
        r = subprocess.run([sys.executable, str(VERIFICAR), "--raiz", t], capture_output=True, text=True, encoding="utf-8", env=ENV)
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
sys.exit(0 if ok and codigo == 1 and c_ok == 0 and atrapo_censo and len(atrapadas) == len(esperadas) and cod_ok == 0 and atrapo
         and s_ok == 0 and atrapo_cat and atrapo_bar else 1)
