#!/bin/bash

set -euo pipefail

# Verificar sintaxis de Python.
python3 -m py_compile prueba_integrada_h1.py

# Verificar los plugins necesarios.
for plugin in videotestsrc x264enc h264parse tee mp4mux rtph264pay
do
    gst-inspect-1.0 "$plugin" > /dev/null
done

# Validar codificación, grabación y empaquetado RTP sin cámara.
gst-launch-1.0 -q -e \
    videotestsrc num-buffers=90 ! \
    video/x-raw,format=I420,width=640,height=360,framerate=30/1 ! \
    x264enc tune=zerolatency bitrate=1000 speed-preset=ultrafast key-int-max=30 ! \
    h264parse ! tee name=t \
    t. ! queue ! mp4mux ! filesink location=/tmp/prueba_docker.mp4 \
    t. ! queue ! rtph264pay pt=96 ! fakesink sync=false

# Verificar que el archivo MP4 no esté vacío.
test -s /tmp/prueba_docker.mp4

# Extraer las características del video generado.
echo "Comprobando el contenido del MP4..."

codec=$(ffprobe -v error -select_streams v:0 \
    -show_entries stream=codec_name \
    -of default=noprint_wrappers=1:nokey=1 \
    /tmp/prueba_docker.mp4)

ancho=$(ffprobe -v error -select_streams v:0 \
    -show_entries stream=width \
    -of default=noprint_wrappers=1:nokey=1 \
    /tmp/prueba_docker.mp4)

alto=$(ffprobe -v error -select_streams v:0 \
    -show_entries stream=height \
    -of default=noprint_wrappers=1:nokey=1 \
    /tmp/prueba_docker.mp4)

# Comparar los resultados con los valores esperados.
test "$codec" = "h264"
test "$ancho" = "640"
test "$alto" = "360"

echo "Codec: $codec"
echo "Resolución: ${ancho}x${alto}"
echo "Todas las pruebas finalizaron correctamente."
