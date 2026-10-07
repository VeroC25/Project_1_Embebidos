#!/bin/sh

set -u

FPS="${1:-30.0}"

RESULTADOS="resultados"
RESUMEN="$RESULTADOS/B_resumen_rpi.txt"

mkdir -p "$RESULTADOS"

rm -f "$RESUMEN"

FALLOS=0


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


registrar "BLOQUE B - TOPOLOGIA Y FLUJO"
registrar "Framerate real usado: $FPS fps"
registrar ""


ejecutar \
    "B1" \
    python3 \
    test_b1_tee_queues.py \
    prueba_integrada_h1.py


ejecutar \
    "B2" \
    python3 \
    test_b2_queue_policy.py \
    prueba_integrada_h1.py


ejecutar \
    "B3" \
    python3 \
    test_b3_queue_latency.py \
    prueba_integrada_h1.py \
    "$FPS"


ejecutar \
    "B4" \
    python3 \
    test_b4_appsink.py \
    prueba_integrada_h1.py


# ============================================================
# B5 necesita la cámara, por lo que detenemos el servicio.
# ============================================================

systemctl stop control-acceso \
    >/dev/null 2>&1 || true

sleep 1


ejecutar \
    "B5" \
    python3 \
    test_b5_callback.py \
    prueba_integrada_h1.py \
    15 \
    "$FPS"


systemctl start control-acceso \
    >/dev/null 2>&1 || true

sleep 3


# ============================================================
# B6 prueba explícitamente systemctl stop + EOS.
# ============================================================

ejecutar \
    "B6" \
    ./test_b6_eos_systemd.sh


registrar ""

if [ "$FALLOS" -eq 0 ]; then

    registrar "BLOQUE B: PASS"

    echo
    echo "========================================"
    echo " BLOQUE B COMPLETO: PASS"
    echo "========================================"

    exit 0

fi


registrar "BLOQUE B: FAIL ($FALLOS pruebas)"

echo
echo "========================================"
echo " BLOQUE B: FAIL"
echo " Fallos: $FALLOS"
echo "========================================"

exit 1
