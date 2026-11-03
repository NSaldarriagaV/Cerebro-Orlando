#!/usr/bin/env python3
"""Zona de consumo y catálogo del lago: lo que leen el tablero, SQL (Athena o DuckDB) y cualquiera que quiera los datos.

Lee:     lago/curado/tema=*/fecha=*/*.json, lago/catalogo/manifiesto_crudo/manifiesto.jsonl, catalogo/fuentes_lago.json
Escribe: lago/consumo/cifras/fecha=<día>/cifras.jsonl.gz   una fila por cifra   (fecha, tema, clave, valor, unidad, vigencia, fuente)
         lago/consumo/series/fecha=<día>/series.jsonl.gz   una fila por punto   (fecha, tema, serie, etiqueta, valor, unidad, fuente)
         lago/catalogo/fuentes/fuentes.jsonl                las fuentes en uso, con licencia y protección
         lago/catalogo/catalogo_lago.json                   inventario: cada archivo del lago con su zona, fecha, tamaño y huella

Las carpetas «clave=valor» son particiones al estilo Hive: Athena y DuckDB las leen como columnas sin configuración extra.
Todo sale ordenado y comprimido sin hora: correr dos veces sobre el mismo lago da los mismos bytes."""
import gzip, hashlib, json, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
LAGO = RAIZ / "lago"


def jsonl_gz(ruta, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = "".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n" for f in filas)
    ruta.write_bytes(gzip.compress(texto.encode("utf-8"), compresslevel=9, mtime=0))
    return len(filas)


def tablas():
    """Aplana cada foto curada en dos tablas (cifras y series)."""
    fechas = sorted({p.parent.name.split("=", 1)[1] for p in LAGO.glob("curado/tema=*/fecha=*/*.json")})
    for fecha in fechas:
        cifras, series = [], []
        for p in sorted(LAGO.glob(f"curado/tema=*/fecha={fecha}/*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            for k, c in sorted(d["cifras"].items()):
                cifras.append({"tema": d["tema"], "clave": k, "valor": c["valor"], "unidad": c["unidad"], "vigencia": str(c["vigencia"]), "fuente": c["fuente"]})
            for k, s in sorted(d["series"].items()):
                for et, v in s["puntos"]:
                    series.append({"tema": d["tema"], "serie": k, "etiqueta": et, "valor": v, "unidad": s["unidad"], "fuente": s["fuente"]})
        n1 = jsonl_gz(LAGO / "consumo" / "cifras" / f"fecha={fecha}" / "cifras.jsonl.gz", cifras)
        n2 = jsonl_gz(LAGO / "consumo" / "series" / f"fecha={fecha}" / "series.jsonl.gz", series)
        print(f"consumo {fecha}: {n1} cifras, {n2} puntos de series")
    fuentes = json.loads((RAIZ / "catalogo" / "fuentes_lago.json").read_text(encoding="utf-8"))
    ruta = LAGO / "catalogo" / "fuentes" / "fuentes.jsonl"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n" for f in fuentes), encoding="utf-8")


ZONAS = {"crudo": "Lo que respondió cada fuente, tal cual (comprimido); solo se retiran datos de personas al guardar",
         "curado": "Un archivo por tema y fecha con la forma del contrato, verificado, con el linaje a lo crudo",
         "territorio": "Capas geográficas de referencia (barrios, distritos, límite, lagos, vías con su tráfico y recorridos de bus) en WGS84",
         "consumo": "Tablas planas para SQL y el archivo que lee el tablero",
         "catalogo": "Manifiesto de lo crudo, fuentes e inventario del lago"}


def catalogar():
    """Inventario de todo el lago (menos el propio inventario)."""
    archivos = []
    for p in sorted(LAGO.rglob("*")):
        if not p.is_file() or p.name == "catalogo_lago.json" or p.name.startswith(".") or p.parent == LAGO:
            continue
        rel = p.relative_to(LAGO).as_posix()
        partes = dict(x.split("=", 1) for x in rel.split("/") if "=" in x)
        archivos.append({"ruta": rel, "zona": rel.split("/")[0], "bytes": p.stat().st_size,
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), **{k: v for k, v in partes.items() if k in ("fecha", "tema", "sitio")}})
    resumen = {}
    for a in archivos:
        z = resumen.setdefault(a["zona"], {"archivos": 0, "bytes": 0, "descripcion": ZONAS.get(a["zona"], "")})
        z["archivos"] += 1; z["bytes"] += a["bytes"]
    m = [json.loads(l) for l in (LAGO / "catalogo" / "manifiesto_crudo" / "manifiesto.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    cat = {"fechas": sorted({a["fecha"] for a in archivos if "fecha" in a}), "zonas": resumen,
           "crudo": {"respuestas": len(m), "bytes_originales": sum(f["bytes_original"] for f in m),
                     "con_campos_retirados": sum(1 for f in m if f.get("retirado")), "bloqueadas": sum(1 for f in m if f["estado"] != "guardado"),
                     "sitios": sorted({f["sitio"] for f in m})},
           "archivos": archivos}
    (LAGO / "catalogo" / "catalogo_lago.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"catálogo: {len(archivos)} archivos en {len(resumen)} zonas; fechas {cat['fechas']}")
    return cat


if __name__ == "__main__":
    tablas()
    catalogar()
