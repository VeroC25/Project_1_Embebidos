#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/B6_eos_rpi.txt"
LOG="$RESULTADOS/B6_eos_journal_rpi.log"
APP="prueba_integrada_h1.py"

mkdir -p "$RESULTADOS"

rm -f "$REPORTE" "$LOG"


cleanup() {
    systemctl start control-acceso \
        >/dev/null 2>&1 || true
}

trap cleanup EXIT


echo "========================================"
echo " B6 - EOS Y CIERRE CON SYSTEMD"
echo "========================================"
echo


# ============================================================
# VALIDAR QUE EL CODIGO IMPLEMENTA EOS
# ============================================================

FALLOS=0

if grep -q \
    "pipeline.send_event" \
    "$APP" \
    && grep -q \
    "Gst.Event.new_eos()" \
    "$APP"; then

    echo "PASS: el pipeline principal envia EOS."

else

    echo "FAIL: no se encontro EOS del pipeline principal."
    FALLOS=$((FALLOS + 1))

fi


if grep -q \
    "detectar_eos_grabacion" \
    "$APP" \
    && grep -q \
    "bloquear_y_finalizar_grabacion" \
    "$APP"; then

    echo "PASS: las ramas de evidencia tienen cierre EOS."

else

    echo "FAIL: no se encontro coordinacion EOS de evidencia."
    FALLOS=$((FALLOS + 1))

fi


echo
echo "Iniciando servicio..."

systemctl start control-acceso

sleep 4


if ! systemctl is-active \
    --quiet control-acceso; then

    echo "FAIL: control-acceso no esta activo."
    exit 1

fi


INICIO="$(
    date '+%Y-%m-%d %H:%M:%S'
)"

sleep 1

echo "Deteniendo servicio con systemctl stop..."

systemctl stop control-acceso


ESTADO="$(
    systemctl is-active \
        control-acceso \
        2>/dev/null \
        || true
)"


journalctl \
    -u control-acceso \
    --since "$INICIO" \
    --no-pager \
    > "$LOG" 2>&1 \
    || journalctl \
        -u control-acceso \
        -n 120 \
        --no-pager \
        > "$LOG" 2>&1


SIGTERM_OK=0
ENVIO_EOS_OK=0
EOS_OK=0


grep -q \
    "SIGTERM recibido" \
    "$LOG" \
    && SIGTERM_OK=1

grep -q \
    "Enviando EOS" \
    "$LOG" \
    && ENVIO_EOS_OK=1

grep -q \
    "EOS recibido correctamente" \
    "$LOG" \
    && EOS_OK=1


{
    echo "B6 - EOS Y CIERRE CON SYSTEMD"
    echo
    echo "Estado despues de stop: $ESTADO"
    echo
    echo "SIGTERM detectado: $SIGTERM_OK"
    echo "Envio EOS detectado: $ENVIO_EOS_OK"
    echo "EOS confirmado: $EOS_OK"
    echo
} > "$REPORTE"


if [ "$ESTADO" != "inactive" ]; then

    echo \
        "FAIL: el servicio no quedo inactive." \
        | tee -a "$REPORTE"

    FALLOS=$((FALLOS + 1))

else

    echo \
        "PASS: servicio quedo inactive." \
        | tee -a "$REPORTE"

fi


if [ "$SIGTERM_OK" -eq 1 ]; then

    echo \
        "PASS: la aplicacion recibio SIGTERM." \
        | tee -a "$REPORTE"

else

    echo \
        "FAIL: no se encontro SIGTERM." \
        | tee -a "$REPORTE"

    FALLOS=$((FALLOS + 1))

fi


if [ "$ENVIO_EOS_OK" -eq 1 ]; then

    echo \
        "PASS: la aplicacion envio EOS." \
        | tee -a "$REPORTE"

else

    echo \
        "FAIL: no se encontro el envio de EOS." \
        | tee -a "$REPORTE"

    FALLOS=$((FALLOS + 1))

fi


if [ "$EOS_OK" -eq 1 ]; then

    echo \
        "PASS: GStreamer confirmo EOS." \
        | tee -a "$REPORTE"

else

    echo \
        "FAIL: GStreamer no confirmo EOS." \
        | tee -a "$REPORTE"

    FALLOS=$((FALLOS + 1))

fi


echo
echo "Evidencias:"
echo "$REPORTE"
echo "$LOG"


if [ "$FALLOS" -ne 0 ]; then

    echo
    echo "FAIL: B6 presenta $FALLOS fallos."
    exit 1

fi


echo
echo "========================================"
echo " TEST B6 EOS/SYSTEMD: PASS"
echo "========================================"
