# Declaración de uso de inteligencia artificial

## Alcance

Durante el desarrollo se utilizó inteligencia artificial como herramienta de apoyo para:

- explicar conceptos de Yocto, GStreamer, Linux, Docker y QEMU;
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

- **OpenAI ChatGPT**, utilizado para apoyo técnico durante la integración del sistema, análisis de errores, así como para la organización y redacción de documentación. En la etapa final de integración y documentación se utilizó el modelo **GPT-5.6 Sol**.
- **Google Gemini**, utilizado como herramienta de consulta y apoyo en investigación técnica.
- **Google NotebookLM (Gemini NotebookLM)**, utilizado principalmente para organizar, consultar y resumir fuentes y documentos durante la etapa de investigación.
- **Anthropic Claude**, utilizado como herramienta complementaria de consulta, programación y revisión técnica.


## Nivel de uso

Se considera un uso de **asistencia técnica y documental**:

- diagnóstico guiado;
- explicación;
- revisión;
- generación de borradores.

Las decisiones finales de arquitectura, ejecución sobre hardware, selección de resultados y validación corresponden al equipo del proyecto.
