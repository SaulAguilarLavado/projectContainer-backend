"""API FastAPI de TextilControl para el avance APF3."""

import logging
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from pymysql.err import IntegrityError, MySQLError

from database import (
    actualizar_estado_reparacion,
    actualizar_producto,
    comprar_producto,
    crear_producto,
    crear_reparacion,
    crear_usuario,
    database_health,
    eliminar_producto,
    initialize_database,
    obtener_compras,
    obtener_producto,
    obtener_productos,
    obtener_reparacion,
    obtener_reparaciones,
    obtener_todos_usuarios,
    obtener_usuario_por_id,
    verificar_credenciales,
)
from database import StockInsuficienteError, CompraInvalidaError
from models import (
    Compra,
    CompraCreate,
    LoginRequest,
    LoginResponse,
    Producto,
    ProductoCreate,
    RegisterRequest,
    Reparacion,
    ReparacionCreate,
    ReparacionEstadoUpdate,
    Usuario,
)


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("textilcontrol.api")

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("TEXTILCONTROL_UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Inicializando esquema MySQL")
    try:
        initialize_database()
    except MySQLError as exc:
        logger.exception("No se pudo inicializar MySQL")
        raise RuntimeError(
            "No se pudo conectar con MySQL. Revisa que el servidor esté iniciado y las variables MYSQL_* sean correctas."
        ) from exc
    logger.info("Esquema MySQL listo")
    yield


app = FastAPI(
    title="TextilControl API",
    description="Gestión de usuarios, reparaciones, evidencias fotográficas y estados.",
    version="3.0.0",
    lifespan=lifespan,
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def _cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "*").strip()
    if raw_origins.startswith("["):
        try:
            origins = json.loads(raw_origins)
        except json.JSONDecodeError:
            origins = [raw_origins]
    else:
        origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return ["*"] if "*" in origins else origins


configured_origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_credentials=configured_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _usuario_publico(row: dict) -> Usuario:
    return Usuario(
        id=row["id"], username=row["username"], email=row["email"],
        nombre=row["nombre"], role=row["role"], activo=bool(row["activo"]),
    )


def _reparacion_publica(row: dict, request: Request) -> Reparacion:
    payload = dict(row)
    if payload.get("foto_url"):
        payload["foto_url"] = str(request.base_url).rstrip("/") + payload["foto_url"]
    return Reparacion(**payload)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid4().hex[:8]
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed id=%s method=%s path=%s", request_id, request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id, request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


@app.get("/", tags=["Salud"])
async def root():
    return {"mensaje": "Bienvenido a TextilControl API", "version": "3.0.0", "estado": "online"}


@app.get("/health", tags=["Salud"])
def health_check():
    return {
        "status": "healthy",
        "servicio": "TextilControl API",
        "version": "3.0.0",
        "database": database_health(),
    }


@app.post("/login", response_model=LoginResponse, tags=["Autenticación"])
async def login(credentials: LoginRequest) -> LoginResponse:
    user = verificar_credenciales(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")
    if not user["activo"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario ha sido desactivado")
    return LoginResponse(
        mensaje=f"¡Bienvenido {user['nombre']}!",
        usuario=_usuario_publico(user),
        token=f"demo-{uuid4().hex}",
    )


@app.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED, tags=["Autenticación"])
async def register(payload: RegisterRequest) -> LoginResponse:
    try:
        user = crear_usuario(payload.nombre, payload.email, payload.password, payload.username)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario o correo ya está registrado") from exc
    return LoginResponse(
        mensaje="Usuario registrado correctamente",
        usuario=_usuario_publico(user),
        token=f"demo-{uuid4().hex}",
    )


@app.get("/usuarios", response_model=list[Usuario], tags=["Usuarios"])
async def list_users():
    return [_usuario_publico(user) for user in obtener_todos_usuarios()]


@app.get("/usuarios/{usuario_id}", response_model=Usuario, tags=["Usuarios"])
async def get_user(usuario_id: int):
    user = obtener_usuario_por_id(usuario_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _usuario_publico(user)


@app.get("/reparaciones", response_model=list[Reparacion], tags=["Reparaciones"])
async def list_repairs(request: Request, cliente_id: int | None = Query(default=None, gt=0)):
    return [_reparacion_publica(repair, request) for repair in obtener_reparaciones(cliente_id)]


@app.get("/reparaciones/{reparacion_id}", response_model=Reparacion, tags=["Reparaciones"])
async def get_repair(reparacion_id: int, request: Request):
    repair = obtener_reparacion(reparacion_id)
    if repair is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reparación no encontrada")
    return _reparacion_publica(repair, request)


@app.post(
    "/reparaciones",
    response_model=Reparacion,
    status_code=status.HTTP_201_CREATED,
    tags=["Reparaciones"],
)
async def create_repair(
    request: Request,
    cliente_id: int = Form(...),
    prenda: str = Form(...),
    descripcion: str = Form(""),
    fecha_entrega: str = Form(...),
    costo: float = Form(...),
    ubicacion: str = Form(...),
    foto: UploadFile | None = File(default=None),
):
    client = obtener_usuario_por_id(cliente_id)
    if client is None or client["role"] != "cliente":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cliente seleccionado no existe")

    try:
        payload = ReparacionCreate(
            cliente_id=cliente_id,
            prenda=prenda,
            descripcion=descripcion,
            fecha_entrega=fecha_entrega,
            costo=costo,
            ubicacion=ubicacion,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()[0]["msg"]) from exc

    stored_path = None
    saved_file = None
    if foto is not None:
        extension = ALLOWED_IMAGE_TYPES.get(foto.content_type or "")
        if extension is None:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="La evidencia debe ser JPG, PNG o WEBP")
        content = await foto.read(MAX_IMAGE_BYTES + 1)
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen está vacía")
        if len(content) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen supera el límite de 5 MB")
        filename = f"{uuid4().hex}{extension}"
        saved_file = UPLOAD_DIR / filename
        saved_file.write_bytes(content)
        stored_path = f"/uploads/{filename}"

    try:
        repair = crear_reparacion(payload.model_dump(), stored_path)
    except Exception:
        if saved_file and saved_file.exists():
            saved_file.unlink()
        raise

    logger.info("repair_created id=%s client_id=%s has_photo=%s", repair["id"], cliente_id, bool(stored_path))
    return _reparacion_publica(repair, request)


@app.patch("/reparaciones/{reparacion_id}/estado", response_model=Reparacion, tags=["Reparaciones"])
async def update_repair_status(reparacion_id: int, payload: ReparacionEstadoUpdate, request: Request):
    repair = actualizar_estado_reparacion(reparacion_id, payload.estado.value)
    if repair is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reparación no encontrada")
    logger.info("repair_status_changed id=%s status=%s", reparacion_id, payload.estado.value)
    return _reparacion_publica(repair, request)


@app.get("/productos", response_model=list[Producto], tags=["Catálogo"])
async def list_products(request: Request):
    return [_producto_publico(product, request) for product in obtener_productos()]


@app.get("/productos/{producto_id}", response_model=Producto, tags=["Catálogo"])
async def get_product(producto_id: int, request: Request):
    product = obtener_producto(producto_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return _producto_publico(product, request)


def _producto_publico(row: dict, request: Request) -> Producto:
    payload = dict(row)
    if payload.get("foto_url"):
        payload["foto_url"] = str(request.base_url).rstrip("/") + payload["foto_url"]
    return Producto(**payload)


def _save_photo(foto: UploadFile) -> tuple[str | None, Path | None]:
    extension = ALLOWED_IMAGE_TYPES.get(foto.content_type or "")
    if extension is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="La foto debe ser JPG, PNG o WEBP")
    content = foto.file.read(MAX_IMAGE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen está vacía")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen supera el límite de 5 MB")
    filename = f"{uuid4().hex}{extension}"
    saved_file = UPLOAD_DIR / filename
    saved_file.write_bytes(content)
    return f"/uploads/{filename}", saved_file


@app.post("/productos", response_model=Producto, status_code=status.HTTP_201_CREATED, tags=["Catálogo"])
async def create_product(
    request: Request,
    nombre: str = Form(...),
    precio: float = Form(...),
    stock: int = Form(...),
    descripcion: str = Form(""),
    foto: UploadFile | None = File(default=None),
):
    try:
        payload = ProductoCreate(nombre=nombre, precio=precio, stock=stock, descripcion=descripcion)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()[0]["msg"]) from exc

    stored_path = None
    if foto is not None:
        stored_path, _ = _save_photo(foto)

    data = payload.model_dump()
    data["foto_url"] = stored_path
    product = crear_producto(data)
    logger.info("product_created id=%s has_photo=%s", product["id"], bool(stored_path))
    return _producto_publico(product, request)


@app.put("/productos/{producto_id}", response_model=Producto, tags=["Catálogo"])
async def update_product(
    request: Request,
    producto_id: int,
    nombre: str = Form(...),
    precio: float = Form(...),
    stock: int = Form(...),
    descripcion: str = Form(""),
    foto: UploadFile | None = File(default=None),
):
    try:
        payload = ProductoCreate(nombre=nombre, precio=precio, stock=stock, descripcion=descripcion)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()[0]["msg"]) from exc

    existing_product = obtener_producto(producto_id)
    if existing_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    stored_path = None
    if foto is not None:
        stored_path, _ = _save_photo(foto)
    else:
        stored_path = existing_product.get("foto_url")

    data = payload.model_dump()
    data["foto_url"] = stored_path
    product = actualizar_producto(producto_id, data)
    logger.info("product_updated id=%s", producto_id)
    return _producto_publico(product, request)


@app.post("/productos/{producto_id}/comprar", response_model=Compra, tags=["Compras"])
async def buy_product(producto_id: int, payload: CompraCreate):
    try:
        purchase = comprar_producto(producto_id, payload.cliente_id, payload.cantidad)
    except CompraInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except StockInsuficienteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    logger.info("purchase_created product_id=%s client_id=%s qty=%s", producto_id, payload.cliente_id, payload.cantidad)
    return purchase


@app.get("/compras", response_model=list[Compra], tags=["Compras"])
async def list_purchases(cliente_id: int | None = Query(default=None, gt=0)):
    return obtener_compras(cliente_id)


@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Catálogo"])
async def delete_product(producto_id: int):
    if not eliminar_producto(producto_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    logger.info("product_deleted id=%s", producto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.exception_handler(MySQLError)
async def mysql_error_handler(request: Request, exc: MySQLError):
    logger.exception("mysql_error method=%s path=%s", request.method, request.url.path)
    return JSONResponse(status_code=503, content={"detail": "Base de datos temporalmente no disponible"})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("unhandled_error method=%s path=%s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
