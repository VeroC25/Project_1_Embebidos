#!/bin/sh

set -u

RESULTADOS="resultados"

REPORTE="$RESULTADOS/C1_hw_encoder_rpi.txt"
LOG="$RESULTADOS/C1_hw_encoder_rpi.log"
DEVICE_FILE="$RESULTADOS/C1_hw_device.txt"
FORMAT_FILE="$RESULTADOS/C1_hw_format.txt"

mkdir -p "$RESULTADOS"

rm -f \
    "$REPORTE" \
    "$LOG" \
    "$DEVICE_FILE" \
    "$FORMAT_FILE"


echo "========================================"
echo " C1 - ENCODER H264 DE HARDWARE"
echo "========================================"
echo


# ============================================================
# VERIFICAR PLUGIN
# ============================================================

if ! gst-inspect-1.0 v4l2h264enc \
    >/dev/null 2>&1; then

    echo "FAIL: v4l2h264enc no esta disponible."
    exit 1
fi

echo "PASS: v4l2h264enc esta disponible."


# ============================================================
# BUSCAR DISPOSITIVO BCM2835 DE ENCODING
# ============================================================

ENCODER_DEVICE=""

for ruta in /sys/class/video4linux/video*/name; do

    [ -f "$ruta" ] || continue

    nombre="$(cat "$ruta" 2>/dev/null || true)"

    if [ "$nombre" = "bcm2835-codec-encode" ]; then

        video="$(basename "$(dirname "$ruta")")"

        ENCODER_DEVICE="/dev/$video"

        break
    fi

done


if [ -z "$ENCODER_DEVICE" ]; then

    echo "FAIL: no se encontro bcm2835-codec-encode."
    exit 1
fi


if [ ! -e "$ENCODER_DEVICE" ]; then

    echo "FAIL: $ENCODER_DEVICE no existe."
    exit 1
fi


echo "PASS: dispositivo hardware encontrado:"
echo "$ENCODER_DEVICE -> bcm2835-codec-encode"

printf '%s\n' \
    "$ENCODER_DEVICE" \
    > "$DEVICE_FILE"


# ============================================================
# PROBAR FORMATOS ACEPTADOS
# ============================================================

FORMATO_OK=""

for FORMATO in NV12 I420; do

    echo
    echo "Probando formato $FORMATO..."

    rm -f "$LOG"

    gst-launch-1.0 -v \
        libcamerasrc ! \
        video/x-raw,width=1280,height=720,framerate=30/1 ! \
        videoconvert ! \
        video/x-raw,format="$FORMATO" ! \
        v4l2h264enc \
        device="$ENCODER_DEVICE" ! \
        h264parse ! \
        fakesink sync=false \
        > "$LOG" 2>&1 &

    PID=$!

    sleep 8

    if kill -0 "$PID" 2>/dev/null; then

        kill -INT "$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true

        if \
            grep -q "video/x-h264" "$LOG" \
            && ! grep -qi "ERROR" "$LOG"; then

            FORMATO_OK="$FORMATO"

            break
        fi

    else

        wait "$PID" 2>/dev/null || true
    fi

done


if [ -z "$FORMATO_OK" ]; then

    echo
    echo "FAIL: el encoder hardware no pudo"
    echo "codificar el flujo de prueba."

    echo
    tail -n 40 "$LOG" || true

    exit 1
fi


printf '%s\n' \
    "$FORMATO_OK" \
    > "$FORMAT_FILE"


{
    echo "C1 - ENCODER H264 DE HARDWARE"
    echo
    echo "Plugin: v4l2h264enc"
    echo "Dispositivo: $ENCODER_DEVICE"
    echo "Driver/nombre: bcm2835-codec-encode"
    echo "Formato raw usado: $FORMATO_OK"
    echo "Resolucion: 1280x720"
    echo "Framerate: 30/1"
    echo
    echo "PASS: el encoder identificado como hardware"
    echo "codifico H.264 correctamente."
} > "$REPORTE"


cat "$REPORTE"

echo
echo "========================================"
echo " TEST C1 HARDWARE ENCODER: PASS"
echo "========================================"
