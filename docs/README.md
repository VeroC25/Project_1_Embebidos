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

10. [Fundamentos y flujo de trabajo: Yocto Project y GStreamer](10_fundamentos_yocto_gstreamer.md)  
    Flujo de Yocto, características de GStreamer, prototipos gst-launch, dependencias y recetas.

11. [Casos de uso](11_casos_de_uso.md)  
    Actores, CU-01 a CU-04, flujos, relaciones y estado de implementación.

12. [Requerimientos del sistema](12_requerimientos_del_sistema.md)  
    RF, RD, RI, RC, RP, RQ y RU, con trazabilidad y estado actual.

13. [Trazabilidad con la metodología del instructivo](13_trazabilidad_metodologia.md)  
    Matriz de cumplimiento punto por punto con evidencia directa en el repositorio.

## Criterio de documentación

Se separa claramente entre:

- **Validado en Raspberry Pi/Yocto**: observado en el hardware objetivo.
- **Validado en host/Docker/QEMU**: comprobado fuera del hardware final.
