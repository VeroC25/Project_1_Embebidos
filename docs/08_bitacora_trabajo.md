# Bitácora técnica resumida

> Este archivo sirve como base para la bitácora individual. Antes de entregar, cada integrante debe completar sus fechas, horas y actividades propias.

## Hitos principales

### Definición del sistema

- selección de Raspberry Pi 4 como target;
- selección de cámara Raspberry Pi Camera Board v1.3 / OV5647;
- identificación mediante QR leído por la misma cámara;
- definición de evidencia persistente y transmisión al vigilante.

### Prototipo en Ubuntu

- pruebas iniciales de GStreamer;
- integración Python + GStreamer;
- OpenCV/QR en hilo separado;
- grabación MP4;
- RTP/UDP;
- validaciones de latencia, estabilidad y manejo de errores.

### Docker

- contenedor emisor con video sintético;
- contenedor vigilante receptor;
- interfaz web MJPEG;
- validación de comunicación entre dos contenedores;
- variante de integración con solo el vigilante para recibir desde Raspberry.

### Yocto

- integración de meta-raspberrypi, meta-openembedded y capa propia;
- creación de `control-acceso-image.bb`;
- receta de la aplicación;
- servicio systemd;
- configuración OV5647;
- inclusión de libcamera-gst, OpenCV y x264.

### Cámara OV5647

Problema encontrado: la imagen inicial no incluía correctamente el overlay OV5647.

Diagnóstico:

- módulos del kernel presentes;
- overlay ausente;
- sensor no aparecía en el media graph.

Solución:

- incluir `ov5647.dtbo`;
- desactivar configuración legacy;
- fijar `dtoverlay=ov5647`.

Resultado:

- `cam -l` detecta la cámara;
- `media-ctl` identifica el sensor;
- `libcamerasrc` funciona.

### Encoder

`v4l2h264enc` estuvo disponible pero falló al iniciar la ruta de codificación. Se adoptó `x264enc` como fallback funcional. Este punto queda documentado como limitación técnica.

### Integración Raspberry -> Docker

- Ethernet directo;
- laptop `10.42.0.1`;
- Raspberry obteniendo `10.42.0.x`;
- puerto UDP 5000;
- video visible en `localhost:8081`.

### QR

- identificador autorizado: `MC001`;
- pruebas denegadas: `NO001`, `TEST123`;
- se observaron dificultades de enfoque/decodificación con algunos QR complejos;
- QR simples permitieron validar correctamente la lógica autorizado/denegado.

### Evidencia

Evolución:

1. archivo continuo;
2. evidencia independiente por evento;
3. duración fija de 60 s;
4. nombre único por timestamp;
5. ruta del video en bitácora;
6. varias evidencias concurrentes;
7. retención de video 7 días y bitácora 30 días.

### Temperatura

Durante pruebas sostenidas sin ventilación activa se observó calentamiento considerable y degradación visual de la cámara. La temperatura registrada llegó a aproximadamente 62.8 °C durante la aplicación. Se instaló ventilador y la imagen de cámara volvió a operar correctamente.

Prueba final de temperatura y throttling con ventilador: pendiente.

## Problemas relevantes y solución

| Problema | Acción |
|---|---|
| AppArmor bloquea BitBake en Ubuntu 26.04 | Ajuste temporal de user namespaces |
| Disco del host lleno durante builds | Limpieza selectiva de builds anteriores |
| Cámara no detectada | Overlay OV5647 + configuración moderna |
| `libcamerasrc` ausente | Instalar `libcamera-gst` |
| `x264enc` ausente | Plugins ugly + licencia commercial |
| Hardware encoder falla | Fallback `x264enc` |
| Host key SSH cambia al reflashear | `ssh-keygen -R` |
| Docker DNS intermitente | Reinicio daemon / reutilización de imagen local |
| QR complejos no decodifican bien | QR simples de prueba |
| Calentamiento | Ventilación activa |

## Pendientes para cerrar la bitácora

- circuito GPIO;
- resultados cuantitativos finales;
- última build Yocto;
- validación de QEMU con la versión entregada;
- preparación y resultado de la demostración presencial.
