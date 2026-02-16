# Usamos la imagen slim de Python
FROM python:3.10-slim

# Evitamos que Python genere basura y vemos logs al instante
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Instalamos dependencias del sistema (libgomp1 es obligatoria para CTranslate2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. COPIAMOS LOS MODELOS DESDE TU LOCAL
# Asegúrate de que estas carpetas están en el mismo sitio que el Dockerfile
COPY nllb_ct2_1.3b/ ./nllb_ct2_1.3b/
COPY nllb-200-distilled-1.3B/ ./nllb-200-distilled-1.3B/
COPY lid.176.ftz .

# 4. Copiamos el código de la API
COPY main.py .

EXPOSE 8000

# Comando para arrancar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]