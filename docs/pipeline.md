# Pipeline ETL — Guía de ejecución

El pipeline se compone de tres etapas secuenciales. Cada etapa lee la salida de la anterior.

## Etapa 1 — Crawler

Descarga concurrentemente las páginas de listado de Kavak.

```bash
python -m src.crawler
```

**Salida:** `data/raw/html/YYYY_MM_DD-HHh_MMm/pagina_N.html`

**Comportamiento:**
- Descarga páginas 1-205 por defecto (configurable en `settings.py`)
- 3 hilos concurrentes con sesiones aisladas
- Reintenta automáticamente errores 429, 500-504 con backoff exponencial
- Omite páginas ya descargadas en ejecuciones previas
- Delays aleatorios de 1-3 segundos entre peticiones

**Logs esperados:**
```
INFO | crawler | Descargando 205 páginas con 3 workers...
INFO | crawler | pagina_1.html guardada
...
INFO | crawler | Pipeline de crawling finalizado
```

---

## Etapa 2 — Parser

Extrae datos de vehículos de los HTML descargados y los guarda en JSONL.

```bash
python -m src.parser
```

**Entrada:** Carpeta HTML más reciente en `data/raw/html/`

**Salida:** `data/raw/json/TIMESTAMP.jsonl`

**Datos extraídos por tarjeta:**

| Campo | Fuente en HTML |
|---|---|
| `id` | Atributo del enlace de la tarjeta |
| `slug` | Path de la URL |
| `price` | Span con clase `amount__large__price` |
| `city` | Footer de la tarjeta |
| `year` | Subtítulo (primer segmento) |
| `km` | Subtítulo (segundo segmento) |
| `details` | Subtítulo (tercer segmento) |
| `gear` | Subtítulo (cuarto segmento) |
| `discount_offer` | Banner `"Precio imbatible"` |
| `is_reserved` | Banner `"Apartado"` |

**Validación:** Los registros sin `id` o `price` son descartados. El resto de campos nulos se registran como `warning`.

---

## Etapa 3 — Enricher

Consulta la API financiera de Kavak y persiste los planes de financiamiento.

```bash
python -m src.enricher
```

**Entrada:** Archivo JSONL más reciente en `data/raw/json/`

**Salida:** `data/processed/kavak_oltp.db` (tablas `auto` y `financialplan`)

**Proceso por vehículo:**
1. Carga y valida el registro
2. Verifica idempotencia: si ya hay un plan con `fecha_captura = hoy`, omite el vehículo
3. Calcula enganche mínimo: `16% del precio`
4. Llama a la API: `GET /api/vip-ui/mx/calculator/{id}?upfront-amount={enganche}`
5. Extrae todos los planes de financiamiento disponibles
6. Inserta en lote cada 60 registros

> **Nota:** El enricher tiene un guard de smoke test en producción (`if i >= 5: break`). Eliminar esa línea para ejecuciones completas.

---

## Ejecución completa del pipeline

```bash
# Etapa 1: Descargar HTML
python -m src.crawler

# Etapa 2: Parsear a JSONL
python -m src.parser

# Etapa 3: Enriquecer y guardar en SQLite
python -m src.enricher
```

---

## Logs

Los logs se guardan en `logs/kavak_pipeline_YYYY-MM-DD.log` con rotación diaria.

Formato: `timestamp | nivel | módulo | mensaje`

Para monitorear en tiempo real:

```bash
tail -f logs/kavak_pipeline_$(date +%Y-%m-%d).log
```

---

## Ejecución parcial / re-ejecución

Cada etapa puede re-ejecutarse de forma independiente:

- **Re-crawl parcial:** El crawler omite archivos ya descargados; solo descarga los faltantes.
- **Re-parse:** Siempre crea un nuevo JSONL con timestamp; no sobreescribe los anteriores.
- **Re-enrich:** Gracias a la idempotencia por `fecha_captura`, re-ejecutar el enricher el mismo día no duplica datos.
