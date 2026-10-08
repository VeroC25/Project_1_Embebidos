#!/bin/sh

set -u

RESULTADOS="resultados"

REPORTE="$RESULTADOS/C1_hardware_encoder_rpi.txt"
DISPOSITIVOS="$RESULTADOS/C1_v4l2_devices_rpi.log"
GST_H264="$RESULTADOS/C1_gst_h264_rpi.log"
PROBE="$RESULTADOS/C1_hardware_probe_rpi.log"
ENVFILE="$RESULTADOS/C1_hardware_encoder.env"

mkdir -p "$RESULTADOS"

rm -f \
    "$REPORTE" \
    "$DISPOSITIVOS" \
    "$GST_H264" \
    "$PROBE" \
    "$ENVFILE"

echo "========================================"
echo " C1 - ENCODER H264 POR HARDWARE"
echo "========================================"
echo


# ============================================================
# INVENTARIO V4L2
# ============================================================

{
    echo "=== v4l2-ctl --list-devices ==="
    echo

    v4l2-ctl --list-devices 2>&1 || true

    echo
    echo "=== /sys/class/video4linux ==="
    echo

    for ruta in /sys/class/video4linux/video*; do

        [ -e "$ruta" ] || continue

        nombre="$(cat "$ruta/name" 2>/dev/null || true)"

        echo "$(basename "$ruta"): $nombre"

    done

} > "$DISPOSITIVOS"


# ============================================================
# INVENTARIO GSTREAMER H264
# ============================================================

{
    echo "=== Elementos H264 disponibles ==="
    echo

    gst-inspect-1.0 2>/dev/null \
        | grep -Ei 'h264|264enc' \
        || true

    echo
    echo "=== gst-inspect v4l2h264enc ==="
    echo

    gst-inspect-1.0 v4l2h264enc 2>&1 || true

} > "$GST_H264"


if ! gst-inspect-1.0 \
    v4l2h264enc \
    >/dev/null 2>&1; then

    {
        echo "C1 - ENCODER H264 POR HARDWARE"
        echo
        echo "FAIL: v4l2h264enc no esta disponible"
        echo "en la imagen Yocto actual."
        echo
        echo "No se puede afirmar que exista una"
        echo "ruta de codificacion H264 por hardware."
        echo
        echo "Revisar:"
        echo "$DISPOSITIVOS"
        echo "$GST_H264"
    } | tee "$REPORTE"

    exit 1
fi


# ============================================================
# PROBAR CODIFICACION REAL
# ============================================================

probar_formato() {

    FORMATO="$1"

    rm -f "$PROBE"

    echo "Probando v4l2h264enc con formato $FORMATO..."

    GST_DEBUG_NO_COLOR=1 \
    GST_DEBUG="v4l2*:4" \
    gst-launch-1.0 -v \
        libcamerasrc ! \
        video/x-raw,width=1280,height=720,framerate=30/1 ! \
        videoconvert ! \
        video/x-raw,format="$FORMATO" ! \
        v4l2h264enc name=encoder_hw ! \
        h264parse ! \
        fakesink sync=false \
        > "$PROBE" 2>&1 &

    PID=$!

    sleep 8

    if ! kill -0 "$PID" 2>/dev/null; then

        wait "$PID" 2>/dev/null || true

        return 1
    fi

    kill -INT "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true

    if grep -qi \
        "ERROR" \
        "$PROBE"; then

        return 1
    fi

    return 0
}


HW_FORMAT=""

if probar_formato "NV12"; then

    HW_FORMAT="NV12"

elif probar_formato "I420"; then

    HW_FORMAT="I420"

fi


if [ -z "$HW_FORMAT" ]; then

    {
        echo "C1 - ENCODER H264 POR HARDWARE"
        echo
        echo "FAIL: v4l2h264enc existe, pero"
        echo "no se logro una codificacion real"
        echo "1280x720@30 con NV12 ni I420."
        echo
        echo "El elemento no se considera validado"
        echo "como ruta hardware funcional."
        echo
        echo "Evidencia:"
        echo "$PROBE"
    } | tee "$REPORTE"

    exit 1
fi


cat > "$ENVFILE" <<EOF
HW_ENCODER=v4l2h264enc
HW_FORMAT=$HW_FORMAT
EOF


{
    echo "C1 - ENCODER H264 POR HARDWARE"
    echo
    echo "Elemento: v4l2h264enc"
    echo "Formato aceptado: $HW_FORMAT"
    echo "Resolucion probada: 1280x720"
    echo "Framerate solicitado: 30/1"
    echo
    echo "PASS: el elemento V4L2 existe y"
    echo "se ejecuto una codificacion H264 real"
    echo "sobre la Raspberry Pi."
    echo
    echo "Evidencias:"
    echo "$DISPOSITIVOS"
    echo "$GST_H264"
    echo "$PROBE"
    echo "$ENVFILE"
} | tee "$REPORTE"


echo
echo "========================================"
echo " TEST C1 HARDWARE ENCODER: PASS"
echo "========================================"
