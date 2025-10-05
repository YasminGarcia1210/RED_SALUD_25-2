#!/bin/bash

echo "💙 Iniciando Ripsy Frontend..."
echo ""

echo "Verificando que FastAPI esté corriendo..."
if ! curl -s http://localhost:8200/ > /dev/null 2>&1; then
    echo "❌ Error: FastAPI no está corriendo en puerto 8200"
    echo "Por favor ejecuta: docker-compose up -d"
    exit 1
fi

echo "✅ FastAPI detectado"
echo ""
echo "🚀 Iniciando Streamlit..."
echo ""
echo "🌐 La aplicación estará disponible en: http://localhost:8501"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
