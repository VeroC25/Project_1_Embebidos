# Declaración de uso de inteligencia artificial

## Alcance

Durante el desarrollo se utilizó inteligencia artificial como herramienta de apoyo para:

- explicar conceptos de Yocto, GStreamer, Linux, Docker y QEMU;
- proponer pasos de diagnóstico;
- revisar comandos antes de ejecutarlos;
- ayudar a interpretar logs;
- organizar documentación técnica;
- revisar consistencia entre código, receta Yocto y arquitectura;
- sugerir pruebas de validación;
- apoyar la redacción de diagramas y documentación.

## Límites de uso

La herramienta de IA no sustituyó las pruebas experimentales. Las afirmaciones marcadas como validadas se basan en ejecuciones realizadas por el equipo en Ubuntu, Docker, QEMU o Raspberry Pi según corresponda.

Los comandos destructivos o de bajo nivel —por ejemplo `dd`, cambios de red, systemd y modificaciones del sistema de archivos— fueron ejecutados manualmente y sus resultados verificados por el equipo.

## Modelo

En la fase de integración y documentación final se utilizó:

```text
OpenAI ChatGPT
Modelo: GPT-5.6 Sol
```

Si durante otras fases se utilizaron modelos o herramientas diferentes, deben agregarse aquí antes de entregar.

## Nivel de uso

Se considera un uso de **asistencia técnica y documental**:

- diagnóstico guiado;
- explicación;
- revisión;
- generación de borradores;
- propuestas de comandos y pruebas.

Las decisiones finales de arquitectura, ejecución sobre hardware, selección de resultados y validación corresponden al equipo del proyecto.
