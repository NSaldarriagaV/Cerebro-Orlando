#!/usr/bin/env python3
"""Monta en AWS la actualización semanal del lago: Lambda + Step Functions + EventBridge Scheduler + CloudFront.

    python3 aws/crear_infra.py --bucket cerebro-orlando-lago-eafit             # todo (AWS CloudShell, desde la raíz del repo)
    python3 aws/crear_infra.py --bucket cerebro-orlando-lago-eafit --solo-codigo   # tras un cambio en el código: actualiza la Lambda
    python3 aws/crear_infra.py --bucket cerebro-orlando-lago-eafit --correr        # además, lanza una ejecución ahora

Qué crea (todo con el prefijo «cerebro-orlando»; se puede correr varias veces: actualiza en vez de duplicar):
- Lambda «cerebro-orlando-actualizar» con aws/lambda_cerebro.py y el código del repositorio (sin lago/: lo baja del bucket).
- Máquina de Step Functions «cerebro-orlando-semanal» (aws/maquina.asl.json): trae cada tema en paralelo, verifica,
  publica solo si pasa y cuenta en Athena las cifras de la foto nueva.
- Programación de EventBridge Scheduler: todos los lunes a las 6:00 (hora de Bogotá).
- CloudFront delante del bucket (el bucket sigue privado: CloudFront entra con Origin Access Control y solo a las zonas
  del lago, nunca a _athena/ ni a _trabajo/). La página publicada lee de ahí la última foto.
- Tres roles de IAM con lo mínimo para cada pieza.
Costo: dentro de la capa gratuita para una ejecución por semana (Lambda, Step Functions, Scheduler, CloudFront)."""
import argparse, io, json, pathlib, time, zipfile
import boto3
from botocore.exceptions import ClientError

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--bucket", required=True)
ap.add_argument("--region", default="us-east-1")
ap.add_argument("--solo-codigo", action="store_true")
ap.add_argument("--correr", action="store_true")
ap.add_argument("--horario", default="cron(0 6 ? * MON *)")
a = ap.parse_args()
N = "cerebro-orlando"
ses = boto3.Session(region_name=a.region)
iam, lam, sfn, sch, cf, s3 = (ses.client(x) for x in ("iam", "lambda", "stepfunctions", "scheduler", "cloudfront", "s3"))
CUENTA = ses.client("sts").get_caller_identity()["Account"]
B_ARN = f"arn:aws:s3:::{a.bucket}"
F_NOMBRE, M_NOMBRE = f"{N}-actualizar", f"{N}-semanal"
F_ARN = f"arn:aws:lambda:{a.region}:{CUENTA}:function:{F_NOMBRE}"
M_ARN = f"arn:aws:states:{a.region}:{CUENTA}:stateMachine:{M_NOMBRE}"
ZONAS = ["crudo", "curado", "consumo", "catalogo", "territorio"]


def paquete():
    """ZIP de la Lambda: el manejador en la raíz y el código del repositorio en repo/ (sin el lago ni lo publicado)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(RAIZ / "aws" / "lambda_cerebro.py", "lambda_cerebro.py")
        for carpeta in ("ingesta", "verificacion", "publicar", "vista", "catalogo"):
            for p in sorted((RAIZ / carpeta).rglob("*")):
                if p.is_file() and "__pycache__" not in p.parts and p.name != "index.html" and not p.name.startswith("athena_"):
                    z.write(p, "repo/" + p.relative_to(RAIZ).as_posix())
        z.write(RAIZ / "reconstruir.py", "repo/reconstruir.py")
    return buf.getvalue()


def rol(nombre, servicio, politica, administradas=()):
    confianza = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": servicio}, "Action": "sts:AssumeRole"}]}
    try:
        arn = iam.get_role(RoleName=nombre)["Role"]["Arn"]
    except ClientError:
        arn = iam.create_role(RoleName=nombre, AssumeRolePolicyDocument=json.dumps(confianza), Tags=[{"Key": "proyecto", "Value": N}])["Role"]["Arn"]
        time.sleep(10)                                   # IAM tarda en propagar un rol nuevo
    iam.put_role_policy(RoleName=nombre, PolicyName=f"{nombre}-permisos", PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": politica}))
    for p in administradas:
        iam.attach_role_policy(RoleName=nombre, PolicyArn=p)
    return arn


def lambda_(rol_arn, distribucion):
    codigo, entorno = paquete(), {"Variables": {"BUCKET": a.bucket, "DISTRIBUCION": distribucion or ""}}
    try:
        lam.get_function(FunctionName=F_NOMBRE)
        lam.update_function_code(FunctionName=F_NOMBRE, ZipFile=codigo)
        lam.get_waiter("function_updated_v2").wait(FunctionName=F_NOMBRE)
        if not a.solo_codigo:
            lam.update_function_configuration(FunctionName=F_NOMBRE, Environment=entorno, Timeout=900, MemorySize=2048, EphemeralStorage={"Size": 1024})
            lam.get_waiter("function_updated_v2").wait(FunctionName=F_NOMBRE)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        for intento in range(6):                         # el rol recién creado a veces todavía no se puede asumir
            try:
                lam.create_function(FunctionName=F_NOMBRE, Runtime="python3.12", Role=rol_arn, Handler="lambda_cerebro.handler", Code={"ZipFile": codigo},
                                    Timeout=900, MemorySize=2048, EphemeralStorage={"Size": 1024}, Environment=entorno,
                                    Description="Cerebro Orlando: trae, verifica y publica una foto nueva del lago", Tags={"proyecto": N})
                break
            except ClientError as e2:
                if "cannot be assumed" not in str(e2) or intento == 5:
                    raise
                time.sleep(10)
        lam.get_waiter("function_active_v2").wait(FunctionName=F_NOMBRE)
    print(f"Lambda {F_NOMBRE}: {len(codigo) // 1024} KB de código")


def cloudfront():
    """Distribución con Origin Access Control: el bucket sigue privado y CloudFront solo puede leer las zonas del lago."""
    for d in cf.list_distributions().get("DistributionList", {}).get("Items", []):
        if d.get("Comment") == f"{N}-lago":
            return d["Id"], d["DomainName"]
    oac = next((o["Id"] for o in cf.list_origin_access_controls()["OriginAccessControlList"].get("Items", []) if o["Name"] == f"{N}-lago"), None)
    if not oac:
        oac = cf.create_origin_access_control(OriginAccessControlConfig={"Name": f"{N}-lago", "Description": "Solo lectura del lago para CloudFront",
                                              "SigningProtocol": "sigv4", "SigningBehavior": "always", "OriginAccessControlOriginType": "s3"})["OriginAccessControl"]["Id"]
    OPTIMIZADA, SIN_CACHE, CORS = "658327ea-f89d-4fab-a63d-7e88639e58f6", "4135ea2d-6df8-44a3-9df3-4b5a84be39ad", "60669652-455b-4ae9-85a4-c4c02393f86c"
    metodos = {"Quantity": 2, "Items": ["GET", "HEAD"], "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}}
    comp = lambda patron: {"PathPattern": patron, "TargetOriginId": "lago", "ViewerProtocolPolicy": "redirect-to-https", "CachePolicyId": SIN_CACHE,
                           "ResponseHeadersPolicyId": CORS, "Compress": True, "AllowedMethods": metodos}
    d = cf.create_distribution(DistributionConfig={
        "CallerReference": f"{N}-{int(time.time())}", "Comment": f"{N}-lago", "Enabled": True, "PriceClass": "PriceClass_100", "HttpVersion": "http2and3",
        "Origins": {"Quantity": 1, "Items": [{"Id": "lago", "DomainName": f"{a.bucket}.s3.{a.region}.amazonaws.com", "OriginPath": "",
                                              "S3OriginConfig": {"OriginAccessIdentity": ""}, "OriginAccessControlId": oac}]},
        "DefaultCacheBehavior": {"TargetOriginId": "lago", "ViewerProtocolPolicy": "redirect-to-https", "CachePolicyId": OPTIMIZADA,
                                 "ResponseHeadersPolicyId": CORS, "Compress": True, "AllowedMethods": metodos},
        "CacheBehaviors": {"Quantity": 2, "Items": [comp("consumo/tablero/*"), comp("catalogo/*")]}})["Distribution"]
    s3.put_bucket_policy(Bucket=a.bucket, Policy=json.dumps({"Version": "2012-10-17", "Statement": [{
        "Sid": "CloudFrontLeeSoloLasZonasDelLago", "Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"}, "Action": "s3:GetObject",
        "Resource": [f"{B_ARN}/{z}/*" for z in ZONAS],
        "Condition": {"StringEquals": {"AWS:SourceArn": f"arn:aws:cloudfront::{CUENTA}:distribution/{d['Id']}"}}}]}))
    return d["Id"], d["DomainName"]


def ciclo_de_vida():
    s3.put_bucket_lifecycle_configuration(Bucket=a.bucket, LifecycleConfiguration={"Rules": [
        {"ID": "resultados-athena-7-dias", "Status": "Enabled", "Filter": {"Prefix": "_athena/"}, "Expiration": {"Days": 7}, "NoncurrentVersionExpiration": {"NoncurrentDays": 1}},
        {"ID": "trabajo-step-functions-3-dias", "Status": "Enabled", "Filter": {"Prefix": "_trabajo/"}, "Expiration": {"Days": 3}, "NoncurrentVersionExpiration": {"NoncurrentDays": 1}}]})


if a.solo_codigo:
    lambda_(None, None)
else:
    dist_id, dominio = cloudfront()
    r_lambda = rol(f"{N}-lambda", "lambda.amazonaws.com", [
        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": f"{B_ARN}/*"},
        {"Effect": "Allow", "Action": "s3:ListBucket", "Resource": B_ARN},
        {"Effect": "Allow", "Action": "cloudfront:CreateInvalidation", "Resource": f"arn:aws:cloudfront::{CUENTA}:distribution/{dist_id}"}],
        ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"])
    lambda_(r_lambda, dist_id)
    r_sfn = rol(f"{N}-stepfunctions", "states.amazonaws.com", [
        {"Effect": "Allow", "Action": "lambda:InvokeFunction", "Resource": [F_ARN, F_ARN + ":*"]},
        {"Effect": "Allow", "Action": ["athena:StartQueryExecution", "athena:GetQueryExecution", "athena:GetQueryResults", "athena:StopQueryExecution", "athena:GetWorkGroup"], "Resource": "*"},
        {"Effect": "Allow", "Action": ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions"], "Resource": "*"},
        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:GetBucketLocation", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"],
         "Resource": [B_ARN, f"{B_ARN}/*"]}])
    definicion = (RAIZ / "aws" / "maquina.asl.json").read_text(encoding="utf-8").replace("__FUNCION__", F_ARN).replace("__BUCKET__", a.bucket)
    try:
        sfn.describe_state_machine(stateMachineArn=M_ARN)
        sfn.update_state_machine(stateMachineArn=M_ARN, definition=definicion, roleArn=r_sfn)
    except ClientError:
        for intento in range(6):
            try:
                sfn.create_state_machine(name=M_NOMBRE, definition=definicion, roleArn=r_sfn, type="STANDARD", tags=[{"key": "proyecto", "value": N}])
                break
            except ClientError as e:
                if "AccessDenied" not in str(e) and "not authorized" not in str(e) or intento == 5:
                    raise
                time.sleep(10)
    r_sch = rol(f"{N}-scheduler", "scheduler.amazonaws.com", [{"Effect": "Allow", "Action": "states:StartExecution", "Resource": M_ARN}])
    prog = {"Name": f"{N}-lunes", "ScheduleExpression": a.horario, "ScheduleExpressionTimezone": "America/Bogota", "FlexibleTimeWindow": {"Mode": "OFF"},
            "Description": "Foto nueva del lago cada semana", "Target": {"Arn": M_ARN, "RoleArn": r_sch, "Input": "{}"}, "State": "ENABLED"}
    for intento in range(6):
        try:
            try:
                sch.get_schedule(Name=prog["Name"])
                sch.update_schedule(**prog)
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    raise
                sch.create_schedule(**prog)
            break
        except ClientError as e:
            if "assume" not in str(e).lower() or intento == 5:
                raise
            time.sleep(10)
    ciclo_de_vida()
    (RAIZ / "publicar" / "nube.json").write_text(json.dumps({"bucket": a.bucket, "region": a.region, "cloudfront": f"https://{dominio}",
                                                             "maquina": M_ARN, "lambda": F_NOMBRE, "horario": f"{a.horario} America/Bogota"}, indent=1) + "\n")
    print(f"CloudFront {dist_id}: https://{dominio}\nStep Functions: {M_ARN}\nEventBridge Scheduler: {prog['Name']} ({a.horario}, America/Bogota)")
if a.correr:
    e = sfn.start_execution(stateMachineArn=M_ARN, name=f"manual-{time.strftime('%Y%m%d-%H%M%S')}")
    print("Ejecución:", e["executionArn"])
