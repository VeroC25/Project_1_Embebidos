#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/G3_registry_rpi.txt"
CACHE="/root/.cache/gstreamer-1.0"

mkdir -p "$RESULTADOS"

echo "========================================"
echo "G3 - REGISTRO DE PLUGINS GSTREAMER"
echo "========================================"

echo "Eliminando cache anterior..."

rm -rf "$CACHE"

echo "Regenerando registro..."

gst-inspect-1.0 > /dev/null 2>&1
STATUS=$?

REGISTRO="$(
    find "$CACHE" \
        -maxdepth 1 \
        -type f \
        -name "registry*.bin" \
        2>/dev/null \
        | head -n 1
)"

{
    echo "G3 - REGENERACION DEL REGISTRO GSTREAMER"
    echo
    echo "Codigo gst-inspect: $STATUS"
    echo

    if [ -n "$REGISTRO" ]; then
        echo "Registro generado: $REGISTRO"
        ls -l "$REGISTRO"
    else
        echo "Registro generado: NO ENCONTRADO"
    fi

    echo
} > "$REPORTE"

cat "$REPORTE"

if [ "$STATUS" -eq 0 ] \
   && [ -n "$REGISTRO" ]; then

    echo "PASS: el registro de plugins fue regenerado correctamente." \
        | tee -a "$REPORTE"

    echo
    echo "TEST G3 REGISTRY: PASS"

    exit 0

fi

echo "FAIL: no se pudo regenerar correctamente el registro." \
    | tee -a "$REPORTE"

echo
echo "TEST G3 REGISTRY: FAIL"

exit 1
