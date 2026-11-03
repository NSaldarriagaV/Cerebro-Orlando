#!/usr/bin/env python3
"""Convierte las hojas del Excel en copias JSON legibles para el repositorio:
«1. Fuentes» -> catalogo/catalogo_completo.json, «2. Diccionario» -> catalogo/diccionario.json y
«3. Bitácora IA» -> catalogo/bitacora_ia.json. La vista (vista/construir_vista.py) las lee sin openpyxl.

Uso (necesita openpyxl: pip install openpyxl):
    python3 catalogo/exportar_catalogo.py ruta/al/Diccionario_de_datos_TallerDatos.xlsx
El Excel es la fuente de verdad del catálogo; este JSON es su copia legible para el repositorio. Vuelvan a correrlo
cada vez que cambie el Excel. Incluye las fuentes que no entraron, con su estado y su nota: es parte de la entrega."""
import json, pathlib, sys
from openpyxl import load_workbook

ESTADO = {"Integrada al lago": "integrado", "Candidata": "candidato", "No responde": "caido",
          "No existe (la inventó la IA)": "inexistente", "Descartada": "excluido"}
libro = load_workbook(sys.argv[1], data_only=True)
ws = libro["1. Fuentes"]
fichas = []
for fila in ws.iter_rows(min_row=5, max_row=ws.max_row, values_only=True):
    if not fila[0]:
        continue
    f = list(fila) + [None] * 16
    fichas.append({"id": f[0], "nombre": f[1], "entidad": f[2], "tipo_publicador": f[3], "url": f[4], "formato": f[5],
                   "como_se_obtiene": f[6], "licencia": f[7], "personas": f[8], "cobertura": f[9],
                   "vigencia": f[10], "frecuencia": f[11], "probado": str(f[12]) if f[12] else None,
                   "estado": ESTADO.get(f[13], f[13]), "hallada_por": f[14], "nota": f[15]})
destino = pathlib.Path(__file__).resolve().parent / "catalogo_completo.json"
destino.write_text(json.dumps(fichas, ensure_ascii=False, indent=1), encoding="utf-8")
cuenta = {}
for f in fichas:
    cuenta[f["estado"]] = cuenta.get(f["estado"], 0) + 1
print(f"{len(fichas)} fichas -> {destino.name}", cuenta)


# La fila 4 de cada hoja es el ejemplo gris de Medellín: no se exporta.
def hoja(nombre, claves):
    filas = []
    for fila in libro[nombre].iter_rows(min_row=5, max_row=libro[nombre].max_row, values_only=True):
        if not any(c is not None for c in fila):
            continue
        f = list(fila) + [None] * len(claves)
        filas.append({k: (str(f[i]) if f[i] is not None else None) for i, k in enumerate(claves)})
    return filas


diccionario = hoja("2. Diccionario", ["fuente", "archivo", "campo", "nombre_original", "significado", "tipo", "unidad", "ejemplo",
                                      "puede_vacio", "rango", "clasificacion", "transformacion", "pregunta"])
bitacora = hoja("3. Bitácora IA", ["n", "herramienta", "encargo", "respuesta", "comprobacion", "resultado", "fuentes", "aprendizaje"])
for nombre, datos in (("diccionario.json", diccionario), ("bitacora_ia.json", bitacora)):
    (destino.parent / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(datos)} filas -> {nombre}")
