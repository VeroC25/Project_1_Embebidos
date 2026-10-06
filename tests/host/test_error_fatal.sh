#!/bin/bash

set -euo pipefail

echo "========================================"
echo " PRUEBA E3 - ERROR FATAL DE GSTREAMER"
echo "========================================"

LOG=$(mktemp)

limpiar() {
    rm -f "$LOG"
}

trap limpiar EXIT

echo
echo "Ejecutando la aplicacion sin dispositivo /dev/video0..."
echo "Se espera que falle de forma controlada."
echo

set +e

CONTROL_ACCESO_MODE=host \
VIDEO_DEVICE=/dev/video99 \
CONTROL_ACCESO_GUI=0 \
timeout 60s \
python3 prueba_integrada_h1.py \
    > "$LOG" 2>&1

CODIGO=$?

set -e

cat "$LOG"

echo
echo "Codigo de salida: $CODIGO"
echo

# timeout devuelve 124 si la aplicacion se quedo esperando.
if [ "$CODIGO" -eq 124 ]; then
    echo "FAIL: la aplicacion no termino despues del error."
    exit 1
fi

# Se espera terminacion con error.
if [ "$CODIGO" -eq 0 ]; then
    echo "FAIL: la aplicacion termino con codigo 0."
    exit 1
fi

# Verificar que realmente hubo un fallo relacionado con GStreamer/camara.
if grep -q "\[GStreamer ERROR\]" "$LOG" ||
   grep -q "No fue posible iniciar el pipeline" "$LOG" ||
   grep -q "Cannot identify device" "$LOG" ||
   grep -q "No such file or directory" "$LOG"; then

    echo "PASS: se detecto el error de la fuente de video."

else
    echo "FAIL: hubo terminacion con error, pero no se encontro"
    echo "evidencia de un fallo esperado de GStreamer/camara."
    exit 1
fi

echo
echo "PASS: la aplicacion no permanecio bloqueada."
echo "PASS: termino con codigo distinto de cero."

echo
echo "========================================"
echo " TEST E3 ERROR FATAL: PASS"
echo "========================================"
