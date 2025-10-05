from fastapi import FastAPI

# Creamos la aplicación FastAPI
app = FastAPI(title="Ripsy Chatbot - MVP")

# Endpoint raíz (GET /)
@app.get("/")
def read_root():
    return {"ok": True, "message": "Hola, soy Ripsy 💙. Tu chatbot está corriendo."}

# Endpoint de prueba para el chat (POST /chat)
@app.post("/chat")
def chat(payload: dict):
    user = payload.get("user", "desconocido")
    message = payload.get("message", "")
    return {
        "user": user,
        "message_recibido": message,
        "respuesta": f"Hola {user}, recibí tu mensaje: {message}"
    }
