import os
from minio import Minio
from minio.error import S3Error
import io

# =======================
# CONFIGURACIÓN MINIO
# =======================
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000").replace("http://", "").replace("https://", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documentos")

# Cliente MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # HTTP para desarrollo
)

# =======================
# FUNCIONES DE MINIO
# =======================
def upload_file_to_minio(file_data, file_name: str, folder: str = "facturas"):
    """
    Sube un archivo a MinIO en el bucket especificado.
    
    Args:
        file_data: Datos del archivo (file-like object)
        file_name: Nombre del archivo
        folder: Carpeta dentro del bucket (prefijo)
    
    Returns:
        str: Mensaje de resultado
    """
    try:
        # Asegurar que el bucket existe
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
        
        # Construir el path completo
        object_name = f"{folder}/{file_name}"
        
        # Subir el archivo
        file_data.seek(0)  # Asegurar que estamos al inicio
        minio_client.put_object(
            MINIO_BUCKET,
            object_name,
            file_data,
            length=-1,  # Auto-detecta el tamaño
            part_size=10*1024*1024  # 10MB por parte
        )
        
        return f"✅ Archivo subido exitosamente: {object_name}"
        
    except S3Error as e:
        return f"❌ Error de MinIO: {e}"
    except Exception as e:
        return f"❌ Error subiendo archivo: {e}"

def read_text_from_minio(object_name: str) -> str:
    """
    Lee un archivo de texto desde MinIO.
    
    Args:
        object_name: Nombre del objeto en MinIO
    
    Returns:
        str: Contenido del archivo como texto
    """
    try:
        response = minio_client.get_object(MINIO_BUCKET, object_name)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return content
        
    except S3Error as e:
        if e.code == 'NoSuchKey':
            raise Exception(f"Archivo no encontrado: {object_name}")
        else:
            raise Exception(f"Error de MinIO: {e}")
    except Exception as e:
        raise Exception(f"Error leyendo archivo: {e}")

def list_files_in_folder(folder: str) -> list:
    """
    Lista archivos en una carpeta específica del bucket.
    
    Args:
        folder: Nombre de la carpeta (prefijo)
    
    Returns:
        list: Lista de archivos encontrados
    """
    try:
        objects = minio_client.list_objects(
            MINIO_BUCKET, 
            prefix=f"{folder}/",
            recursive=True
        )
        
        files = []
        for obj in objects:
            files.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified
            })
        
        return files
        
    except Exception as e:
        return [{"error": f"Error listando archivos: {e}"}]
