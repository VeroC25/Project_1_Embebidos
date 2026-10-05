# Pruebas y validación

## 1. Criterio

Una función se marca como validada únicamente cuando existe evidencia de ejecución en el entorno indicado.

## 2. Validaciones actuales

| Prueba | Entorno | Estado | Resultado |
|---|---|---|---|
| Imagen Yocto arranca en Raspberry Pi 4 | Raspberry | OK | Boot correcto |
| Servicio systemd habilitado | Raspberry | OK | `active (running)` |
| Cámara OV5647 detectada | Raspberry | OK | libcamera registra OV5647 |
| `libcamerasrc` disponible | Raspberry | OK | plugin presente |
| Captura 1280x720 configurada | Raspberry | OK | negociación observada |
| Streaming RTP/UDP a laptop | Raspberry + Docker | OK | video visible en navegador |
| QR MC001 | Raspberry | OK | ACCESO AUTORIZADO |
| QR NO001 | Raspberry | OK | ACCESO DENEGADO |
| QR TEST123 | Raspberry | OK | ACCESO DENEGADO cuando se decodifica correctamente |
| Evidencia 60 s | Raspberry | OK | MP4 individual guardado |
| Evidencias concurrentes | Raspberry | OK | varias ramas activas/finalizadas |
| Bitácora con ruta de evidencia | Raspberry | OK | ruta relativa registrada |
| Retención de videos 7 días | Host/prueba aislada | OK lógico | elimina solo evidencias vencidas |
| Retención de bitácora 30 días | Host/prueba aislada | OK lógico | conserva líneas recientes/desconocidas |
| Dos contenedores Docker | Laptop | OK | emisor -> vigilante |
| QEMU | QEMU | OK previo | debe repetirse con versión final |

## 3. Evidencia de acceso

Ejemplo esperado de log:

```text
QR detectado:
MC001
Resultado: ACCESO AUTORIZADO
Evento registrado en /var/lib/control-acceso/bitacora_accesos.log
Evidencia asociada: evidencias/evidencia_....mp4
Grabacion de evidencia iniciada.
Duracion: 60 s
```

Para un QR no autorizado:

```text
QR detectado:
NO001
Resultado: ACCESO DENEGADO
```

## 4. Pruebas finales pendientes en Raspberry

### 4.1 Rearme QR

Objetivo:

- mantener un QR visible -> un solo evento;
- retirarlo durante el intervalo de rearme;
- volverlo a presentar -> nuevo evento;
- cambiar a otro QR -> procesarlo sin esperar el fin de las evidencias activas.

### 4.2 FPS real

No usar el capsfilter como evidencia de FPS. Contar frames durante un intervalo conocido.

Registrar:

```text
frames:
duración:
FPS reales = frames / duración
```

### 4.3 Latencia extremo a extremo

Medir desde un evento visible en la escena hasta su aparición en el navegador del vigilante.

### 4.4 CPU y memoria

Registrar durante una prueba representativa:

```bash
top
ps -o pid,%cpu,%mem,rss,cmd -C python3
```

### 4.5 Temperatura y throttling

Con ventilación instalada:

```bash
cat /sys/class/thermal/thermal_zone0/temp
vcgencmd get_throttled
```

Objetivo de checklist:

```text
get_throttled = 0x0
```

### 4.6 Cierre limpio

Durante una evidencia:

```bash
systemctl stop control-acceso
```

Verificar que los MP4 queden reproducibles.

### 4.7 Reinicio automático

Forzar fallo del proceso y comprobar que systemd crea un nuevo PID y recupera el servicio.

### 4.8 Persistencia

Después de reiniciar la Raspberry:

```bash
ls -lh /var/lib/control-acceso/evidencias
tail /var/lib/control-acceso/bitacora_accesos.log
```

### 4.9 GPIO

Validar estado seguro y activación únicamente para acceso autorizado.

## 5. Encoder H.264

`x264enc` está operativo. La ruta `v4l2h264enc` no quedó validada. Mientras esto no se resuelva, las mediciones de CPU corresponden a codificación por software.

## 6. Registro de resultados finales

Completar antes de entrega:

| Métrica | Resultado final |
|---|---|
| FPS reales | PENDIENTE |
| Latencia E2E | PENDIENTE |
| CPU promedio | PENDIENTE |
| RSS | PENDIENTE |
| Temperatura máxima con ventilador | PENDIENTE |
| `get_throttled` | PENDIENTE |
| Tasa de escritura | PENDIENTE final RPi |
| Estado GPIO en boot | PENDIENTE |
| Tiempo de activación de apertura | PENDIENTE |
