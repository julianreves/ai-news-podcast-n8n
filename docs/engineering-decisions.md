# Decisiones de ingeniería y compromisos

## Un flujo editorial y uno para alertas

Se mantiene un único flujo n8n de producción dividido visualmente en secciones. El Error Trigger requiere un workflow separado para avisar de fallos aun cuando el principal se interrumpe.

## Uso de LLM

Se prefirió DeepSeek para clasificación y análisis sustancial, con más presupuesto de razonamiento en el análisis profundo. La prioridad es distinguir hechos, inferencias y señales a vigilar, no minimizar artificialmente tokens. Se registran tokens y coste estimado por ejecución.

## Fuentes

Se priorizan proveedores creíbles y accesibles sin suscripción. WSJ y The Economist pueden aportar titulares por RSS, pero su contenido de pago se considera contexto parcial. No se eluden restricciones de acceso y no se republican textos íntegros de terceros.

## Voz en Mac mini M1

Se eligió Kokoro local en Apple Silicon para no consumir créditos de inferencia por cada minuto de voz. El bridge desacopla el flujo de n8n de dependencias de MLX, FFmpeg y la API sendVoice.

## Respuestas vacías de la API

Durante las pruebas un nodo HTTP completó sin datos válidos; un validador posterior detuvo el flujo. Este caso motivó distinguir éxito de transporte (HTTP) de éxito semántico (JSON y fichas válidas), añadir diagnóstico de respuesta y diseñar reintentos.

## Envío de Telegram

Se encontró un conflicto de formato Markdown en el envío del índice. La solución es codificar el texto correctamente (p. ej. HTML escapado) y manejar límites de tamaño de Telegram. El índice no sustituye la confirmación del envío de voz.

## Pendientes de endurecimiento

- Verificar feeds activos desde la red del contenedor.
- Confirmar el envío desatendido de audio y registrar el mensaje de Telegram.
- Probar validaciones y reintentos ante respuestas JSON vacías o truncadas.
- Configurar aviso externo cuando el Mac mini o Docker no estén disponibles.
- Integrar prueba de contrato e2e en entorno de staging.
