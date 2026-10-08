#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/E4_cierre_mp4_rpi.txt"
LOG="$RESULTADOS/E4_systemd_rpi.log"
VIDEO="/tmp/e4_cierre.mp4"
GST_LOG="/tmp/e4_gstreamer.log"

mkdir -p "$RESULTADOS"

rm -f \
    "$REPORTE" \
    "$LOG" \
    "$VIDEO" \
    "$GST_LOG"


cleanup() {
    rm -f "$VIDEO"

    systemctl start control-acceso \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT


echo "========================================"
echo " E4 - CIERRE LIMPIO Y MP4 REPRODUCIBLE"
echo "========================================"
echo


# ============================================================
# PARTE 1 - SYSTEMD / EOS DE LA APLICACION
# ============================================================

echo "=== CIERRE DE LA APLICACION ==="

systemctl start control-acceso

sleep 4

if ! systemctl is-active \
    --quiet control-acceso; then

    echo "FAIL: control-acceso no inicio."
    exit 1
fi


INICIO="$(
    date '+%Y-%m-%d %H:%M:%S'
)"

sleep 1

echo "Deteniendo control-acceso..."

systemctl stop control-acceso


ESTADO="$(
    systemctl is-active \
        control-acceso \
        2>/dev/null \
        || true
)"


journalctl \
    -u control-acceso \
    --since "$INICIO" \
    --no-pager \
    > "$LOG" 2>&1


SIGTERM_OK=0
ENVIO_EOS_OK=0
EOS_OK=0


grep -q \
    "SIGTERM recibido" \
    "$LOG" \
    && SIGTERM_OK=1

grep -q \
    "Enviando EOS" \
    "$LOG" \
    && ENVIO_EOS_OK=1

grep -q \
    "EOS recibido correctamente" \
    "$LOG" \
    && EOS_OK=1


echo "Estado despues de stop: $ESTADO"
echo "SIGTERM detectado: $SIGTERM_OK"
echo "Envio EOS detectado: $ENVIO_EOS_OK"
echo "EOS confirmado: $EOS_OK"

echo


# ============================================================
# PARTE 2 - CIERRE REAL DE MP4
# ============================================================

echo "=== GENERANDO MP4 Y CERRANDO CON EOS ==="

gst-launch-1.0 -e \
    videotestsrc is-live=true \
    ! video/x-raw,width=1280,height=720,framerate=30/1 \
    ! videoconvert \
    ! video/x-raw,format=NV12 \
    ! x264enc \
        tune=zerolatency \
        bitrate=2000 \
        speed-preset=veryfast \
        key-int-max=30 \
    ! h264parse \
    ! mp4mux \
    ! filesink \
        location="$VIDEO" \
        sync=false \
    > "$GST_LOG" 2>&1 &

GST_PID=$!

sleep 5

echo "Enviando SIGINT a gst-launch para solicitar EOS..."

kill -INT "$GST_PID"

set +e
wait "$GST_PID"
GST_STATUS=$?
set -e

echo "gst-launch finalizacion: $GST_STATUS"

if [ ! -s "$VIDEO" ]; then
    echo "FAIL: no se genero el MP4."
    exit 1
fi


echo
echo "=== VALIDACION GST-DISCOVERER ==="

set +e

gst-discoverer-1.0 "$VIDEO"

DISC_STATUS=$?

set -e


echo
echo "=== LECTURA COMPLETA GSTREAMER ==="

set +e

gst-launch-1.0 -q \
    filesrc location="$VIDEO" \
    ! qtdemux \
    ! h264parse \
    ! fakesink

PLAY_STATUS=$?

set -e


TAMANO="$(
    stat -c '%s' "$VIDEO"
)"


echo
echo "=== RESULTADOS ==="

echo "Estado systemd: $ESTADO"
echo "SIGTERM: $SIGTERM_OK"
echo "Envio EOS: $ENVIO_EOS_OK"
echo "EOS confirmado: $EOS_OK"
echo "Tamano MP4: $TAMANO bytes"
echo "gst-discoverer exit: $DISC_STATUS"
echo "gst-launch lectura exit: $PLAY_STATUS"


{
    echo "E4 - CIERRE LIMPIO Y MP4 REPRODUCIBLE"
    echo
    echo "Estado systemd: $ESTADO"
    echo "SIGTERM detectado: $SIGTERM_OK"
    echo "Envio EOS detectado: $ENVIO_EOS_OK"
    echo "EOS confirmado: $EOS_OK"
    echo "Tamano MP4: $TAMANO bytes"
    echo "gst-discoverer exit: $DISC_STATUS"
    echo "gst-launch lectura exit: $PLAY_STATUS"
} > "$REPORTE"


if [ "$ESTADO" != "inactive" ] \
    || [ "$SIGTERM_OK" -ne 1 ] \
    || [ "$ENVIO_EOS_OK" -ne 1 ] \
    || [ "$EOS_OK" -ne 1 ] \
    || [ "$DISC_STATUS" -ne 0 ] \
    || [ "$PLAY_STATUS" -ne 0 ]; then

    echo
    echo "TEST E4 CIERRE MP4: FAIL"

    echo \
        "TEST E4 CIERRE MP4: FAIL" \
        >> "$REPORTE"

    exit 1
fi


echo
echo "========================================"
echo " TEST E4 CIERRE MP4: PASS"
echo "========================================"

echo \
    "TEST E4 CIERRE MP4: PASS" \
    >> "$REPORTE"
