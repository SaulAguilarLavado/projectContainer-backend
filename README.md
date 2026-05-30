# TextilControl API - Backend FastAPI

Backend para la aplicación TextilControl desarrollado con FastAPI y Python.

## 📋 Descripción

API RESTful para gestionar usuarios, autenticación y reparaciones en talleres de confección. Para este avance, se implementa el sistema de autenticación con usuarios estáticos predefinidos.

## 🛠️ Requisitos

- Python 3.8+
- pip o conda
- Virtual Environment (recomendado)

## 📦 Instalación

### 1. Crear entorno virtual

```bash
cd projectContainer-backend
python3 -m venv .venv

# Activar entorno virtual
# En macOS/Linux:
source .venv/bin/activate

# En Windows:
# .venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🚀 Ejecución

### Iniciar servidor de desarrollo

```bash
python main.py

# O alternativamente:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 Documentación API

Una vez que el servidor esté corriendo:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 👥 Usuarios Predefinidos

| Username | Password | Role | Nombre |
|----------|----------|------|--------|
| `admin` | `admin123` | admin | Administrador |
| `costurera1` | `costurera123` | admin | María García |
| `cliente1` | `cliente123` | cliente | Juan Pérez |
| `cliente2` | `cliente123` | cliente | María Luz |

## 🔐 Endpoints de Autenticación

### POST /login
Autentica un usuario con sus credenciales.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "mensaje": "¡Bienvenido Administrador!",
  "usuario": {
    "id": 1,
    "username": "admin",
    "email": "admin@textilcontrol.com",
    "nombre": "Administrador",
    "role": "admin",
    "activo": true
  },
  "token": null
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Usuario o contraseña incorrectos"
}
```

## 👤 Endpoints de Usuario

### GET /usuarios
Obtiene la lista de todos los usuarios (solo para desarrollo).

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@textilcontrol.com",
    "nombre": "Administrador",
    "role": "admin",
    "activo": true
  },
  ...
]
```

### GET /usuarios/{usuario_id}
Obtiene información de un usuario específico.

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@textilcontrol.com",
  "nombre": "Administrador",
  "role": "admin",
  "activo": true
}
```

## ❤️ Health Checks

### GET /health
Verifica el estado de la API.

**Response:**
```json
{
  "status": "healthy",
  "servicio": "TextilControl API"
}
```

### GET /
Endpoint raíz.

**Response:**
```json
{
  "mensaje": "Bienvenido a TextilControl API",
  "version": "1.0.0",
  "estado": "online"
}
```

## 📁 Estructura del Proyecto

```
projectContainer-backend/
├── .venv/                    # Ambiente virtual
├── main.py                   # Aplicación principal FastAPI
├── models.py                 # Esquemas Pydantic (Usuario, Login, etc)
├── database.py               # Base de datos estática con usuarios
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Este archivo
```

## 🔧 Configuración CORS

La API está configurada para aceptar solicitudes desde:

- `http://localhost:8081` (Expo)
- `http://localhost:3000` (Web)
- `http://192.168.1.*` (Red local)
- `http://127.0.0.1:*` (Localhost)
- `*` (En desarrollo)

En producción, ajusta `allow_origins` en `main.py`.

## 📝 Notas Importantes

- Las contraseñas se almacenan en texto plano para este avance educativo
- En producción, las contraseñas deben hashearse (usar bcrypt)
- Los usuarios están definidos en `database.py` (base de datos estática)
- El token JWT no está implementado aún

## 🔄 Proximos Pasos

- [ ] Implementar autenticación con JWT
- [ ] Hash de contraseñas con bcrypt
- [ ] Endpoint para crear reparaciones
- [ ] Endpoint para obtener reparaciones
- [ ] Base de datos real (PostgreSQL/MongoDB)
- [ ] Validación de permisos por rol

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'fastapi'"

Asegúrate de que el entorno virtual esté activado e instala las dependencias:

```bash
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Error: "Address already in use"

El puerto 8000 está en uso. Usa otro puerto:

```bash
uvicorn main:app --reload --port 8001
```

### CORS Error

Asegúrate de que la URL del frontend esté en `allow_origins` en `main.py`.

## 👨‍💻 Autor

Proyecto desarrollado para TextilControl.

## 📄 Licencia

Proyecto educativo sin licencia especificada.

---

**Última actualización**: Mayo 2026
**Estado**: Funcional ✅
