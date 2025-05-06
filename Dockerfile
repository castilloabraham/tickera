# 1) Usa una imagen ligera de Python
FROM python:3.10-slim

# 2) Define el directorio de trabajo
WORKDIR /app

# 3) Copia sólo requirements para aprovechar cache de Docker
COPY requirements.txt .

# 4) Instala dependencias (incluye gunicorn para producción)
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copia el resto de tu código
COPY . .

# 6) Asegura que exista la carpeta de QR
RUN mkdir -p static/qr_codes

# 7) Expone el puerto interno (Vercel lo mapeará automáticamente)
EXPOSE 5000

# 8) Arranca con Gunicorn en el puerto 5000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "--workers", "1"]
