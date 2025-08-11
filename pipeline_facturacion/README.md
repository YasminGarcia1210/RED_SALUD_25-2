📄 Proyecto: Automatización de RIPS
Este proyecto es una solución en Python para automatizar la generación y validación de archivos RIPS (Registros Individuales de Prestación de Servicios de Salud) a partir de documentos de entrada como facturas (XML), validaciones (JSON) e historias clínicas electrónicas (PDF).

🏛️ Arquitectura del Proyecto

La estructura de carpetas está organizada para manejar el flujo de trabajo de manera clara:

.
├── FEV_JSON-20250807T191037Z-1-001/
│   └── rips/
│       └── FERO941728_Rips.json
│       └── ...
├── pipeline_facturacion/
│   ├── hev_extractor/
│   │   ├── extractor.py           # Funciones de extracción de datos
│   │   └── generar_rips.py        # Script principal de generación
│   ├── input/
│   │   ├── cuv/
│   │   │   └── FERO941728_CUV.json
│   │   │   └── ...
│   │   ├── fev/
│   │   │   └── FERO941728.xml
│   │   │   └── ...
│   │   └── hev/
│   │       └── HEV_805027337_FERO941728.pdf
│   │       └── ...
│   ├── output/
│   │   └── rips/
│   │       └── (Aquí se guardan los RIPS generados)
│   ├── scripts/
│   │   └── probar_extractor.py    # Script de prueba para el extractor
│   └── validar_rips.py            # Script para validar los RIPS
└── reporte_rips_comparacion.csv   # Reporte de los resultados

🐍 Librerías Utilizadas
Asegúrate de tener estas librerías instaladas para que los scripts funcionen.

os: Para interactuar con el sistema de archivos (navegar por carpetas, listar archivos).

json: Para trabajar con archivos en formato JSON.

xml.etree.ElementTree: Para parsear y extraer datos de los archivos XML.

pdfplumber: Para extraer texto de los archivos PDF.

pandas: Para manejar y generar el reporte de validación en formato CSV.

re: Para usar expresiones regulares y extraer patrones de texto.

Puedes instalarlas todas con el siguiente comando:
pip install pdfplumber pandas

🚀 Paso a Paso: Flujo de Trabajo
1. Generar los RIPS
Ejecuta este script para generar los archivos RIPS en la carpeta output/rips.

Comando:

python pipeline_facturacion/hev_extractor/generar_rips.py

Función del script:

Lee los archivos XML (fev), JSON (cuv) y PDF (hev).

Usa las funciones de extractor.py para obtener datos como CUPS, diagnósticos, datos del paciente y del profesional.

Genera un archivo [numero_factura]_Rips.json con la información consolidada.

2. Validar los RIPS
Ejecuta este script para comparar los RIPS generados con los RIPS reales del hospital.

Comando:

python pipeline_facturacion/validar_rips.py

Función del script:

Compara los archivos en las carpetas pipeline_facturacion/output/rips (generados) y FEV_JSON-20250807T191037Z-1-001/rips (reales).

Genera un archivo reporte_rips_comparacion.csv con los resultados.

El reporte indica si los archivos coinciden, el porcentaje de coincidencia y las diferencias encontradas. También lista las facturas para las que no se generó un RIPS.

📝 Tareas Pendientes
Aunque el script funciona, hay algunas áreas de mejora para hacerlo aún más robusto:

Extraer el valor del servicio (vrServicio): Actualmente, se está usando un valor fijo (9000). Se debe crear una función en extractor.py para leer este valor del archivo XML (fev).

Manejar múltiples servicios por factura: El script actual asume un solo servicio por factura. Es necesario ajustar la lógica para procesar múltiples procedimientos en los archivos fev y hev.

Mejorar la extracción del codPrestador: Si bien el script ya no asume un valor, es importante encontrar un patrón más confiable en los documentos para extraer este código cuando esté disponible.

Refinar la extracción de tipo de usuario: El campo tipoUsuario se está asignando con un valor fijo ("01"). Este valor debería ser extraído del PDF del HEV o de un documento de referencia si está disponible.