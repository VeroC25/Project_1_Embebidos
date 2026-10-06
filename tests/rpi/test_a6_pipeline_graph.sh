#!/bin/bash

set -euo pipefail

MODO="${1:-qemu}"

RESULTADOS="resultados"
DOT_DIR="$RESULTADOS/a6_dot"
LOG="$RESULTADOS/A6_pipeline_${MODO}.log"
DOT_FINAL="$RESULTADOS/A6_pipeline_${MODO}.dot"
REPORTE="$RESULTADOS/A6_revision_${MODO}.txt"

mkdir -p "$DOT_DIR"
rm -f "$DOT_DIR"/*.dot
rm -f "$LOG" "$DOT_FINAL" "$REPORTE"

echo "========================================"
echo " A6 - GRAFO DEL PIPELINE"
echo " Modo: $MODO"
echo "========================================"
echo

case "$MODO" in

    qemu)
        CONTROL_ACCESO_MODE="qemu"
        ;;

    rpi)
        CONTROL_ACCESO_MODE="rpi"
        ;;

    *)
        echo "Uso:"
        echo "  $0 qemu"
        echo "  $0 rpi"
        exit 1
        ;;
esac


echo "Iniciando aplicacion para generar el grafo..."

CONTROL_ACCESO_MODE="$CONTROL_ACCESO_MODE" \
CONTROL_ACCESO_GUI=0 \
CONTROL_ACCESO_DATA_DIR="$PWD/resultados/a6_data" \
GST_DEBUG_DUMP_DOT_DIR="$PWD/$DOT_DIR" \
PYTHONUNBUFFERED=1 \
python3 -u prueba_integrada_h1.py \
    > "$LOG" 2>&1 &

PID=$!

DOT=""

# Esperar hasta 60 segundos por el grafo.
for i in $(seq 1 60); do

    DOT=$(find "$DOT_DIR" \
        -maxdepth 1 \
        -type f \
        -name '*pipeline_integrado_PLAYING*.dot' \
        | head -n 1)

    if [ -n "$DOT" ]; then
        break
    fi

    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi

    sleep 1
done


# Cierre coordinado.
if kill -0 "$PID" 2>/dev/null; then
    kill -TERM "$PID"
    wait "$PID" || true
fi


if [ -z "$DOT" ] || [ ! -f "$DOT" ]; then

    echo "FAIL: no se genero el archivo .dot."
    echo
    echo "Ultimas lineas del log:"
    tail -n 30 "$LOG" || true

    exit 1
fi


cp "$DOT" "$DOT_FINAL"


# ============================================================
# REVISION AUTOMATICA DE LA TOPOLOGIA
# ============================================================

TEES=$(grep -c "GstTee" "$DOT_FINAL" || true)
QUEUES=$(grep -c "GstQueue" "$DOT_FINAL" || true)
APPSINKS=$(grep -c "GstAppSink" "$DOT_FINAL" || true)
UDPSINKS=$(grep -c "GstUDPSink" "$DOT_FINAL" || true)
VIDEOCONVERT=$(grep -c "GstVideoConvert" "$DOT_FINAL" || true)


{
    echo "A6 - REVISION DEL GRAFO REAL"
    echo "Modo: $MODO"
    echo
    echo "GstTee encontrados: $TEES"
    echo "GstQueue encontrados: $QUEUES"
    echo "GstAppSink encontrados: $APPSINKS"
    echo "GstUDPSink encontrados: $UDPSINKS"
    echo "GstVideoConvert encontrados: $VIDEOCONVERT"
    echo
} | tee "$REPORTE"


FALLOS=0


if [ "$TEES" -lt 2 ]; then
    echo "FAIL: se esperaban al menos 2 elementos tee." | tee -a "$REPORTE"
    FALLOS=$((FALLOS + 1))
else
    echo "PASS: se encontraron los dos tee principales." | tee -a "$REPORTE"
fi


if [ "$QUEUES" -lt 4 ]; then
    echo "FAIL: se esperaban al menos 4 queues en el grafo base." | tee -a "$REPORTE"
    FALLOS=$((FALLOS + 1))
else
    echo "PASS: existen queues independientes en las ramas." | tee -a "$REPORTE"
fi


if [ "$APPSINKS" -lt 1 ]; then
    echo "FAIL: no se encontro la rama de analisis/QR." | tee -a "$REPORTE"
    FALLOS=$((FALLOS + 1))
else
    echo "PASS: se encontro la rama appsink/QR." | tee -a "$REPORTE"
fi


if [ "$UDPSINKS" -lt 1 ]; then
    echo "FAIL: no se encontro la rama de streaming RTP/UDP." | tee -a "$REPORTE"
    FALLOS=$((FALLOS + 1))
else
    echo "PASS: se encontro la rama de streaming RTP/UDP." | tee -a "$REPORTE"
fi


if [ "$VIDEOCONVERT" -lt 3 ]; then
    echo "FAIL: faltan elementos videoconvert esperados." | tee -a "$REPORTE"
    FALLOS=$((FALLOS + 1))
else
    echo "PASS: se encontraron los videoconvert esperados." | tee -a "$REPORTE"
fi


echo | tee -a "$REPORTE"


if [ "$FALLOS" -ne 0 ]; then
    echo "FAIL: el grafo presenta $FALLOS comprobaciones incorrectas." | tee -a "$REPORTE"
    exit 1
fi


echo "PASS: el grafo fue generado y su estructura" | tee -a "$REPORTE"
echo "principal fue revisada automaticamente." | tee -a "$REPORTE"

echo
echo "Evidencias:"
echo "$DOT_FINAL"
echo "$REPORTE"
echo "$LOG"

echo
echo "========================================"
echo " TEST A6 GRAFO: PASS"
echo "========================================"
