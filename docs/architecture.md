# Arquitectura técnica

## Componentes

- **n8n (Docker Desktop en macOS):** Schedule Trigger diario, nodos de extracción RSS, Code, HTTP Request a DeepSeek, Telegram y control de ramas.
- **DeepSeek API:** selección editorial, fichas analíticas, guion y validación de consistencia. El modelo y el presupuesto de tokens pueden cambiar con la versión exportada.
- **Kokoro (MLX Audio):** servicio TTS local en macOS escuchando en `127.0.0.1:8765`.
- **Bridge Python:** servicio HTTP en macOS en puerto `8766`, con header `X-Bridge-Key` para llamadas desde n8n vía `http://host.docker.internal:8766/render-and-send`.
- **FFmpeg:** concatena fragmentos y produce OGG/Opus.
- **Telegram:** entrega de texto por nodo n8n y voz mediante `sendVoice` en el bridge.

## Recorrido de datos

1. n8n recoge y normaliza noticias recientes.
2. Elimina duplicados exactos y agrupa acontecimientos similares.
3. DeepSeek selecciona los temas relevantes para cinco secciones.
4. Se intenta recuperar el texto permitido de artículos seleccionados, conservando la procedencia.
5. DeepSeek genera análisis fundamentados, guion, auditoría y métricas de uso.
6. n8n manda índice con enlaces a Telegram.
7. Si se habilitó la voz, n8n pasa guion a bridge mediante HTTP autenticado.
8. Bridge divide en fragmentos, llama a Kokoro, utiliza FFmpeg, manda OGG/Opus a Telegram y devuelve una confirmación.
9. Un Error Workflow separado avisa de fallos automáticos en Telegram.

## Fronteras de seguridad

- **Nube:** titulares/extractos y contexto necesarios se envían a DeepSeek; no subir información privada ni credenciales.
- **Local:** n8n en Docker, Kokoro y bridge en host macOS.
- **Salida:** Telegram recibe guion/índice y audio. Configurar destinatario permitido `ALLOWED_CHAT_ID`.
- **Exposición:** mantener puertos 8765/8766 fuera de Internet; restringir acceso al bridge y utilizar clave compartida fuerte.

## Persistencia y recuperación

El bridge guarda el registro reciente de envíos por `run_id` para reducir duplicados. Un éxito del nodo de Telegram no certifica el éxito del audio: la confirmación debe incluir `ok:true` y un `message_id`. Reintentos y controles adicionales deben probarse con el workflow vivo.
