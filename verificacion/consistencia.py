#!/usr/bin/env python3
"""Consistencia entre pestañas: una cifra que aparece en varias pestañas tiene que salir del mismo dato.

La página lee cada número con C("tema", "cifra") o S("tema", "serie"). Si una pestaña usa la cifra suelta y otra el último
punto de su serie, o una suma por barrio, los dos tienen que coincidir. Aquí se revisa eso sobre la última foto de la zona
curada, más lo que la página lee de verdad (lago/consumo/tablero/tablero.json) y los textos fijos de la plantilla.
Uso:
    python3 verificacion/consistencia.py [--raiz CARPETA]
verificar.py también la corre: con un FAIL no se publica. Los WARN no hacen fallar, pero hay que leerlos."""
import argparse, glob, json, pathlib, re, sys

# Cifra suelta = punto de su serie con la misma vigencia (la tarjeta y el gráfico de cada pestaña)
CIFRA_EN_SERIE = [
    ("permisos", "permisos_emitidos_ultimo_anio_completo", "permisos_por_anio"),
    ("seguridad", "hurtos_ultimo_anio", "hurtos_por_anio"),
    ("seguridad", "violencia_ultimo_anio", "violencia_por_anio"),
    ("seguridad", "drogas_ultimo_anio", "drogas_por_anio"),
    ("codigo", "casos_ultimo_anio", "casos_por_anio"),
    ("codigo", "quejas_ultimo_anio", "quejas_por_anio"),
    ("economia", "desempleo_ultimo_mes", "desempleo_orlando"),
    ("economia", "desempleo_hace_un_anio", "desempleo_orlando"),
    ("economia", "salario_hora_ultimo_mes", "salario_hora_orlando"),
    ("economia", "empleo_total_ultimo_mes", "empleo_total"),
    ("empleo", "indice_ultimo_dia", "indice_diario"),
    ("escucha", "vistas_ultimo_mes", "vistas_mensuales"),
    ("gente", "poblacion_condado_ultimo_anio", "poblacion_condado"),
    ("gente", "poblacion_condado_ultimo_anio", "poblacion_orange"),
    ("gente", "poblacion_area_metro_ultimo_anio", "poblacion_area_metro"),
    ("gente", "ingreso_mediano_condado", "ingreso_mediano_orange"),
    ("gente", "pobreza_condado", "pobreza_orange"),
    ("gente", "ingreso_por_persona_condado", "ingreso_por_persona_orange"),
    ("turismo", "empleo_ocio_ultimo_mes", "empleo_ocio_hoteleria"),
    ("turismo", "participacion_ocio_ultimo_mes", "participacion_ocio_en_empleo"),
    ("vivienda", "indice_ultimo_trimestre", "indice_trimestral"),
    ("vivienda", "precio_mediano_lista_ultimo_mes", "precio_mediano_lista"),
    ("vivienda", "casas_en_venta_ultimo_mes", "casas_en_venta"),
    ("vivienda", "dias_en_mercado_ultimo_mes", "dias_en_mercado"),
    ("clima_historico", "temperatura_media_ultimo_anio", "temperatura_anual"),
    ("clima_historico", "lluvia_ultimo_anio", "lluvia_anual"),
]
# Total de la ciudad frente a la suma por barrio: lo que falta son casos sin barrio o en barrios bajo el umbral (privacidad)
TOTAL_Y_BARRIOS = [
    # tema, cifra total, serie por barrio, cifra «sin barrio» (o None), cifra «barrios suprimidos»
    ("permisos", "permisos_emitidos_ultimo_anio_completo", "permisos_barrio_{anio}", "permisos_sin_barrio_ultimo_anio", "barrios_suprimidos_ultimo_anio"),
    ("seguridad", "delitos_ultimo_anio", "delitos_barrio_{anio}", "casos_sin_barrio_ultimo_anio", "barrios_suprimidos_ultimo_anio"),
    ("codigo", "casos_ultimo_anio", "casos_barrio_{anio}", "casos_sin_barrio_ultimo_anio", "barrios_suprimidos_ultimo_anio"),
    ("negocios", "negocios_vigentes", "negocios_barrio", "negocios_sin_barrio", "barrios_suprimidos_negocios"),
    ("negocios", "hospedajes_vigentes", "hospedajes_barrio", None, "barrios_suprimidos_hospedajes"),
]
# Series que la página pone lado a lado (pares): tienen que terminar en el mismo periodo, o la página tiene que avisarlo
PARES = {
    "economia": ["desempleo_orlando", "desempleo_tampa", "desempleo_miami", "desempleo_jacksonville", "desempleo_florida"],
    "economia ": ["salario_hora_orlando", "salario_hora_tampa", "salario_hora_miami", "salario_hora_jacksonville"],
    "turismo": ["participacion_ocio_en_empleo", "participacion_ocio_tampa", "participacion_ocio_miami", "participacion_ocio_jacksonville"],
    "escucha": ["vistas_mensuales", "vistas_mensuales_tampa", "vistas_mensuales_miami", "vistas_mensuales_jacksonville"],
    "empleo": ["indice_mensual", "indice_mensual_tampa", "indice_mensual_miami", "indice_mensual_jacksonville"],
    "vivienda": ["indice_trimestral", "indice_trimestral_tampa", "indice_trimestral_miami", "indice_trimestral_jacksonville"],
    "gente": ["ingreso_mediano_orange", "ingreso_mediano_hillsborough", "ingreso_mediano_duval", "ingreso_mediano_miami_dade", "ingreso_mediano_florida"],
}
AVISADAS = {("vivienda", "indice_trimestral_tampa")}   # la pestaña Economía dice «La serie de Tampa termina en …»


def ultimo_curado(raiz):
    temas = {}
    for ruta in sorted(glob.glob(str(raiz / "lago" / "curado" / "tema=*" / "fecha=*" / "*.json"))):
        d = json.load(open(ruta, encoding="utf-8"))
        temas[d["tema"]] = d   # orden por fecha: queda la última
    return temas


def revisar(raiz, check, warn, tablero_estricto=False):
    """tablero_estricto: el tablero ya se construyó con esta foto (después de vista/construir_vista.py). Antes de construir,
    un tablero atrasado es un aviso, no un error: construir_vista.py corre verificar.py antes de escribirlo."""
    raiz = pathlib.Path(raiz)
    L = ultimo_curado(raiz)
    if not L:
        warn("consistencia: no hay zona curada que revisar")
        return
    cifra = lambda t, k: L.get(t, {}).get("cifras", {}).get(k)
    serie = lambda t, k: L.get(t, {}).get("series", {}).get(k)
    cerca = lambda a, b, tol=0.051: a is not None and b is not None and abs(a - b) <= tol

    # 1. la tarjeta y el gráfico dicen lo mismo
    for t, c, s in CIFRA_EN_SERIE:
        x, ss = cifra(t, c), serie(t, s)
        if x is None or ss is None:
            warn(f"consistencia: {t}.{c} o {t}.{s} no está en el lago")
            continue
        pts = dict(map(tuple, ss["puntos"]))
        check(f"consistencia: {t}.{c} = punto {x['vigencia']} de la serie {s}", cerca(x["valor"], pts.get(x["vigencia"])),
              f"cifra {x['valor']} ({x['vigencia']}) · serie {pts.get(x['vigencia'])}")

    # 2. cifras derivadas de otras
    seg = [cifra("seguridad", k) for k in ("delitos_ultimo_anio", "hurtos_ultimo_anio", "violencia_ultimo_anio", "drogas_ultimo_anio")]
    if all(seg):
        check("consistencia: casos de policía = hurtos + violencia + drogas (Seguridad y Barrios)", seg[0]["valor"] == sum(x["valor"] for x in seg[1:]),
              [x["valor"] for x in seg])
    d, df, dfl = cifra("economia", "desempleo_ultimo_mes"), cifra("economia", "diferencia_con_florida"), serie("economia", "desempleo_florida")
    if d and df and dfl:
        fl = dict(map(tuple, dfl["puntos"])).get(d["vigencia"])
        check("consistencia: diferencia con Florida = desempleo de Orlando − desempleo de Florida", cerca(df["valor"], None if fl is None else round(d["valor"] - fl, 1)),
              f"{df['valor']} frente a {d['valor']} − {fl}")
    pc, pb = cifra("censo", "poblacion_estimada_en_barrios"), serie("censo", "poblacion_barrio")
    if pc and pb:
        check("consistencia: población estimada en barrios = suma de la serie por barrio (Gente y Barrios)", abs(pc["valor"] - sum(v for _, v in pb["puntos"])) <= 1,
              f"{pc['valor']} frente a {sum(v for _, v in pb['puntos'])}")
    for t, c, s in [("permisos", "permisos_emitidos_ultimo_anio_completo", "permisos_por_anio")]:
        x, ss, var = cifra(t, c), serie(t, s), cifra(t, "variacion_ultimo_anio")
        if x and ss and var:
            pts = dict(map(tuple, ss["puntos"])); ant = pts.get(str(int(x["vigencia"]) - 1))
            check(f"consistencia: {t}.variacion_ultimo_anio sale de la serie {s}", ant is not None and cerca(var["valor"], round((x["valor"] / ant - 1) * 100, 1)),
                  f"{var['valor']} frente a {x['valor']}/{ant}")

    # 3. el mismo conteo por barrio leído de dos series distintas
    a, b = serie("permisos", "permisos_por_barrio_ultimo_anio"), None
    tot = cifra("permisos", "permisos_emitidos_ultimo_anio_completo")
    if a and tot:
        b = serie("permisos", f"permisos_barrio_{tot['vigencia']}")
        if b is None:
            warn(f"consistencia: no está permisos.permisos_barrio_{tot['vigencia']} para compararla con permisos_por_barrio_ultimo_anio")
        else:
            check("consistencia: permisos por barrio iguales en la frase (permisos_por_barrio_ultimo_anio) y en el mapa (permisos_barrio_<año>)",
                  dict(map(tuple, a["puntos"])) == dict(map(tuple, b["puntos"])), "las dos series difieren")

    # 4. total de la ciudad frente a la suma por barrio (con el umbral de privacidad)
    for t, ct, sb, csin, csup in TOTAL_Y_BARRIOS:
        x = cifra(t, ct)
        if not x:
            continue
        nombre = sb.format(anio=x["vigencia"])
        ss, sin, sup, umb = serie(t, nombre), cifra(t, csin) if csin else None, cifra(t, csup), cifra(t, "umbral_minimo_por_barrio")
        if not (ss and sup and umb):
            warn(f"consistencia: falta algo para cuadrar {t}.{ct} con {nombre}")
            continue
        suma = sum(v for _, v in ss["puntos"])
        falta = x["valor"] - (sin["valor"] if sin else 0) - suma
        tope = sup["valor"] * (umb["valor"] - 1)
        check(f"consistencia: {t}.{ct} cuadra con la suma por barrio ({nombre}): lo que falta cabe en {int(sup['valor'])} barrios bajo el umbral",
              0 <= falta <= tope, f"total {x['valor']} − sin barrio {sin['valor'] if sin else 0} − suma {suma} = {falta}; máximo {tope}")
        menor = [k for k, v in ss["puntos"] if v < umb["valor"]]
        check(f"consistencia: {t}.{nombre} no muestra barrios bajo el umbral de {int(umb['valor'])}", not menor, menor[:5])
    # años anteriores: la suma por barrio nunca pasa del total del año
    for t, pref, total in [("permisos", "permisos_barrio_", "permisos_por_anio"), ("codigo", "casos_barrio_", "casos_por_anio")]:
        tot_s = dict(map(tuple, (serie(t, total) or {"puntos": []})["puntos"]))
        for k, ss in sorted(L.get(t, {}).get("series", {}).items()):
            if k.startswith(pref) and k[len(pref):].isdigit():
                suma, t_anio = sum(v for _, v in ss["puntos"]), tot_s.get(k[len(pref):])
                check(f"consistencia: suma de {t}.{k} ≤ total del año en {total}", t_anio is not None and suma <= t_anio, f"{suma} > {t_anio}")
    por_anio = {k: dict(map(tuple, (serie("seguridad", f"{k}_por_anio") or {"puntos": []})["puntos"])) for k in ("hurtos", "violencia", "drogas")}
    for k, ss in sorted(L.get("seguridad", {}).get("series", {}).items()):
        if k.startswith("delitos_barrio_"):
            anio = k[-4:]
            if not all(anio in por_anio[g] for g in por_anio):
                warn(f"consistencia: no hay hurtos, violencia y drogas de {anio} para cuadrar seguridad.{k}")
                continue
            t_anio = sum(por_anio[g][anio] for g in por_anio)
            check(f"consistencia: suma de seguridad.{k} ≤ casos del año (hurtos + violencia + drogas)", sum(v for _, v in ss["puntos"]) <= t_anio,
                  f"{sum(v for _, v in ss['puntos'])} > {t_anio}")
    # un barrio: hurtos + violencia + drogas no pasa de sus casos (cada tipo se suprime aparte)
    tot_b = dict(map(tuple, (serie("seguridad", f"delitos_barrio_{(cifra('seguridad', 'delitos_ultimo_anio') or {}).get('vigencia')}") or {"puntos": []})["puntos"]))
    partes = {}
    for g in ("hurtos", "violencia", "drogas"):
        for n, v in (serie("seguridad", f"{g}_barrio_{(cifra('seguridad', 'delitos_ultimo_anio') or {}).get('vigencia')}") or {"puntos": []})["puntos"]:
            partes[n] = partes.get(n, 0) + v
    raros = [n for n, v in partes.items() if v > tot_b.get(n, 0)]
    check("consistencia: en cada barrio, hurtos + violencia + drogas ≤ casos de policía del barrio", not raros, raros[:5])

    # 5. series que se comparan lado a lado terminan en el mismo periodo
    for t, nombres in PARES.items():
        t = t.strip()
        fin = {n: serie(t, n)["puntos"][-1][0] for n in nombres if serie(t, n)}
        if not fin:
            continue
        ref = fin.get(nombres[0])
        for n, f in fin.items():
            if f != ref:
                (warn if (t, n) in AVISADAS else lambda m: check(m, False, f"{f} frente a {ref}"))(
                    f"consistencia: {t}.{n} termina en {f} y {nombres[0]} en {ref}" + (" (la página lo avisa)" if (t, n) in AVISADAS else ""))
        if all(f == ref for f in fin.values()):
            check(f"consistencia: {t}: {', '.join(nombres)} terminan en el mismo periodo ({ref})", True)

    # 6. lo que la página lee es la última foto del lago
    tab = raiz / "lago" / "consumo" / "tablero" / "tablero.json"
    if tab.exists():
        lago_t = json.load(open(tab, encoding="utf-8")).get("lago", {})
        dif = [f"{t}.{k}" for t, d in L.items() for k, c in d.get("cifras", {}).items()
               if lago_t.get(t, {}).get("cifras", {}).get(k, {}).get("valor") != c["valor"]
               or lago_t.get(t, {}).get("cifras", {}).get(k, {}).get("vigencia") != c["vigencia"]]
        nombre = "consistencia: el tablero publicado (consumo/tablero/tablero.json) trae las mismas cifras que la última foto curada"
        if tablero_estricto or not dif:
            check(nombre, not dif, f"{len(dif)} distintas, p. ej. {dif[:4]}")
        else:
            warn(f"{nombre}: todavía no, {len(dif)} cifras nuevas o distintas (se pone al día con vista/construir_vista.py)")
    else:
        warn("consistencia: todavía no hay lago/consumo/tablero/tablero.json (se crea con vista/construir_vista.py)")

    # 7. textos fijos de la vista que dependen de los datos
    umbrales = {t: d["cifras"]["umbral_minimo_por_barrio"]["valor"] for t, d in L.items() if "umbral_minimo_por_barrio" in d.get("cifras", {})}
    plantilla = (raiz / "vista" / "plantilla.html").read_text(encoding="utf-8") if (raiz / "vista" / "plantilla.html").exists() else ""
    for n in sorted(set(re.findall(r"menos de (\d+) casos", plantilla))):
        check(f"consistencia: el texto fijo «menos de {n} casos» coincide con el umbral de cada tema", all(v == int(n) for v in umbrales.values()), umbrales)
    app = (raiz / "vista" / "app.js").read_text(encoding="utf-8") if (raiz / "vista" / "app.js").exists() else ""
    sueltas = [m.group(0)[:70] for m in re.finditer(r"por cada 1?0?\.?000 personas(?! entre residentes| \(residentes)[^`\"]{0,40}", app)]
    check("consistencia: toda tasa «por cada 1.000 personas» dice que cuenta residentes y empleos (Vivir y Seguridad usan habitantes)", not sueltas, sueltas[:3])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=str(pathlib.Path(__file__).resolve().parents[1]))
    fallos = 0

    def check(nombre, ok, detalle=""):
        global fallos
        print(("PASS " if ok else "FAIL ") + nombre + ("" if ok else f" <- {detalle}"))
        fallos += 0 if ok else 1

    ap.add_argument("--antes-de-construir", action="store_true", help="un tablero atrasado es aviso, no falla")
    a = ap.parse_args()
    revisar(a.raiz, check, lambda m: print("WARN " + m), tablero_estricto=not a.antes_de_construir)
    print(f"\n{fallos} fallos")
    sys.exit(1 if fallos else 0)
