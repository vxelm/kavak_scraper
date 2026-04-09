# Kavak Data Pipeline (ETL)

Pipeline de Ingeniería de Datos para extraer, parsear y enriquecer datos de vehículos seminuevos del marketplace de Kavak México.

---

## Arquitectura

```
Kavak.com → [crawler.py] → data/raw/html/TIMESTAMP/pagina_N.html
                                  ↓
           [parser.py]  → data/raw/json/TIMESTAMP.jsonl
                                  ↓
           [enricher.py]→ Kavak Financial API → data/processed/kavak_oltp.db
```

### Módulos

| Módulo | Responsabilidad |
|---|---|
| `settings.py` | Paths, constantes globales (`BASE_URL`, `MAX_WORKERS`, `USER_AGENTS`, `DATABASE_URL`). Crea directorios `data/` al importar. |
| `logger.py` | Setup centralizado de logging. Siempre llamar `setup_logging()` antes de `getLogger(__name__)`. |
| `schemas.py` | Pydantic `Autokavak` — valida datos crudos antes de escribir al JSONL. |
| `models.py` | SQLModel ORM: `Auto` (PK: `id: str`) y `FinancialPlan` (FK → `Auto`). |
| `database.py` | Engine SQLite + `create_db_n_tables()`. |
| `crawler.py` | Descargador concurrente de HTML. Usa `threading.local()` para aislar `requests.Session` por hilo. Omite páginas ya descargadas. |
| `parser.py` | BeautifulSoup HTML → JSONL. Deduplica por ID de auto en cada run. Valida cada registro con `Autokavak`. |
| `enricher.py` | Lee JSONL, llama a `kavak.com/api/vip-ui/mx/calculator/{id}`, reconcilia estado del `Auto`, escribe a SQLite en batch. Idempotente por día (`fecha_captura`). |

### Estructura de datos

```
data/
  raw/
    html/TIMESTAMP/pagina_N.html   ← salida del crawler
    json/TIMESTAMP.jsonl           ← salida del parser
  processed/
    kavak_oltp.db                  ← salida del enricher (SQLite)
    csv/financial_data/            ← exportaciones opcionales
logs/                              ← logs por módulo
```

---

## Ejecución

Cada etapa corre de forma independiente desde la raíz del repo:

```bash
# Etapa 1 — Descargar páginas HTML (páginas 1–205 por defecto)
python -m src.crawler

# Etapa 2 — Parsear HTML → JSONL (lee la carpeta HTML más reciente)
python -m src.parser

# Etapa 3 — Enriquecer con API financiera → SQLite (lee el JSONL más reciente)
python -m src.enricher
```

> `enricher.py` tiene un guard de smoke-test (`if i >= 5: break`) — elimínalo para runs completos.

### Docker (contenedor único)

```bash
docker build -t kavak-scraper:v1 .
docker run kavak-scraper:v1
```

### Docker Compose (Postgres + pgAdmin)

```bash
docker-compose up -d
```

| Servicio | URL / Puerto |
|---|---|
| PostgreSQL | `localhost:5432` |
| pgAdmin | `localhost:8080` |

Credenciales pgAdmin: `admin@kavak.com` / `admin`

---

## Modelos de datos

### `Auto` (tabla principal)

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `str` | PK — nunca nulo |
| `slug` | `str` | — |
| `city` | `str` | — |
| `price` | `int \| None` | Drop si ausente |
| `year` | `int` | — |
| `km` | `int` | — |
| `gear` | `str \| None` | — |
| `discount_offer` | `bool` | Default: `False` |
| `is_reserved` | `bool` | Default: `False` |
| `details` | `str \| None` | — |

### `FinancialPlan` (tabla de planes, FK → `Auto`)

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `int` | PK autoincremental |
| `id_auto` | `str` | FK → `auto.id` |
| `precio` | `int \| None` | — |
| `tasa_servicio` | `float` | — |
| `plazo` | `int` | Meses |
| `mensualidad` | `int \| None` | — |
| `tasa_interes` | `float \| None` | — |
| `seguro` | `float \| None` | — |
| `enganche_simulado` | `float` | — |
| `enganche_min` | `float` | — |
| `enganche_max` | `float` | — |
| `fecha_captura` | `date` | Default: hoy (idempotencia diaria) |

---

## Estándares de código

- **Imports absolutos:** siempre `from src.X import Y`. Sin imports relativos en `.py`.
- **Sin `print()`:** toda salida pasa por `logging.getLogger(__name__)`.
- **Sin estado global dinámico:** `TIMESTAMP = datetime.now()` a nivel de módulo está prohibido. Instanciar dentro de `main()`.
- **Thread safety:** `requests.Session` aislado por hilo con `threading.local()`.
- **Data drop policy:** solo se descarta un registro si falta el PK (`id`) o el precio. Cualquier otro campo fallido se guarda como `None` con un log de warning.
- **Resiliencia de red:** retry con exponential backoff en todas las llamadas a APIs externas.

---

## Stack

- Python 3.11+
- `requests`, `beautifulsoup4` — crawler y parser
- `pydantic` — validación de esquemas
- `sqlmodel` / `sqlalchemy` — ORM y engine
- `psycopg2-binary` — conector Postgres (Docker Compose)
- SQLite — almacenamiento local por defecto
- Docker / Docker Compose
