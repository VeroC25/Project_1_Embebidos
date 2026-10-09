#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/E5_disco_lleno_rpi.txt"

MOUNT_DIR="/mnt/e5-disk"
GST_LOG="/tmp/e5_gstreamer.log"
VIDEO="$MOUNT_DIR/e5_full.mp4"
RELLENO="$MOUNT_DIR/relleno_e5.bin"

mkdir -p "$RESULTADOS"

rm -f \
    "$REPORTE" \
    "$GST_LOG"


cleanup() {

    echo
    echo "Limpiando entorno temporal E5..."

    rm -f "$VIDEO" \
        "$RELLENO" \
        2>/dev/null || true

    umount "$MOUNT_DIR" \
        2>/dev/null || true

    rmdir "$MOUNT_DIR" \
        2>/dev/null || true

    systemctl start control-acceso \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT


echo "========================================"
echo " E5 - COMPORTAMIENTO ANTE DISCO LLENO"
echo "========================================"
echo


# ============================================================
# PREPARAR FILESYSTEM TEMPORAL
# ============================================================

systemctl stop control-acceso \
    >/dev/null 2>&1 || true

mkdir -p "$MOUNT_DIR"

if mountpoint -q "$MOUNT_DIR"; then
    umount "$MOUNT_DIR"
fi

mount \
    -t tmpfs \
    -o size=8M \
    tmpfs \
    "$MOUNT_DIR"


dd \
    if=/dev/zero \
    of="$RELLENO" \
    bs=1M \
    count=7 \
    >/dev/null 2>&1

sync


echo "=== ESPACIO INICIAL ==="

df -h "$MOUNT_DIR"

echo


# ============================================================
# PROVOCAR ENOSPC CON LA RAMA DE EVIDENCIA
# ============================================================

echo "=== EJECUTANDO PIPELINE ==="

set +e

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
    > "$GST_LOG" 2>&1

GST_STATUS=$?

set -e


cat "$GST_LOG"


echo
echo "=== ESPACIO FINAL ==="

df -h "$MOUNT_DIR"


# ============================================================
# VALIDAR ERROR
# ============================================================

ENOSPC_OK=0
MUX_OK=0


if grep -qi \
    "No space left" \
    "$GST_LOG"; then

    ENOSPC_OK=1
fi


if grep -qi \
    "Could not multiplex" \
    "$GST_LOG"; then

    MUX_OK=1
fi


USO="$(
    df -P "$MOUNT_DIR" \
    | awk 'NR==2 {print $5}'
)"


echo
echo "=== RESULTADOS ==="

echo "gst-launch exit: $GST_STATUS"
echo "ENOSPC detectado: $ENOSPC_OK"
echo "Error de mux detectado: $MUX_OK"
echo "Uso final filesystem: $USO"


{
    echo "E5 - COMPORTAMIENTO ANTE DISCO LLENO"
    echo
    echo "gst-launch exit: $GST_STATUS"
    echo "ENOSPC detectado: $ENOSPC_OK"
    echo "Error de mux detectado: $MUX_OK"
    echo "Uso final filesystem: $USO"
} > "$REPORTE"


if [ "$ENOSPC_OK" -ne 1 ] \
    || [ "$MUX_OK" -ne 1 ]; then

    echo
    echo "TEST E5 DISCO LLENO: FAIL"

    echo \
        "TEST E5 DISCO LLENO: FAIL" \
        >> "$REPORTE"

    exit 1
fi


echo
echo "========================================"
echo " TEST E5 DISCO LLENO: PASS"
echo "========================================"

echo \
    "TEST E5 DISCO LLENO: PASS" \
    >> "$REPORTE"
