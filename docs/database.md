# Base de datos

## Motor

**SQLite** en `data/processed/kavak_oltp.db` para uso local.
**PostgreSQL 15** disponible vía Docker Compose para escalado.

La base de datos se inicializa automáticamente al ejecutar:

```python
from src.database import create_db_n_tables
create_db_n_tables()
```

---

## Tabla `auto`

Almacena los vehículos extraídos del marketplace.

| Columna | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | Identificador único del vehículo en Kavak |
| `slug` | TEXT | | URL amigable (marca/modelo/año/versión) |
| `city` | TEXT | | Ciudad donde está disponible el vehículo |
| `price` | INTEGER | | Precio de contado en MXN |
| `year` | INTEGER | | Año del modelo |
| `km` | INTEGER | | Kilometraje |
| `gear` | TEXT | NULLABLE | Tipo de transmisión (Automático / Manual) |
| `discount_offer` | BOOLEAN | DEFAULT False | Bandera "Precio imbatible" |
| `is_reserved` | BOOLEAN | DEFAULT False | Vehículo apartado |
| `details` | TEXT | NULLABLE | Motor, versión y trim del vehículo |

```sql
CREATE TABLE auto (
    id              TEXT    PRIMARY KEY,
    slug            TEXT,
    city            TEXT,
    price           INTEGER,
    year            INTEGER,
    km              INTEGER,
    gear            TEXT,
    discount_offer  BOOLEAN NOT NULL DEFAULT 0,
    is_reserved     BOOLEAN NOT NULL DEFAULT 0,
    details         TEXT
);
```

---

## Tabla `financialplan`

Almacena los planes de financiamiento por vehículo. Un vehículo puede tener múltiples planes (uno por plazo disponible).

| Columna | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | ID interno del plan |
| `id_auto` | TEXT | FOREIGN KEY → auto.id | Vehículo al que pertenece |
| `precio` | INTEGER | | Precio del vehículo al momento del plan |
| `tasa_servicio` | FLOAT | | Tasa de servicio (%) |
| `plazo` | INTEGER | | Duración del crédito en meses |
| `mensualidad` | INTEGER | | Pago mensual en MXN |
| `tasa_interes` | FLOAT | | Tasa de interés anual (%) |
| `seguro` | FLOAT | | Costo del seguro incluido |
| `enganche_simulado` | FLOAT | | Porcentaje de enganche utilizado en la simulación |
| `enganche_min` | FLOAT | | Enganche mínimo permitido (%) |
| `enganche_max` | FLOAT | | Enganche máximo permitido (%) |
| `fecha_captura` | DATE | DEFAULT hoy | Fecha de captura; previene duplicados diarios |

```sql
CREATE TABLE financialplan (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_auto             TEXT    REFERENCES auto(id),
    precio              INTEGER,
    tasa_servicio       FLOAT,
    plazo               INTEGER,
    mensualidad         INTEGER,
    tasa_interes        FLOAT,
    seguro              FLOAT,
    enganche_simulado   FLOAT,
    enganche_min        FLOAT,
    enganche_max        FLOAT,
    fecha_captura       DATE    NOT NULL DEFAULT (date('now'))
);
```

---

## Relaciones

```
auto (1) ──────────── (N) financialplan
      id ◄────────── id_auto
```

Un vehículo tiene múltiples planes (uno por cada plazo: 12, 24, 36, 48, 60 meses).

---

## Consultas de ejemplo

### Vehículos con menor costo total de financiamiento

```sql
SELECT
    a.slug,
    a.price,
    fp.plazo,
    fp.mensualidad,
    ROUND((fp.mensualidad * fp.plazo + a.price * fp.enganche_simulado / 100.0) / a.price * 100 - 100, 2) AS pct_interes
FROM financialplan fp
JOIN auto a ON fp.id_auto = a.id
WHERE fp.plazo = 48
ORDER BY pct_interes ASC
LIMIT 20;
```

### Autos con descuento por pago de contado

```sql
SELECT
    a.slug,
    a.price AS precio_contado,
    fp.precio AS precio_financiado,
    ROUND((fp.precio - a.price) * 100.0 / fp.precio, 2) AS descuento_pct
FROM financialplan fp
JOIN auto a ON fp.id_auto = a.id
WHERE fp.precio > a.price
ORDER BY descuento_pct DESC;
```

### Resumen diario de capturas

```sql
SELECT
    fecha_captura,
    COUNT(DISTINCT id_auto) AS vehiculos,
    COUNT(*) AS planes
FROM financialplan
GROUP BY fecha_captura
ORDER BY fecha_captura DESC;
```
