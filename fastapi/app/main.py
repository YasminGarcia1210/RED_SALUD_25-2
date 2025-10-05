from fastapi import FastAPI, Query, UploadFile, File, Form, HTTPException, Request
from db import init_db, save_message, fetch_messages
from storage import upload_file_to_minio, read_text_from_minio
import requests
import os
import json
import openai
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# ======================================================
# 🚀 CONFIGURACIÓN INICIAL
# ======================================================
app = FastAPI(title="Ripsy Chatbot - MVP")
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

SYSTEM_PROMPT_KEY = os.getenv("SYSTEM_PROMPT_KEY", "config/prompt_ripsy.txt")
GLOSSARY_KEY = os.getenv("GLOSSARY_KEY", "config/glosario_salud.txt")

DEFAULT_PROMPT_FALLBACK = (
    "Eres Ripsy 💙, un asistente experto en facturación en salud en Colombia. "
    "Responde únicamente sobre RIPS, radicación de facturas, auditoría y glosas. "
    "Si la pregunta no es de salud, responde: "
    "\"Lo siento, solo puedo responder sobre temas de facturación en salud en Colombia.\""
)

SYSTEM_PROMPT = DEFAULT_PROMPT_FALLBACK
GLOSSARY_TEXT = ""


# ======================================================
# 🔹 FUNCIONES UTILES
# ======================================================
def chunk_text(text: str, max_chars: int = 3500):
    """
    Divide texto en fragmentos pequeños (útil para glosarios largos)
    """
    text = (text or "").strip()
    if not text:
        return []
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


# ======================================================
# 🔹 EVENTO DE INICIO
# ======================================================
@app.on_event("startup")
def on_startup():
    """
    Al iniciar FastAPI:
    - Inicializa la base de datos
    - Carga el prompt y el glosario desde MinIO
    """
    init_db()
    global SYSTEM_PROMPT, GLOSSARY_TEXT

    try:
        SYSTEM_PROMPT = read_text_from_minio(SYSTEM_PROMPT_KEY)
        print(f"✅ Prompt cargado ({len(SYSTEM_PROMPT)} caracteres)")
    except Exception as e:
        SYSTEM_PROMPT = DEFAULT_PROMPT_FALLBACK
        print(f"⚠️ Error cargando prompt, usando fallback: {e}")

    try:
        GLOSSARY_TEXT = read_text_from_minio(GLOSSARY_KEY)
        print(f"✅ Glosario cargado ({len(GLOSSARY_TEXT)} caracteres)")
    except Exception as e:
        GLOSSARY_TEXT = ""
        print(f"⚠️ No se pudo leer glosario: {e}")


# ======================================================
# 🔹 ENDPOINTS PRINCIPALES
# ======================================================
@app.get("/")
def read_root():
    return {"ok": True, "message": "Hola, soy Ripsy 💙. Tu chatbot está corriendo."}


# ======================================================
# 🔹 CHAT OPENAI
# ======================================================
from llm import generate_reply, test_openai_connection

@app.post("/chat")
def chat(payload: dict):
    user = payload.get("user", "desconocido")
    message = payload.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Falta 'message' en el payload")

    history = fetch_messages(limit=10)
    reply = generate_reply(user, message, history)
    save_message(user, message, reply)
    return {"ok": True, "user": user, "respuesta": reply}


@app.get("/test-openai")
def test_openai():
    return test_openai_connection()


# ======================================================
# 🔹 CHAT LLAMA (modelo local)
# ======================================================
@app.post("/chat-llama")
def chat_llama(payload: dict):
    user = payload.get("user", "desconocido")
    message = payload.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Falta 'message' en el payload")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if GLOSSARY_TEXT:
        for idx, chunk in enumerate(chunk_text(GLOSSARY_TEXT, 3500), start=1):
            messages.append({
                "role": "system",
                "content": f"📚 Glosario de salud (fragmento {idx}):\n{chunk}"
            })
    messages.append({"role": "user", "content": message})

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": "llama3", "messages": messages, "options": {"num_ctx": 4096}},
            stream=True, timeout=30
        )
        resp.raise_for_status()

        reply_parts = []
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        reply_parts.append(data["message"]["content"])
                except json.JSONDecodeError:
                    continue
        reply = "".join(reply_parts).strip() or "Lo siento, no recibí respuesta de Llama3."
    except Exception as e:
        reply = f"❌ Error con Llama3: {e}"

    save_message(user, message, reply)
    return {"ok": True, "user": user, "respuesta": reply}


# ======================================================
# 🧠 ENDPOINT RAG: CONSULTAR NORMAS
# ======================================================
@app.post("/consultar-normas")
async def consultar_normas(request: Request):
    """
    Usa embeddings para buscar y responder basándose en las normas vectorizadas.
    """
    body = await request.json()
    pregunta = body.get("message")

    if not pregunta:
        raise HTTPException(status_code=400, detail="Debe incluir 'message' en el body")

    # 1️⃣ Crear embedding de la pregunta
    emb_res = openai.embeddings.create(
        model="text-embedding-3-small",
        input=pregunta
    )
    emb_vector = emb_res.data[0].embedding

    # 2️⃣ Buscar los fragmentos más parecidos
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT filename, chunk,
               1 - (embedding <=> %s::vector) AS similarity
        FROM normativas_embeddings
        ORDER BY embedding <=> %s::vector
        LIMIT 5;
    """, (emb_vector, emb_vector))
    resultados = cur.fetchall()
    conn.close()

    contexto = "\n".join([r["chunk"] for r in resultados])

    # 3️⃣ Generar respuesta con contexto
    prompt = f"""
    Eres Ripsy 💙, asistente especializado en facturación y normatividad en salud.
    Usa los siguientes fragmentos normativos para responder con precisión y referencias cuando sea posible.

    Contexto normativo:
    {contexto}

    Pregunta:
    {pregunta}
    """

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.3
    )

    respuesta = completion.choices[0].message.content
    return {
        "ok": True,
        "pregunta": pregunta,
        "respuesta": respuesta,
        "documentos_usados": [r["filename"] for r in resultados]
    }


# ======================================================
# 🔹 RECARGAR PROMPT / GLOSARIO
# ======================================================
@app.post("/config/reload-prompt")
def reload_prompt():
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = read_text_from_minio(SYSTEM_PROMPT_KEY)
    return {"ok": True, "chars": len(SYSTEM_PROMPT)}

@app.post("/config/reload-glossary")
def reload_glossary():
    global GLOSSARY_TEXT
    GLOSSARY_TEXT = read_text_from_minio(GLOSSARY_KEY)
    return {"ok": True, "chars": len(GLOSSARY_TEXT)}

@app.post("/config/reload")
def reload_both():
    global SYSTEM_PROMPT, GLOSSARY_TEXT
    SYSTEM_PROMPT = read_text_from_minio(SYSTEM_PROMPT_KEY)
    GLOSSARY_TEXT = read_text_from_minio(GLOSSARY_KEY)
    return {
        "ok": True,
        "prompt_chars": len(SYSTEM_PROMPT),
        "glossary_chars": len(GLOSSARY_TEXT)
    }


# ======================================================
# 🔹 HISTORIAL DE MENSAJES
# ======================================================
@app.get("/messages")
def get_messages(limit: int = Query(20, ge=1, le=200)):
    return {"count": limit, "items": fetch_messages(limit)}


# ======================================================
# 🔹 DOCUMENTOS (subir / listar)
# ======================================================
@app.post("/documents/upload")
def upload_document(file: UploadFile = File(...), folder: str = Form("facturas")):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    allowed = {'.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.json', '.xml'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida: {ext}")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 10MB)")

    result = upload_file_to_minio(file.file, file.filename, folder)
    return {"ok": True, "folder": folder, "file": file.filename, "message": result}


@app.get("/documents/list")
def list_documents(folder: str = Query("facturas")):
    from storage import list_files_in_folder
    files = list_files_in_folder(folder)
    return {"ok": True, "folder": folder, "files": files}


# ======================================================
# 🔍 ANÁLISIS DE PROBABILIDAD DE GLOSA
# ======================================================
@app.post("/analizar-glosa")
async def analizar_probabilidad_glosa(
    factura: UploadFile = File(...),
    historia_clinica: UploadFile = File(...)
):
    """
    Analiza la probabilidad de glosa basándose en factura e historia clínica.
    """
    try:
        # Verificar que sean PDFs
        if not factura.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="La factura debe ser un archivo PDF")
        if not historia_clinica.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="La historia clínica debe ser un archivo PDF")
        
        # Extraer texto de los PDFs
        texto_factura = extract_text_from_pdf(factura.file)
        texto_historia = extract_text_from_pdf(historia_clinica.file)
        
        # Analizar con IA
        analisis = analyze_documents_with_ai(texto_factura, texto_historia)
        
        return {
            "ok": True,
            "probabilidad_glosa": analisis["probabilidad"],
            "nivel_riesgo": analisis["nivel_riesgo"],
            "factores_riesgo": analisis["factores_riesgo"],
            "recomendaciones": analisis["recomendaciones"],
            "puntuacion_detallada": analisis["puntuacion_detallada"],
            "archivos_analizados": {
                "factura": factura.filename,
                "historia_clinica": historia_clinica.filename
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el análisis: {str(e)}")


def extract_text_from_pdf(file_data):
    """Extrae texto de un archivo PDF."""
    try:
        import pdfplumber
        
        # Leer el PDF
        with pdfplumber.open(file_data) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extrayendo texto del PDF: {str(e)}")


def analyze_documents_with_ai(texto_factura, texto_historia):
    """Analiza los documentos con IA para determinar probabilidad de glosa."""
    try:
        # Usar el modelo mejorado
        from modelo_glosa import ModeloGlosaMejorado
        
        modelo = ModeloGlosaMejorado()
        resultado = modelo.analizar_documentos(texto_factura, texto_historia)
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error en análisis con modelo mejorado: {e}")
        
        # Fallback a OpenAI si el modelo falla
        try:
            prompt = f"""
            Eres un experto en auditoría de facturas médicas en Colombia. 
            Analiza estos documentos y determina la probabilidad de glosa (0-100%).
            
            FACTURA:
            {texto_factura[:2000]}...
            
            HISTORIA CLÍNICA:
            {texto_historia[:2000]}...
            
            Analiza y responde en formato JSON:
            {{
                "probabilidad": número_entero_0_a_100,
                "nivel_riesgo": "BAJO" o "MEDIO" o "ALTO",
                "factores_riesgo": ["factor1", "factor2", "factor3"],
                "recomendaciones": ["recomendación1", "recomendación2"],
                "puntuacion_detallada": {{
                    "coherencia_diagnostica": 0-100,
                    "justificacion_medica": 0-100,
                    "cumplimiento_normativo": 0-100,
                    "calidad_documental": 0-100
                }}
            }}
            """
            
            # Llamar a OpenAI
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parsear respuesta JSON
            import json
            resultado = json.loads(response.choices[0].message.content)
            
            return resultado
            
        except Exception as e2:
            print(f"❌ Error en fallback OpenAI: {e2}")
            
            # Respuesta de fallback final
            return {
                "probabilidad": 50,
                "nivel_riesgo": "MEDIO",
                "factores_riesgo": ["Error en el análisis", "Revisar documentos"],
                "recomendaciones": ["Verificar calidad de los PDFs", "Intentar nuevamente"],
                "puntuacion_detallada": {
                    "coherencia_diagnostica": 50,
                    "justificacion_medica": 50,
                    "cumplimiento_normativo": 50,
                    "calidad_documental": 50
                }
            }