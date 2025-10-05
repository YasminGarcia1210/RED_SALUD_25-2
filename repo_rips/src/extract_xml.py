import os
import re
import csv
import xml.etree.ElementTree as ET
from datetime import datetime

def sin_decimales(valor):
    if not valor:
        return ""
    s = valor.strip()
    if s.replace(".", "", 1).isdigit() and "." in s:
        entero, dec = s.split(".", 1)
        if set(dec) <= {"0"}:
            return entero
    return s

def extraer_campos_factura_xml(xml_path):
    campos = {
        'numero_factura': "",
        'fecha_emision': "",
        'identificacion': "",
        'tipo_documento': "CC",  # por defecto
        'codigo_servicio': "",
        'descripcion_servicio': "",
        'valor_servicio': "",
        'codigo_prestador': ""
    }
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # En muchos casos el XML tiene namespaces
        ns = {k if k else '': v for k, v in [node for _, node in ET.iterparse(xml_path, events=['start-ns'])]}

        # --- Número de factura ---
        num_fac = root.find(".//{*}ID")
        if num_fac is not None and num_fac.text:
            campos['numero_factura'] = num_fac.text.strip()

        # --- Fecha de emisión ---
        fecha = root.find(".//{*}IssueDate")
        if fecha is not None and fecha.text:
            campos['fecha_emision'] = fecha.text.strip()

        # --- Código prestador ---
        prestador = root.find(".//{*}AccountingSupplierParty//{*}ID")
        if prestador is not None and prestador.text:
            campos['codigo_prestador'] = sin_decimales(prestador.text.strip())

        # --- Identificación ---
        ident = root.find(".//{*}AccountingCustomerParty//{*}ID")
        if ident is not None and ident.text:
            campos['identificacion'] = ident.text.strip()

        # --- Tipo documento ---
        tipo_doc = root.find(".//{*}AccountingCustomerParty//{*}AdditionalAccountID")
        if tipo_doc is not None and tipo_doc.text:
            campos['tipo_documento'] = tipo_doc.text.strip().upper()

        # --- Servicios ---
        codigos, descripciones, valores = [], [], []

        for item in root.findall(".//{*}InvoiceLine"):
            # Código servicio
            codigo = item.find(".//{*}ItemIdentification//{*}ID")
            if codigo is not None and codigo.text:
                cod_limpio = sin_decimales(codigo.text.strip())
                if cod_limpio not in codigos:
                    codigos.append(cod_limpio)

            # Descripción
            descripcion = item.find(".//{*}Description")
            if descripcion is not None and descripcion.text:
                descripciones.append(descripcion.text.strip())

            # Valor unitario (PriceAmount)
            valor = item.find(".//{*}PriceAmount")
            if valor is not None and valor.text:
                valores.append(valor.text.strip())

        campos['codigo_servicio'] = ",".join(codigos)
        campos['descripcion_servicio'] = ",".join(descripciones)
        campos['valor_servicio'] = ",".join(valores)

    except Exception as e:
        print(f"❌ Error procesando {xml_path}: {e}")

    return campos

def procesar_xmls(ruta_carpeta):
    resultados = {}
    archivos_xml = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(".xml")]
    for archivo in archivos_xml:
        ruta = os.path.join(ruta_carpeta, archivo)
        resultados[archivo] = {'campos_extraidos': extraer_campos_factura_xml(ruta)}
        print(f"✅ Procesado: {archivo}")
    return resultados

def guardar_csv(datos, ruta_salida):
    columnas = [
        'archivo', 'numero_factura', 'fecha_emision', 'identificacion', 'tipo_documento',
        'codigo_servicio', 'descripcion_servicio', 'valor_servicio', 'codigo_prestador'
    ]
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with open(ruta_salida, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for archivo, info in datos.items():
            fila = {'archivo': archivo}
            fila.update(info.get('campos_extraidos', {}))
            writer.writerow(fila)
    print(f"CSV guardado en: {ruta_salida}")

if __name__ == "__main__":
    ruta_xml = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\repo_rips\data\input\fact_xml"
    ruta_salida = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\repo_rips\data\output\control"
    datos = procesar_xmls(ruta_xml)
    nombre_csv = f"control_xml_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    guardar_csv(datos, os.path.join(ruta_salida, nombre_csv))
