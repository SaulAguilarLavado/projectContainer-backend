# TextilControl API - APF3

Backend FastAPI con persistencia MySQL para la aplicación móvil TextilControl.

Requiere Python 3.10 o superior.

## Incluye

- Login y registro de clientes.
- Contraseñas derivadas con PBKDF2 y salt.
- MySQL para usuarios, reparaciones y catálogo.
- Alta de reparaciones con evidencia JPG, PNG o WEBP de hasta 5 MB.
- Consulta global o filtrada por cliente.
- Cambio validado de estado: `Pendiente`, `En Proceso`, `Completado`.
- Archivos de evidencia servidos en `/uploads`.
- Validación Pydantic, CORS configurable, logging con duración e ID por petición.
- Pruebas del flujo principal.

## Inicio rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Configura en `.env` el usuario y contraseña de MySQL. Con `MYSQL_AUTO_CREATE_DATABASE=true`, el backend ejecuta automáticamente `CREATE DATABASE IF NOT EXISTS textilcontrol` y después crea las tablas. El usuario MySQL debe tener permiso `CREATE`.

Si el usuario no puede crear bases de datos, créala una sola vez y usa `MYSQL_AUTO_CREATE_DATABASE=false`:

```sql
CREATE DATABASE textilcontrol
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Para usar un teléfono físico, inicia con `--host 0.0.0.0` y configura el frontend con `EXPO_PUBLIC_API_URL=http://IP-LOCAL:8000`.

## Credenciales de demostración

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin` | `admin123` |
| Administrador | `costurera1` | `costurera123` |
| Cliente | `cliente1` | `cliente123` |
| Cliente | `cliente2` | `cliente123` |

## Endpoints

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `/health` | Salud del servicio |
| POST | `/login` | Autenticación |
| POST | `/register` | Registro de cliente |
| GET | `/usuarios` | Usuarios disponibles |
| GET | `/reparaciones?cliente_id=3` | Reparaciones, con filtro opcional |
| POST | `/reparaciones` | Orden `multipart/form-data` con foto opcional |
| PATCH | `/reparaciones/{id}/estado` | Actualizar estado |
| GET | `/productos` | Catálogo |
| POST | `/productos` | Crear producto |
| PUT | `/productos/{id}` | Actualizar producto |
| DELETE | `/productos/{id}` | Eliminar producto |

## Variables opcionales

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=textilcontrol
MYSQL_USER=root
MYSQL_PASSWORD=tu_clave
MYSQL_AUTO_CREATE_DATABASE=true
TEXTILCONTROL_UPLOAD_DIR=/ruta/uploads
CORS_ORIGINS=http://localhost:8081,http://localhost:3000
LOG_LEVEL=INFO
```

## Pruebas

```bash
.venv/bin/python -m unittest discover -v
```

Las imágenes `uploads/`, las credenciales `.env` y los archivos temporales no se versionan.
