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

# Instalar dependencias si falta FastAPI o el controlador MySQL
if ! python -c "import fastapi, pymysql, dotenv" 2>/dev/null; then
    echo "📚 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Iniciar el servidor
echo ""
echo "========================================"
echo "🌐 Iniciando servidor en http://localhost:8000"
echo "📚 Documentación: http://localhost:8000/docs"
echo "🗄️  Base de datos: MySQL"
echo "========================================"
echo ""

python main.py
