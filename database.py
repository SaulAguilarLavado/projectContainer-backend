"""Persistencia MySQL para usuarios, reparaciones y catálogo."""

import hashlib
import hmac
import os
import re
import secrets
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator, Optional

import pymysql
from dotenv import load_dotenv
from pymysql.connections import Connection
from pymysql.cursors import DictCursor


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "textilcontrol")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "admin123")
MYSQL_AUTO_CREATE_DATABASE = os.getenv("MYSQL_AUTO_CREATE_DATABASE", "true").lower() in {
    "1", "true", "yes", "on"
}
MYSQL_CONNECT_TIMEOUT = int(os.getenv("MYSQL_CONNECT_TIMEOUT", "5"))
PASSWORD_ITERATIONS = 210_000


class StockInsuficienteError(Exception):
    pass


class CompraInvalidaError(Exception):
    pass

if not re.fullmatch(r"[A-Za-z0-9_]+", MYSQL_DATABASE):
    raise RuntimeError("MYSQL_DATABASE sólo puede contener letras, números y guion bajo")


@contextmanager
def _connect(use_database: bool = True) -> Iterator[Connection]:
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE if use_database else None,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=MYSQL_CONNECT_TIMEOUT,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, expected)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _row(row: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    normalized = {key: _normalize_value(value) for key, value in row.items()}
    if "activo" in normalized:
        normalized["activo"] = bool(normalized["activo"])
    return normalized


def _create_database_if_needed() -> None:
    if not MYSQL_AUTO_CREATE_DATABASE:
        return
    with _connect(use_database=False) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )


def initialize_database() -> None:
    """Crea la base opcionalmente, genera tablas y carga datos iniciales."""
    _create_database_if_needed()

    table_statements = [
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            username VARCHAR(120) NOT NULL,
            email VARCHAR(120) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'cliente') NOT NULL DEFAULT 'cliente',
            activo BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_usuarios_username (username),
            UNIQUE KEY uq_usuarios_email (email),
            KEY idx_usuarios_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS reparaciones (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            cliente_id INT UNSIGNED NOT NULL,
            prenda VARCHAR(100) NOT NULL,
            descripcion VARCHAR(500) NOT NULL DEFAULT '',
            estado ENUM('Pendiente', 'En Proceso', 'Completado') NOT NULL DEFAULT 'Pendiente',
            fecha_entrega DATE NOT NULL,
            costo DECIMAL(10, 2) NOT NULL,
            ubicacion VARCHAR(3) NOT NULL,
            foto_url VARCHAR(255) NULL,
            creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_reparaciones_cliente (cliente_id),
            KEY idx_reparaciones_estado (estado),
            KEY idx_reparaciones_entrega (fecha_entrega),
            CONSTRAINT fk_reparaciones_cliente
                FOREIGN KEY (cliente_id) REFERENCES usuarios(id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
            CONSTRAINT chk_reparaciones_costo CHECK (costo > 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            nombre VARCHAR(120) NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            stock INT UNSIGNED NOT NULL DEFAULT 0,
            descripcion VARCHAR(500) NOT NULL DEFAULT '',
            foto_url VARCHAR(255) NULL,
            PRIMARY KEY (id),
            CONSTRAINT chk_productos_precio CHECK (precio >= 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS compras (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            producto_id INT UNSIGNED NOT NULL,
            cliente_id INT UNSIGNED NOT NULL,
            cantidad INT UNSIGNED NOT NULL,
            precio_unitario DECIMAL(10, 2) NOT NULL,
            total DECIMAL(10, 2) NOT NULL,
            creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_compras_producto (producto_id),
            KEY idx_compras_cliente (cliente_id),
            KEY idx_compras_fecha (creado_en),
            CONSTRAINT fk_compras_producto
                FOREIGN KEY (producto_id) REFERENCES productos(id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
            CONSTRAINT fk_compras_cliente
                FOREIGN KEY (cliente_id) REFERENCES usuarios(id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
            CONSTRAINT chk_compras_cantidad CHECK (cantidad > 0),
            CONSTRAINT chk_compras_total CHECK (total > 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ]

    with _connect() as connection:
        with connection.cursor() as cursor:
            for statement in table_statements:
                cursor.execute(statement)

            cursor.execute(
                """SELECT COUNT(*) AS total
                   FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'foto_url'""",
                (MYSQL_DATABASE,),
            )
            if cursor.fetchone()["total"] == 0:
                cursor.execute("ALTER TABLE productos ADD COLUMN foto_url VARCHAR(255) NULL")

            cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
            if cursor.fetchone()["total"] == 0:
                seed_users = [
                    ("admin", "admin@textilcontrol.com", "Administrador", "admin123", "admin"),
                    ("costurera1", "costurera1@textilcontrol.com", "María García", "costurera123", "admin"),
                    ("cliente1", "cliente1@example.com", "Juan Pérez", "cliente123", "cliente"),
                    ("cliente2", "cliente2@example.com", "María Luz", "cliente123", "cliente"),
                ]
                cursor.executemany(
                    """INSERT INTO usuarios
                       (username, email, nombre, password_hash, role)
                       VALUES (%s, %s, %s, %s, %s)""",
                    [
                        (username, email, name, _hash_password(password), role)
                        for username, email, name, password, role in seed_users
                    ],
                )

            cursor.execute("SELECT COUNT(*) AS total FROM productos")
            if cursor.fetchone()["total"] == 0:
                cursor.executemany(
                    """INSERT INTO productos (nombre, precio, stock, descripcion)
                       VALUES (%s, %s, %s, %s)""",
                    [
                        ("Hilo de algodón", 8.90, 40, "Hilo resistente para arreglos y acabados."),
                        ("Cierre metálico", 12.50, 18, "Cierre de 20 cm para pantalón o casaca."),
                        ("Botones clásicos", 6.00, 65, "Set de seis botones en colores neutros."),
                        ("Parche de mezclilla", 10.00, 24, "Parche reforzado para prendas de jean."),
                    ],
                )


def database_health() -> dict[str, Any]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name, VERSION() AS version")
            row = cursor.fetchone()
    return {
        "status": "connected",
        "database": row["database_name"],
        "engine": "MySQL",
        "version": row["version"],
    }


def verificar_credenciales(username: str, password: str) -> Optional[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM usuarios
                   WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)
                   LIMIT 1""",
                (username, username),
            )
            user = _row(cursor.fetchone())
    if not user or not _verify_password(password, user["password_hash"]):
        return None
    return user


def obtener_usuario_por_id(user_id: int) -> Optional[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            return _row(cursor.fetchone())


def obtener_todos_usuarios() -> list[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios ORDER BY nombre")
            return [_row(row) for row in cursor.fetchall()]


def crear_usuario(nombre: str, email: str, password: str, username: Optional[str]) -> dict[str, Any]:
    normalized_username = (username or email).strip().lower()
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO usuarios (username, email, nombre, password_hash, role)
                   VALUES (%s, %s, %s, %s, 'cliente')""",
                (normalized_username, email.lower(), nombre, _hash_password(password)),
            )
            user_id = cursor.lastrowid
    return obtener_usuario_por_id(user_id)


def crear_reparacion(data: dict[str, Any], foto_url: Optional[str]) -> dict[str, Any]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO reparaciones
                   (cliente_id, prenda, descripcion, fecha_entrega, costo, ubicacion, foto_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    data["cliente_id"], data["prenda"], data["descripcion"],
                    data["fecha_entrega"], data["costo"], data["ubicacion"], foto_url,
                ),
            )
            repair_id = cursor.lastrowid
    return obtener_reparacion(repair_id)


def obtener_reparacion(repair_id: int) -> Optional[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT r.*, u.nombre AS cliente
                   FROM reparaciones r
                   INNER JOIN usuarios u ON u.id = r.cliente_id
                   WHERE r.id = %s""",
                (repair_id,),
            )
            return _row(cursor.fetchone())


def obtener_reparaciones(cliente_id: Optional[int] = None) -> list[dict[str, Any]]:
    query = """SELECT r.*, u.nombre AS cliente
               FROM reparaciones r
               INNER JOIN usuarios u ON u.id = r.cliente_id"""
    params: tuple[Any, ...] = ()
    if cliente_id is not None:
        query += " WHERE r.cliente_id = %s"
        params = (cliente_id,)
    query += " ORDER BY r.creado_en DESC, r.id DESC"
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return [_row(row) for row in cursor.fetchall()]


def actualizar_estado_reparacion(repair_id: int, estado: str) -> Optional[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE reparaciones SET estado = %s WHERE id = %s",
                (estado, repair_id),
            )
            if cursor.rowcount == 0:
                return None
    return obtener_reparacion(repair_id)


def obtener_productos() -> list[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM productos ORDER BY nombre")
            return [_row(row) for row in cursor.fetchall()]


def obtener_producto(product_id: int) -> Optional[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM productos WHERE id = %s", (product_id,))
            return _row(cursor.fetchone())


def crear_producto(data: dict[str, Any]) -> dict[str, Any]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO productos (nombre, precio, stock, descripcion, foto_url)
                   VALUES (%s, %s, %s, %s, %s)""",
                (data["nombre"], data["precio"], data["stock"], data["descripcion"], data.get("foto_url")),
            )
            product_id = cursor.lastrowid
    return obtener_producto(product_id)


def actualizar_producto(product_id: int, data: dict[str, Any]) -> Optional[dict[str, Any]]:
    if obtener_producto(product_id) is None:
        return None
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE productos
                   SET nombre = %s, precio = %s, stock = %s, descripcion = %s, foto_url = %s
                   WHERE id = %s""",
                (
                    data["nombre"], data["precio"], data["stock"], data["descripcion"],
                    data.get("foto_url"), product_id,
                ),
            )
    return obtener_producto(product_id)


def eliminar_producto(product_id: int) -> bool:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM productos WHERE id = %s", (product_id,))
            return cursor.rowcount > 0


def comprar_producto(product_id: int, cliente_id: int, cantidad: int) -> Optional[dict[str, Any]]:
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, role, activo FROM usuarios WHERE id = %s", (cliente_id,))
            client = cursor.fetchone()
            if client is None or client["role"] != "cliente" or not client["activo"]:
                raise CompraInvalidaError("El cliente seleccionado no es válido")

            cursor.execute("SELECT * FROM productos WHERE id = %s FOR UPDATE", (product_id,))
            product = cursor.fetchone()
            if product is None:
                return None
            if product["stock"] < cantidad:
                raise StockInsuficienteError(
                    f"Stock insuficiente. Sólo quedan {product['stock']} unidades"
                )

            total = product["precio"] * cantidad
            cursor.execute(
                "UPDATE productos SET stock = stock - %s WHERE id = %s",
                (cantidad, product_id),
            )
            cursor.execute(
                """INSERT INTO compras
                   (producto_id, cliente_id, cantidad, precio_unitario, total)
                   VALUES (%s, %s, %s, %s, %s)""",
                (product_id, cliente_id, cantidad, product["precio"], total),
            )
            purchase_id = cursor.lastrowid
            cursor.execute(
                """SELECT c.*, p.nombre AS producto
                   FROM compras c INNER JOIN productos p ON p.id = c.producto_id
                   WHERE c.id = %s""",
                (purchase_id,),
            )
            return _row(cursor.fetchone())


def obtener_compras(cliente_id: Optional[int] = None) -> list[dict[str, Any]]:
    query = """SELECT c.*, p.nombre AS producto
               FROM compras c INNER JOIN productos p ON p.id = c.producto_id"""
    params: tuple[Any, ...] = ()
    if cliente_id is not None:
        query += " WHERE c.cliente_id = %s"
        params = (cliente_id,)
    query += " ORDER BY c.creado_en DESC, c.id DESC"
    with _connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return [_row(row) for row in cursor.fetchall()]
