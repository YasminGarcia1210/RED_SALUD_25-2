import os
import re
import csv
import pdfplumber
from datetime import datetime

def sin_decimales(valor):
    """Convierte 123.0 o 123.00 en 123, deja el resto igual."""
    if not valor:
        return ""
    s = valor.strip()
    if s.replace(".", "", 1).isdigit() and "." in s:
        entero, dec = s.split(".", 1)
        if set(dec) <= {"0"}:
            return entero
    return s

def extraer_campos_factura(pdf_path):
    campos = {
        'numero_factura': "",
        'fecha_emision': "",
        'identificacion': "",
        'tipo_documento': "",
        'codigo_servicio': "",
        'descripcion_servicio': "",
        'valor_servicio': "",
        'codigo_prestador': ""
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto = "\n".join([p.extract_text() or "" for p in pdf.pages])

        # --- Número de factura ---
        m_fac = re.search(r"Factura electrónica de Venta\s+(FERO\d+)", texto, re.IGNORECASE)
        if m_fac:
            campos['numero_factura'] = m_fac.group(1).strip()

        # --- Fecha de emisión ---
        m_fecha = re.search(r"Fecha de Emision\s+([\d/]+)", texto, re.IGNORECASE)
        if m_fecha:
            campos['fecha_emision'] = m_fecha.group(1).strip()

        # --- Identificación ---
        m_ident = re.search(r"Identificacion:\s*([0-9]+)", texto, re.IGNORECASE)
        if m_ident:
            campos['identificacion'] = m_ident.group(1).strip()

        # --- Tipo de documento ---
        m_tipo = re.search(r"Tipo[\s\n]+([A-Z]{1,3})", texto, re.IGNORECASE)
        if m_tipo:
            campos['tipo_documento'] = m_tipo.group(1).strip().upper()

        # --- Código prestador ---
        m_prestador = re.search(r"C[oó]digo prestador (?:de servicio|de)\s*:?\s*([0-9.]+)", texto, re.IGNORECASE)
        if m_prestador:
            campos['codigo_prestador'] = sin_decimales(m_prestador.group(1))

        # --- Bloque de servicios ---
        bloque_servicios = ""
        inicio = re.search(r"Cod\. Prestador de servicios de", texto, re.IGNORECASE)
        fin = re.search(r"Firma Digital", texto, re.IGNORECASE)
        if inicio and fin:
            bloque_servicios = texto[inicio.end():fin.start()]

        codigos, descripciones, valores = [], [], []

        # Regex para todas las filas de servicios
        patron_servicio = re.compile(
            r"^([0-9A-Za-z\-]{3,})\s+(.+?)\s+\d+\s+\$?\s*([\d\.,]+)",
            re.MULTILINE
        )

        for codigo, desc, valor in patron_servicio.findall(bloque_servicios):
            codigo_limpio = sin_decimales(codigo)
            if codigo_limpio not in codigos:
                codigos.append(codigo_limpio)
                descripciones.append(desc.strip())
                valores.append(valor.replace(".", "").replace(",", ".").strip())

        campos['codigo_servicio'] = ",".join(codigos)
        campos['descripcion_servicio'] = ",".join(descripciones)
        campos['valor_servicio'] = ",".join(valores)

    except Exception as e:
        print(f"❌ Error procesando {pdf_path}: {e}")

    return campos

def procesar_pdfs(ruta_carpeta):
    resultados = {}
    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(".pdf")]
    for archivo in archivos_pdf:
        ruta = os.path.join(ruta_carpeta, archivo)
        resultados[archivo] = {'campos_extraidos': extraer_campos_factura(ruta)}
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
    ruta_pdf = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\repo_rips\data\input\fact_pdf"
    ruta_salida = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\repo_rips\data\output\control"
    datos = procesar_pdfs(ruta_pdf)
    nombre_csv = f"control_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    guardar_csv(datos, os.path.join(ruta_salida, nombre_csv))
