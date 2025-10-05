import os
import shutil

def mover_archivos_rips(carpeta_origen, carpeta_destino):
    """
    Busca archivos JSON con 'Rips' en su nombre y los mueve a una carpeta de destino.

    Args:
        carpeta_origen (str): La ruta de la carpeta donde se inicia la búsqueda.
        carpeta_destino (str): La ruta de la carpeta a la que se moverán los archivos.
    """
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    for ruta_actual, directorios, archivos in os.walk(carpeta_origen):
        for nombre_archivo in archivos:
            if nombre_archivo.endswith('.json') and 'Rips' in nombre_archivo:
                ruta_archivo_completa = os.path.join(ruta_actual, nombre_archivo)
                shutil.move(ruta_archivo_completa, carpeta_destino)
                print(f"Archivo movido: {nombre_archivo}")

# Define las rutas de las carpetas
carpeta_origen = r'C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\FEV_JSON-20250807T191037Z-1-001\FEV_JSON'
carpeta_destino = r'C:\Users\yasmi\OneDrive\Documentos\PIPELINE_FACTUR\FEV_JSON-20250807T191037Z-1-001\rips'

# Llama a la función para ejecutar el script
mover_archivos_rips(carpeta_origen, carpeta_destino)

print("Proceso completado. ✅")