import os
import re
import pdfplumber
import xml.etree.ElementTree as ET
import pandas as pd

# === Rutas ===
carpeta_pdf = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\fact_pdf"
carpeta_xml = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\fact_xml"
carpeta_hev = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\hev"
salida_csv = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\control\control_servicios.csv"

tabla_control = []

# === Función para extraer datos desde PDF ===
def extraer_info_pdf(ruta_pdf):
    codigos_pdf = []
    descripciones_pdf = []
    fecha_emision = ""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            texto = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        # Buscar fecha de emisión
        match_fecha = re.search(r"Fecha de Emision\s+(\d{2}/\d{2}/\d{4})", texto)
        if match_fecha:
            fecha_emision = match_fecha.group(1)

        # Buscar códigos y descripciones en tabla de servicios
        pattern_servicio = re.compile(
            r"(?P<codigo>\d{4,7}(?:-\d{1,2})?)\s+(?P<descripcion>[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\.\-\,\s]+?)\s+1\s+\$\s*(?P<vr_unitario>[\d,\.]+)\s+0%\s+\$\s*(?P<vr_total>[\d,\.]+)\s+0%"
        )

        for match in pattern_servicio.finditer(texto):
            codigo = match.group("codigo").strip()
            descripcion = match.group("descripcion").strip()
            codigos_pdf.append(codigo)
            descripciones_pdf.append(descripcion)

    except Exception as e:
        print(f"⚠️ Error leyendo PDF: {ruta_pdf} -> {e}")

    return fecha_emision, codigos_pdf, descripciones_pdf

# === Función para extraer códigos CUPS desde XML embebido ===
def extraer_cups_xml(ruta_xml):
    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()

        ns = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        for attachment in root.findall('.//cac:Attachment', ns):
            description_node = attachment.find('.//cbc:Description', ns)
            if description_node is not None and description_node.text:
                contenido_embebido = description_node.text.strip()
                try:
                    embedded_root = ET.fromstring(contenido_embebido)
                    cups = []
                    for elem in embedded_root.iter():
                        if elem.tag.endswith('ID') and elem.text and elem.text.strip().isdigit():
                            cups.append(elem.text.strip())
                    return ", ".join(cups) if cups else None
                except ET.ParseError as e:
                    print(f"⚠️ Error parseando XML embebido en {ruta_xml} -> {e}")
    except Exception as e:
        print(f"⚠️ Error leyendo XML externo {ruta_xml} -> {e}")
    return None

# === Procesar todos los PDFs ===
for archivo_pdf in os.listdir(carpeta_pdf):
    if archivo_pdf.endswith(".pdf"):
        ruta_pdf = os.path.join(carpeta_pdf, archivo_pdf)
        factura_archivo = archivo_pdf.replace(".pdf", "")

        # Extraer del PDF
        fecha_pdf, codigos_pdf, descripciones_pdf = extraer_info_pdf(ruta_pdf)

        # Buscar XML correspondiente
        ruta_xml = os.path.join(carpeta_xml, factura_archivo + ".xml")
        cups_xml = extraer_cups_xml(ruta_xml) if os.path.exists(ruta_xml) else None

        # Extraer FEROxxxxxx para todo
        match_fero = re.search(r"(FERO[\-_]?\d{6})", factura_archivo, re.IGNORECASE)
        if match_fero:
            fero_id = re.sub(r"[\-_]", "", match_fero.group(1))  # Ej: FERO948038
        else:
            fero_id = factura_archivo

        factura_id = fero_id  # Mostrado como nombre de factura (solo FEROxxxxxx)

        # Verificar HEV, PDX o PDE
        archivos_soporte = os.listdir(carpeta_hev)
        def existe_soporte(tipo):
            return any(tipo in archivo and fero_id in archivo for archivo in archivos_soporte)

        if existe_soporte("HEV"):
            soporte_clinico = "✅ HEV"
        elif existe_soporte("PDX") or existe_soporte("PDE"):
            soporte_clinico = "✅ PDX/PDE"
        else:
            soporte_clinico = "❌ No"

        # Evaluar estado
        if codigos_pdf or cups_xml:
            estado = "Lista para RIPS" if soporte_clinico != "❌ No" else "Riesgo de glosa"
        else:
            estado = "❌ Servicios no encontrados"

        # Agregar fila
        tabla_control.append({
            "Factura": factura_id,
            "Fecha": fecha_pdf if fecha_pdf else "❌",
            "CUPS_PDF_CODIGO": ", ".join(codigos_pdf) if codigos_pdf else "❌",
            "CUPS_PDF_DESC": ", ".join(descripciones_pdf) if descripciones_pdf else "❌",
            "CUPS_XML": cups_xml if cups_xml else "❌",
            "Soporte clínico": soporte_clinico,
            "Estado": estado
        })

# === Guardar resultado ===
df = pd.DataFrame(tabla_control)
os.makedirs(os.path.dirname(salida_csv), exist_ok=True)
df.to_csv(salida_csv, index=False, encoding="utf-8-sig")
print(f"✅ Control generado con {len(tabla_control)} facturas en:\n{salida_csv}")
