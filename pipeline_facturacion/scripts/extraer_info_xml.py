import xml.etree.ElementTree as ET
import os
import pandas as pd

# === CONFIGURACIÓN DE RUTAS ===
carpeta_xml = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\fact_xml"

archivos = [f for f in os.listdir(carpeta_xml) if f.endswith(".xml")]

# === LISTA PARA GUARDAR RESULTADOS ===
datos = []

for archivo in archivos:
    ruta = os.path.join(carpeta_xml, archivo)
    tree = ET.parse(ruta)
    root = tree.getroot()

    # Namespaces para que funcione el .find
    ns = {
        'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    }

    factura_id = root.find('.//cac:DocumentReference/cbc:ID', ns)
    cufe = root.find('.//cac:DocumentReference/cbc:UUID', ns)
    val_code = root.find('.//cac:Response/cbc:ResponseCode', ns)
    val_desc = root.find('.//cac:Response/cbc:Description', ns)
    val_fecha = root.find('.//cac:ResultOfVerification/cbc:ValidationDate', ns)
    val_hora = root.find('.//cac:ResultOfVerification/cbc:ValidationTime', ns)

    # NIT emisor y receptor
    emisor = root.find('.//cac:SenderParty/cac:PartyTaxScheme/cbc:CompanyID', ns)
    receptor = root.find('.//cac:ReceiverParty/cac:PartyTaxScheme/cbc:CompanyID', ns)

    # Errores detallados
    errores = []
    for linea in root.findall('.//cac:LineResponse', ns):
        code = linea.find('.//cbc:ResponseCode', ns)
        desc = linea.find('.//cbc:Description', ns)
        if code is not None and desc is not None:
            errores.append(f"{code.text} - {desc.text}")

    datos.append({
        "archivo": archivo,
        "factura_id": factura_id.text if factura_id is not None else None,
        "cufe": cufe.text if cufe is not None else None,
        "val_code": val_code.text if val_code is not None else None,
        "val_desc": val_desc.text if val_desc is not None else None,
        "fecha_validacion": val_fecha.text if val_fecha is not None else None,
        "hora_validacion": val_hora.text if val_hora is not None else None,
        "nit_emisor": emisor.text if emisor is not None else None,
        "nit_receptor": receptor.text if receptor is not None else None,
        "errores_xml": " | ".join(errores)
    })

# === EXPORTAR A CSV ===
df = pd.DataFrame(datos)
df.to_csv("xml_extraidos.csv", index=False, encoding="utf-8-sig")
print("✅ Extracción finalizada. Guardado en xml_extraidos.csv")
