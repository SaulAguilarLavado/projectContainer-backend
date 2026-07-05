import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse


_temp_dir = tempfile.TemporaryDirectory()
os.environ["TEXTILCONTROL_UPLOAD_DIR"] = str(Path(_temp_dir.name) / "uploads")

from fastapi.testclient import TestClient  # noqa: E402
from pymysql.err import IntegrityError  # noqa: E402
import main  # noqa: E402


USERS = [
    {"id": 1, "username": "admin", "email": "admin@textilcontrol.com", "nombre": "Administrador", "role": "admin", "activo": True, "password": "admin123"},
    {"id": 2, "username": "costurera1", "email": "costurera1@textilcontrol.com", "nombre": "María García", "role": "admin", "activo": True, "password": "costurera123"},
    {"id": 3, "username": "cliente1", "email": "cliente1@example.com", "nombre": "Juan Pérez", "role": "cliente", "activo": True, "password": "cliente123"},
    {"id": 4, "username": "cliente2", "email": "cliente2@example.com", "nombre": "María Luz", "role": "cliente", "activo": True, "password": "cliente123"},
]
REPAIRS = []
PRODUCTS = [
    {"id": 1, "nombre": "Hilo de algodón", "precio": 8.90, "stock": 40, "descripcion": "Hilo resistente"}
]


def _now():
    return datetime.now().isoformat()


def fake_verify(username, password):
    return next(
        (
            user for user in USERS
            if (user["username"].lower() == username.lower() or user["email"].lower() == username.lower())
            and user["password"] == password
        ),
        None,
    )


def fake_get_user(user_id):
    return next((user for user in USERS if user["id"] == user_id), None)


def fake_get_users():
    return USERS


def fake_create_user(nombre, email, password, username):
    normalized = (username or email).lower()
    if any(user["username"].lower() == normalized or user["email"].lower() == email.lower() for user in USERS):
        raise IntegrityError(1062, "Duplicate entry")
    user = {
        "id": len(USERS) + 1,
        "username": normalized,
        "email": email,
        "nombre": nombre,
        "role": "cliente",
        "activo": True,
        "password": password,
    }
    USERS.append(user)
    return user


def fake_create_repair(data, photo_url):
    client = fake_get_user(data["cliente_id"])
    repair = {
        "id": len(REPAIRS) + 1,
        "cliente_id": data["cliente_id"],
        "cliente": client["nombre"],
        "prenda": data["prenda"],
        "descripcion": data["descripcion"],
        "estado": "Pendiente",
        "fecha_entrega": data["fecha_entrega"],
        "costo": data["costo"],
        "ubicacion": data["ubicacion"],
        "foto_url": photo_url,
        "creado_en": _now(),
        "actualizado_en": _now(),
    }
    REPAIRS.append(repair)
    return repair


def fake_get_repair(repair_id):
    return next((repair for repair in REPAIRS if repair["id"] == repair_id), None)


def fake_get_repairs(client_id=None):
    return [repair for repair in REPAIRS if client_id is None or repair["cliente_id"] == client_id]


def fake_update_status(repair_id, status):
    repair = fake_get_repair(repair_id)
    if repair:
        repair["estado"] = status
        repair["actualizado_en"] = _now()
    return repair


def fake_get_product(product_id):
    return next((product for product in PRODUCTS if product["id"] == product_id), None)


def fake_create_product(data):
    product = {"id": max((item["id"] for item in PRODUCTS), default=0) + 1, **data}
    PRODUCTS.append(product)
    return product


def fake_update_product(product_id, data):
    product = fake_get_product(product_id)
    if product:
        product.update(data)
    return product


def fake_delete_product(product_id):
    product = fake_get_product(product_id)
    if not product:
        return False
    PRODUCTS.remove(product)
    return True


def tearDownModule():
    _temp_dir.cleanup()


class TextilControlApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        replacements = {
            "database_health": lambda: {"status": "connected", "database": "textilcontrol", "engine": "MySQL", "version": "test"},
            "verificar_credenciales": fake_verify,
            "obtener_usuario_por_id": fake_get_user,
            "obtener_todos_usuarios": fake_get_users,
            "crear_usuario": fake_create_user,
            "crear_reparacion": fake_create_repair,
            "obtener_reparacion": fake_get_repair,
            "obtener_reparaciones": fake_get_repairs,
            "actualizar_estado_reparacion": fake_update_status,
            "obtener_productos": lambda: PRODUCTS,
            "obtener_producto": fake_get_product,
            "crear_producto": fake_create_product,
            "actualizar_producto": fake_update_product,
            "eliminar_producto": fake_delete_product,
        }
        cls.patchers = [patch.object(main, name, replacement) for name, replacement in replacements.items()]
        for patcher in cls.patchers:
            patcher.start()
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        for patcher in cls.patchers:
            patcher.stop()

    def test_01_health_and_login(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["database"]["engine"], "MySQL")

        invalid = self.client.post("/login", json={"username": "admin", "password": "bad-password"})
        self.assertEqual(invalid.status_code, 401)

        valid = self.client.post("/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.json()["usuario"]["role"], "admin")

    def test_02_register_rejects_duplicate_email(self):
        payload = {"nombre": "Cliente APF3", "email": "apf3@example.com", "password": "segura123"}
        created = self.client.post("/register", json=payload)
        self.assertEqual(created.status_code, 201)
        duplicate = self.client.post("/register", json=payload)
        self.assertEqual(duplicate.status_code, 409)

    def test_03_repair_photo_and_status_flow(self):
        created = self.client.post(
            "/reparaciones",
            data={
                "cliente_id": "3",
                "prenda": "Casaca de jean",
                "descripcion": "Reforzar manga derecha",
                "fecha_entrega": "2026-07-15",
                "costo": "45.50",
                "ubicacion": "A",
            },
            files={"foto": ("evidencia.jpg", b"fake-jpeg-for-contract-test", "image/jpeg")},
        )
        self.assertEqual(created.status_code, 201, created.text)
        repair = created.json()
        self.assertEqual(repair["estado"], "Pendiente")
        self.assertIn("/uploads/", repair["foto_url"])

        photo_response = self.client.get(urlparse(repair["foto_url"]).path)
        self.assertEqual(photo_response.status_code, 200)
        self.assertEqual(photo_response.content, b"fake-jpeg-for-contract-test")

        customer_repairs = self.client.get("/reparaciones", params={"cliente_id": 3})
        self.assertEqual(customer_repairs.status_code, 200)
        self.assertEqual(len(customer_repairs.json()), 1)

        updated = self.client.patch(
            f"/reparaciones/{repair['id']}/estado", json={"estado": "Completado"}
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["estado"], "Completado")

    def test_04_rejects_invalid_photo_type(self):
        response = self.client.post(
            "/reparaciones",
            data={
                "cliente_id": "3",
                "prenda": "Camisa",
                "descripcion": "Cambio de botones",
                "fecha_entrega": "2026-07-20",
                "costo": "15",
                "ubicacion": "B",
            },
            files={"foto": ("not-image.txt", b"not-an-image", "text/plain")},
        )
        self.assertEqual(response.status_code, 415)

    def test_05_rejects_invalid_delivery_date(self):
        response = self.client.post(
            "/reparaciones",
            data={
                "cliente_id": "3",
                "prenda": "Camisa",
                "descripcion": "Cambio de botones",
                "fecha_entrega": "2026-02-30",
                "costo": "15",
                "ubicacion": "B",
            },
            files={"foto": ("evidencia.jpg", b"image", "image/jpeg")},
        )
        self.assertEqual(response.status_code, 422)

    def test_06_product_crud(self):
        payload = {
            "nombre": "Agujas reforzadas",
            "precio": 14.50,
            "stock": 20,
            "descripcion": "Set para telas gruesas",
        }
        created = self.client.post("/productos", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        product_id = created.json()["id"]

        payload["stock"] = 35
        updated = self.client.put(f"/productos/{product_id}", json=payload)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["stock"], 35)

        deleted = self.client.delete(f"/productos/{product_id}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get(f"/productos/{product_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
