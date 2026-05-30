"""
Modelos de datos para la aplicación
Define esquemas Pydantic para validación de datos
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    """Roles disponibles en la aplicación"""
    ADMIN = "admin"
    CLIENTE = "cliente"


class Usuario(BaseModel):
    """Modelo de usuario base"""
    id: int
    username: str
    email: str
    nombre: str
    role: RoleEnum
    activo: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@textilcontrol.com",
                "nombre": "Administrador",
                "role": "admin",
                "activo": True
            }
        }


class UsuarioConPassword(Usuario):
    """Modelo interno de usuario con contraseña"""
    password: str


class LoginRequest(BaseModel):
    """Request para login - solo username y password"""
    username: str = Field(..., min_length=1, description="Nombre de usuario")
    password: str = Field(..., min_length=1, description="Contraseña")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }


class LoginResponse(BaseModel):
    """Response exitoso del login"""
    mensaje: str
    usuario: Usuario
    token: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "mensaje": "Login exitoso",
                "usuario": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@textilcontrol.com",
                    "nombre": "Administrador",
                    "role": "admin",
                    "activo": True
                },
                "token": None
            }
        }


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    detalle: str

    class Config:
        json_schema_extra = {
            "example": {
                "detalle": "Usuario o contraseña incorrectos"
            }
        }
