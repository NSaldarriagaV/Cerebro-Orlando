#!/usr/bin/env python3
"""Prueba que el verificador sepa fallar: «una verificación que nunca falla no está verificando».

Arma dos carpetas temporales. En la buena pone un lago correcto y espera código 0. En la mala rompe el lago a
propósito (cifra sin fuente, licencia pendiente, hora en 'probado', un correo y dos teléfonos) y espera código 1
con cada falla nombrada."""
import json, pathlib, subprocess, sys, tempfile, datetime

VERIFICAR = pathlib.Path(__file__).resolve().parent / "verificar.py"
HOY = datetime.date.today().isoformat()


def correr(lago):
    with tempfile.TemporaryDirectory() as t:
        (pathlib.Path(t) / "lago").mkdir()
        (pathlib.Path(t) / "lago" / "prueba.json").write_text(json.dumps(lago, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(VERIFICAR), "--raiz", t], capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout


fuente = {"id": "f", "nombre": "f", "url": "https://ejemplo.org", "estado": "vivo", "licencia": "CC0"}
bueno = {"tema": "prueba", "probado": HOY, "fuentes": [fuente],
         "cifras": {"x": {"valor": 1, "unidad": "u", "vigencia": "2026-09", "fuente": "f"}}, "series": {}}
malo = {"tema": "prueba", "probado": HOY + "T10:00:00", "fuentes": [dict(fuente, licencia="por verificar: leer")],
        "cifras": {"sin_fuente": {"valor": 12, "unidad": "personas", "vigencia": "2026"}},
        "series": {}, "nota": "escribir a nombre@ejemplo.com, al 3000000000 o al 407-555-0123"}

codigo, _ = correr(bueno)
print("lago correcto ->", "PASA (código 0)" if codigo == 0 else f"FALLA, código {codigo}: el verificador es demasiado estricto")
ok = codigo == 0
codigo, salida = correr(malo)
esperadas = ["probado es un día", "ninguna licencia pendiente", "sin_fuente con valor", "ningún texto con correo o teléfono"]
atrapadas = [e for e in esperadas if any(l.startswith("FAIL") and e in l for l in salida.splitlines())]
print(f"lago roto -> código {codigo}; atrapó {len(atrapadas)} de {len(esperadas)} fallos esperados")
for e in esperadas:
    print("   ", "OK " if e in atrapadas else "NO ", e)
sys.exit(0 if ok and codigo == 1 and len(atrapadas) == len(esperadas) else 1)
