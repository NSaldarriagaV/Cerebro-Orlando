"""Lambda de la actualización semanal del lago (la orquesta aws/maquina.asl.json en Step Functions).

Cuatro modos, uno por paso de la máquina:
  planear    la fecha de la foto nueva y la lista de scripts de ingesta (uno por tema)
  traer      corre UN script de ingesta contra las fuentes (con internet) y deja lo nuevo en s3://<bucket>/_trabajo/<ejecución>/
  verificar  junta lo que trajeron todos los scripts con el lago y corre verificacion/verificar.py; no toca el lago
  publicar   solo si la verificación pasó: arma la zona de consumo y el tablero, sube al lago lo nuevo o cambiado e
             invalida la copia de CloudFront del tablero
El código del repositorio viene en el paquete (carpeta repo/); el lago se baja del bucket a /tmp en cada paso."""
import concurrent.futures, datetime, hashlib, io, json, os, pathlib, shutil, subprocess, sys, tarfile, time
from zoneinfo import ZoneInfo
import boto3

BUCKET = os.environ["BUCKET"]
DISTRIBUCION = os.environ.get("DISTRIBUCION", "")
CODIGO = pathlib.Path(os.environ.get("LAMBDA_TASK_ROOT", ".")) / "repo"
REPO = pathlib.Path("/tmp/repo")
LAGO = REPO / "lago"
MANIF = "catalogo/manifiesto_crudo/manifiesto.jsonl"
s3 = boto3.client("s3")


def huella(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def huellas():
    return {p.relative_to(LAGO).as_posix(): huella(p) for p in LAGO.rglob("*") if p.is_file()}


def preparar(zonas):
    """Copia el código a /tmp (Lambda solo deja escribir ahí) y baja del bucket las zonas pedidas del lago."""
    if REPO.exists():
        shutil.rmtree(REPO)
    shutil.copytree(CODIGO, REPO)
    claves = [o["Key"] for z in zonas for pag in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=z + "/")
              for o in pag.get("Contents", []) if not o["Key"].endswith("/")]

    def bajar(k):
        destino = LAGO / k
        destino.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(BUCKET, k, str(destino))
    with concurrent.futures.ThreadPoolExecutor(16) as ex:
        list(ex.map(bajar, claves))
    return len(claves)


def correr(args, env=None):
    r = subprocess.run([sys.executable] + args, cwd=REPO, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {})), timeout=840)
    return r.returncode, (r.stdout + r.stderr).strip()


def manifiesto(ruta):
    if not ruta.exists():
        return {}
    filas = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {(f["fecha"], f["url"]): f for f in filas}


def empacar(rutas, extra=None):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for r in rutas:
            t.add(LAGO / r, arcname=r)
        for nombre, texto in (extra or {}).items():
            datos = texto.encode("utf-8")
            info = tarfile.TarInfo(nombre); info.size = len(datos)
            t.addfile(info, io.BytesIO(datos))
    return buf.getvalue()


def desempacar(cuerpo):
    """Pone los archivos del paquete en el lago y devuelve el delta de manifiesto que traía (o {})."""
    delta = {}
    with tarfile.open(fileobj=io.BytesIO(cuerpo), mode="r:gz") as t:
        for m in t.getmembers():
            if not m.isfile() or ".." in m.name or m.name.startswith("/"):
                continue
            datos = t.extractfile(m).read()
            if m.name == "manifiesto_delta.jsonl":
                for l in datos.decode("utf-8").splitlines():
                    if l.strip():
                        f = json.loads(l)
                        delta[(f["fecha"], f["url"])] = f
                continue
            destino = LAGO / m.name
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(datos)
    return delta


def escribir_manifiesto(m):
    """Mismo formato que ingesta/crudo.py: una fila por respuesta, ordenadas por fecha, sitio y URL."""
    filas = sorted(m.values(), key=lambda f: (f["fecha"], f["sitio"], f["url"]))
    (LAGO / MANIF).parent.mkdir(parents=True, exist_ok=True)
    (LAGO / MANIF).write_text("".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n" for f in filas), encoding="utf-8")


def juntar(ejecucion):
    """El lago más lo que trajo cada script de esta ejecución (los deltas de manifiesto se suman; una URL pedida por
    dos scripts queda con los dos temas, como en crudo.py)."""
    m = manifiesto(LAGO / MANIF)
    pag = s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=f"_trabajo/{ejecucion}/traido/")
    for k in sorted(o["Key"] for p in pag for o in p.get("Contents", [])):
        for clave, f in desempacar(s3.get_object(Bucket=BUCKET, Key=k)["Body"].read()).items():
            previa = m.get(clave)
            if previa and previa.get("fecha") == f["fecha"] and previa.get("tema") and previa["tema"] != f["tema"]:
                f["tema"] = ",".join(sorted(set(previa["tema"].split(",")) | set(f["tema"].split(","))))
            m[clave] = f
    escribir_manifiesto(m)


def handler(evento, contexto):
    modo, ejecucion = evento["modo"], evento.get("ejecucion", "manual")
    t0 = time.time()
    if modo == "planear":
        fecha = evento.get("fecha") or datetime.datetime.now(ZoneInfo("America/Bogota")).date().isoformat()
        scripts = sorted(p.name for p in (CODIGO / "ingesta").glob("pull_*.py"))
        return {"fecha": fecha, "scripts": scripts}

    if modo == "traer":
        preparar(["curado", "territorio", "catalogo"])
        antes, man_antes = huellas(), manifiesto(LAGO / MANIF)
        codigo, salida = correr([f"ingesta/{evento['script']}"], {"CEREBRO_FECHA_PRUEBA": evento["fecha"]})
        despues = huellas()
        nuevos = sorted(r for r, h in despues.items() if antes.get(r) != h and r != MANIF)
        delta = [f for k, f in manifiesto(LAGO / MANIF).items() if man_antes.get(k) != f]
        paquete = empacar(nuevos, {"manifiesto_delta.jsonl": "".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n" for f in delta)})
        s3.put_object(Bucket=BUCKET, Key=f"_trabajo/{ejecucion}/traido/{evento['script']}.tar.gz", Body=paquete)
        return {"script": evento["script"], "ok": codigo == 0, "archivos": len(nuevos), "respuestas": len(delta),
                "segundos": round(time.time() - t0), "salida": salida[-400:]}

    if modo == "verificar":
        preparar(["crudo", "curado", "territorio", "catalogo", "consumo"])
        antes = huellas()
        juntar(ejecucion)
        codigo, salida = correr(["verificacion/verificar.py"])
        lineas = salida.splitlines()
        cambiados = sorted(r for r, h in huellas().items() if antes.get(r) != h)
        s3.put_object(Bucket=BUCKET, Key=f"_trabajo/{ejecucion}/verificado.tar.gz", Body=empacar(cambiados))
        return {"fallos": sum(1 for l in lineas if l.startswith("FAIL ")), "pasan": sum(1 for l in lineas if l.startswith("PASS ")),
                "avisos": sum(1 for l in lineas if l.startswith("WARN ")), "primeros_fallos": [l[5:160] for l in lineas if l.startswith("FAIL ")][:5],
                "archivos_nuevos": len(cambiados), "segundos": round(time.time() - t0)}

    if modo == "publicar":
        preparar(["crudo", "curado", "territorio", "catalogo", "consumo"])
        antes = huellas()
        desempacar(s3.get_object(Bucket=BUCKET, Key=f"_trabajo/{ejecucion}/verificado.tar.gz")["Body"].read())
        for paso in (["publicar/consumo.py"], ["vista/construir_vista.py"]):
            codigo, salida = correr(paso)
            if codigo:
                raise RuntimeError(f"{paso[0]} falló: {salida[-600:]}")
        subir = sorted(r for r, h in huellas().items() if antes.get(r) != h)
        tipos = {".gz": "application/gzip", ".jsonl": "application/x-ndjson", ".geojson": "application/geo+json", ".json": "application/json"}

        def poner(r):
            p = LAGO / r
            s3.put_object(Bucket=BUCKET, Key=r, Body=p.read_bytes(), Metadata={"sha256": huella(p)},
                          ContentType=tipos.get(p.suffix, "application/octet-stream"))
        with concurrent.futures.ThreadPoolExecutor(16) as ex:
            list(ex.map(poner, subir))
        if DISTRIBUCION:
            boto3.client("cloudfront").create_invalidation(DistributionId=DISTRIBUCION, InvalidationBatch={
                "Paths": {"Quantity": 2, "Items": ["/consumo/*", "/catalogo/*"]}, "CallerReference": f"{ejecucion}-{int(t0)}"})
        return {"subidos": len(subir), "ultima_linea": salida.splitlines()[-1][:200] if salida else "", "segundos": round(time.time() - t0)}

    raise ValueError(f"modo desconocido: {modo}")
