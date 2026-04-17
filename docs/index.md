# Kavak Scraper — Documentación

Pipeline ETL para extraer, parsear y enriquecer datos de vehículos seminuevos del marketplace [Kavak México](https://www.kavak.com/mx/seminuevos).

## Contenido

| Documento | Descripción |
|---|---|
| [Arquitectura](architecture.md) | Diseño del sistema, componentes y flujo de datos |
| [Instalación y configuración](setup.md) | Requisitos, instalación y variables de entorno |
| [Pipeline ETL](pipeline.md) | Guía paso a paso para ejecutar el pipeline completo |
| [Base de datos](database.md) | Esquema de tablas y modelo de datos |
| [Módulos](modules.md) | Referencia de cada módulo en `src/` |
| [Notebooks de análisis](notebooks.md) | Guía de los notebooks de análisis y ML |

## Visión general

```
Kavak.com ──→ [Crawler] ──→ HTML ──→ [Parser] ──→ JSONL ──→ [Enricher] ──→ SQLite ──→ [Notebooks]
```

El proyecto consta de **tres etapas ETL** seguidas de **análisis en Jupyter**:

1. **Crawler** — descarga concurrente de páginas HTML del marketplace
2. **Parser** — extracción de datos de vehículos a formato JSONL
3. **Enricher** — consulta la API financiera de Kavak y persiste en SQLite
4. **Notebooks** — análisis financiero, clustering y predicción de precios

## Tecnologías principales

- **Python 3.12** con `uv` como gestor de dependencias
- **BeautifulSoup4** para parseo de HTML
- **Pydantic / SQLModel** para validación y ORM
- **SQLite** como base de datos local; **PostgreSQL** disponible vía Docker
- **Pandas + Scikit-learn** para análisis y ML en notebooks
