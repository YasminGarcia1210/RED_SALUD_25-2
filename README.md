# 💙 Ripsy - Chatbot de Auditoría de Facturas en Salud

<div align="center">

![Ripsy Logo](https://img.shields.io/badge/Ripsy-💙-blue?style=for-the-badge&logo=heart)

**Sistema Inteligente de Auditoría de Facturas en el Sector Salud Colombiano**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai)](https://openai.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## 🎯 Descripción del Proyecto

**Ripsy** es un chatbot inteligente especializado en auditoría de facturas del sector salud en Colombia. Utiliza inteligencia artificial avanzada para ayudar a profesionales de la salud a entender, validar y procesar información relacionada con RIPS (Registro Individual de Prestación de Servicios de Salud), radicación de facturas, auditoría y glosas.

### ✨ Características Principales

- 🤖 **Chatbot Inteligente**: Respuestas precisas sobre facturación en salud
- 📊 **Auditoría Automatizada**: Análisis inteligente de facturas y documentos
- 🔍 **Validación RIPS**: Verificación automática de registros de salud
- 📁 **Gestión de Documentos**: Almacenamiento y procesamiento de archivos
- 🔐 **Seguro y Confiable**: Cumple con estándares de seguridad en salud

---

## 🚀 Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **Python 3.10+** - Lenguaje de programación principal
- **PostgreSQL** - Base de datos relacional con soporte vectorial
- **MinIO** - Almacenamiento de objetos compatible con S3

### Inteligencia Artificial
- **OpenAI GPT-4o-mini** - Modelo de lenguaje avanzado
- **Ollama + Llama3** - Modelo local alternativo
- **Procesamiento de Lenguaje Natural** - Análisis inteligente de texto

### Infraestructura
- **Docker & Docker Compose** - Containerización
- **Nginx** - Servidor web y proxy reverso
- **Git** - Control de versiones

---

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git** 2.30+
- **8GB RAM** mínimo
- **20GB** espacio en disco

### Requisitos Recomendados
- **16GB RAM** para mejor rendimiento
- **50GB** espacio en disco
- **CPU** con 4+ núcleos

---

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/YasminGarcia1210/RED_SALUD_25-2.git
cd RED_SALUD_25-2/repo_rips
```

### 2. Configurar Variables de Entorno
```bash
# Crear archivo .env con la siguiente configuración:
cp .env.example .env
```

Editar el archivo `.env` con tus credenciales:
```env
# Configuración de OpenAI
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# Configuración de Base de Datos
POSTGRES_PASSWORD=ripsy2024
POSTGRES_USER=ripsy
POSTGRES_DB=ripsy_chatbot

# Configuración de MinIO
MINIO_ROOT_USER=ripsy
MINIO_ROOT_PASSWORD=ripsy2024
```

### 3. Levantar los Servicios
```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar el estado
docker-compose ps
```

### 4. Verificar la Instalación
```bash
# Probar la API
curl http://localhost:8200/

# Probar conexión con OpenAI
curl http://localhost:8200/test-openai
```

---

## 🎮 Uso del Sistema

### Endpoints Principales

#### 🏠 **Página Principal**
```http
GET http://localhost:8200/
```

#### 💬 **Chat con OpenAI**
```http
POST http://localhost:8200/chat
Content-Type: application/json

{
  "user": "nombre_usuario",
  "message": "¿Cómo funciona la auditoría de facturas?"
}
```

#### 🦙 **Chat con Llama3 (Local)**
```http
POST http://localhost:8200/chat-llama
Content-Type: application/json

{
  "user": "nombre_usuario", 
  "message": "Explica el proceso de radicación de RIPS"
}
```

#### 📁 **Subir Documentos**
```http
POST http://localhost:8200/documents/upload
Content-Type: multipart/form-data

file: [archivo.pdf]
folder: "facturas"
```

#### 📋 **Listar Documentos**
```http
GET http://localhost:8200/documents/list?folder=facturas
```

#### 🔄 **Recargar Configuración**
```http
POST http://localhost:8200/config/reload
```

---

## 🏗️ Arquitectura del Sistema

```mermaid
graph TB
    A[Usuario] --> B[FastAPI]
    B --> C[OpenAI GPT-4o-mini]
    B --> D[Ollama + Llama3]
    B --> E[PostgreSQL]
    B --> F[MinIO Storage]
    
    C --> G[Respuesta Inteligente]
    D --> G
    E --> H[Historial de Conversaciones]
    F --> I[Documentos y Archivos]
    
    G --> A
    H --> A
    I --> A
```

### Componentes Principales

1. **FastAPI Application** - API REST principal
2. **OpenAI Integration** - IA avanzada para respuestas
3. **PostgreSQL Database** - Almacenamiento de conversaciones
4. **MinIO Storage** - Gestión de documentos
5. **Docker Containers** - Infraestructura containerizada

---

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real
```bash
# Logs de FastAPI
docker-compose logs -f fastapi

# Logs de PostgreSQL
docker-compose logs -f postgres

# Logs de MinIO
docker-compose logs -f minio
```

### Estado de los Servicios
```bash
# Verificar estado
docker-compose ps

# Reiniciar servicios
docker-compose restart

# Parar servicios
docker-compose down
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno Disponibles

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `OPENAI_API_KEY` | Clave API de OpenAI | Requerida |
| `OPENAI_MODEL` | Modelo de OpenAI | `gpt-4o-mini` |
| `OPENAI_MAX_TOKENS` | Máximo de tokens | `2000` |
| `OPENAI_TEMPERATURE` | Temperatura del modelo | `0.7` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `ripsy2024` |
| `MINIO_ROOT_PASSWORD` | Contraseña de MinIO | `ripsy2024` |

### Puertos del Sistema

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| FastAPI | 8200 | API principal |
| PostgreSQL | 5432 | Base de datos |
| MinIO API | 9100 | Almacenamiento |
| MinIO Console | 9101 | Interfaz web |

---

## 🚨 Solución de Problemas

### Problemas Comunes

#### ❌ Error de Conexión a OpenAI
```bash
# Verificar API key
curl http://localhost:8200/test-openai
```

#### ❌ Error de Base de Datos
```bash
# Reiniciar PostgreSQL
docker-compose restart postgres
```

#### ❌ Error de Almacenamiento
```bash
# Verificar MinIO
docker-compose logs minio
```

### Comandos de Diagnóstico
```bash
# Verificar todos los servicios
docker-compose ps

# Ver logs detallados
docker-compose logs --tail=50

# Reiniciar todo el sistema
docker-compose down -v && docker-compose up -d
```

---

## 🤝 Contribución

### Cómo Contribuir

1. **Fork** el repositorio
2. **Crear** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Abrir** un Pull Request

### Estándares de Código

- **Python**: PEP 8
- **Commits**: Mensajes descriptivos en español
- **Documentación**: Comentarios claros en el código

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👥 Equipo de Desarrollo

<div align="center">

**Desarrollado con 💙 por el equipo de RED_SALUD_25-2**

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/YasminGarcia1210)

</div>

---

## 📞 Soporte y Contacto

- **GitHub Issues**: [Reportar problemas](https://github.com/YasminGarcia1210/RED_SALUD_25-2/issues)
- **Email**: [contacto@redsalud.com](mailto:contacto@redsalud.com)
- **Documentación**: [Wiki del proyecto](https://github.com/YasminGarcia1210/RED_SALUD_25-2/wiki)

---

<div align="center">

**¡Gracias por usar Ripsy! 💙**

*Transformando la auditoría de facturas en salud con inteligencia artificial*

</div>
