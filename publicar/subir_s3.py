#!/usr/bin/env python3
"""Sube el lago a un bucket de Amazon S3 con la misma estructura de carpetas (crudo/, curado/, territorio/, consumo/, catalogo/).

    pip install boto3
    aws configure                                    # una vez: llaves de una cuenta de AWS (o AWS Academy) con permiso sobre el bucket
    python publicar/subir_s3.py --bucket cerebro-orlando-lago-eafit --crear   # la primera vez: crea el bucket privado
    python publicar/subir_s3.py --bucket cerebro-orlando-lago-eafit           # después de cada actualización
    python publicar/subir_s3.py --bucket ... --prueba                        # solo muestra qué subiría

Qué hace:
- Con --crear, crea el bucket bloqueando todo acceso público, con cifrado por defecto (SSE-S3) y con versionado: si un
  archivo cambiara, S3 guarda la versión anterior (el lago no pierde historia).
- Sube solo lo nuevo: compara la huella sha256 de cada archivo con la que quedó en los metadatos del objeto.
- Nunca pisa lo que ya está en el bucket: desde que existe la actualización semanal (aws/), el lago maestro es el de S3 y
  la Lambda le agrega una foto cada lunes. Lo crudo y lo curado de cada fecha no cambian nunca; el manifiesto se une
  (filas de los dos lados); lo derivado (consumo/ e inventario) que difiera se deja y lo rehace la próxima ejecución en
  AWS. Con --reemplazar sí pisa (por ejemplo, para corregir una foto a propósito).
- Nunca borra nada del bucket.
- Sube publicar/explorador.html a catalogo/explorador.html: la página que muestra el lago (zonas, fotos y cada archivo)
  a través de CloudFront, leyendo el inventario catalogo/catalogo_lago.json.
- Escribe publicar/athena_<bucket>.sql con las tablas de athena.sql apuntando a este bucket.
El bucket es privado: la web lee la última foto a través de CloudFront (solo las zonas del lago) y, si no responde, su
copia en Vercel. Costo: el lago pesa decenas de MB (crece con cada foto semanal); S3 cobra centavos al año."""
import argparse, hashlib, json, mimetypes, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
LAGO = RAIZ / "lago"
TIPOS = {".gz": "application/gzip", ".jsonl": "application/x-ndjson", ".geojson": "application/geo+json", ".json": "application/json"}

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--bucket", required=True)
ap.add_argument("--region", default="us-east-1")
ap.add_argument("--perfil", help="perfil de ~/.aws/credentials (opcional)")
ap.add_argument("--crear", action="store_true", help="crear el bucket privado, cifrado y con versionado")
ap.add_argument("--prueba", action="store_true", help="no sube nada: solo lista lo que subiría")
ap.add_argument("--reemplazar", action="store_true", help="pisar en el bucket los archivos que difieran (por defecto no se pisan)")
args = ap.parse_args()

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    sys.exit("Falta boto3: pip install boto3")

sesion = boto3.Session(profile_name=args.perfil, region_name=args.region) if args.perfil else boto3.Session(region_name=args.region)
s3 = sesion.client("s3")

if args.crear and not args.prueba:
    try:
        if args.region == "us-east-1":
            s3.create_bucket(Bucket=args.bucket)
        else:
            s3.create_bucket(Bucket=args.bucket, CreateBucketConfiguration={"LocationConstraint": args.region})
        print(f"bucket {args.bucket} creado en {args.region}")
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou",):
            raise
        print(f"el bucket {args.bucket} ya existía (es de esta cuenta)")
    s3.put_public_access_block(Bucket=args.bucket, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
    s3.put_bucket_encryption(Bucket=args.bucket, ServerSideEncryptionConfiguration={
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]})
    s3.put_bucket_versioning(Bucket=args.bucket, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_tagging(Bucket=args.bucket, Tagging={"TagSet": [{"Key": "proyecto", "Value": "cerebro-orlando"}, {"Key": "curso", "Value": "eafit-topicos-si"}]})
    print("acceso público bloqueado, cifrado SSE-S3 y versionado activos")

MANIF = "catalogo/manifiesto_crudo/manifiesto.jsonl"


def unir_manifiesto(local, remoto):
    """Une los dos manifiestos (una fila por fecha y URL); gana la fila del bucket si las dos tienen la misma."""
    filas = {}
    for texto in (local, remoto):
        for l in texto.decode("utf-8").splitlines():
            if l.strip():
                f = json.loads(l)
                filas[(f["fecha"], f["url"])] = f
    orden = sorted(filas.values(), key=lambda f: (f["fecha"], f["sitio"], f["url"]))
    return "".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n" for f in orden).encode("utf-8")


subidos = iguales = bytes_subidos = 0
sin_pisar = []
for p in sorted(LAGO.rglob("*")):
    if not p.is_file():
        continue
    clave = p.relative_to(LAGO).as_posix()
    cuerpo = p.read_bytes()
    huella = hashlib.sha256(cuerpo).hexdigest()
    if not args.prueba:
        try:
            meta = s3.head_object(Bucket=args.bucket, Key=clave).get("Metadata", {})
            if meta.get("sha256") == huella:
                iguales += 1
                continue
            if clave == MANIF and not args.reemplazar:
                cuerpo = unir_manifiesto(cuerpo, s3.get_object(Bucket=args.bucket, Key=clave)["Body"].read())
                huella = hashlib.sha256(cuerpo).hexdigest()
                if meta.get("sha256") == huella:
                    iguales += 1
                    continue
            elif not args.reemplazar:
                sin_pisar.append(clave)
                continue
        except ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchKey", "NotFound"):
                raise
        tipo = TIPOS.get(p.suffix) or mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        s3.put_object(Bucket=args.bucket, Key=clave, Body=cuerpo, ContentType=tipo, Metadata={"sha256": huella})
    subidos += 1
    bytes_subidos += len(cuerpo)
    if args.prueba and subidos <= 10:
        print("subiría", clave)
print(f"{'subiría' if args.prueba else 'subidos'}: {subidos} archivos ({bytes_subidos / 1e6:.1f} MB); sin cambios: {iguales}")
if sin_pisar:
    print(f"no se pisaron {len(sin_pisar)} archivos que en el bucket son distintos (p. ej. {', '.join(sin_pisar[:3])}).")
    print("  Lo derivado lo rehace la próxima ejecución en AWS; para pisarlos a propósito: --reemplazar")

# La página que muestra el lago por CloudFront (no es un dato del lago: se pone al día siempre que cambie)
EXPLORADOR, CLAVE_EXP = RAIZ / "publicar" / "explorador.html", "catalogo/explorador.html"
if EXPLORADOR.exists() and not args.prueba:
    cuerpo = EXPLORADOR.read_bytes()
    huella = hashlib.sha256(cuerpo).hexdigest()
    try:
        actual = s3.head_object(Bucket=args.bucket, Key=CLAVE_EXP).get("Metadata", {}).get("sha256")
    except ClientError:
        actual = None
    if actual != huella:
        s3.put_object(Bucket=args.bucket, Key=CLAVE_EXP, Body=cuerpo, ContentType="text/html; charset=utf-8",
                      CacheControl="max-age=300", Metadata={"sha256": huella})
        print("explorador del lago al día:", CLAVE_EXP)

sql = (RAIZ / "publicar" / "athena.sql").read_text(encoding="utf-8").replace("<BUCKET>", args.bucket)
destino = RAIZ / "publicar" / f"athena_{args.bucket}.sql"
destino.write_text(sql, encoding="utf-8")
print(f"tablas para Athena listas en {destino.relative_to(RAIZ)} (pegarlas en el editor de consultas de Athena)")
