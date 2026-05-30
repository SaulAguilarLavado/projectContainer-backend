"""
Base de datos simulada con usuarios estáticos
Contiene usuarios predefinidos para la demostración
"""

from models import UsuarioConPassword, RoleEnum
from typing import Optional, List

# Usuarios predefinidos (base de datos estática)
USUARIOS_ESTATICOS = [
    UsuarioConPassword(
        id=1,
        username="admin",
        email="admin@textilcontrol.com",
        nombre="Administrador",
        password="admin123",
        role=RoleEnum.ADMIN,
        activo=True
    ),
    UsuarioConPassword(
        id=2,
        username="costurera1",
        email="costurera1@textilcontrol.com",
        nombre="María García",
        password="costurera123",
        role=RoleEnum.ADMIN,
        activo=True
    ),
    UsuarioConPassword(
        id=3,
        username="cliente1",
        email="cliente1@example.com",
        nombre="Juan Pérez",
        password="cliente123",
        role=RoleEnum.CLIENTE,
        activo=True
    ),
    UsuarioConPassword(
        id=4,
        username="cliente2",
        email="cliente2@example.com",
        nombre="María Luz",
        password="cliente123",
        role=RoleEnum.CLIENTE,
        activo=True
    ),
]


def obtener_usuario_por_username(username: str) -> Optional[UsuarioConPassword]:
    """
    Busca un usuario por su username
    
    Args:
        username: Nombre de usuario a buscar
        
    Returns:
        UsuarioConPassword si encuentra el usuario, None si no existe
    """
    for usuario in USUARIOS_ESTATICOS:
        if usuario.username.lower() == username.lower():
            return usuario
    return None


def obtener_usuario_por_id(user_id: int) -> Optional[UsuarioConPassword]:
    """
    Busca un usuario por su ID
    
    Args:
        user_id: ID del usuario a buscar
        
    Returns:
        UsuarioConPassword si encuentra el usuario, None si no existe
    """
    for usuario in USUARIOS_ESTATICOS:
        if usuario.id == user_id:
            return usuario
    return None


def obtener_todos_usuarios() -> List[UsuarioConPassword]:
    """
    Retorna la lista de todos los usuarios
    
    Returns:
        Lista de usuarios
    """
    return USUARIOS_ESTATICOS


def verificar_credenciales(username: str, password: str) -> Optional[UsuarioConPassword]:
    """
    Verifica que el usuario y contraseña sean correctos
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        
    Returns:
        UsuarioConPassword si las credenciales son válidas, None si no lo son
    """
    usuario = obtener_usuario_por_username(username)
    
    if usuario is None:
        return None
    
    # Comparación simple de contraseña (en producción usar hash)
    if usuario.password == password:
        return usuario
    
    return None
