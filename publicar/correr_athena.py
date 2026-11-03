#!/usr/bin/env python3
"""Crea en Amazon Athena las tablas de athena.sql sobre el lago en S3 y corre las consultas de ejemplo.

    python publicar/correr_athena.py --bucket cerebro-orlando-lago-eafit              # tablas + las 5 consultas
    python publicar/correr_athena.py --bucket cerebro-orlando-lago-eafit --solo-tablas

Va después de publicar/subir_s3.py (en AWS CloudShell no hace falta configurar llaves). Los resultados de Athena quedan
en s3://<bucket>/_athena/, que se borra solo a los 7 días (regla de ciclo de vida). Athena cobra por datos leídos:
las 5 consultas leen menos de 1 MB, o sea, nada."""
import argparse, re, sys, time, pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--bucket", required=True)
ap.add_argument("--region", default="us-east-1")
ap.add_argument("--perfil")
ap.add_argument("--solo-tablas", action="store_true")
args = ap.parse_args()
import boto3

ses = boto3.Session(profile_name=args.perfil, region_name=args.region) if args.perfil else boto3.Session(region_name=args.region)
athena, s3 = ses.client("athena"), ses.client("s3")
SALIDA = f"s3://{args.bucket}/_athena/"
s3.put_bucket_lifecycle_configuration(Bucket=args.bucket, LifecycleConfiguration={"Rules": [{
    "ID": "resultados-athena-7-dias", "Status": "Enabled", "Filter": {"Prefix": "_athena/"},
    "Expiration": {"Days": 7}, "NoncurrentVersionExpiration": {"NoncurrentDays": 1}}]})

texto = (RAIZ / "publicar" / "athena.sql").read_text(encoding="utf-8").replace("<BUCKET>", args.bucket)
sentencias = []   # (comentario que la precede, sql)
for trozo in texto.split(";"):
    lineas = trozo.strip().splitlines()
    coment = [l[2:].strip() for l in lineas if l.startswith("--")]
    sql = "\n".join(l for l in lineas if not l.startswith("--")).strip()
    if sql:
        sentencias.append((coment[-1] if coment else "", sql))


def correr(sql):
    q = athena.start_query_execution(QueryString=sql, ResultConfiguration={"OutputLocation": SALIDA})["QueryExecutionId"]
    while True:
        e = athena.get_query_execution(QueryExecutionId=q)["QueryExecution"]
        estado = e["Status"]["State"]
        if estado in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return q, estado, e["Status"].get("StateChangeReason", ""), e.get("Statistics", {}).get("DataScannedInBytes", 0)
        time.sleep(0.7)


fallas = hechas = 0
for coment, sql in sentencias:
    es_consulta = sql.upper().startswith("SELECT")
    if es_consulta and args.solo_tablas:
        continue
    q, estado, motivo, leidos = correr(sql)
    hechas += 1
    titulo = coment if es_consulta else re.sub(r"\s+", " ", sql)[:80]
    print(f"\n[{'ok' if estado == 'SUCCEEDED' else estado}] {titulo}" + (f"  ({leidos / 1e3:.0f} KB leídos)" if es_consulta else ""))
    if estado != "SUCCEEDED":
        fallas += 1
        print("   ", motivo)
        continue
    if es_consulta:
        filas = athena.get_query_results(QueryExecutionId=q, MaxResults=9)["ResultSet"]["Rows"]
        for f in filas:
            print("    " + " | ".join((c.get("VarCharValue") or "")[:60] for c in f["Data"]))
print(f"\n{hechas - fallas} de {hechas} sentencias bien; resultados en {SALIDA}")
sys.exit(1 if fallas else 0)
