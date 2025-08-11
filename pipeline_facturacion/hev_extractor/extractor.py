import os
import re
import json
import pdfplumber
import pandas as pd
from datetime import datetime

# === RUTAS DE ENTRADA Y SALIDA ===
carpeta_pdf = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\fact_pdf"
carpeta_xml = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\fact_xml"
carpeta_soportes = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\hev"
carpeta_salida = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\rips_json"

os.makedirs(carpeta_salida, exist_ok=True)

# === FUNCIONES EXTRACCIÓN ===

def extract_text_pdf(ruta_pdf):
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
    except:
        return ""

def extract_documento_paciente(text):
    match = re.search(r"\b(CC|TI|RC|AS|MS|PA|PE)\s+(\d{6,15})", text)
    if match:
        return match.group(1), match.group(2)
    match2 = re.search(r"Identificaci[oó]n:\s*(CC|TI|RC|AS|MS|PA|PE)\s*(\d{6,15})", text, re.IGNORECASE)
    if match2:
        return match2.group(1), match2.group(2)
    return None, None

def extract_fecha_nacimiento(text):
    match = re.search(r"Fecha de Nacimiento y Edad:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
        except:
            return None
    return None

def extract_sexo(text):
    match = re.search(r"G[eé]nero:\s*(Femenino|Masculino)", text, re.IGNORECASE)
    if match:
        return "F" if "femenino" in match.group(1).lower() else "M"
    return None

def extract_diagnostico_principal(text):
    match = re.search(r"DXP:\s*([A-Z]\d{2,4})", text)
    return match.group(1).strip() if match else None

def extract_fecha_atencion(text):
    match = re.search(r"Fecha y Hora de Ingreso:\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})", text)
    if match:
        try:
            fecha_obj = datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
            return f"{fecha_obj} {match.group(2)}"
        except:
            return None
    return None

def was_service_given(text):
    texto = text.lower()
    frases_validas = [
        "se realiza", "se aplica", "se entrega", "se vacuna",
        "se atiende", "se atendió", "se valoró", "valorado", "atendido",
        "control realizado", "se hace control", "consulta realizada", 
        "paciente asistió", "realiza control", "realiza cita", "evaluado",
        "intervención realizada", "procedimiento realizado", "vacuna aplicada",
        "se ejecuta", "cita completada", "se cumplió", "realiza procedimiento",
        "se realiza la consulta", "se efectúa", "cita atendida", "asistió",
        "presente", "se presentó", "consulta realizada", "realizó la consulta",
        "cumple con la cita", "cumple cita", "cumple control"
    ]

    frases_no_atendido = [
        "no se presenta", "no asistió", "se cancela", "ausente",
        "cita no realizada", "no se realiza", "no se aplica", "paciente no viene",
        "cita cancelada", "no acude", "no acudió", "se inasiste", "inasistencia",
        "no se presentó", "cita incumplida", "no llega", "no asistió a cita",
        "paciente no asistió", "no se atiende", "no fue posible", 
        "se rechaza", "rechazada", "cita fallida", "no se ejecuta", "sin atención",
        "cita perdida", "no se completó", "no disponible", "no atendido",
        "cancelación", "cancelada por paciente", "no vino", "no pasó consulta"
    ]

    for f in frases_no_atendido:
        if f in texto:
            return False, f
    for f in frases_validas:
        if f in texto:
            i = texto.find(f)
            evidencia = text[max(0, i-40):i+60].strip().replace("\n", " ")
            return True, evidencia
    return None, None

def extract_cod_prestador(text):
    match = re.search(r"C[oó]digo prestador de servicio:\s*(\d{10})", text)
    if match:
        return match.group(1) + "01"
    return None

def normalizar_codigo_cups(codigo):
    codigo = re.sub(r"[^\d]", "", codigo)
    return (codigo[:6], codigo) if len(codigo) >= 6 else (codigo, codigo)

def extract_servicios(text):
    pattern = re.compile(r"(\d{6,8})\s+-\s+([A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s\-]+)")
    return pattern.findall(text)

# === BUCLE PRINCIPAL ===

for archivo in os.listdir(carpeta_soportes):
    if not archivo.endswith(".pdf"):
        continue

    match = re.search(r"(FERO\d{6})", archivo)
    if not match:
        continue

    num_factura = match.group(1)
    ruta_pdf = os.path.join(carpeta_soportes, archivo)
    texto = extract_text_pdf(ruta_pdf)

    tipo_doc, num_doc = extract_documento_paciente(texto)
    fecha_nac = extract_fecha_nacimiento(texto)
    sexo = extract_sexo(texto)
    dxp = extract_diagnostico_principal(texto)
    fecha_aten = extract_fecha_atencion(texto)
    cod_prestador = extract_cod_prestador(texto)
    servicio_ok, detalle = was_service_given(texto)

    # === DETECTAR INASISTENCIA ===
    if servicio_ok is False:
        accion = (
            "Emitida: Generar nota crédito total/parcial"
            if os.path.exists(os.path.join(carpeta_pdf, f"{num_factura}.pdf"))
            else "No emitida: Registrar como cita no efectiva"
        )
        fila = {
            "Factura": num_factura,
            "Motivo": detalle or "Frase negativa detectada",
            "Acción recomendada": accion
        }
        path_csv = os.path.join(carpeta_salida, "facturas_no_atendidas.csv")
        if os.path.exists(path_csv):
            df = pd.read_csv(path_csv)
            df = df.append(fila, ignore_index=True)
        else:
            df = pd.DataFrame([fila])
        df.to_csv(path_csv, index=False, encoding="utf-8-sig")
        print(f"❌ Omite RIPS por inasistencia: {num_factura}")
        continue

    # === SERVICIOS ===
    servicios_extraidos = extract_servicios(texto)
    procedimientos = []
    for cod, desc in servicios_extraidos:
        cod_proc, subcod = normalizar_codigo_cups(cod)
        procedimientos.append({
            "codProcedimiento": cod_proc,
            "subCodigo": subcod,
            "descripcion": desc.strip(),
            "codPrestador": cod_prestador
        })

    usuario = {
        "tipoDocumentoIdentificacion": tipo_doc,
        "numDocumentoIdentificacion": num_doc,
        "fechaNacimiento": fecha_nac,
        "codSexo": sexo,
        "codDiagnosticoPrincipal": dxp,
        "fechaInicioAtencion": fecha_aten,
        "servicioPrestado": servicio_ok,
        "detalle": detalle,
        "servicios": {
            "procedimientos": procedimientos,
            "consultas": [],
            "medicamentos": [],
            "otrosServicios": []
        }
    }

    salida = {
        "numFactura": num_factura,
        "numDocumentoIdObligado": "805027337",
        "usuarios": [usuario]
    }

    with open(os.path.join(carpeta_salida, f"{num_factura}_Rips.json"), "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(f"✅ Generado: {num_factura}_Rips.json")
