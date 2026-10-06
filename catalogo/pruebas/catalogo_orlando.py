"""Baja el catálogo completo de datasets del portal de Orlando (API de descubrimiento de Socrata)
y lo guarda en catalogo_orlando.csv (una fila por dataset) y catalogo_orlando.json (respuesta completa).
Uso:  python catalogo_orlando.py
Sirve para elegir qué datasets entran al lago y para copiar la licencia de cada ficha en el Excel.
Si una columna sale vacía, abran catalogo_orlando.json y busquen el campo: no todos los datasets traen todo."""
import csv, json, urllib.request, urllib.parse, datetime

CONTACTO = "correo-del-grupo@ejemplo.com"
BASE = "https://api.us.socrata.com/api/catalog/v1"
resultados, offset, total = [], 0, None
while total is None or offset < total:
    url = BASE + "?" + urllib.parse.urlencode({"domains": "data.cityoforlando.net", "limit": 100, "offset": offset})
    req = urllib.request.Request(url, headers={"User-Agent": f"TallerDatos-EAFIT/1.0 ({CONTACTO})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    total = data.get("resultSetSize", 0)
    resultados += data.get("results", [])
    offset += 100
    print(f"{len(resultados)} / {total}")

with open("catalogo_orlando.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=1)

hoy = datetime.date.today().isoformat()
with open("catalogo_orlando.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "nombre", "tipo", "categoria", "licencia", "actualizado", "creado", "num_columnas", "columnas", "descripcion", "enlace_ficha", "url_json_sugerida", "fecha_consulta"])
    for x in resultados:
        res, cls, meta = x.get("resource", {}), x.get("classification", {}), x.get("metadata", {})
        cols = res.get("columns_field_name", []) or []
        w.writerow([res.get("id"), res.get("name"), res.get("type"), cls.get("domain_category", ""),
                    meta.get("license", ""), res.get("data_updated_at") or res.get("updatedAt", ""), res.get("createdAt", ""),
                    len(cols), "; ".join(cols), (res.get("description") or "").replace("\n", " ")[:300],
                    x.get("permalink") or x.get("link", ""),
                    f"https://data.cityoforlando.net/resource/{res.get('id')}.json" if res.get("type") == "dataset" else "", hoy])
print("Listo: catalogo_orlando.csv y catalogo_orlando.json")
