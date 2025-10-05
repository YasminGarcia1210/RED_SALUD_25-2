# =======================
# OPENAI LLM - CONFIGURADO ✅
# =======================
import os
from openai import OpenAI
from typing import List, Dict, Any

# =======================
# CONFIGURACIÓN DE OPENAI
# =======================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

def generate_reply(user: str, message: str, history: List[Dict[str, Any]]) -> str:
    '''
    Genera una respuesta usando OpenAI GPT basada en el mensaje del usuario y el historial.
    
    Args:
        user: Nombre del usuario
        message: Mensaje actual del usuario
        history: Lista de mensajes anteriores para contexto
        
    Returns:
        str: Respuesta generada por el modelo
    '''
    try:
        # Verificar que la API key esté configurada
        if not os.getenv("OPENAI_API_KEY"):
            return "❌ Error: API Key de OpenAI no configurada. Por favor, configura OPENAI_API_KEY en el archivo .env"
        
        # Construir el contexto del historial
        context_messages = []
        
        # Agregar mensajes del historial (últimos 5 para mantener contexto)
        for msg in history[-5:]:
            if msg.get("user_message"):
                context_messages.append({"role": "user", "content": msg["user_message"]})
            if msg.get("bot_response"):
                context_messages.append({"role": "assistant", "content": msg["bot_response"]})
        
        # Agregar el mensaje actual
        context_messages.append({"role": "user", "content": message})
        
        # Llamar a la API de OpenAI
        response = client.chat.completions.create(
            model=MODEL,
            messages=context_messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            user=user
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"❌ Error con OpenAI: {str(e)}"

def test_openai_connection() -> Dict[str, Any]:
    '''
    Prueba la conexión con OpenAI para verificar que la API Key funciona.
    
    Returns:
        Dict con el resultado de la prueba
    '''
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "success": False,
                "error": "API Key no configurada",
                "message": "Configura OPENAI_API_KEY en el archivo .env"
            }
        
        # Hacer una llamada simple para probar la conexión
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hola, ¿funcionas?"}],
            max_tokens=10
        )
        
        return {
            "success": True,
            "message": "Conexión con OpenAI exitosa",
            "model": MODEL,
            "response": response.choices[0].message.content
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error al conectar con OpenAI"
        }
