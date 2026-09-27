
# Imagen base para el entorno de desarrollo.
FROM ubuntu:24.04

# Instalar Python, OpenCV, NumPy, PyGObject y GStreamer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-opencv \
    python3-numpy \
    python3-gi \
    python3-gst-1.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Crear el directorio de trabajo.
WORKDIR /proyecto

# Incorporar una copia de la aplicación.
COPY prueba_integrada_h1.py ./prueba_integrada_h1.py

# Incorporar los scripts del emisor y del vigilante.
COPY docker/ ./docker/

# Mantener Bash como comando predeterminado.
CMD ["bash"]
