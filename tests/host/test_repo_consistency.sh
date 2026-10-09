#!/bin/bash

set -euo pipefail

APP="prueba_integrada_h1.py"
YOCTO_APP="meta-control-acceso/recipes-apps/control-acceso/files/prueba_integrada_h1.py"
SERVICE="meta-control-acceso/recipes-apps/control-acceso/files/control-acceso.service"

echo "========================================"
echo " PRUEBA DE CONSISTENCIA DEL REPOSITORIO "
echo "========================================"

echo
echo "[1/4] Verificando sintaxis Python..."

python3 -m py_compile "$APP"

echo "PASS: sintaxis Python correcta."


echo
echo "[2/4] Verificando copia usada por Yocto..."

if cmp -s "$APP" "$YOCTO_APP"; then
    echo "PASS: ambas copias de la aplicacion son identicas."
else
    echo "FAIL: prueba_integrada_h1.py y la copia de Yocto son diferentes."
    exit 1
fi


echo
echo "[3/4] Verificando politica de retencion..."

grep -q 'DIAS_RETENCION_VIDEO = 7' "$APP"
grep -q 'DIAS_RETENCION_BITACORA = 30' "$APP"

echo "PASS: videos = 7 dias, bitacora = 30 dias."


echo
echo "[4/4] Verificando politica systemd..."

grep -q '^Restart=on-failure$' "$SERVICE"

echo "PASS: Restart=on-failure configurado."


echo
echo "========================================"
echo " TEST REPO CONSISTENCY: PASS"
echo "========================================"
