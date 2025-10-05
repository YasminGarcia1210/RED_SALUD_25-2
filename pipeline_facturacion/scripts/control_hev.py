import os
import re
import pandas as pd
import pdfplumber
from datetime import datetime

# === RUTAS DE ENTRADA Y SALIDA ===
carpeta_soportes = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\hev"
carpeta_salida_control = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\control"

os.makedirs(carpeta_salida_control, exist_ok=True)

# Lista para almacenar los datos extraídos
datos_control = []

# === FUNCIONES DE EXTRACCIÓN ===

def extract_text_pdf(ruta_pdf):
    """Extrae todo el texto de un PDF usando pdfplumber."""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
    except Exception as e:
        print(f"Error al extraer texto de {ruta_pdf}: {e}")
        return ""

def extract_documento_paciente(text):
    """Extrae el tipo y número de documento del paciente."""
    match = re.search(r"^\s*(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})", text, re.MULTILINE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    match_alt = re.search(r"Identificaci[oó]n:\s*\n\s*(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})", text, re.IGNORECASE)
    if match_alt:
        return match_alt.group(1).strip(), match_alt.group(2).strip()
    
    return None, None

def extract_fecha_nacimiento(text):
    """Extrae la fecha de nacimiento del paciente."""
    match = re.search(r"Fecha de Nacimiento y Edad:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
        except:
            return None
    return None

def extract_sexo(text):
    """Extrae el género del paciente."""
    match = re.search(r"G[eé]nero:\s*(Femenino|Masculino)", text, re.IGNORECASE)
    if match:
        return "F" if "femenino" in match.group(1).lower() else "M"
    return None

def extract_procedimientos(text):
    """Extrae códigos, nombres y descripciones de procedimientos."""
    codigos = []
    nombres = []
    descripciones = []
    
    patron_procedimiento = re.compile(
        r"Cod:\s*(\d{6,8})\s+Nomb:\s*(.*?)\s+Cant:.*?Descripción:\s*(.*?)(?=\nFecha y Hora:|\nAtendido Por:|\Z)", 
        re.DOTALL | re.IGNORECASE
    )

    matches = patron_procedimiento.finditer(text)
    
    for match in matches:
        cod_completo, nomb_procedimiento, descripcion = match.groups()
        
        cod_procedimiento = cod_completo[:6] if len(cod_completo) >= 6 else cod_completo

        codigos.append(cod_procedimiento.strip())
        nombres.append(nomb_procedimiento.strip())
        descripciones.append(descripcion.strip().replace('\n', ' ').replace(' ,', ',').replace(' .', '.').replace('  ', ' '))
        
    return ", ".join(codigos), ", ".join(nombres), ", ".join(descripciones)

# === BUCLE PRINCIPAL ===
# Procesar cada archivo PDF en la carpeta de soportes
for archivo_soporte in os.listdir(carpeta_soportes):
    if not archivo_soporte.endswith(".pdf"):
        continue

    # Extraer el número de factura (FEROxxxxxx) del nombre del archivo
    match_factura = re.search(r"FERO(\d{6})", archivo_soporte)
    if not match_factura:
        continue
    
    num_factura = f"FERO{match_factura.group(1)}"
    ruta_soporte = os.path.join(carpeta_soportes, archivo_soporte)
    
    print(f"Procesando documento de soporte: {archivo_soporte}")
    texto_soporte = extract_text_pdf(ruta_soporte)
    
    if not texto_soporte:
        print(f"❌ No se pudo extraer texto de {archivo_soporte}")
        continue
        
    # Extraer datos del paciente
    tipo_doc, num_doc = extract_documento_paciente(texto_soporte)
    fecha_nac = extract_fecha_nacimiento(texto_soporte)
    sexo = extract_sexo(texto_soporte)
    
    # Extraer datos de los procedimientos
    cod_procedimiento_str, nomb_procedimiento_str, descripcion_str = extract_procedimientos(texto_soporte)

    # Identificar el tipo de soporte (HEV, PDE, PDX, etc.)
    tipo_soporte_encontrado = "No identificado"
    if archivo_soporte.upper().startswith("HEV"):
        tipo_soporte_encontrado = "HEV"
    elif archivo_soporte.upper().startswith("PDE"):
        tipo_soporte_encontrado = "PDE"
    elif archivo_soporte.upper().startswith("PDX"):
        tipo_soporte_encontrado = "PDX"

    # === Agregar una única fila a la tabla de control ===
    datos_control.append({
        "numFactura": num_factura,
        "tipoDocumentoIdentificacion": tipo_doc,
        "numDocumentoIdentificacion": num_doc,
        "fechaNacimiento": fecha_nac,
        "codSexo": sexo,
        "codProcedimiento": cod_procedimiento_str,
        "nombProcedimiento": nomb_procedimiento_str,
        "descripcionServicio": descripcion_str,
        "Soporte Encontrado": tipo_soporte_encontrado
    })

if datos_control:
    df_control = pd.DataFrame(datos_control)
    ruta_salida_csv = os.path.join(carpeta_salida_control, "control_HEV_datos.csv")
    df_control.to_csv(ruta_salida_csv, index=False, encoding="utf-8-sig")
    print(f"✅ Archivo de control CSV generado en: {ruta_salida_csv}")
else:
    print("⚠️ No se encontraron datos para generar el archivo de control.")