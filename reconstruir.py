#!/usr/bin/env python3
"""Reconstruir el lago y comprobar que la ingesta es reproducible.

    python3 reconstruir.py                         pide todo a las fuentes (internet) y guarda una foto nueva con la fecha de hoy
    python3 reconstruir.py --desde-crudo 2026-11-02   rehace la zona curada de esa fecha SIN internet, solo con la zona cruda

En los dos casos corre la verificación al final y, si pasa, arma la zona de consumo (publicar/consumo.py). Con --desde-crudo, «git diff» sobre lago/ tiene que salir vacío: si cambia
algo, lo crudo no alcanza para explicar lo publicado (el linaje está roto). Funciona igual en Windows.
Orden: territorio va primero porque los demás reparten sus datos por barrio con esas capas."""
import argparse, os, pathlib, re, shutil, subprocess, sys

RAIZ = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--desde-crudo", metavar="AAAA-MM-DD", help="reconstruir esa fecha desde lago/crudo, sin internet")
args = ap.parse_args()

ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
scripts = sorted((RAIZ / "ingesta").glob("pull_*.py"), key=lambda s: (s.stem != "pull_territorio", s.name))
if args.desde_crudo:
    ENV.update(CEREBRO_DESDE_CRUDO=args.desde_crudo, CEREBRO_FECHA_PRUEBA=args.desde_crudo, CEREBRO_GUARDAR_CRUDO="0")
    habia = set()
    for f in (RAIZ / "lago" / "curado").glob(f"tema=*/fecha={args.desde_crudo}/*.json"):
        habia.add(f.parent.parent.name[len("tema="):])
        f.unlink()
    # Solo los temas que ya existían ese día: un tema nuevo (por ejemplo tráfico) no tiene respuestas crudas de fotos viejas
    escribe = lambda s: set(re.findall(r'escribir_lago\("(\w+)"', s.read_text(encoding="utf-8")))
    scripts = [s for s in scripts if escribe(s) & habia]
fallaron = []
for s in scripts:
    print(f"\n== {s.name}")
    if subprocess.run([sys.executable, str(s)], cwd=RAIZ, env=ENV).returncode != 0:
        fallaron.append(s.name)
print("\n== verificar.py")
verif = subprocess.run([sys.executable, str(RAIZ / "verificacion" / "verificar.py")], cwd=RAIZ, env=ENV).returncode
if verif == 0:
    print("\n== publicar/consumo.py (tablas para SQL e inventario del lago)")
    subprocess.run([sys.executable, str(RAIZ / "publicar" / "consumo.py")], cwd=RAIZ, env=ENV)
if shutil.which("git"):
    print("\n== git diff --stat -- lago")
    subprocess.run(["git", "diff", "--stat", "--", "lago"], cwd=RAIZ)
print("\nScripts que fallaron:", ", ".join(fallaron) or "ninguno", "| verificación:", "pasó" if verif == 0 else "FALLÓ (no se publica)")
sys.exit(1 if fallaron or verif else 0)
