#!/usr/bin/env python3
"""Corre en local, con DuckDB, las consultas de athena.sql sobre los mismos archivos del lago (sin nube ni llaves).
Así se prueba que el lago se puede consultar con SQL antes de subirlo a S3.   pip install duckdb"""
import pathlib, sys
try:
    import duckdb
except ImportError:
    sys.exit("Falta DuckDB: pip install duckdb")

L = pathlib.Path(__file__).resolve().parents[1] / "lago"
con = duckdb.connect()
con.execute(f"CREATE VIEW cifras AS SELECT * FROM read_json_auto('{L}/consumo/cifras/*/*.jsonl.gz', hive_partitioning=true)")
con.execute(f"CREATE VIEW series AS SELECT * FROM read_json_auto('{L}/consumo/series/*/*.jsonl.gz', hive_partitioning=true)")
con.execute(f"CREATE VIEW manifiesto AS SELECT * FROM read_json_auto('{L}/catalogo/manifiesto_crudo/manifiesto.jsonl')")
con.execute(f"CREATE VIEW fuentes AS SELECT * FROM read_json_auto('{L}/catalogo/fuentes/fuentes.jsonl')")
con.execute("CREATE VIEW por_barrio AS SELECT fecha, tema, serie, etiqueta AS barrio, valor, unidad, fuente FROM series WHERE serie LIKE '%barrio%'")
f = sorted(r[0] for r in con.execute("SELECT DISTINCT CAST(fecha AS VARCHAR) FROM cifras").fetchall())
a, b = f[-2] if len(f) > 1 else f[-1], f[-1]
CONSULTAS = [
    ("¿Qué cifras cambiaron entre las dos fotos del lago?",
     f"""SELECT a.tema, a.clave, a.valor AS antes, b.valor AS ahora, a.vigencia AS vig_antes, b.vigencia AS vig_ahora
         FROM cifras a JOIN cifras b ON a.tema = b.tema AND a.clave = b.clave
         WHERE CAST(a.fecha AS VARCHAR) = '{a}' AND CAST(b.fecha AS VARCHAR) = '{b}' AND (a.valor <> b.valor OR a.vigencia <> b.vigencia)
         ORDER BY a.tema, a.clave"""),
    ("Los 10 barrios con más casos de policía en 2025",
     f"SELECT barrio, valor AS casos FROM por_barrio WHERE CAST(fecha AS VARCHAR) = '{b}' AND serie = 'delitos_barrio_2025' ORDER BY casos DESC LIMIT 10"),
    ("De qué sitios sale cada tema",
     f"SELECT tema, sitio, count(*) AS respuestas, round(sum(bytes_original) / 1e6, 2) AS mb FROM manifiesto WHERE CAST(fecha AS VARCHAR) = '{b}' GROUP BY tema, sitio ORDER BY tema, sitio"),
    ("Qué se retiró por privacidad antes de guardar",
     "SELECT CAST(fecha AS VARCHAR) AS fecha, url, retirado FROM manifiesto WHERE retirado IS NOT NULL AND json_array_length(json_keys(to_json(retirado))) > 0 ORDER BY fecha, url"),
    ("Cada cifra con su fuente y licencia (primeras 8)",
     f"SELECT c.tema, c.clave, c.valor, f.entidad, f.licencia FROM cifras c JOIN fuentes f ON c.fuente = f.id WHERE CAST(c.fecha AS VARCHAR) = '{b}' ORDER BY c.tema, c.clave LIMIT 8"),
]
for titulo, sql in CONSULTAS:
    r = con.execute(sql)
    filas, cols = r.fetchall(), [d[0] for d in r.description]
    print(f"\n## {titulo} ({len(filas)} filas)")
    print(" | ".join(cols))
    for fila in filas[:20]:
        print(" | ".join(str(x)[:70] for x in fila))
