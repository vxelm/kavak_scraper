# USAMOS UNA IMAGEN LIGERA (SLIM)
# Best Practice: Siempre fija la versión menor (3.10), no uses "latest".
FROM python:3.10-slim

# VARIABLES DE ENTORNO
# Evita que Python genere archivos .pyc y fuerza logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# DIRECTORIO DE TRABAJO
WORKDIR /app

# CAPA DE DEPENDENCIAS (CACHE)
# Copiamos solo requirements primero. Si cambias tu código pero no las librerías,
# Docker no reinstalará todo (ahorra tiempo de build).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# CREAR USUARIO NO-ROOT (SEGURIDAD)
# Best Practice: Nunca corras apps como root dentro del contenedor.
RUN useradd -m appuser
USER appuser

# COPIAR EL CÓDIGO
COPY . .

# COMANDO POR DEFECTO
# Sobreescribiremos esto al correr, pero es un buen default.
CMD ["python", "etl_kavak_v1.py"]