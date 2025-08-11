import os
import re
import csv
import pdfplumber
from datetime import datetime

# === RUTAS DE ENTRADA Y SALIDA ===
carpeta_hev = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\repo_rips\data\input\hev"
carpeta_salida_control = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\repo_rips\data\output\control"

os.makedirs(carpeta_salida_control, exist_ok=True)

CODIGO_PRESTADOR_DEFECTO = "760010395701"

def extract_text_pdf(ruta_pdf):
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
    except Exception as e:
        print(f"❌ Error al extraer texto de {ruta_pdf}: {e}")
        return ""

def extract_documento_paciente(text):
    match = re.search(r"^\s*(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})", text, re.MULTILINE)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    match_alt = re.search(
        r"Identificaci[oó]n:\s*\n?\s*(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})",
        text,
        re.IGNORECASE,
    )
    if match_alt:
        return match_alt.group(1).strip(), match_alt.group(2).strip()

    return "", ""

def extract_codigo_prestador(text):
    match = re.search(r"(?:NIT|Nit)[: ]+\s*([0-9\-]{6,20})", text)
    if match:
        return match.group(1).strip()
    return CODIGO_PRESTADOR_DEFECTO

def extract_procedimientos(text):
    codigos, nombres = [], []
    patron = re.compile(r"Cod:\s*(\d{3,10})\s+Nomb:\s*(.+)", re.IGNORECASE)
    for line in text.splitlines():
        m = patron.search(line)
        if m:
            cod = m.group(1).strip()
            nom = m.group(2).strip()
            if cod not in codigos:
                codigos.append(cod)
                nombres.append(nom)
    return ",".join(codigos), ",".join(nombres)

def extract_dx_principal(text):
    dx_list = []
    for dx_tag in ["DXP", "DXR"]:
        match = re.search(rf"{dx_tag}[: ]+([A-Z0-9]{{3,10}})", text, re.IGNORECASE)
        if match:
            dx_list.append(match.group(1).strip().upper())
    return ",".join(set(dx_list))

def procesar_hev():
    columnas = [
        "archivo",
        "numero_factura",
        "tipo_documento",
        "identificacion",
        "cod_prestador",
        "codigos_servicio",
        "nombres_servicio",
        "dx_principal",
        "estado_revision"
    ]
    datos = []

    archivos_pdf = [f for f in os.listdir(carpeta_hev) if f.lower().endswith(".pdf")]

    for archivo in archivos_pdf:
        match_factura = re.search(r"FERO\d+", archivo)
        if not match_factura:
            continue

        num_factura = match_factura.group(0)
        ruta_pdf = os.path.join(carpeta_hev, archivo)
        texto = extract_text_pdf(ruta_pdf)

        tipo_doc, identificacion = extract_documento_paciente(texto)
        cod_prestador = extract_codigo_prestador(texto)
        cod_serv, nom_serv = extract_procedimientos(texto)
        dx_principal = extract_dx_principal(texto)

        # Estado de revisión
        if archivo.upper().startswith("PDE") or archivo.upper().startswith("PDX"):
            estado_revision = "Revisar"
        else:
            estado_revision = "Lista para RIPS"

        datos.append(
            {
                "archivo": archivo,
                "numero_factura": num_factura,
                "tipo_documento": tipo_doc,
                "identificacion": identificacion,
                "cod_prestador": cod_prestador,
                "codigos_servicio": cod_serv,
                "nombres_servicio": nom_serv,
                "dx_principal": dx_principal,
                "estado_revision": estado_revision
            }
        )

    nombre_csv = f"control_hev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ruta_csv = os.path.join(carpeta_salida_control, nombre_csv)
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(datos)

    print(f"✅ Archivo CSV guardado en: {ruta_csv}")

if __name__ == "__main__":
    procesar_hev()
