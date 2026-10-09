#!/bin/sh

set -u

RESULTADOS="resultados"
REPORTE="$RESULTADOS/E3_recovery_policy_rpi.txt"

mkdir -p "$RESULTADOS"

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

CODIGO="/usr/bin/control-acceso"

OK=1

{
    echo "E3 - POLITICA DE RECUPERACION"
    echo
    echo "Decision:"
    echo "Ante un error fatal, la aplicacion termina"
    echo "con codigo distinto de cero."
    echo
    echo "La recuperacion queda delegada a systemd."
    echo
    echo "Restart=$RESTART"
    echo "RestartUSec=$RESTART_SEC"
    echo

    if grep -q \
        "error_fatal.is_set" \
        "$CODIGO"; then

        echo "[PASS] La aplicacion controla errores fatales."

    else

        echo "[FAIL] No se encontro manejo de error fatal."
        OK=0
    fi

    if grep -q \
        "raise SystemExit" \
        "$CODIGO"; then

        echo "[PASS] La aplicacion puede terminar con error."

    else

        echo "[FAIL] No se encontro salida no-cero."
        OK=0
    fi

    if [ "$RESTART" = "on-failure" ]; then

        echo "[PASS] systemd usa Restart=on-failure."

    else

        echo "[FAIL] Restart=$RESTART"
        OK=0
    fi

    echo

    if [ "$OK" -eq 1 ]; then

        echo "PASS: politica de recuperacion definida y documentada."

    else

        echo "FAIL: politica incompleta."
    fi

} | tee "$REPORTE"

if [ "$OK" -ne 1 ]; then
    exit 1
fi

echo
echo "TEST E3 RECOVERY POLICY: PASS"
