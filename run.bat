@echo off
REM Script para iniciar el backend de TextilControl en Windows

echo ========================================
echo ^O^ TextilControl API - Backend FastAPI
echo ========================================

REM Verificar si el entorno virtual existe
if not exist ".venv" (
    echo ^>^ Creando entorno virtual...
    python -m venv .venv
)

REM Activar entorno virtual
echo ^>^ Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Instalar dependencias si falta FastAPI o el controlador MySQL
python -c "import fastapi, pymysql, dotenv" >nul 2>&1
if %errorlevel% neq 0 (
    echo ^>^ Instalando dependencias...
    pip install -r requirements.txt
)

REM Iniciar el servidor
echo.
echo ========================================
echo ^?^ Iniciando servidor en http://localhost:8000
echo ^?^ Documentacion: http://localhost:8000/docs
echo ^?^ Base de datos: MySQL
echo ========================================
echo.

python main.py
pause
