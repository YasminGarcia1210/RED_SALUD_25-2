import os
import pdfplumber

# --- LA CORRECCIÓN ESTÁ AQUÍ ---
# Se cambia la importación para que apunte correctamente a la carpeta hev_extractor
from hev_extractor.extractor import (
    extract_cups,
    extract_diagnostico_principal,
    was_service_given,
    extract_fecha_atencion,
    extract_documento_paciente,
    extract_sexo,
)

# Ruta de la carpeta donde están las HEV
carpeta_hev = r"C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\pipeline_facturacion\input\hev"

# Obtener los primeros 5 archivos PDF
archivos_hev = [f for f in os.listdir(carpeta_hev) if f.endswith(".pdf")][:5]

# Procesar cada archivo HEV
for archivo in archivos_hev:
    ruta_pdf = os.path.join(carpeta_hev, archivo)
    print(f"\n🔎 Procesando archivo: {archivo}")

    with pdfplumber.open(ruta_pdf) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Aplicar funciones de extracción (con los nombres corregidos)
    cups = extract_cups(text)
    diag_cod = extract_diagnostico_principal(text)
    prestado, evidencia = was_service_given(text)
    fecha = extract_fecha_atencion(text)
    tipo_doc, num_doc = extract_documento_paciente(text)
    sexo = extract_sexo(text)

    # Imprimir resultados
    print("🩺 Resultado del análisis de HEV\n")

    if prestado:
        print(f"✅ Evidencia de atención prestada:\n📝 \"{evidencia}\"\n")
    elif prestado is False:
        print(f"⚠️ Se detectó que NO se prestó el servicio:\n🚫 \"{evidencia}\"\n")
    else:
        print("❔ No se pudo determinar si se prestó el servicio.\n")

    print(f"✅ CUPS encontrados: {cups}")
    print("📌 Diagnóstico principal:")
    print(f"   🧬 Código: {diag_cod}")
    print("   📝 Descripción: No se extrajo una descripción específica en este script.")
    print("   📄 Tipo: No se extrajo el tipo en este script.")

    print(f"📅 Fecha de atención: {fecha}")
    print(f"🆔 Documento del paciente: {tipo_doc} {num_doc}")
    print(f"🚻 Sexo: {sexo}")
    print(f"🧾 Servicio prestado: {'Sí' if prestado else 'No' if prestado is False else 'Indeterminado'}")
    print("\n--- Fin del análisis de esta HEV ---")