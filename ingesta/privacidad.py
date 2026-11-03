"""Reglas de privacidad compartidas: las usa la ingesta al guardar la zona cruda y verificar.py antes de publicar.
Una sola lista, para que lo que se retira al guardar y lo que se revisa al publicar no se desincronicen."""
import re

# Textos que parecen correos o teléfonos
PII = [re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I),                                       # correos
       re.compile(r"(?<!\d)3\d{9}(?!\d)"),                                                       # celulares colombianos
       re.compile(r"(?<![\d.])(?:\+?1[ .-]?)?\(?[2-9]\d{2}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")]   # teléfonos de EE. UU.
# Para la zona cruda: respuestas enteras, llenas de números largos (códigos de sector censal, coordenadas, fechas
# AAAAMMDDHH). Ahí solo cuentan los correos y los teléfonos escritos como teléfono (con separadores).
PII_CRUDO = [PII[0], re.compile(r"(?<![\w.])(?:\+?1[ .-])?(?:\(\d{3}\)\s?|\d{3}[ .-])\d{3}[ .-]\d{4}(?![\w.])")]
# Nombres de campo que delatan datos de personas
CAMPOS_PERSONALES = re.compile(r"cedula|documento_identidad|telefono|celular|correo|email|phone|owner|contractor|applicant|suspect|officer|name_?holder|commissionername"
                               r"|casenumber|case_number|license_holder|casename|case_comments|add_by|property_address"
                               r"|tableauthor|displayname|screenname|createdby|modifiedby|approvals|userid", re.I)
# Campos de las fichas del portal (Socrata) que copian valores de muestra de cada columna: ahí aparecen correos de personas
MUESTRAS = {"cachedContents"}
RETIRADO = "[retirado al guardar: dato de personas]"
RETIRADO_MUESTRA = "[retirado al guardar: valores de muestra de la columna]"


def retirar(obj):
    """Reemplaza, en el lugar, los valores de campos personales y de muestras. Devuelve {campo: veces}."""
    cuenta = {}

    def anda(o):
        if isinstance(o, dict):
            for k in list(o):
                if k in MUESTRAS:
                    o[k] = RETIRADO_MUESTRA; cuenta[k] = cuenta.get(k, 0) + 1
                elif CAMPOS_PERSONALES.search(k):
                    o[k] = RETIRADO; cuenta[k] = cuenta.get(k, 0) + 1
                else:
                    anda(o[k])
        elif isinstance(o, list):
            for x in o:
                anda(x)
    anda(obj)
    return cuenta


# Buzones de instituciones, no de personas (p. ej. el remitente de las alertas del clima: w-nws.webmaster@noaa.gov)
INSTITUCIONAL = re.compile(r"^[\w.-]*(webmaster|no-?reply|noreply)[\w.-]*@[\w.-]+\.gov$", re.I)


def texto_con_pii(texto, crudo=False):
    """Primer trozo que parece correo o teléfono, o None. En la zona cruda se aceptan los buzones institucionales."""
    for p in (PII_CRUDO if crudo else PII):
        for m in p.finditer(texto):
            if crudo and INSTITUCIONAL.match(m.group(0)):
                continue
            return m.group(0)
    return None


# Archivos ZIP (el GTFS de los buses): se revisa el texto de cada archivo de adentro. agency.txt trae, por norma del
# formato, el teléfono y el correo de atención al público de la empresa de transporte: no son de personas.
CONTACTO_INSTITUCIONAL_ZIP = {"agency.txt"}


def zip_con_pii(cuerpo):
    """Primer correo o teléfono dentro de un ZIP (fuera de los contactos institucionales), o None."""
    import io, zipfile
    with zipfile.ZipFile(io.BytesIO(cuerpo)) as z:
        for n in z.namelist():
            if n.rsplit("/", 1)[-1] in CONTACTO_INSTITUCIONAL_ZIP:
                continue
            hallado = texto_con_pii(z.read(n).decode("utf-8", "replace"), crudo=True)
            if hallado:
                return f"{n}: {hallado}"
    return None

