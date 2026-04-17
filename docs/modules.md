# Referencia de módulos

Todos los módulos están en [src/](../src/) y siguen estas convenciones:

- Imports absolutos: siempre `from src.X import Y`
- Sin `print()`: toda salida via `logging.getLogger(__name__)`
- Sin estado global dinámico: timestamps y variables de sesión se crean en `main()`

---

## settings.py

Configuración global del proyecto. Se importa en todos los demás módulos.

**Rutas creadas automáticamente al importar:**

| Variable | Ruta |
|---|---|
| `RAW_HTML_DIR` | `data/raw/html/` |
| `RAW_JSON_DIR` | `data/raw/json/` |
| `PROCESSED_DIR` | `data/processed/` |
| `LOGS_DIR` | `logs/` |
| `DB_PATH` | `data/processed/kavak_oltp.db` |

**Configuración de red:**

| Variable | Valor | Descripción |
|---|---|---|
| `BASE_URL` | `https://www.kavak.com/mx/seminuevos` | URL base del marketplace |
| `TOTAL_PAGES` | `205` | Número de páginas a descargar |
| `MAX_WORKERS` | `3` | Hilos concurrentes en el crawler |
| `REQUEST_TIMEOUT` | `10` | Timeout de petición HTTP en segundos |
| `USER_AGENTS` | lista de 5 | Strings de User-Agent rotatorios |

---

## logger.py

Setup centralizado de logging.

```python
from src.logger import setup_logging
setup_logging()
```

Debe llamarse **antes** de cualquier `getLogger()`. Crea el archivo de log diario en `logs/kavak_pipeline_YYYY-MM-DD.log`.

**Formato del log:**
```
2025-01-15 10:30:45,123 | INFO     | src.crawler | Página 1 descargada
```

---

## schemas.py

Validación de entrada con Pydantic. Define el modelo `Autokavak`.

### `Autokavak`

| Campo | Tipo | Regla de validación |
|---|---|---|
| `id` | `str` | Requerido, min 1 carácter |
| `slug` | `str` | Requerido, min 1 carácter |
| `city` | `str` | Requerido, min 1 carácter |
| `price` | `int \| None` | Opcional; si presente, debe ser > 0 |
| `year` | `int` | Requerido; rango 2000 a año_actual+1 |
| `km` | `int` | Requerido; debe ser ≥ 0 |
| `gear` | `str \| None` | Opcional |
| `discount_offer` | `bool` | Default: `False` |
| `is_reserved` | `bool` | Default: `False` |
| `details` | `str \| None` | Opcional |

**Política de nulos:**
- Sin `id` → registro descartado
- Sin `price` → registro descartado
- Otros campos nulos → se registran como `warning`, valor `None`

---

## models.py

Modelos ORM con SQLModel. Define las tablas `Auto` y `FinancialPlan`.

Ver [database.md](database.md) para el esquema completo de cada tabla.

**Relación:**
```python
class Auto(SQLModel, table=True):
    planes: list["FinancialPlan"] = Relationship(back_populates="auto")

class FinancialPlan(SQLModel, table=True):
    auto: Auto = Relationship(back_populates="planes")
```

---

## database.py

Inicialización de la base de datos.

```python
from src.database import create_db_n_tables, engine

# Crear tablas si no existen
create_db_n_tables()

# Usar engine en sesiones SQLModel
with Session(engine) as session:
    ...
```

---

## crawler.py

Descargador concurrente de páginas HTML.

### Flujo interno

1. Genera lista de URLs: `BASE_URL?page=1` ... `BASE_URL?page=205`
2. Crea directorio con timestamp: `data/raw/html/YYYY_MM_DD-HHh_MMm/`
3. `ThreadPoolExecutor(max_workers=3)` procesa URLs en paralelo
4. Cada hilo usa `threading.local()` para su propia `requests.Session`
5. Reintentos automáticos con backoff exponencial para errores transitorios
6. Guarda cada página como `pagina_N.html`

### Configuración de reintentos

```python
Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
```

### Ejecución

```bash
python -m src.crawler
```

---

## parser.py

Conversor de HTML a JSONL usando BeautifulSoup.

### Selector de tarjetas

```python
cards = soup.find_all("a", attrs={"data-testid": re.compile("card-product")})
```

### Extracción de campos

| Campo | Selector |
|---|---|
| ID / slug | Atributos del `<a>` |
| Precio | `span.amount__large__price` |
| Ciudad | `footer.product_cardProduct__footerInfo` → split por `•` |
| Año, km, details, gear | `.Product__subtitle` → split por `•` |
| discount_offer | Banner con texto `"Precio imbatible"` |
| is_reserved | Banner con texto `"Apartado"` |

### Ejecución

```bash
python -m src.parser
```

Lee automáticamente la carpeta HTML más reciente.

---

## enricher.py

Enriquecimiento vía API financiera de Kavak.

### Endpoint de la API

```
GET /api/vip-ui/mx/calculator/{vehicle_id}?upfront-amount={amount}
```

Donde `amount = precio * 0.16` (enganche mínimo del 16%).

### Respuesta de la API

La API devuelve una lista de planes, uno por cada plazo disponible (12, 24, 36, 48, 60 meses), con:
- `mensualidad`: pago mensual
- `tasa_interes`: tasa de interés anual
- `seguro`: seguro vehicular
- `enganche_min` / `enganche_max`: rango de enganche permitido

### Mecanismo de idempotencia

```python
existing = session.exec(
    select(FinancialPlan)
    .where(FinancialPlan.id_auto == vehicle_id)
    .where(FinancialPlan.fecha_captura == date.today())
).first()

if existing:
    continue  # Ya procesado hoy
```

### Ejecución

```bash
python -m src.enricher
```

> **Advertencia:** Verificar que no exista el guard `if i >= 5: break` antes de una ejecución de producción.
