"""Para cada dataset del catálogo de Orlando (catalogo_orlando.json) consulta su ficha completa
(/api/views/<id>.json), copia la licencia tal como aparece y prueba que la descarga responda de verdad.
Uso:  python licencias_orlando.py          (poner catalogo_orlando.json en la misma carpeta)
Salida: licencias_orlando.csv. La fecha_prueba solo vale para el Excel si http_datos=200 y filas_muestra>0.
El catálogo no trae la licencia (su campo 'metadata' solo tiene el dominio); por eso se pide la ficha."""
import csv, json, datetime, urllib.request, urllib.error

CONTACTO = "correo-del-grupo@ejemplo.com"
H = {"User-Agent": f"TallerDatos-EAFIT/1.0 ({CONTACTO})"}
BASE = "https://data.cityoforlando.net"
hoy = datetime.date.today().isoformat()

def get(url, n=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
        return r.status, r.headers.get("Content-Type", ""), (r.read(n) if n else r.read())

datasets = [e["resource"] for e in json.load(open("catalogo_orlando.json", encoding="utf-8")) if e["resource"]["type"] == "dataset"]
with open("licencias_orlando.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "nombre", "licencia", "enlace_licencia", "licencia_id", "atribucion", "categoria", "filas_actualizadas",
                "http_datos", "tipo_contenido", "filas_muestra", "url_json", "url_csv", "fecha_prueba", "error"])
    for d in datasets:
        i = d["id"]; lic = enl = lid = attr = cat = upd = ""; http = ct = ""; filas = 0; err = ""
        try:
            _, _, cuerpo = get(f"{BASE}/api/views/{i}.json")
            v = json.loads(cuerpo)
            l = v.get("license") or {}
            lic, enl, lid = l.get("name", ""), l.get("termsLink", ""), v.get("licenseId", "")
            attr, cat = v.get("attribution", "") or "", v.get("category", "") or ""
            upd = datetime.datetime.fromtimestamp(v["rowsUpdatedAt"]).date().isoformat() if v.get("rowsUpdatedAt") else ""
        except Exception as e:
            err = "ficha: " + str(e)[:80]
        try:
            http, ct, cuerpo = get(f"{BASE}/resource/{i}.json?$limit=5")
            filas = len(json.loads(cuerpo))
        except Exception as e:
            err += " | datos: " + str(e)[:80]
        w.writerow([i, d["name"], lic, enl, lid, attr, cat, upd, http, ct, filas,
                    f"{BASE}/resource/{i}.json", f"{BASE}/resource/{i}.csv", hoy, err])
        print(i, d["name"][:40], "|", lic or "(sin licencia en la ficha)", "|", http, filas)
print("Listo: licencias_orlando.csv")
