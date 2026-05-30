"""
Backend FastAPI para TextilControl
API para gestión de talleres de confección y reparación textil
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import (
    LoginRequest, 
    LoginResponse, 
    Usuario, 
    ErrorResponse,
    RoleEnum
)
from database import (
    verificar_credenciales,
    obtener_usuario_por_id,
    obtener_todos_usuarios
)

# Crear aplicación FastAPI
app = FastAPI(
    title="TextilControl API",
    description="API para la gestión de talleres de confección y reparación textil",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir solicitudes desde React Native Expo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://localhost:3000",
        "http://192.168.1.*",
        "http://127.0.0.1:*",
        "*"  # En desarrollo, permitir todas las origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= RUTAS PÚBLICAS =============

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {
        "mensaje": "Bienvenido a TextilControl API",
        "version": "1.0.0",
        "estado": "online"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica el estado de salud de la API"""
    return {
        "status": "healthy",
        "servicio": "TextilControl API"
    }


@app.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["Autenticación"],
    summary="Login de usuario",
    description="Autentica un usuario con username y password"
)
async def login(credenciales: LoginRequest) -> LoginResponse:
    """
    Endpoint de login para autenticar usuarios
    
    **Usuarios de prueba disponibles:**
    - Admin: username='admin', password='admin123'
    - Costurera: username='costurera1', password='costurera123'
    - Cliente: username='cliente1', password='cliente123'
    - Cliente: username='cliente2', password='cliente123'
    
    Args:
        credenciales: LoginRequest con username y password
        
    Returns:
        LoginResponse con datos del usuario autenticado
        
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    
    # Validar entrada
    if not credenciales.username or not credenciales.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username y password son requeridos"
        )
    
    # Verificar credenciales
    usuario_db = verificar_credenciales(
        credenciales.username,
        credenciales.password
    )
    
    if usuario_db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )
    
    if not usuario_db.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario ha sido desactivado"
        )
    
    # Crear respuesta sin la contraseña
    usuario_respuesta = Usuario(
        id=usuario_db.id,
        username=usuario_db.username,
        email=usuario_db.email,
        nombre=usuario_db.nombre,
        role=usuario_db.role,
        activo=usuario_db.activo
    )
    
    return LoginResponse(
        mensaje=f"¡Bienvenido {usuario_db.nombre}!",
        usuario=usuario_respuesta,
        token=None  # En futuro, aquí iría un JWT
    )


@app.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Autenticación"],
    summary="Registro de nuevo usuario (no implementado)",
)
async def register(credenciales: LoginRequest):
    """
    Endpoint para registrar nuevos usuarios
    
    Nota: Para este avance, el registro no está implementado.
    Use los usuarios predefinidos en la base de datos.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="El registro aún no está disponible. Use los usuarios predefinidos."
    )


# ============= RUTAS DE USUARIO =============

@app.get(
    "/usuarios/{usuario_id}",
    response_model=Usuario,
    tags=["Usuarios"],
    summary="Obtener usuario por ID"
)
async def obtener_usuario(usuario_id: int):
    """
    Obtiene información de un usuario específico
    
    Args:
        usuario_id: ID del usuario
        
    Returns:
        Datos del usuario
        
    Raises:
        HTTPException: Si el usuario no existe
    """
    usuario = obtener_usuario_por_id(usuario_id)
    
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {usuario_id} no encontrado"
        )
    
    return Usuario(
        id=usuario.id,
        username=usuario.username,
        email=usuario.email,
        nombre=usuario.nombre,
        role=usuario.role,
        activo=usuario.activo
    )


@app.get(
    "/usuarios",
    response_model=list[Usuario],
    tags=["Usuarios"],
    summary="Obtener todos los usuarios (solo para desarrollo)"
)
async def obtener_usuarios():
    """
    Obtiene la lista de todos los usuarios
    
    **Nota:** Este endpoint es solo para desarrollo.
    En producción, debe estar protegido con autenticación.
    
    Returns:
        Lista de usuarios sin contraseñas
    """
    usuarios = obtener_todos_usuarios()
    return [
        Usuario(
            id=u.id,
            username=u.username,
            email=u.email,
            nombre=u.nombre,
            role=u.role,
            activo=u.activo
        )
        for u in usuarios
    ]


# ============= MANEJO DE ERRORES =============

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Manejador global de excepciones"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detalle": "Error interno del servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Iniciando TextilControl API")
    print("=" * 60)
    print("📍 URL: http://localhost:8000")
    print("📚 Documentación: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
