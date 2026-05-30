#!/bin/bash

# Script para iniciar el backend de TextilControl

echo "========================================"
echo "🚀 TextilControl API - Backend FastAPI"
echo "========================================"

# Verificar si el entorno virtual existe
if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv .venv
fi

# Activar entorno virtual
echo "✅ Activando entorno virtual..."
source .venv/bin/activate

# Instalar dependencias si no existen
if ! pip show fastapi > /dev/null; then
    echo "📚 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Iniciar el servidor
echo ""
echo "========================================"
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "📚 Documentación: http://localhost:8000/docs"
echo "========================================"
echo ""

python main.py
