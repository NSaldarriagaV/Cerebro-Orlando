#!/usr/bin/env python3
"""La puerta de salida del tramo: borrar el lago y reconstruirlo desde los scripts.

Equivale a: rm -rf lago/raw; for s in ingesta/pull_*.py; do python3 $s; done; python3 verificacion/verificar.py; git diff --stat
Funciona igual en Windows. Si después git muestra cambios que nadie esperaba, la ingesta no es reproducible.
(clima.json cambia siempre: es tiempo real y es esperado.)"""
import os, pathlib, shutil, subprocess, sys

RAIZ = pathlib.Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

for carpeta, patron in (("lago/raw", "*/*.json"), ("lago/territorio", "*.geojson")):
    for f in (RAIZ / carpeta).glob(patron):
        f.unlink()
fallaron = []
for s in sorted((RAIZ / "ingesta").glob("pull_*.py")):
    print(f"\n== {s.name}")
    if subprocess.run([sys.executable, str(s)], cwd=RAIZ, env=ENV).returncode != 0:
        fallaron.append(s.name)
print("\n== verificar.py")
verif = subprocess.run([sys.executable, str(RAIZ / "verificacion" / "verificar.py")], cwd=RAIZ, env=ENV).returncode
if shutil.which("git"):
    print("\n== git diff --stat")
    subprocess.run(["git", "diff", "--stat", "--", "lago"], cwd=RAIZ)
print("\nScripts que fallaron:", ", ".join(fallaron) or "ninguno", "| verificación:", "pasó" if verif == 0 else "FALLÓ (no se publica)")
sys.exit(1 if fallaron or verif else 0)
