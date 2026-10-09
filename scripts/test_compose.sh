
#!/bin/bash
set -euo pipefail

# Crear un entorno de prueba independiente.
PROYECTO="control-acceso-ci-${BUILD_NUMBER:-$$}"

COMPOSE=(
    docker compose
    -p "$PROYECTO"
    -f compose.offline.yaml
)

# Eliminar únicamente los contenedores de esta prueba.
limpiar() {
    echo "Deteniendo los contenedores de prueba..."
    "${COMPOSE[@]}" down --remove-orphans || true
}

trap limpiar EXIT

# Verificar que la imagen y la configuración estén disponibles.
echo "Comprobando requisitos..."

docker image inspect control-acceso-dev:ci > /dev/null
"${COMPOSE[@]}" config -q

# Iniciar el emisor y el vigilante sin descargar imágenes.
echo "Iniciando los dos contenedores..."

"${COMPOSE[@]}" up -d --no-build --pull never

# Confirmar que los dos servicios estén en ejecución.
test -n "$("${COMPOSE[@]}" ps --status running -q emisor)"
test -n "$("${COMPOSE[@]}" ps --status running -q vigilante)"

# Esperar hasta 60 segundos a que lleguen los frames.
echo "Comprobando la recepción de video..."

VALIDADO=0

for INTENTO in $(seq 1 30); do

    REGISTRO=$("${COMPOSE[@]}" logs \
        --no-color --tail=100 vigilante)

    # Comprobar resolución y un mínimo de 30 frames decodificados.
    if grep -Eq 'width=\(int\)1280' <<< "$REGISTRO" &&
       grep -Eq 'height=\(int\)720' <<< "$REGISTRO" &&
       grep -Eq 'rendered: ([3-9][0-9]|[1-9][0-9]{2,})' <<< "$REGISTRO"
    then
        VALIDADO=1
        break
    fi

    sleep 2
done

# Mostrar un diagnóstico si no se cumple alguna condición.
if [ "$VALIDADO" -ne 1 ]; then
    echo "ERROR: no se pudo validar la comunicación."
    "${COMPOSE[@]}" logs --tail=30
    exit 1
fi

# Presentar la evidencia de recepción.
echo "Resolución recibida: 1280x720"
echo "Se comprobaron al menos 30 frames decodificados."

grep 'rendered:' <<< "$REGISTRO" | tail -n 3

echo "Prueba de comunicación: SUCCESS"
