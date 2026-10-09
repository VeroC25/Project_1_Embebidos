#!/bin/sh

set -eu

MODO="${1:-qemu}"
ENCODER="${2:-x264enc}"

mkdir -p resultados

LOG="resultados/A2_formato_${MODO}.log"

echo "========================================"
echo " A2 - COMPATIBILIDAD DE FORMATO"
echo " Modo: $MODO"
echo " Encoder: $ENCODER"
echo "========================================"
echo

# ============================================================
# Verificar que el encoder solicitado exista
# ============================================================

if ! gst-inspect-1.0 "$ENCODER" > /dev/null 2>&1; then
    echo "FAIL: el encoder '$ENCODER' no esta disponible."
    exit 1
fi


# ============================================================
# Ejecutar pipeline segun plataforma
# ============================================================

case "$MODO" in

    qemu)

        echo "Fuente: videotestsrc"
        echo "Formato objetivo hacia encoder: NV12"
        echo

        gst-launch-1.0 -v \
            videotestsrc num-buffers=90 pattern=smpte ! \
            video/x-raw,width=1280,height=720,framerate=30/1 ! \
            videoconvert ! \
            video/x-raw,format=NV12 ! \
            "$ENCODER" name=encoder_a2 \
            tune=zerolatency \
            bitrate=2000 \
            speed-preset=veryfast \
            key-int-max=30 ! \
            fakesink sync=false \
            > "$LOG" 2>&1

        cat "$LOG"
        ;;


    rpi)

        echo "Fuente: libcamerasrc"
        echo "Encoder final: $ENCODER"
        echo "Formato objetivo hacia encoder: NV12"
        echo

        # Verificar que la fuente de cámara de libcamera esté disponible.
        if ! gst-inspect-1.0 libcamerasrc > /dev/null 2>&1; then
            echo "FAIL: libcamerasrc no esta disponible."
            exit 1
        fi

        # libcamerasrc no soporta num-buffers en nuestra imagen Yocto.
        # Por eso el pipeline se ejecuta en background durante 5 segundos
        # y luego se detiene mediante SIGINT.
        gst-launch-1.0 -v \
            libcamerasrc ! \
            video/x-raw,width=1280,height=720,framerate=30/1 ! \
            videoconvert ! \
            video/x-raw,format=NV12 ! \
            "$ENCODER" name=encoder_a2 \
            tune=zerolatency \
            bitrate=2000 \
            speed-preset=veryfast \
            key-int-max=30 ! \
            fakesink sync=false \
            > "$LOG" 2>&1 &

        GST_PID=$!

        echo "Pipeline iniciado con PID $GST_PID."
        echo "Verificando negociacion durante 5 segundos..."
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
        echo
        echo "Opcionalmente:"
        echo "  $0 rpi x264enc"
        exit 1
        ;;

esac


# ============================================================
# Buscar los caps negociados en la entrada del encoder
# ============================================================

echo
echo "========================================"
echo " CAPS DE ENTRADA AL ENCODER"
echo "========================================"

CAPS_ENCODER=$(
    grep "encoder_a2.GstPad:sink: caps" "$LOG" || true
)

if [ -z "$CAPS_ENCODER" ]; then
    echo "FAIL: no se encontraron los caps"
    echo "negociados en la entrada del encoder."
    exit 1
fi

echo "$CAPS_ENCODER"


# ============================================================
# Validar formato NV12
# ============================================================

if ! echo "$CAPS_ENCODER" | grep -q "format=(string)NV12"; then
    echo
    echo "FAIL: el encoder no negocio NV12 en su entrada."
    exit 1
fi


# ============================================================
# Resultado
# ============================================================

echo
echo "PASS: el encoder recibio video/x-raw en formato NV12."

echo
echo "Evidencia guardada en:"
echo "$LOG"

echo
echo "========================================"
echo " TEST A2 FORMATO: PASS"
echo "========================================"
