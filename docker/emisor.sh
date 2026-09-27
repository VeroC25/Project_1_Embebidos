
#!/bin/bash
set -euo pipefail

# Destino configurable para Docker, QEMU o Raspberry Pi.
DEST_HOST="${DEST_HOST:-vigilante}"
DEST_PORT="${DEST_PORT:-5000}"

echo "Emisor iniciado"
echo "Resolucion: 1280x720"
echo "Frecuencia objetivo: 30 FPS"
echo "Destino: ${DEST_HOST}:${DEST_PORT}"

# Generar video simulado y transmitirlo por RTP/UDP.
exec gst-launch-1.0 -v \
    videotestsrc is-live=true pattern=ball ! \
    video/x-raw,format=I420,width=1280,height=720,framerate=30/1 ! \
    x264enc tune=zerolatency bitrate=2000 \
        speed-preset=veryfast key-int-max=30 ! \
    h264parse ! \
    rtph264pay pt=96 config-interval=1 ! \
    udpsink host="$DEST_HOST" port="$DEST_PORT" sync=false
