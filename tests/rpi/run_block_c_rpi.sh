#!/bin/sh

set -u

FPS_REAL="${1:-30.0}"

RESULTADOS="resultados"
RESUMEN="$RESULTADOS/C_resumen_rpi.txt"

mkdir -p "$RESULTADOS"

rm -f "$RESUMEN"

FALLOS=0


cleanup() {

    systemctl start control-acceso \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT


registrar() {
    echo "$1" | tee -a "$RESUMEN"
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


registrar "BLOQUE C - HARDWARE VS SOFTWARE"
registrar "FPS real usado: $FPS_REAL"
registrar ""


systemctl stop control-acceso \
    >/dev/null 2>&1 || true

sleep 2


ejecutar \
    "C1" \
    ./test_c1_hw_encoder.sh


if [ -f resultados/C1_hw_device.txt ] \
    && [ -f resultados/C1_hw_format.txt ]; then

    ejecutar \
        "C2" \
        python3 \
        test_c2_cpu_compare.py \
        60

    ejecutar \
        "C3" \
        ./test_c3_hw_operating_point.sh \
        "$FPS_REAL"

    ejecutar \
        "C4" \
        ./test_c4_dmabuf.sh

else

    registrar "C2: FAIL (C1 no produjo dispositivo/formato)"
    registrar "C3: FAIL (C1 no produjo dispositivo/formato)"
    registrar "C4: FAIL (C1 no produjo dispositivo/formato)"

    FALLOS=$((FALLOS + 3))

fi


registrar ""


if [ "$FALLOS" -eq 0 ]; then

    registrar "BLOQUE C: PASS"

    echo
    echo "========================================"
    echo " BLOQUE C COMPLETO: PASS"
    echo "========================================"

    exit 0

fi


registrar "BLOQUE C: FAIL ($FALLOS pruebas)"

echo
echo "========================================"
echo " BLOQUE C: FAIL"
echo " Fallos: $FALLOS"
echo "========================================"

exit 1
