# ⚡ Quick Start Guide - TextilControl Full Stack

## 🚀 Inicio en 5 Minutos

### Terminal 1️⃣ - Backend FastAPI

```bash
cd projectContainer-backend

# Opción A: Script automático (macOS/Linux)
./run.sh

# Opción B: Manual
python3 -m venv .venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
python main.py
```

**Resultado esperado:**
```
🚀 Iniciando TextilControl API
📍 URL: http://localhost:8000
📚 Documentación: http://localhost:8000/docs
```

---

### Terminal 2️⃣ - Frontend React Native

```bash
cd projectContainer

npm install
npm start
# o
expo start
```

**Resultado esperado:**
```
Expo server is running on ✓ http://localhost:19000
```

---

## 🧪 Prueba Rápida

### 1. Abre la documentación del backend
```
http://localhost:8000/docs
```

### 2. Prueba el endpoint POST /login
En Swagger UI, click en **POST /login** → **Try it out**

**Ingresa:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Espera respuesta 200 OK:**
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

### 3. Prueba el login en la app
- En Expo, escanea el código QR con tu teléfono
- Ingresa: `admin` / `admin123`
- Deberías navegar al Panel Costurera

---

## 👥 Usuarios Disponibles

```
✅ admin / admin123        → Panel Costurera
✅ costurera1 / costurera123 → Panel Costurera
✅ cliente1 / cliente123   → Estado Cliente
✅ cliente2 / cliente123   → Estado Cliente
```

---

## ❌ Solución Rápida de Problemas

| Problema | Solución |
|----------|----------|
| "Cannot connect to backend" | Verifica que backend esté en `http://localhost:8000` |
| "CORS Error" | Reinicia el backend |
| "ModuleNotFoundError" | Activa entorno virtual: `source .venv/bin/activate` |
| "Port 8000 in use" | Usa otro puerto: `uvicorn main:app --port 8001` |
| "Usuario o contraseña incorrectos" | Revisa las credenciales en la tabla arriba |

---

## 📊 Estado de Cada Componente

- ✅ Backend FastAPI - Funcionando
- ✅ Autenticación - Implementada  
- ✅ Usuarios estáticos - 4 usuarios
- ✅ Frontend conectado - Integración lista
- ✅ AsyncStorage - Persistencia local
- ✅ Componentes reutilizables - 6 componentes

---

## 📚 Documentación Completa

- Frontend: `/projectContainer/README.md`
- Backend: `/projectContainer-backend/README.md`
- Full Stack: `/projectContainer/SETUP_FULLSTACK.md`
- Backend Resumen: `/projectContainer-backend/IMPLEMENTATION_SUMMARY.md`

---

**¡Todo listo para usar!** 🎉
