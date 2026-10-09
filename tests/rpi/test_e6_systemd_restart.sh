#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/E6_systemd_restart_rpi.txt"

mkdir -p "$RESULTADOS"

echo "========================================"
echo "E6 - REINICIO AUTOMATICO POR SYSTEMD"
echo "========================================"

PID_ANTES="$(
    systemctl show \
        -p MainPID \
        --value \
        control-acceso
)"

RESTART="$(
    systemctl show \
        -p Restart \
        --value \
        control-acceso
)"

RESTART_SEC="$(
    systemctl show \
        -p RestartUSec \
        --value \
        control-acceso
)"

echo "PID antes: $PID_ANTES"
echo "Restart=$RESTART"
echo "RestartUSec=$RESTART_SEC"

if [ -z "$PID_ANTES" ] || [ "$PID_ANTES" = "0" ]; then

    echo "FAIL: el servicio no tiene PID principal."
    exit 1

fi

if [ "$RESTART" != "on-failure" ]; then

    echo "FAIL: Restart no es on-failure."
    exit 1

fi

INICIO="$(date "+%Y-%m-%d %H:%M:%S")"

echo
echo "Enviando SIGKILL al proceso principal..."

kill -9 "$PID_ANTES"

echo "Esperando reinicio de systemd..."
sleep 8

PID_DESPUES="$(
    systemctl show \
        -p MainPID \
        --value \
        control-acceso
)"

ESTADO="$(
    systemctl is-active \
        control-acceso \
        2>/dev/null || true
)"

{
    echo "E6 - REINICIO AUTOMATICO POR SYSTEMD"
    echo
    echo "Restart=$RESTART"
    echo "RestartUSec=$RESTART_SEC"
    echo "PID antes: $PID_ANTES"
    echo "PID despues: $PID_DESPUES"
    echo "Estado final: $ESTADO"
    echo
    echo "Journal:"
    journalctl -u control-acceso \
        --since "$INICIO" \
        --no-pager \
        2>/dev/null \
        | grep -E \
        "Main process exited|Failed with result|Scheduled restart|Started Sistema" \
        || true
} > "$REPORTE"

cat "$REPORTE"

echo

if [ "$ESTADO" = "active" ] \
   && [ -n "$PID_DESPUES" ] \
   && [ "$PID_DESPUES" != "0" ] \
   && [ "$PID_DESPUES" != "$PID_ANTES" ]; then

    echo "PASS: systemd reinicio correctamente el servicio." \
        | tee -a "$REPORTE"

    echo
    echo "TEST E6 SYSTEMD RESTART: PASS"

    exit 0

fi

echo "FAIL: systemd no recupero correctamente el servicio." \
    | tee -a "$REPORTE"

echo
echo "TEST E6 SYSTEMD RESTART: FAIL"

exit 1
