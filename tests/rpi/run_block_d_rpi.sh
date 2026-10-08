#!/bin/sh

set -u

FPS="${1:-30.0}"

RESULTADOS="resultados"
RESUMEN="$RESULTADOS/D_resumen_rpi.txt"

mkdir -p "$RESULTADOS"

rm -f "$RESUMEN"

FALLOS=0


cleanup() {

    systemctl start control-acceso \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT


registrar() {

    echo "$1" \
        | tee -a "$RESUMEN"
}


ejecutar() {

    NOMBRE="$1"
    shift

    echo
    echo "========================================"
    echo " EJECUTANDO $NOMBRE"
    echo "========================================"

    "$@"

    ESTADO=$?

    if [ "$ESTADO" -eq 0 ]; then

        registrar "$NOMBRE: PASS"

    else

        registrar "$NOMBRE: FAIL"

        FALLOS=$((FALLOS + 1))

    fi
}


registrar "BLOQUE D - LATENCIA"
registrar "FPS real usado: $FPS fps"
registrar ""


# La cámara debe quedar libre.
systemctl stop control-acceso \
    >/dev/null 2>&1 || true

sleep 2


# D1 - tracer real.
ejecutar \
    "D1" \
    python3 \
    test_d1_latency.py \
    prueba_integrada_h1.py \
    20


# D2 NO se automatiza.
registrar \
    "D2: PENDIENTE PRUEBA MANUAL E2E"


# D3 - GOP/keyframes.
ejecutar \
    "D3" \
    python3 \
    test_d3_keyframes.py \
    prueba_integrada_h1.py \
    "$FPS"


# D4 depende de D1.
if [ -f \
    resultados/D1_latency_tracer_rpi.log ]; then

    ejecutar \
        "D4" \
        python3 \
        test_d4_latency_budget.py

else

    registrar \
        "D4: FAIL (falta evidencia D1)"

    FALLOS=$((FALLOS + 1))

fi


registrar ""


if [ "$FALLOS" -eq 0 ]; then

    registrar \
        "BLOQUE D AUTOMATICO: PASS"

    registrar \
        "D2 permanece manual."

    echo
    echo "========================================"
    echo " BLOQUE D AUTOMATICO: PASS"
    echo " D2: PENDIENTE MANUAL"
    echo "========================================"

    exit 0
fi


registrar \
    "BLOQUE D: FAIL ($FALLOS pruebas automaticas)"


echo
echo "========================================"
echo " BLOQUE D: FAIL"
echo " Fallos automaticos: $FALLOS"
echo "========================================"

exit 1
