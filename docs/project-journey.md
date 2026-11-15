# Construcción del proyecto: bitácora

## Necesidad original

Transformar noticias dispersas de México, España, inteligencia artificial, geopolítica y economía en un resumen diario escuchable con explicaciones de *qué ocurrió*, *por qué importa* y *qué vigilar*.

## Inspiración

El repositorio [`kindle-news-filter`](https://github.com/sebagarciar/kindle-news-filter) motivó la idea de curación personalizada. La solución se replanteó para podcasts breves en Telegram, con enfoque analítico y despliegue n8n en Mac mini.

## Evolución del prototipo

1. RSS y agrupación inicial de acontecimientos.
2. Selección y análisis de DeepSeek, más guion y auditoría.
3. Expansión de fuentes, incluidos feeds para negocios de WSJ y The Economist.
4. Integración de bot de Telegram para índice de enlaces.
5. Incorporación de Kokoro en Mac mini y bridge de voz para `sendVoice`.
6. Incorporación de workflow de alertas y controles de errores.

## Fallos que generaron aprendizaje

- Telegram rechazó texto por marcado Markdown sin escapar.
- Hubo ejecuciones finalizadas sin evidencia de haber pasado por el nodo Kokoro.
- En otra ejecución DeepSeek devolvió una salida vacía al pasar por el análisis profundo.

Estos problemas ilustran la importancia de validar respuestas, asegurar observabilidad y no confundir ejecución técnica con resultado editorial o entrega.

## Cómo mantener la bitácora

Registrar fecha, cambio, motivo, resultado del test y referencia al commit. No publicar capturas que contengan credenciales, identificadores personales o contenido protegido por derechos de autor.
