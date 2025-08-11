import os
import json
import xml.etree.ElementTree as ET
import pdfplumber

# La importación es local porque 'extractor.py' está en la misma carpeta.
from extractor import (
    extract_cups,
    extract_diagnostico_principal,
    extract_fecha_atencion,
    extract_documento_paciente,
    extract_sexo,
    extract_fecha_nacimiento,
    extract_nit_obligado,
    extract_cod_prestador,
    extraer_cups_de_json,
    extract_documento_profesional
)

# --- Rutas de entrada y salida ---
# 🔥 ¡ATENCIÓN A ESTA LÍNEA! Ruta corregida para que coincida con el error
base_path = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion"

rutas = {
    "carpeta_cuv": os.path.join(base_path, "input", "cuv"),
    "carpeta_fev": os.path.join(base_path, "input", "fev"),
    "carpeta_hev": os.path.join(base_path, "input", "hev"),
    "carpeta_salida_rips": os.path.join(base_path, "output", "rips")
}

# Crear la carpeta de salida si no existe
if not os.path.exists(rutas["carpeta_salida_rips"]):
    os.makedirs(rutas["carpeta_salida_rips"])
    print(f"📁 Creada carpeta de salida: {rutas['carpeta_salida_rips']}")

# --- Lógica principal del script ---
def procesar_facturas_y_generar_rips():
    """
    Recorre los archivos en la carpeta FEV (XML), extrae la información
    de los archivos CUV (JSON) y HEV (PDF) correspondientes,
    y genera un Rips.json para cada factura.
    """
    try:
        archivos_fev = os.listdir(rutas["carpeta_fev"])
    except FileNotFoundError:
        print(f"❌ ERROR: La carpeta de archivos FEV no se encontró en la ruta: {rutas['carpeta_fev']}. Verifica la ruta base.")
        return

    for archivo_xml in archivos_fev:
        if archivo_xml.endswith(".xml"):
            ruta_xml = os.path.join(rutas["carpeta_fev"], archivo_xml)
            try:
                tree = ET.parse(ruta_xml)
                root = tree.getroot()
                num_factura_completa = root.findtext(".//{*}ID") 
                
                if num_factura_completa and num_factura_completa.startswith('ad'):
                    num_factura = num_factura_completa[2:]
                else:
                    num_factura = num_factura_completa
                
            except Exception as e:
                print(f"❌ Error al leer XML {archivo_xml}: {e}")
                continue

            if not num_factura:
                print(f"⚠️ No se pudo extraer el número de factura del XML {archivo_xml}. Saltando...")
                continue
            
            print(f"\n🔎 Procesando factura: {num_factura}...")

            ruta_hev = None
            for filename in os.listdir(rutas["carpeta_hev"]):
                if filename.endswith(".pdf") and num_factura in filename:
                    ruta_hev = os.path.join(rutas["carpeta_hev"], filename)
                    break

            if not ruta_hev or not os.path.exists(ruta_hev):
                print(f"⚠️ No se encontró el archivo HEV para la factura {num_factura}. Saltando...")
                continue

            try:
                with pdfplumber.open(ruta_hev) as pdf:
                    text_hev = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            except Exception as e:
                print(f"❌ Error al leer el PDF {ruta_hev}: {e}")
                continue

            # Extracción de todos los datos necesarios
            tipo_doc_paciente, num_doc_paciente = extract_documento_paciente(text_hev)
            sexo_paciente = extract_sexo(text_hev)
            fecha_nacimiento_paciente = extract_fecha_nacimiento(text_hev)
            nit_obligado = extract_nit_obligado(text_hev)
            cod_prestador = extract_cod_prestador(text_hev)
            
            tipo_doc_profesional, num_doc_profesional = extract_documento_profesional(text_hev)

            cod_diagnostico_principal = extract_diagnostico_principal(text_hev)
            fecha_atencion = extract_fecha_atencion(text_hev)
            
            ruta_cuv = os.path.join(rutas["carpeta_cuv"], f"{num_factura}_CUV.json")
            cups_cuv = extraer_cups_de_json(ruta_cuv) if os.path.exists(ruta_cuv) else []
            cups_hev = extract_cups(text_hev)
            lista_cups = list(set(cups_cuv + cups_hev))
            
            if not lista_cups or not cod_diagnostico_principal:
                print(f"⚠️ Faltan datos clave (CUPS o Diagnóstico) para la factura {num_factura}. Saltando...")
                continue

            # Creación de la estructura del RIPS
            procedimientos = []
            for i, cups in enumerate(lista_cups):
                procedimiento = {
                    "idMIPRES": None,
                    "vrServicio": 9000, 
                    "codServicio": 328,
                    "consecutivo": i + 1,
                    "codPrestador": cod_prestador,
                    "grupoServicios": "02",
                    "codComplicacion": None,
                    "conceptoRecaudo": "05",
                    "numAutorizacion": None,
                    "codProcedimiento": cups,
                    "valorPagoModerador": 0,
                    "fechaInicioAtencion": fecha_atencion,
                    "numFEVPagoModerador": None,
                    "codDiagnosticoPrincipal": cod_diagnostico_principal,
                    "viaIngresoServicioSalud": "02",
                    "finalidadTecnologiaSalud": "14",
                    "codDiagnosticoRelacionado": None,
                    "numDocumentoIdentificacion": num_doc_profesional,
                    "tipoDocumentoIdentificacion": tipo_doc_profesional,
                    "modalidadGrupoServicioTecSal": "01"
                }
                procedimientos.append(procedimiento)

            rips_data = {
                "numNota": None,
                "tipoNota": None,
                "usuarios": [
                    {
                        "codSexo": sexo_paciente,
                        "servicios": {"procedimientos": procedimientos},
                        "consecutivo": 1,
                        "incapacidad": "NO",
                        "tipoUsuario": "01",
                        "codPaisOrigen": "170",
                        "fechaNacimiento": fecha_nacimiento_paciente,
                        "codPaisResidencia": "170",
                        "codMunicipioResidencia": "76001",
                        "numDocumentoIdentificacion": num_doc_paciente, 
                        "tipoDocumentoIdentificacion": tipo_doc_paciente,
                        "codZonaTerritorialResidencia": "02"
                    }
                ],
                "numFactura": num_factura,
                "numDocumentoIdObligado": nit_obligado
            }

            # Guardar el archivo RIPS generado
            nombre_salida = f"{num_factura}_Rips.json"
            ruta_salida = os.path.join(rutas["carpeta_salida_rips"], nombre_salida)
            
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(rips_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ RIPS generado con éxito: {nombre_salida}")

# Ejecutar el proceso
procesar_facturas_y_generar_rips()
print("\n--- Proceso de generación de RIPS finalizado ---")