# 💙 Ripsy Frontend - Interfaz de Usuario

## 🎨 Características del Frontend

### ✨ **Diseño Moderno y Atractivo**
- **Interfaz responsive** que se adapta a cualquier pantalla
- **Gradientes y animaciones** para una experiencia visual premium
- **Tema personalizado** con colores corporativos
- **Cards informativos** con métricas en tiempo real

### 🚀 **Funcionalidades Principales**
- **💬 Chat en tiempo real** con Ripsy
- **📊 Dashboard de estado** del sistema
- **🤖 Integración con OpenAI** GPT-4o-mini
- **📈 Métricas en vivo** de conversaciones
- **🔄 Recarga de configuración** sin reiniciar
- **📋 Historial de conversaciones** (próximamente)

### 🎯 **Características Técnicas**
- **FastAPI Backend** integrado
- **Streamlit Frontend** moderno
- **Docker Compose** para servicios
- **Responsive Design** para móviles y desktop
- **Real-time Updates** sin recargar página

---

## 🚀 Instalación y Uso

### **Prerrequisitos**
- ✅ FastAPI corriendo en puerto 8200
- ✅ Docker Compose con servicios activos
- ✅ Python 3.10+ con Streamlit instalado

### **Inicio Rápido**

#### **Opción 1: Script Automático (Recomendado)**
```bash
# Windows
start_streamlit.bat

# Linux/Mac
./start_streamlit.sh
```

#### **Opción 2: Comando Manual**
```bash
streamlit run streamlit_app.py --server.port 8501
```

### **Acceso a la Aplicación**
- 🌐 **URL**: http://localhost:8501
- 🔧 **Backend API**: http://localhost:8200
- 📊 **MinIO Console**: http://localhost:9001

---

## 🎨 Interfaz de Usuario

### **Header Principal**
- **Título**: Ripsy - Chatbot de Auditoría en Salud
- **Descripción**: Asistente inteligente para facturación
- **Gradiente azul** corporativo

### **Sidebar (Panel Lateral)**
- **🔧 Estado del Sistema**
  - ✅ API Conectada
  - 🤖 OpenAI Status
  - ❌ Alertas de error
- **📊 Estadísticas**
  - 💬 Contador de mensajes
  - ⏱️ Tiempo de respuesta
- **🛠️ Herramientas**
  - 🔄 Recargar configuración
  - 📋 Ver historial

### **Área Principal de Chat**
- **💬 Interfaz de Chat**
  - Input para nombre de usuario
  - Área de mensajes con scroll
  - Botón de envío con animación
  - Botón de limpiar chat
  - Botón de prueba OpenAI
- **🎯 Características de Ripsy**
  - Cards informativos
  - Iconos descriptivos
  - Descripción de capacidades

### **Mensajes del Chat**
- **👤 Mensajes del Usuario**
  - Gradiente púrpura
  - Alineados a la derecha
  - Animación de entrada
- **💙 Respuestas de Ripsy**
  - Gradiente azul
  - Alineados a la izquierda
  - Animación de entrada

---

## 🎨 Estilos y Temas

### **Paleta de Colores**
- **Primario**: #1e3c72 (Azul corporativo)
- **Secundario**: #2a5298 (Azul claro)
- **Acento**: #667eea (Púrpura)
- **Éxito**: #28a745 (Verde)
- **Error**: #dc3545 (Rojo)

### **Gradientes Utilizados**
- **Header**: `linear-gradient(90deg, #1e3c72 0%, #2a5298 100%)`
- **Usuario**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- **Bot**: `linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)`
- **Métricas**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`

### **Animaciones**
- **fadeIn**: Entrada suave de elementos
- **Hover Effects**: Efectos al pasar el mouse
- **Button Transitions**: Transiciones en botones

---

## 🔧 Configuración Avanzada

### **Variables de Entorno**
```env
# API Configuration
API_BASE_URL=http://localhost:8200

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### **Personalización de Tema**
Editar `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1e3c72"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## 🚨 Solución de Problemas

### **Error: "No se puede conectar con la API"**
```bash
# Verificar que FastAPI esté corriendo
curl http://localhost:8200/

# Si no responde, reiniciar servicios
docker-compose restart fastapi
```

### **Error: "Streamlit no inicia"**
```bash
# Instalar Streamlit
pip install streamlit

# Verificar puerto disponible
netstat -an | findstr 8501
```

### **Error: "OpenAI no conecta"**
```bash
# Verificar API key en .env
# Probar endpoint directamente
curl http://localhost:8200/test-openai
```

---

## 📱 Responsive Design

### **Desktop (1200px+)**
- Layout de 2 columnas
- Sidebar expandido
- Chat de ancho completo

### **Tablet (768px - 1199px)**
- Layout de 1 columna
- Sidebar colapsable
- Chat optimizado

### **Mobile (< 768px)**
- Layout vertical
- Sidebar como drawer
- Botones grandes para touch

---

## 🎯 Próximas Mejoras

### **Funcionalidades Planificadas**
- [ ] **📋 Historial de conversaciones** persistente
- [ ] **📁 Subida de documentos** drag & drop
- [ ] **📊 Dashboard avanzado** con gráficos
- [ ] **🔍 Búsqueda en conversaciones**
- [ ] **💾 Exportar conversaciones** a PDF
- [ ] **🌙 Modo oscuro** toggle
- [ ] **🔔 Notificaciones** en tiempo real
- [ ] **👥 Múltiples usuarios** simultáneos

### **Mejoras Técnicas**
- [ ] **⚡ Caching** de respuestas
- [ ] **🔄 WebSockets** para tiempo real
- [ ] **📱 PWA** (Progressive Web App)
- [ ] **🔐 Autenticación** de usuarios
- [ ] **📈 Analytics** de uso
- [ ] **🌍 Internacionalización** (i18n)

---

## 💙 Créditos

**Desarrollado con 💙 para la Red de Salud del Oriente E.S.E.**

- **Backend**: FastAPI + OpenAI + PostgreSQL + MinIO
- **Frontend**: Streamlit + CSS3 + JavaScript
- **Infraestructura**: Docker + Docker Compose
- **IA**: OpenAI GPT-4o-mini + RAG con normativas

---

## 📞 Soporte

Para soporte técnico o reportar bugs:
- 📧 **Email**: soporte@redsaludoriente.gov.co
- 🐛 **Issues**: GitHub Issues
- 📖 **Docs**: README.md principal

---

**¡Disfruta usando Ripsy! 💙**
