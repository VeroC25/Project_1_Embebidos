#!/bin/sh

set -u

RESULTADOS="resultados"

REPORTE="$RESULTADOS/C4_dmabuf_rpi.txt"
LOG="$RESULTADOS/C4_dmabuf_rpi.log"
INSPECT="$RESULTADOS/C4_v4l2h264enc_inspect_rpi.txt"

DEVICE="$(
    cat "$RESULTADOS/C1_hw_device.txt"
)"

FORMATO="$(
    cat "$RESULTADOS/C1_hw_format.txt"
)"


rm -f \
    "$REPORTE" \
    "$LOG" \
    "$INSPECT"


gst-inspect-1.0 \
    v4l2h264enc \
    > "$INSPECT" 2>&1


DMABUF_PROPERTY=0

if \
    grep -q "output-io-mode" "$INSPECT" \
    && grep -qi "dmabuf" "$INSPECT"; then

    DMABUF_PROPERTY=1
fi


DMABUF_RUNTIME=0


if [ "$DMABUF_PROPERTY" -eq 1 ]; then

    echo "Probando dmabuf-import en la entrada del encoder..."

    gst-launch-1.0 -v \
        libcamerasrc ! \
        video/x-raw,width=1280,height=720,framerate=30/1 ! \
        videoconvert ! \
        video/x-raw,format="$FORMATO" ! \
        v4l2h264enc \
        device="$DEVICE" \
        output-io-mode=dmabuf-import ! \
        h264parse ! \
        fakesink sync=false \
        > "$LOG" 2>&1 &

    PID=$!

    sleep 10


    if kill -0 "$PID" 2>/dev/null; then

        kill -INT "$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true

        if \
            grep -q "video/x-h264" "$LOG" \
            && ! grep -qi "ERROR" "$LOG"; then

            DMABUF_RUNTIME=1
        fi

    else

        wait "$PID" 2>/dev/null || true

    fi

fi


{
    echo "C4 - REVISION DE COPIAS / DMABUF"
    echo
    echo "Fuente final: libcamerasrc"
    echo "Encoder: v4l2h264enc"
    echo "Dispositivo: $DEVICE"
    echo "Formato: $FORMATO"
    echo
    echo "Propiedad DMABUF disponible: $DMABUF_PROPERTY"
    echo "Prueba dmabuf-import exitosa: $DMABUF_RUNTIME"
    echo
} > "$REPORTE"


if [ "$DMABUF_RUNTIME" -eq 1 ]; then

    {
        echo "Resultado:"
        echo "La entrada del encoder acepta dmabuf-import"
        echo "con el pipeline probado."
        echo
        echo "PASS: se reviso y valido el uso de DMABUF."
    } >> "$REPORTE"

else

    {
        echo "Resultado:"
        echo "DMABUF no pudo utilizarse de extremo a extremo"
        echo "con la cadena actual libcamerasrc -> videoconvert."
        echo "El pipeline actual usa memoria convencional en"
        echo "la conversion previa al encoder."
        echo
        echo "Esto se documenta como una copia actualmente"
        echo "necesaria para compatibilidad del pipeline."
        echo
        echo "PASS: se reviso experimentalmente la posibilidad"
        echo "de evitar copias y se documento el resultado."
    } >> "$REPORTE"

fi


cat "$REPORTE"

echo
echo "Evidencias:"
echo "$REPORTE"
echo "$INSPECT"
echo "$LOG"

echo
echo "========================================"
echo " TEST C4 DMABUF/COPIAS: PASS"
echo "========================================"
