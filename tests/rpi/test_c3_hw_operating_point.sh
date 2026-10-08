#!/bin/sh

set -u

FPS_REAL="${1:-30.0}"

RESULTADOS="resultados"

REPORTE="$RESULTADOS/C3_hw_operating_point_rpi.txt"
LOG="$RESULTADOS/C3_hw_operating_point_rpi.log"

DEVICE="$(
    cat "$RESULTADOS/C1_hw_device.txt"
)"

FORMATO="$(
    cat "$RESULTADOS/C1_hw_format.txt"
)"


rm -f "$REPORTE" "$LOG"


echo "========================================"
echo " C3 - PUNTO DE OPERACION DEL ENCODER"
echo "========================================"
echo


gst-launch-1.0 -v \
    libcamerasrc ! \
    video/x-raw,width=1280,height=720,framerate=30/1 ! \
    videoconvert ! \
    video/x-raw,format="$FORMATO" ! \
    v4l2h264enc \
    device="$DEVICE" ! \
    h264parse ! \
    fakesink sync=false \
    > "$LOG" 2>&1 &

PID=$!

sleep 20


if ! kill -0 "$PID" 2>/dev/null; then

    wait "$PID" 2>/dev/null || true

    echo "FAIL: el pipeline hardware termino"
    echo "antes de completar 20 segundos."

    tail -n 40 "$LOG" || true

    exit 1
fi


kill -INT "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true


CAPS_OK=0
H264_OK=0
FPS_OK=0


if \
    grep -q "width=(int)1280" "$LOG" \
    && grep -q "height=(int)720" "$LOG" \
    && grep -q "framerate=(fraction)30/1" "$LOG"; then

    CAPS_OK=1
fi


if grep -q "video/x-h264" "$LOG"; then
    H264_OK=1
fi


FPS_MIN="28.5"
FPS_MAX="31.5"


FPS_OK="$(
    awk \
        -v fps="$FPS_REAL" \
        -v minimo="$FPS_MIN" \
        -v maximo="$FPS_MAX" \
        'BEGIN {
            if (fps >= minimo && fps <= maximo)
                print 1;
            else
                print 0;
        }'
)"


{
    echo "C3 - PUNTO DE OPERACION HARDWARE"
    echo
    echo "Dispositivo: $DEVICE"
    echo "Formato raw: $FORMATO"
    echo "Resolucion objetivo: 1280x720"
    echo "Framerate objetivo: 30 fps"
    echo "Framerate real A3: $FPS_REAL fps"
    echo "Duracion estable: 20 s"
    echo
    echo "Caps 1280x720@30 negociados: $CAPS_OK"
    echo "Salida H264 confirmada: $H264_OK"
    echo "FPS real dentro de +/-5%: $FPS_OK"
} > "$REPORTE"


cat "$REPORTE"


if \
    [ "$CAPS_OK" -ne 1 ] \
    || [ "$H264_OK" -ne 1 ] \
    || [ "$FPS_OK" -ne 1 ]; then

    echo
    echo "FAIL: el punto de operacion"
    echo "no quedo validado."

    exit 1
fi


echo >> "$REPORTE"

echo \
    "PASS: 1280x720@30 opera estable con el encoder hardware." \
    | tee -a "$REPORTE"


echo
echo "========================================"
echo " TEST C3 OPERATING POINT: PASS"
echo "========================================"
