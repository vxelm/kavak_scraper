# Notebooks de análisis

Los notebooks en [notebooks/](../notebooks/) consumen los datos del pipeline ETL para generar insights financieros, segmentación de mercado y modelos predictivos.

**Prerequisito:** Tener la base de datos poblada (`data/processed/kavak_oltp.db`) o los CSV exportados.

---

## kavak_analytics.ipynb — Análisis financiero

Análisis principal del mercado de seminuevos Kavak con enfoque en financiamiento.

### Secciones

#### 1. Carga de datos
Lee la tabla `financialplan` desde SQLite y configura display de Pandas.

#### 2. Estadísticas básicas
- Total de registros y vehículos únicos
- Distribución de precios, mensualidades y tasas de interés

#### 3. Descuento por pago de contado
Identifica el "bonus de contado": algunos vehículos tienen un precio de contado menor al precio financiado. El análisis muestra que:
- Vehículos más caros tienden a tener descuentos de contado mayores (hasta 6.5%)
- Hipótesis: el descuento correlaciona con el monto del crédito

#### 4. Feature engineering
Campos calculados a partir del slug y los datos financieros:

| Campo calculado | Fórmula |
|---|---|
| `marca` | Primer segmento del slug |
| `modelo` | Segundo segmento del slug |
| `total_a_pagar` | `mensualidad × plazo + precio × enganche_simulado / 100` |
| `costo_interes` | `total_a_pagar - precio` |
| `pct_interes` | `costo_interes / precio × 100` |
| `rango_enganche` | Categorización de `enganche_simulado` |

#### 5. Mapa de correlaciones
Heatmap de correlaciones entre precio, antigüedad, km, tasa de interés y mensualidad.

#### 6. Smart buys
Vehículos donde el costo de financiamiento representa menos del 40-45% del precio de compra. Representan las mejores oportunidades de compra financiada.

#### 7. Peores tratos
Vehículos con mayor porcentaje de interés — útil para identificar qué evitar.

#### 8. Lujo accesible
Vehículos con precio > 300,000 MXN y mensualidad < 10,000 MXN (con cierto plazo/enganche).

#### 9. Caso de estudio
Análisis detallado del financiamiento de un Nissan Sentra 2023 como ejemplo ilustrativo.

### Salida
Exporta CSV limpio a `data/processed/csv/cleaned_final_csv_scrap_completo.csv`.

---

## kavak_clustering.ipynb — Segmentación de mercado

Agrupa vehículos en segmentos de mercado usando K-means clustering.

### Enfoque

1. **Filtrado:** Solo planes a un plazo específico (ej. 12 meses); excluye autos "Aliado"
2. **Features:** Precio, km, año, porcentaje de interés
3. **Normalización:** Z-score por feature
4. **Número óptimo de clusters:** Método del codo (Elbow Method)
5. **Resultado:** Segmentos tipo "Económico", "Gama media", "Premium"

### Uso

Útil para entender la distribución del inventario y comparar un vehículo específico con su segmento.

---

## kavak_fair_prices.ipynb — Predicción de precios justos

Modelo de machine learning para estimar el precio justo de un vehículo y detectar sobrevaluaciones.

### Enfoque

1. **Target:** Precio de venta
2. **Features:** Marca, modelo, tipo de vehículo, año, km, transmisión, ciudad
3. **Preprocesamiento:** One-hot encoding para variables categóricas
4. **Split:** Train / test
5. **Modelo:** Regresión (Linear Regression o Random Forest)
6. **Aplicación:** Identificar vehículos sobre o subvalorados respecto al modelo

### Uso

Ingresar los atributos de un vehículo para obtener un precio de referencia y compararlo con el precio listado en Kavak.

---

## Ejecutar los notebooks

```bash
# Activar entorno virtual primero
source .venv/bin/activate

# Iniciar Jupyter
jupyter notebook notebooks/
```

O directamente desde VS Code con la extensión de Jupyter.
