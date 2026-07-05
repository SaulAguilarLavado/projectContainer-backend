"""Esquemas de validación de la API de TextilControl."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RoleEnum(str, Enum):
    ADMIN = "admin"
    CLIENTE = "cliente"


class EstadoReparacion(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En Proceso"
    COMPLETADO = "Completado"


class Usuario(BaseModel):
    id: int
    username: str
    email: str
    nombre: str
    role: RoleEnum
    activo: bool = True


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("username", "password")
    @classmethod
    def limpiar_credencial(cls, value: str) -> str:
        return value.strip()


class RegisterRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)

    @field_validator("nombre", "email", "username")
    @classmethod
    def limpiar_texto(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value

    @field_validator("email")
    @classmethod
    def validar_email(cls, value: str) -> str:
        normalized = value.lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Ingrese un correo válido")
        return normalized


class LoginResponse(BaseModel):
    mensaje: str
    usuario: Usuario
    token: Optional[str] = None


class ReparacionCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    prenda: str = Field(..., min_length=2, max_length=100)
    descripcion: str = Field(default="", max_length=500)
    fecha_entrega: str = Field(..., min_length=10, max_length=10)
    costo: float = Field(..., gt=0, le=100000)
    ubicacion: str = Field(..., min_length=1, max_length=3)

    @field_validator("prenda", "descripcion")
    @classmethod
    def limpiar_texto(cls, value: str) -> str:
        return value.strip()

    @field_validator("ubicacion")
    @classmethod
    def validar_ubicacion(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized.isalpha():
            raise ValueError("La ubicación debe contener solo letras")
        return normalized

    @field_validator("fecha_entrega")
    @classmethod
    def validar_fecha(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("La fecha debe usar el formato AAAA-MM-DD") from exc
        return value


class ReparacionEstadoUpdate(BaseModel):
    estado: EstadoReparacion


class Reparacion(BaseModel):
    id: int
    cliente_id: int
    cliente: str
    prenda: str
    descripcion: str
    estado: EstadoReparacion
    fecha_entrega: str
    costo: float
    ubicacion: str
    foto_url: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime


class Producto(BaseModel):
    id: int
    nombre: str
    precio: float
    stock: int
    descripcion: str
    foto_url: Optional[str] = None


class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    precio: float = Field(..., gt=0, le=100000)
    stock: int = Field(..., ge=0, le=1000000)
    descripcion: str = Field(default="", max_length=500)

    @field_validator("nombre", "descripcion")
    @classmethod
    def limpiar_texto(cls, value: str) -> str:
        return value.strip()


class CompraCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=1000)


class Compra(BaseModel):
    id: int
    producto_id: int
    producto: str
    cliente_id: int
    cantidad: int
    precio_unitario: float
    total: float
    creado_en: datetime


class ErrorResponse(BaseModel):
    detail: str
