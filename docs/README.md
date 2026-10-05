# Índice de documentación

Esta carpeta concentra la documentación técnica del Proyecto 1.

## Documentos

1. [Arquitectura del sistema](01_arquitectura.md)  
   Componentes, interfaces, flujo de datos y decisiones de diseño.

2. [Pipeline GStreamer](02_pipeline_gstreamer.md)  
   Captura, OpenCV/QR, H.264, evidencia y RTP/UDP.

3. [Yocto: construcción e instalación](03_yocto_build_install.md)  
   Versiones fijadas, configuración, build, flasheo y primer arranque.

4. [Docker y QEMU](04_docker_qemu.md)  
   Demostración de dos contenedores, receptor final y estado de QEMU.

5. [Circuito y GPIO](05_circuito_gpio.md)  
   Diseño propuesto para salida de apertura e indicadores; incluye estado seguro.

6. [Pruebas y validación](06_validacion.md)  
   Evidencias ya obtenidas, pruebas finales y métricas pendientes.

7. [Demostración presencial](07_demostracion.md)  
   Orden recomendado para mostrar el sistema al profesor.

8. [Bitácora técnica resumida](08_bitacora_trabajo.md)  
   Hitos, problemas encontrados y soluciones aplicadas.

9. [Uso de inteligencia artificial](09_uso_ia.md)  
   Declaración de alcance y uso de herramientas de IA.

## Criterio de documentación

Se separa claramente entre:

- **Validado en Raspberry Pi/Yocto**: observado en el hardware objetivo.
- **Validado en host/Docker/QEMU**: comprobado fuera del hardware final.
- **Pendiente**: todavía requiere implementación o evidencia final.

Esto evita presentar como resultado final una condición que solo haya sido ensayada en Ubuntu o simulación.
