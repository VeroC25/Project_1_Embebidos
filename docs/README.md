# Índice de documentación

Esta carpeta concentra la documentación técnica del sistema de control de acceso desarrollado con **Raspberry Pi 4, Yocto Project, GStreamer, OpenCV y Docker**.

## Documentos

1. [Arquitectura del sistema](01_arquitectura.md)  
   Describe los componentes principales, el flujo de datos, la concurrencia, la transmisión, las evidencias, el GPIO y la recuperación mediante systemd.

2. [Pipeline GStreamer](02_pipeline_gstreamer.md)  
   Explica la captura de video, las ramas del pipeline, procesamiento QR, codificación H.264, RTP/UDP, evidencias dinámicas y manejo de EOS.

3. [Yocto: construcción e instalación](03_yocto_build_install.md)  
   Documenta las capas, versiones, configuración, recetas, construcción de la imagen, flasheo de la microSD y puesta en operación de la Raspberry Pi.

4. [Docker y QEMU](04_docker_qemu.md)  
   Describe la estación de vigilancia, el emisor sintético, Docker Compose, el entorno de CI y el uso de QEMU como entorno de emulación.

5. [Circuito y GPIO](05_circuito_gpio.md)  
   Documenta la lógica de apertura mediante BCM17, el estado seguro y las consideraciones para conectar una etapa de potencia externa.

6. [Pruebas y validación](06_validacion.md)  
   Resume la metodología de pruebas, los resultados obtenidos, métricas de desempeño, recuperación ante fallos y la limitación encontrada con el encoder H.264 por hardware.

7. [Operación y demostración](07_demostracion.md)  
   Presenta el procedimiento para iniciar, operar y demostrar el sistema integrado, incluyendo vigilancia, QR, evidencias, bitácora y recuperación.

8. [Bitácora técnica del desarrollo](08_bitacora_trabajo.md)  
   Resume la evolución técnica del proyecto, los principales problemas encontrados, las soluciones adoptadas y las decisiones de arquitectura.

9. [Uso de inteligencia artificial](09_uso_ia.md)  
   Declara de forma resumida cómo se utilizaron herramientas de inteligencia artificial como apoyo técnico y documental.

10. [Fundamentos y flujo de trabajo: Yocto Project y GStreamer](10_fundamentos_yocto_gstreamer.md)  
    Explica los fundamentos de Yocto, BitBake, capas, recetas, GStreamer, caps, `tee`, `queue`, `appsink`, RTP, EOS y el flujo metodológico utilizado.

11. [Casos de uso](11_casos_de_uso.md)  
    Define los actores y los casos de uso principales del sistema: solicitud de acceso, validación, vigilancia, evidencia, apertura y administración.

12. [Requerimientos del sistema](12_requerimientos_del_sistema.md)  
    Especifica los requerimientos funcionales, de desempeño, interfaz, persistencia, seguridad funcional, plataforma, despliegue y trazabilidad.

13. [Trazabilidad y metodología](13_trazabilidad_metodologia.md)  
    Relaciona casos de uso, requerimientos, arquitectura, implementación, recetas Yocto, pruebas y evidencias.

---

## Estructura documental

La documentación sigue el flujo:

```text
casos de uso
→ requerimientos
→ arquitectura
→ implementación
→ despliegue
→ validación
→ demostración
```

Los documentos técnicos describen por separado:

- el diseño del sistema;
- la implementación;
- los resultados de validación.

Esta separación evita confundir una capacidad implementada con una función experimentalmente validada.

---

## Archivos principales relacionados

Además de la documentación, el repositorio contiene:

```text
prueba_integrada_h1.py
Dockerfile
compose.yaml
compose.web.yaml
compose.offline.yaml
Jenkinsfile
meta-control-acceso/
yocto-config/
docker/
scripts/
tests/
resultados/
```

Estos archivos contienen la implementación, configuración, automatización y evidencia utilizada por el proyecto.

---

## Lectura recomendada

Para una revisión completa del proyecto se recomienda el siguiente orden:

```text
README.md
→ 11_casos_de_uso.md
→ 12_requerimientos_del_sistema.md
→ 01_arquitectura.md
→ 02_pipeline_gstreamer.md
→ 03_yocto_build_install.md
→ 04_docker_qemu.md
→ 05_circuito_gpio.md
→ 06_validacion.md
→ 07_demostracion.md
```

Los documentos `08`, `09`, `10` y `13` complementan la revisión con el proceso de desarrollo, uso de IA, fundamentos técnicos y trazabilidad global.
