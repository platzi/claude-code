Crea un proyecto FastAPI básico para una plataforma de cursos llamada Platziflix. Debe tener configuración de base de datos PostgreSQL y un endpoint de health. Primero hazlo funcionar localmente, luego dockerízalo.

## PASO 1: Crear estructura básica del proyecto

Crea la estructura de carpetas:
```
platziflix/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   └── db/
│       ├── __init__.py
│       └── base.py
├── pyproject.toml
└── README.md
```

## PASO 2: Configurar dependencias

Crea pyproject.toml con estas dependencias mínimas:
- fastapi (>=0.104.0)
- uvicorn[standard] (>=0.24.0)
- sqlalchemy (>=2.0.0)
- psycopg2-binary (>=2.9.0)
- pydantic-settings (>=2.0.0)
- python-dotenv (>=1.0.0)

## PASO 3: Crear configuración de la aplicación

En app/core/config.py:
- Crear clase Settings usando pydantic-settings
- Incluir PROJECT_NAME, VERSION
- Incluir DATABASE_URL para PostgreSQL
- Configurar para leer variables de entorno


## PASO 4: Crear aplicación FastAPI básica

En app/main.py:
- Crear instancia FastAPI con título y versión desde config
- Endpoint GET "/" que retorne mensaje de bienvenida
- Endpoint GET "/health" que retorne status, service name y version
- NO crear otros endpoints aún

## PASO 5: Verificar funcionamiento local

Instalar dependencias y ejecutar:
```bash
uv sync
uv run uvicorn app.main:app --reload
```

Verificar que respondan:
- http://localhost:8000/ (mensaje bienvenida)
- http://localhost:8000/health (status ok)
- http://localhost:8000/docs (documentación automática)

## PASO 6: Crear Dockerfile

- Usar imagen Python 3.11-slim
- Instalar uv para gestión de dependencias
- Copiar y instalar dependencias del pyproject.toml
- Copiar código de la aplicación
- Exponer puerto 8000
- Comando para ejecutar uvicorn con hot reload

## PASO 7: Crear docker-compose.yml

Configurar dos servicios:

**Servicio db:**
- PostgreSQL 15
- Variables de entorno: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- Puerto 5432
- Volume para persistencia de datos

**Servicio api:**
- Build desde Dockerfile local
- Puerto 8000
- Volume para desarrollo (hot reload)
- Variables de entorno para conexión a DB
- Depende del servicio db

## PASO 8: Verificar funcionamiento en Docker

Ejecutar:
```bash
docker-compose up --build
```

Verificar que respondan igual que en local:
- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/docs

## PASO 9: Configurar conexión a base de datos

En app/db/base.py:
- Configurar SQLAlchemy engine
- Crear SessionLocal para sesiones de DB
- Crear Base declarativa para futuros modelos
- Función get_db() para dependency injection