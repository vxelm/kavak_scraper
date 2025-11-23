# 🚗 Kavak Data Pipeline (ETL)

Pipeline de Ingeniería de Datos para extraer, transformar y analizar el mercado de autos seminuevos en México.

## 🏗 Arquitectura
- **Ingesta:** Python + Requests (Imitando comportamiento humano).
- **Almacenamiento Raw:** JSON Lines (JSONL) para tolerancia a fallos.
- **Procesamiento:** Pandas para limpieza y tipado de datos.
- **Storage Final:** SQLite (Simulando Data Warehouse).
- **Containerización:** Docker.

## 🚀 Cómo ejecutar
1. Construir la imagen:
   ```bash
   docker build -t kavak-scraper:v1 .