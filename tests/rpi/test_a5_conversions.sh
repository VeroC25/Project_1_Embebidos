#!/bin/sh

set -eu

MODO="${1:-qemu}"

RESULTADOS="resultados"
DOT_DIR="$RESULTADOS/a5_dot"
LOG="$RESULTADOS/A5_pipeline_${MODO}.log"
REPORTE="$RESULTADOS/A5_conversiones_${MODO}.txt"
DOT_FINAL="$RESULTADOS/A5_pipeline_${MODO}.dot"

mkdir -p "$DOT_DIR"

rm -f "$DOT_DIR"/*.dot
rm -f "$LOG" "$REPORTE" "$DOT_FINAL"

echo "========================================"
echo " A5 - ELEMENTOS DE CONVERSION"
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

echo "Iniciando pipeline para generar el grafo real..."
echo

CONTROL_ACCESO_MODE="$CONTROL_ACCESO_MODE" \
CONTROL_ACCESO_GUI=0 \
CONTROL_ACCESO_GPIO=0 \
CONTROL_ACCESO_DATA_DIR="$PWD/resultados/a5_data" \
GST_DEBUG_DUMP_DOT_DIR="$PWD/$DOT_DIR" \
PYTHONUNBUFFERED=1 \
python3 -u prueba_integrada_h1.py \
    > "$LOG" 2>&1 &

PID=$!

DOT=""
I=0

# Esperar hasta 60 segundos por el grafo.
while [ "$I" -lt 60 ]; do

    I=$((I + 1))

    DOT=$(
        find "$DOT_DIR" \
            -maxdepth 1 \
            -type f \
            -name '*pipeline_integrado_PLAYING*.dot' \
            | head -n 1
    )

    if [ -n "$DOT" ]; then
        break
    fi

    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi

    sleep 1
done

# Cerrar la aplicacion de forma coordinada.
if kill -0 "$PID" 2>/dev/null; then
    kill -TERM "$PID"
    wait "$PID" || true
fi

if [ -z "$DOT" ] || [ ! -f "$DOT" ]; then

    echo
    echo "FAIL: no se genero el grafo .dot."
    echo
    echo "Ultimas lineas de la aplicacion:"

    tail -n 30 "$LOG" || true

    exit 1
fi

cp "$DOT" "$DOT_FINAL"

VIDEOCONVERT=$(
    grep -c "GstVideoConvert" "$DOT_FINAL" || true
)

VIDEOSCALE=$(
    grep -c "GstVideoScale" "$DOT_FINAL" || true
)

V4L2CONVERT=$(
    grep -c "GstV4l2Convert" "$DOT_FINAL" || true
)

{
    echo "A5 - CONTEO DEL GRAFO REAL"
    echo "Modo: $MODO"
    echo
    echo "videoconvert: $VIDEOCONVERT"
    echo "videoscale: $VIDEOSCALE"
    echo "v4l2convert: $V4L2CONVERT"
} | tee "$REPORTE"

echo

# El pipeline integrado contiene tres conversiones explícitas:
# visualizacion, OpenCV/QR y encoder H.264.
if [ "$VIDEOCONVERT" -ne 3 ]; then
    echo "FAIL: se esperaban exactamente 3 videoconvert."
    exit 1
fi

if [ "$VIDEOSCALE" -ne 0 ]; then
    echo "FAIL: aparecio videoscale inesperadamente."
    exit 1
fi

if [ "$V4L2CONVERT" -ne 0 ]; then
    echo "FAIL: aparecio v4l2convert inesperadamente."
    exit 1
fi

echo "PASS: se encontraron exactamente los elementos"
echo "de conversion esperados en el grafo real."

echo
echo "Evidencias:"
echo "$DOT_FINAL"
echo "$REPORTE"
echo "$LOG"

echo
echo "========================================"
echo " TEST A5 CONVERSIONES: PASS"
echo "========================================"
