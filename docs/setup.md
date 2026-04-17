# Instalación y configuración

## Requisitos

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (gestor de dependencias)
- Docker + Docker Compose (opcional, para PostgreSQL)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd kavak_scraper
```

### 2. Crear entorno virtual e instalar dependencias

```bash
uv sync
```

Esto crea `.venv/` e instala todas las dependencias definidas en `pyproject.toml`.

### 3. Activar el entorno

```bash
source .venv/bin/activate    # Linux / macOS
.venv\Scripts\activate       # Windows
```

## Dependencias principales

| Paquete | Versión | Uso |
|---|---|---|
| `beautifulsoup4` | 4.13.5 | Parseo de HTML |
| `requests` | 2.32.5 | Cliente HTTP con reintentos |
| `pydantic` | ≥2.0 | Validación de datos |
| `sqlmodel` | ≥0.0.38 | ORM (SQLAlchemy + Pydantic) |
| `sqlalchemy` | ≥2.0.49 | Motor de base de datos |
| `pandas` | ≥3.0.2 | Análisis de datos en notebooks |
| `ipython` | ≥9.12.0 | Kernel de Jupyter |
| `psycopg2-binary` | ≥2.9.11 | Driver PostgreSQL (Docker) |

## Infraestructura opcional con Docker

Para levantar PostgreSQL y pgAdmin:

```bash
docker-compose up -d
```

Servicios disponibles:
- **PostgreSQL:** `localhost:5432`
- **pgAdmin:** `http://localhost:8080` (usuario: `admin@kavak.com` / contraseña: `admin`)

### Variables de entorno para Docker

Crear un archivo `.env` en la raíz del proyecto:

```env
POSTGRES_USER=kavak
POSTGRES_PASSWORD=<contraseña-segura>
POSTGRES_DB=kavak_db
```

## Verificar la instalación

```bash
python -c "import src.settings; print('OK')"
```

Esto también crea automáticamente los directorios necesarios:
- `data/raw/html/`
- `data/raw/json/`
- `data/processed/`
- `logs/`
