from fastapi import FastAPI, Query, UploadFile, File, Form, HTTPException
from db import init_db, save_message, fetch_messages
from storage import upload_file_to_minio, read_text_from_minio
import requests
import os
import json

app = FastAPI(title="Ripsy Chatbot - MVP")

# =======================
# CONFIGURACIÓN
# =======================
# Dirección de Ollama en tu host (Docker lo llama así)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

# Claves para leer los archivos en MinIO (definidos en tu .env)
SYSTEM_PROMPT_KEY = os.getenv("SYSTEM_PROMPT_KEY", "config/prompt_ripsy.txt")
GLOSSARY_KEY = os.getenv("GLOSSARY_KEY", "config/glosario_salud.txt")

# Prompt de respaldo (por si no se logra leer MinIO al iniciar)
DEFAULT_PROMPT_FALLBACK = (
    "Eres Ripsy 💙, un asistente experto en facturación en salud en Colombia. "
    "Responde únicamente sobre RIPS, radicación de facturas, auditoría y glosas en el sector salud colombiano. "
    "Si la pregunta no es de salud, responde: "
    "\"Lo siento, solo puedo responder sobre temas de facturación en salud en Colombia.\""
)

# Variables globales (se cargan al iniciar)
SYSTEM_PROMPT = DEFAULT_PROMPT_FALLBACK
GLOSSARY_TEXT = ""


# =======================
# UTILS
# =======================
def chunk_text(text: str, max_chars: int = 3500):
    """
    Divide un texto largo en fragmentos para no exceder el límite de contexto del modelo.
    """
    text = (text or "").strip()
    if not text:
        return []
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


# =======================
# EVENTO DE INICIO
# =======================
@app.on_event("startup")
def on_startup():
    """
    Al iniciar FastAPI:
    - Inicializa la base de datos (crea tabla messages si no existe).
    - Carga el prompt y el glosario desde MinIO.
    """
    init_db()
    global SYSTEM_PROMPT, GLOSSARY_TEXT

    # Prompt base
    try:
        SYSTEM_PROMPT = read_text_from_minio(SYSTEM_PROMPT_KEY)
        print(f"✅ System prompt cargado: {SYSTEM_PROMPT_KEY} (len={len(SYSTEM_PROMPT)})")
    except Exception as e:
        SYSTEM_PROMPT = DEFAULT_PROMPT_FALLBACK
        print(f"⚠️ No pude leer prompt de MinIO, uso fallback. Error: {e}")

    # Glosario adicional
    try:
        GLOSSARY_TEXT = read_text_from_minio(GLOSSARY_KEY)
        print(f"✅ Glosario cargado: {GLOSSARY_KEY} (len={len(GLOSSARY_TEXT)})")
    except Exception as e:
        GLOSSARY_TEXT = ""
        print(f"⚠️ No pude leer glosario de MinIO. Error: {e}")


# =======================
# HOME
# =======================
@app.get("/")
def read_root():
    return {"ok": True, "message": "Hola, soy Ripsy 💙. Tu chatbot está corriendo."}


# =======================
# OPENAI ENDPOINTS - ACTIVADOS ✅
# =======================
from llm import generate_reply, test_openai_connection

@app.post("/chat")
def chat(payload: dict):
    """
    Endpoint principal de conversación usando OpenAI GPT.
    """
    user = payload.get("user", "desconocido")
    message = payload.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Falta 'message' en el payload")

    history = fetch_messages(limit=10)
    reply = generate_reply(user, message, history)  # OpenAI
    save_message(user, message, reply)

    return {"ok": True, "user": user, "message_recibido": message, "respuesta": reply}

@app.get("/test-openai")
def test_openai():
    """
    Prueba la conexión con OpenAI.
    """
    return test_openai_connection()


# =======================
# CHAT (LLAMA + PROMPT + GLOSARIO)
# =======================
@app.post("/chat-llama")
def chat_llama(payload: dict):
    """
    Endpoint principal de conversación usando Llama3 + prompt base + glosario.
    """
    user = payload.get("user", "desconocido")
    message = payload.get("message", "")

    if not message:
        raise HTTPException(status_code=400, detail="Falta 'message' en el payload")

    # Construir el contexto
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inyectar glosario en fragmentos (cada uno es un "system message")
    if GLOSSARY_TEXT:
        for idx, chunk in enumerate(chunk_text(GLOSSARY_TEXT, 3500), start=1):
            messages.append({
                "role": "system",
                "content": f"📚 Glosario de salud (fragmento {idx}):\n{chunk}"
            })

    # Mensaje del usuario
    messages.append({"role": "user", "content": message})

    # Llamar a Ollama
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "llama3",
                "messages": messages,
                "options": {"num_ctx": 4096}  # aumentar contexto si el modelo lo soporta
            },
            stream=True,  # Ollama devuelve JSON por línea
            timeout=30  # 👈 timeout para evitar cuelgues
        )
        resp.raise_for_status()

        # Procesar respuesta por streaming
        reply_parts = []
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        reply_parts.append(data["message"]["content"])
                except json.JSONDecodeError:
                    continue  # 👈 ignorar líneas malformadas

        reply = "".join(reply_parts).strip()
        if not reply:
            reply = "Lo siento, no recibí respuesta de Llama3."
            
    except requests.exceptions.ConnectionError:
        reply = "❌ Error: No se puede conectar con Ollama. Verifica que esté ejecutándose."
    except requests.exceptions.Timeout:
        reply = "❌ Error: Timeout esperando respuesta de Llama3."
    except requests.exceptions.RequestException as e:
        reply = f"❌ Error de conexión con Ollama: {e}"
    except Exception as e:
        reply = f"❌ Error inesperado: {e}"

    # Guardar en la base de datos
    save_message(user, message, reply)

    return {
        "ok": True,
        "user": user,
        "message_recibido": message,
        "respuesta": reply
    }


# =======================
# ENDPOINTS DE RECARGA
# =======================
@app.post("/config/reload-prompt")
def reload_prompt():
    """
    Recarga solo el prompt del sistema desde MinIO.
    """
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = read_text_from_minio(SYSTEM_PROMPT_KEY)
    return {"ok": True, "key": SYSTEM_PROMPT_KEY, "chars": len(SYSTEM_PROMPT)}

@app.post("/config/reload-glossary")
def reload_glossary():
    """
    Recarga solo el glosario desde MinIO.
    """
    global GLOSSARY_TEXT
    GLOSSARY_TEXT = read_text_from_minio(GLOSSARY_KEY)
    return {"ok": True, "key": GLOSSARY_KEY, "chars": len(GLOSSARY_TEXT)}

@app.post("/config/reload")
def reload_both():
    """
    Recarga prompt y glosario de MinIO en un solo llamado.
    """
    global SYSTEM_PROMPT, GLOSSARY_TEXT
    SYSTEM_PROMPT = read_text_from_minio(SYSTEM_PROMPT_KEY)
    GLOSSARY_TEXT = read_text_from_minio(GLOSSARY_KEY)
    return {
        "ok": True,
        "prompt_key": SYSTEM_PROMPT_KEY, "prompt_chars": len(SYSTEM_PROMPT),
        "glossary_key": GLOSSARY_KEY, "glossary_chars": len(GLOSSARY_TEXT)
    }


# =======================
# HISTORIAL DE MENSAJES
# =======================
@app.get("/messages")
def get_messages(limit: int = Query(20, ge=1, le=200)):
    """
    Devuelve los últimos 'limit' mensajes guardados en la base de datos.
    """
    return {"count": limit, "items": fetch_messages(limit)}


# =======================
# DOCUMENTOS
# =======================
@app.post("/documents/upload")
def upload_document(file: UploadFile = File(...), folder: str = Form("facturas")):
    """
    Sube un archivo a MinIO en la carpeta indicada dentro del bucket 'documentos'.
    Ejemplo: folder = facturas, historias_clinicas, rips_json, soportes
    """
    # 👈 Validar que el archivo tenga nombre
    if not file.filename:
        raise HTTPException(status_code=400, detail="El archivo debe tener un nombre")
    
    # 👈 Validar tipos de archivo permitidos
    allowed_extensions = {'.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.json', '.xml'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no permitido. Extensiones válidas: {allowed_extensions}"
        )
    
    # 👈 Validar tamaño del archivo (máximo 10MB)
    file.file.seek(0, 2)  # Ir al final del archivo
    file_size = file.file.tell()
    file.file.seek(0)  # Volver al inicio
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 10MB")
    
    file_name = file.filename
    result = upload_file_to_minio(file.file, file_name, folder)
    return {"ok": True, "folder": folder, "file": file_name, "message": result}

@app.get("/documents/list")
def list_documents(folder: str = Query("facturas")):
    """
    Lista archivos dentro de una carpeta del bucket 'documentos'.
    """
    from storage import list_files_in_folder
    files = list_files_in_folder(folder)
    return {"ok": True, "folder": folder, "files": files}
