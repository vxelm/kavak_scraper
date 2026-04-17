# Arquitectura del sistema

## Diagrama de flujo

```
┌──────────────────────────────────────────────────────────────────┐
│  ETAPA 1 — CRAWLER  (src/crawler.py)                             │
│                                                                  │
│  Kavak.com/mx/seminuevos                                         │
│  páginas 1-205         ──→  ThreadPoolExecutor (3 workers)       │
│                                  │                               │
│                             requests.Session                     │
│                             + exponential backoff                │
│                             + random User-Agent                  │
│                                  │                               │
│                                  ↓                               │
│                   data/raw/html/TIMESTAMP/pagina_N.html          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  ETAPA 2 — PARSER  (src/parser.py)                               │
│                                                                  │
│  data/raw/html/…/*.html  ──→  BeautifulSoup                      │
│                                  │                               │
│                          Extracción de tarjetas                  │
│                          + validación Pydantic                   │
│                          + de-duplicación por ID                 │
│                                  │                               │
│                                  ↓                               │
│                   data/raw/json/TIMESTAMP.jsonl                  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  ETAPA 3 — ENRICHER  (src/enricher.py)                           │
│                                                                  │
│  data/raw/json/…/*.jsonl ──→  Kavak Financial API                │
│                                  │                               │
│                          Planes de financiamiento                │
│                          + idempotencia por fecha                │
│                          + batch insert (60 registros)           │
│                                  │                               │
│                                  ↓                               │
│                   data/processed/kavak_oltp.db (SQLite)          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  ETAPA 4 — ANÁLISIS  (notebooks/)                                │
│                                                                  │
│  kavak_analytics.ipynb   →  Análisis financiero y smart buys     │
│  kavak_clustering.ipynb  →  Segmentación K-means del mercado     │
│  kavak_fair_prices.ipynb →  Modelo ML de predicción de precios   │
└──────────────────────────────────────────────────────────────────┘
```

## Estructura de directorios

```
kavak_scraper/
├── src/                       # Módulos del pipeline ETL
│   ├── settings.py            # Configuración global y rutas
│   ├── logger.py              # Setup de logging centralizado
│   ├── schemas.py             # Esquemas Pydantic de validación
│   ├── models.py              # Modelos SQLModel (ORM)
│   ├── database.py            # Motor SQLAlchemy e inicialización
│   ├── crawler.py             # Descargador concurrente de HTML
│   ├── parser.py              # Conversor HTML → JSONL
│   └── enricher.py            # Enriquecimiento vía API y carga a SQLite
│
├── notebooks/                 # Análisis exploratorio y ML
│   ├── kavak_analytics.ipynb
│   ├── kavak_clustering.ipynb
│   └── kavak_fair_prices.ipynb
│
├── data/                      # Generado en ejecución
│   ├── raw/
│   │   ├── html/              # Páginas HTML por timestamp
│   │   └── json/              # Archivos JSONL del parser
│   └── processed/
│       ├── kavak_oltp.db      # Base de datos SQLite
│       └── csv/               # Exportaciones CSV
│
├── logs/                      # Logs diarios (generado en ejecución)
├── docs/                      # Esta documentación
├── docker-compose.yml         # Servicios PostgreSQL + pgAdmin
├── Dockerfile                 # Imagen Docker de la aplicación
└── pyproject.toml             # Metadatos y dependencias del proyecto
```

## Decisiones de diseño

### Thread safety en el Crawler
Cada hilo del `ThreadPoolExecutor` usa su propia instancia de `requests.Session` mediante `threading.local()`. Esto evita condiciones de carrera al compartir cookies o estado de conexión entre hilos.

### Idempotencia en el Enricher
El campo `fecha_captura` (fecha de hoy por defecto) en la tabla `FinancialPlan` actúa como guardia: si un vehículo ya fue enriquecido hoy, se omite. Esto permite re-ejecutar el enricher sin duplicar datos.

### Validación en dos capas
- **Capa 1 (schemas.py):** Pydantic valida y descarta registros con `id` o `price` ausentes. Otros campos nulos generan `warning`.
- **Capa 2 (models.py):** SQLModel asegura integridad referencial en la base de datos.

### Separación de responsabilidades
Cada módulo tiene una única responsabilidad y puede ejecutarse de forma independiente. El acoplamiento se limita a archivos en disco (HTML → JSONL → SQLite), lo que facilita pruebas y re-ejecuciones parciales del pipeline.
