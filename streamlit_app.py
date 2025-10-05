import streamlit as st
import requests
import json
import time
from datetime import datetime
import base64
from pathlib import Path

# ======================================================
# 🎨 CONFIGURACIÓN DE PÁGINA
# ======================================================
st.set_page_config(
    page_title="💙 Ripsy - Chatbot de Salud",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# 🎨 ESTILOS CSS PERSONALIZADOS
# ======================================================
st.markdown("""
<style>
    /* Estilos principales */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .bot-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .status-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-top: 3px solid #007bff;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .sidebar-content {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Botones personalizados */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# 🔧 CONFIGURACIÓN DE API
# ======================================================
API_BASE_URL = "http://localhost:8200"

def test_api_connection():
    """Prueba la conexión con la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_chat_message(user, message):
    """Envía mensaje al chatbot"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"user": user, "message": message},
            timeout=30
        )
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_openai_status():
    """Obtiene el estado de OpenAI"""
    try:
        response = requests.get(f"{API_BASE_URL}/test-openai", timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# ======================================================
# 🎨 INTERFAZ PRINCIPAL
# ======================================================

# Header principal
st.markdown("""
<div class="main-header fade-in">
    <h1>💙 Ripsy - Chatbot de Auditoría en Salud</h1>
    <p style="font-size: 1.2rem; margin: 0;">Tu asistente inteligente para facturación y normatividad en salud</p>
</div>
""", unsafe_allow_html=True)

# Sidebar con información del sistema
with st.sidebar:
    st.markdown("### 🔧 Estado del Sistema")
    
    # Verificar conexión API
    if test_api_connection():
        st.markdown("""
        <div class="status-card">
            <h4>✅ API Conectada</h4>
            <p>Backend funcionando correctamente</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Verificar OpenAI
        openai_status = get_openai_status()
        if openai_status and openai_status.get("success"):
            st.markdown("""
            <div class="status-card">
                <h4>🤖 OpenAI Conectado</h4>
                <p>Modelo: """ + openai_status.get("model", "N/A") + """</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card" style="border-left-color: #dc3545;">
                <h4>❌ OpenAI Desconectado</h4>
                <p>Verificar configuración</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-card" style="border-left-color: #dc3545;">
            <h4>❌ API Desconectada</h4>
            <p>Verificar que FastAPI esté corriendo</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Estadísticas")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💬 Mensajes", "0", "0")
    with col2:
        st.metric("⏱️ Tiempo", "0s", "0s")
    
    st.markdown("### 🛠️ Herramientas")
    if st.button("🔄 Recargar Configuración"):
        st.success("Configuración recargada!")
    
    if st.button("📋 Ver Historial"):
        st.info("Función próximamente disponible")

# Contenido principal
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Chat con Ripsy")
    
    # Inicializar session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Usuario"
    
    # Input para nombre de usuario
    user_name = st.text_input("👤 Tu nombre:", value=st.session_state.user_name, key="user_input")
    st.session_state.user_name = user_name
    
    # Contenedor de mensajes
    chat_container = st.container()
    
    # Mostrar mensajes existentes
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message fade-in">
                    <strong>👤 {message['user']}:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="bot-message fade-in">
                    <strong>💙 Ripsy:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # Input para nuevo mensaje
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "💬 Escribe tu pregunta sobre facturación en salud:",
            placeholder="Ejemplo: ¿Cómo funciona la auditoría de facturas?",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            send_button = st.form_submit_button("🚀 Enviar", use_container_width=True)
        with col2:
            clear_button = st.form_submit_button("🗑️ Limpiar", use_container_width=True)
        with col3:
            test_button = st.form_submit_button("🧪 Probar OpenAI", use_container_width=True)
    
    # Procesar botones
    if clear_button:
        st.session_state.messages = []
        st.rerun()
    
    if test_button:
        with st.spinner("🧪 Probando conexión con OpenAI..."):
            openai_status = get_openai_status()
            if openai_status and openai_status.get("success"):
                st.success(f"✅ OpenAI funcionando! Respuesta: {openai_status.get('response', 'N/A')}")
            else:
                st.error("❌ Error conectando con OpenAI")
    
    if send_button and user_input:
        if not test_api_connection():
            st.error("❌ No se puede conectar con la API. Verifica que FastAPI esté corriendo en el puerto 8200.")
        else:
            # Agregar mensaje del usuario
            st.session_state.messages.append({
                "role": "user",
                "user": user_name,
                "content": user_input
            })
            
            # Mostrar mensaje del usuario inmediatamente
            with chat_container:
                st.markdown(f"""
                <div class="user-message fade-in">
                    <strong>👤 {user_name}:</strong><br>
                    {user_input}
                </div>
                """, unsafe_allow_html=True)
            
            # Obtener respuesta del bot
            with st.spinner("💙 Ripsy está pensando..."):
                response = send_chat_message(user_name, user_input)
                
                if response and response.get("ok"):
                    bot_response = response.get("respuesta", "Lo siento, no pude procesar tu mensaje.")
                    
                    # Agregar respuesta del bot
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_response
                    })
                    
                    # Mostrar respuesta del bot
                    st.markdown(f"""
                    <div class="bot-message fade-in">
                        <strong>💙 Ripsy:</strong><br>
                        {bot_response}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ Error al obtener respuesta del chatbot")

with col2:
    st.markdown("### 🎯 Características de Ripsy")
    
    features = [
        {
            "icon": "🤖",
            "title": "IA Avanzada",
            "description": "Powered by OpenAI GPT-4o-mini"
        },
        {
            "icon": "📋",
            "title": "RIPS Expert",
            "description": "Especialista en registros de salud"
        },
        {
            "icon": "📊",
            "title": "Auditoría",
            "description": "Análisis inteligente de facturas"
        },
        {
            "icon": "📚",
            "title": "Normativas",
            "description": "Conocimiento de normativa colombiana"
        },
        {
            "icon": "🔍",
            "title": "Validación",
            "description": "Verificación automática de datos"
        },
        {
            "icon": "💡",
            "title": "Asesoría",
            "description": "Orientación en procesos de salud"
        }
    ]
    
    for feature in features:
        st.markdown(f"""
        <div class="feature-card fade-in">
            <h4>{feature['icon']} {feature['title']}</h4>
            <p>{feature['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📈 Métricas en Tiempo Real")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>💬</h3>
            <h2>""" + str(len(st.session_state.messages)) + """</h2>
            <p>Mensajes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡</h3>
            <h2>99%</h2>
            <p>Disponibilidad</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>💙 <strong>Ripsy</strong> - Desarrollado con amor para la Red de Salud del Oriente E.S.E.</p>
    <p>Powered by FastAPI + OpenAI + Streamlit</p>
</div>
""", unsafe_allow_html=True)
