"""La zona cruda del lago: guarda lo que respondió cada fuente, tal cual, y lo vuelve a leer para reconstruir sin internet.

lago/crudo/sitio=<servidor>/fecha=<AAAA-MM-DD>/<nombre>-<huella>.<json|csv|txt>.gz
lago/catalogo/manifiesto_crudo/manifiesto.jsonl   una línea por respuesta: URL, fecha, huellas, tamaño, cómo se pidió y qué se retiró

Antes de guardar se retiran los datos de personas (privacidad.py): las fichas del portal de la ciudad traen el nombre de
quien publicó el conjunto y valores de muestra de cada columna (ahí aparecen correos). El manifiesto guarda la huella de
la respuesta tal como llegó y la de lo guardado, y dice qué campos se retiraron. Si después de retirar todavía aparece un
correo o un teléfono, la respuesta NO se guarda (estado «bloqueado») y la reconstrucción desde la zona cruda lo avisa."""
import gzip, hashlib, json, pathlib, re, sys, urllib.parse

from privacidad import retirar, texto_con_pii, zip_con_pii

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "lago" / "crudo"
MANIFIESTO = RAIZ / "lago" / "catalogo" / "manifiesto_crudo" / "manifiesto.jsonl"
LEIDOS = []                    # lo que leyó este script: [{url, crudo, sha256}] (para el linaje del archivo curado)


def tema_actual():
    return pathlib.Path(sys.argv[0]).stem.replace("pull_", "") or "?"


def _nombre(url):
    u = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(u.query)
    partes = [p for p in u.path.split("/") if p]
    if "fred.stlouisfed.org" in u.netloc and "id" in q:
        base = "fred-" + q["id"][0].split(",")[0]
    elif re.search(r"(Map|Feature)Server", u.path):
        i = next(k for k, p in enumerate(partes) if p in ("MapServer", "FeatureServer"))
        base = f"{partes[i - 1]}-{partes[i + 1] if i + 1 < len(partes) and partes[i + 1].isdigit() else 'servicio'}"
    elif "/resource/" in u.path or "/api/views/" in u.path:
        base = ("ficha-" if "/api/views/" in u.path else "datos-") + partes[-1].split(".")[0]
    elif "censusreporter" in u.netloc:
        base = "censo-" + (q.get("table_ids", ["geo"])[0].split(",")[0])
    elif "wikimedia" in u.netloc:
        base = "vistas-" + "-".join(partes[3:6])
    else:
        base = partes[-1] if partes else u.netloc
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).strip("-").lower()[:50]
    return base + "-" + hashlib.sha1(url.encode()).hexdigest()[:10]


def _formato(url, cuerpo):
    if cuerpo[:4] == b"PK\x03\x04":
        return "zip", None
    try:
        return "json", json.loads(cuerpo)
    except Exception:
        pass
    texto = cuerpo.decode("utf-8", "replace")
    if ".csv" in url or (texto[:200].count(",") >= 2 and "<" not in texto[:200]):
        return "csv", None
    return "txt", None


def leer_manifiesto():
    if not MANIFIESTO.exists():
        return {}
    filas = [json.loads(l) for l in MANIFIESTO.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {(f["fecha"], f["url"]): f for f in filas}


def _escribir_manifiesto(m):
    MANIFIESTO.parent.mkdir(parents=True, exist_ok=True)
    filas = sorted(m.values(), key=lambda f: (f["fecha"], f["sitio"], f["url"]))
    MANIFIESTO.write_text("".join(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n" for f in filas), encoding="utf-8")


def guardar(url, cuerpo, fecha, como):
    """Guarda la respuesta en la zona cruda (comprimida) y la anota en el manifiesto. Devuelve la fila del manifiesto."""
    sitio = urllib.parse.urlsplit(url).netloc
    formato, obj = _formato(url, cuerpo)
    retirado, guardado = {}, cuerpo
    if obj is not None:
        retirado = retirar(obj)
        if retirado:
            guardado = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        valores = [v for v in _hojas(obj) if isinstance(v, str)]
        pii = next((p for p in (texto_con_pii(v, crudo=True) for v in valores) if p), None)
    elif formato == "zip":
        pii = zip_con_pii(guardado)
    else:
        pii = texto_con_pii(guardado.decode("utf-8", "replace"), crudo=True)
    rel = f"crudo/sitio={sitio}/fecha={fecha}/{_nombre(url)}.{formato}.gz"
    fila = {"fecha": fecha, "sitio": sitio, "url": url, "tema": tema_actual(), "como": como, "formato": formato,
            "bytes_original": len(cuerpo), "sha256_original": hashlib.sha256(cuerpo).hexdigest(),
            "retirado": retirado, "estado": "guardado", "archivo": rel}
    destino = RAIZ / "lago" / rel
    if pii:
        fila.update(estado="bloqueado", archivo=None, motivo="después de retirar campos personales todavía aparece un correo o un teléfono")
        if destino.exists():
            destino.unlink()
    else:
        destino.parent.mkdir(parents=True, exist_ok=True)
        # mtime fijo: el mismo contenido da el mismo .gz, byte a byte (reconstruir no cambia el repositorio)
        destino.write_bytes(gzip.compress(guardado, compresslevel=9, mtime=0))
        fila.update(bytes_guardado=len(guardado), sha256_guardado=hashlib.sha256(guardado).hexdigest())
    m = leer_manifiesto()
    previa = m.get((fecha, url))
    if previa and previa.get("tema") and previa["tema"] != fila["tema"]:          # la misma URL la piden dos scripts
        fila["tema"] = ",".join(sorted(set(previa["tema"].split(",")) | {fila["tema"]}))
    m[(fecha, url)] = fila
    _escribir_manifiesto(m)
    LEIDOS.append({"url": url, "crudo": fila["archivo"], "sha256": fila.get("sha256_guardado")})
    return fila


def leer(url, fecha):
    """Lo guardado para esa URL en esa fecha (para reconstruir sin internet)."""
    fila = leer_manifiesto().get((fecha, url))
    if not fila:
        raise SystemExit(f"La zona cruda no tiene la respuesta de {fecha} para {url[:160]}")
    if fila["estado"] != "guardado":
        raise SystemExit(f"La respuesta de {url[:120]} quedó {fila['estado']}: {fila.get('motivo', '')}")
    cuerpo = gzip.decompress((RAIZ / "lago" / fila["archivo"]).read_bytes())
    if hashlib.sha256(cuerpo).hexdigest() != fila["sha256_guardado"]:
        raise SystemExit(f"La huella de {fila['archivo']} no coincide con el manifiesto: el archivo cambió")
    # al leer también se anota: así el archivo curado reconstruido trae el mismo linaje
    LEIDOS.append({"url": url, "crudo": fila["archivo"], "sha256": fila["sha256_guardado"]})
    return cuerpo


def _hojas(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _hojas(v)
    elif isinstance(o, list):
        for v in o:
            yield from _hojas(v)
    else:
        yield o


ASIGNADO = {}                 # crudo -> id de la fuente a la que se atribuyó (un script puede escribir dos temas)


def linaje_por_fuente(fuentes):
    """Reparte lo leído entre las fuentes del archivo curado: mismo servidor y el prefijo de URL más largo en común.
    Si ninguna fuente comparte servidor y el tema tiene una sola fuente, va a esa (p. ej. los títulos de Wikipedia que
    se consultan antes de pedir las visitas). Lo que ya se atribuyó en otro tema del mismo script solo se repite si la
    fuente es la misma."""
    def comun(a, b):
        n = 0
        for x, y in zip(a, b):
            if x != y:
                break
            n += 1
        return n
    for f in fuentes:
        f["crudo"] = []
    ids = {f["id"]: f for f in fuentes}
    for l in LEIDOS:
        if l["crudo"] is None:
            continue
        previo = ASIGNADO.get(l["crudo"])
        if previo:
            if previo in ids:
                ids[previo]["crudo"].append(l["crudo"])
            continue
        sitio = urllib.parse.urlsplit(l["url"]).netloc
        cand = [f for f in fuentes if urllib.parse.urlsplit(f["url"]).netloc == sitio] or (fuentes if len(fuentes) == 1 else [])
        if not cand:
            continue
        mejor = max(cand, key=lambda f: comun(f["url"], l["url"]))
        mejor["crudo"].append(l["crudo"])
        ASIGNADO[l["crudo"]] = mejor["id"]
    for f in fuentes:
        f["crudo"] = sorted(set(f["crudo"]))
    return fuentes
