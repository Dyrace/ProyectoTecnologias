# Usa una imagen base de Python ligera
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los requisitos e instálalos
# Esto asegura que todas las librerías necesarias (de requirements.txt) se instalen.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto
COPY . .

# El puerto 5000 es el que usará la aplicación internamente (típico de Flask)
EXPOSE 5000

# Comando para iniciar la aplicación
CMD ["python", "app.py"]