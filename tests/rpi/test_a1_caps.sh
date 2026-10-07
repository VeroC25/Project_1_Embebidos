#!/bin/sh

set -eu

MODO="${1:-qemu}"

mkdir -p resultados

LOG="resultados/A1_caps_${MODO}.log"

echo "========================================"
echo " A1 - CAPS NEGOCIADOS"
echo " Modo: $MODO"
echo "========================================"
echo

case "$MODO" in

    qemu)

        echo "Fuente: videotestsrc"
        echo "Prueba preparatoria para Jenkins."
        echo

        gst-launch-1.0 -v \
            videotestsrc num-buffers=90 pattern=smpte ! \
            video/x-raw,width=1280,height=720,framerate=30/1 ! \
            videoconvert ! \
            video/x-raw,format=NV12 ! \
            fakesink sync=false \
            2>&1 | tee "$LOG"
        ;;

    rpi)

        echo "Fuente: libcamerasrc"
        echo "Prueba final sobre Raspberry Pi."
        echo

        if ! gst-inspect-1.0 libcamerasrc > /dev/null 2>&1; then
            echo "FAIL: libcamerasrc no esta disponible."
            exit 1
        fi

        gst-launch-1.0 -v \
            libcamerasrc ! \
            video/x-raw,width=1280,height=720,framerate=30/1 ! \
            videoconvert ! \
            video/x-raw,format=NV12 ! \
            fakesink sync=false \
            > "$LOG" 2>&1 &

        GST_PID=$!

        echo "Pipeline iniciado con PID $GST_PID."
        echo "Capturando negociacion durante 5 segundos..."
        echo

        sleep 5

        kill -INT "$GST_PID" 2>/dev/null || true
        wait "$GST_PID" 2>/dev/null || true

        cat "$LOG"
        ;;

    *)

        echo "Uso:"
        echo "  $0 qemu"
        echo "  $0 rpi"
        exit 1
        ;;

esac


echo
echo "========================================"
echo " CAPS NEGOCIADOS ENCONTRADOS"
echo "========================================"

CAPS=$(grep "caps = " "$LOG" || true)

if [ -z "$CAPS" ]; then
    echo "FAIL: no se encontraron caps negociados."
    exit 1
fi

echo "$CAPS"

echo
echo "PASS: los caps fueron leidos de la"
echo "negociacion real de GStreamer."

echo
echo "Evidencia guardada en:"
echo "$LOG"

echo
echo "========================================"
echo " TEST A1 CAPS: PASS"
echo "========================================"
