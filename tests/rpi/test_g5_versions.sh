#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/G5_versiones_rpi.txt"

POKY_RAMA="scarthgap"
POKY_COMMIT="cbd62bb2a9f2ab3466a0f72f4289bc86ca20a019"

META_RPI_RAMA="scarthgap"
META_RPI_COMMIT="6ca1f75017cc5d5acdb8bb05634c4bc01fa049fd"

mkdir -p "$RESULTADOS"

echo "========================================"
echo "G5 - VERSIONES EXACTAS DEL ENTORNO"
echo "========================================"

GST_VERSION="$(
    gst-inspect-1.0 --version 2>/dev/null \
        | awk '/^GStreamer / {print $2}' \
        | head -n 1
)"

{
    echo "G5 - VERSIONES EXACTAS DEL ENTORNO YOCTO"
    echo
    echo "GStreamer:"
    echo "Version: $GST_VERSION"
    echo
    echo "Poky:"
    echo "Rama: $POKY_RAMA"
    echo "Commit: $POKY_COMMIT"
    echo
    echo "meta-raspberrypi:"
    echo "Rama: $META_RPI_RAMA"
    echo "Commit: $META_RPI_COMMIT"
    echo
} > "$REPORTE"

cat "$REPORTE"

echo

if [ "$GST_VERSION" = "1.22.12" ] \
   && [ -n "$POKY_COMMIT" ] \
   && [ -n "$META_RPI_COMMIT" ]; then

    echo "PASS: versiones exactas documentadas." \
        | tee -a "$REPORTE"

    echo
    echo "TEST G5 VERSIONES: PASS"

    exit 0
fi

echo "FAIL: informacion de versiones incompleta." \
    | tee -a "$REPORTE"

echo
echo "TEST G5 VERSIONES: FAIL"

exit 1
