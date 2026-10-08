#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/E2_watchdog_rpi.txt"
LOG="$RESULTADOS/E2_watchdog_rpi.log"

APP="${1:-prueba_integrada_h1.py}"
DATA_DIR="/tmp/e2-data"

mkdir -p "$RESULTADOS"

rm -f \
    "$REPORTE" \
    "$LOG"

rm -rf "$DATA_DIR"
mkdir -p "$DATA_DIR"


cleanup() {

    echo
    echo "Restaurando servicio control-acceso..."

    systemctl start control-acceso \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT


echo "========================================"
echo " E2 - WATCHDOG DE CAMARA"
echo "========================================"
echo
echo "Prueba mediante inyeccion controlada."
echo "No se desconecta la camara ni se modifica el driver."
echo


systemctl stop control-acceso


# ============================================================
# EJECUTAR INYECCION DE PERDIDA DE FRAMES
# ============================================================

echo "Retardo de simulacion: 2 s"
echo "Timeout watchdog: 3 s"
echo


PYTHONUNBUFFERED=1 \
CONTROL_ACCESO_MODE=rpi \
CONTROL_ACCESO_GUI=0 \
CONTROL_ACCESO_GPIO=0 \
CONTROL_ACCESO_DATA_DIR="$DATA_DIR" \
CONTROL_ACCESO_TEST_NO_FRAMES=1 \
CONTROL_ACCESO_TEST_NO_FRAMES_DELAY=2.0 \
python3 "$APP" \
    > "$LOG" 2>&1 &

PID=$!


# ============================================================
# ESPERAR TERMINACION CONTROLADA
# ============================================================

i=0

while kill -0 "$PID" 2>/dev/null \
    && [ "$i" -lt 15 ]; do

    sleep 1
    i=$((i + 1))
done


if kill -0 "$PID" 2>/dev/null; then

    echo "FAIL: la aplicacion seguia activa despues de 15 s."

    kill "$PID" \
        2>/dev/null || true

    wait "$PID" \
        2>/dev/null || true

    STATUS=124

else

    set +e

    wait "$PID"
    STATUS=$?

    set -e

fi


echo
echo "=== LOG E2 ==="

cat "$LOG"


# ============================================================
# VALIDAR RESULTADO
# ============================================================

WATCHDOG_OK=0
SIN_FRAMES_OK=0
ERROR_FATAL_OK=0


grep -q \
    "\[WATCHDOG CAMARA\]" \
    "$LOG" \
    && WATCHDOG_OK=1


grep -q \
    "No se recibieron frames" \
    "$LOG" \
    && SIN_FRAMES_OK=1


grep -q \
    "Terminacion por error fatal" \
    "$LOG" \
    && ERROR_FATAL_OK=1


echo
echo "=== RESULTADOS ==="

echo "Codigo de salida: $STATUS"
echo "Watchdog detectado: $WATCHDOG_OK"
echo "Perdida de frames detectada: $SIN_FRAMES_OK"
echo "Terminacion fatal detectada: $ERROR_FATAL_OK"


{
    echo "E2 - WATCHDOG DE CAMARA"
    echo
    echo "Metodo: inyeccion controlada de perdida de heartbeat"
    echo "Camara desconectada fisicamente: no"
    echo "Driver modificado/unbind: no"
    echo
    echo "Codigo de salida: $STATUS"
    echo "Watchdog detectado: $WATCHDOG_OK"
    echo "Perdida de frames detectada: $SIN_FRAMES_OK"
    echo "Terminacion fatal detectada: $ERROR_FATAL_OK"
} > "$REPORTE"


if [ "$STATUS" -ne 1 ] \
    || [ "$WATCHDOG_OK" -ne 1 ] \
    || [ "$SIN_FRAMES_OK" -ne 1 ] \
    || [ "$ERROR_FATAL_OK" -ne 1 ]; then

    echo
    echo "TEST E2 WATCHDOG: FAIL"

    echo \
        "TEST E2 WATCHDOG: FAIL" \
        >> "$REPORTE"

    exit 1
fi


echo
echo "========================================"
echo " TEST E2 WATCHDOG: PASS"
echo "========================================"

echo \
    "TEST E2 WATCHDOG: PASS" \
    >> "$REPORTE"
