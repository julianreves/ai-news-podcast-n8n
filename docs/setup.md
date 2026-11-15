# Instalación y reproducción

## Requisitos

- Mac mini con Apple Silicon y macOS; Docker Desktop corriendo n8n.
- Python 3.11+ y FFmpeg en macOS.
- Kokoro MLX Audio disponible como servidor HTTP local en puerto 8765.
- Cuenta y credencial DeepSeek, bot de Telegram con Chat ID y clave compartida del bridge.

## 1. Exportar workflows actuales

En cada workflow n8n: abrir **Editor → menú `...` → Download**. Exportar tanto el workflow principal como el de alertas. **Usar las versiones actuales del editor**, no snapshots anteriores compartidos durante el desarrollo.

## 2. Sanitizar antes de publicar

```bash
python3 scripts/sanitize_n8n_export.py ./podcast-current.json ./workflows/podcast-daily.json
python3 scripts/sanitize_n8n_export.py ./alerts-current.json ./workflows/error-alerts.json
```

El script retira referencias a credenciales y sustituye ciertos identificadores y tokens visibles, **pero no sustituye una revisión manual**. Revisar especialmente código JavaScript incrustado, URL, encabezados, Chat ID, nombres de credenciales, capturas y respuestas fijadas en nodos (pinned data). Consultar [security-checklist.md](security-checklist.md).

## 3. Preparar credenciales en n8n

- Credencial DeepSeek en cada nodo HTTP relevante.
- Credencial Telegram en el nodo de mensajes y el workflow de alertas.
- Credencial Header Auth `X-Bridge-Key` para la llamada al bridge.
- Ajustar Chat ID y configuración del modo audio en `CONFIG` con valores de entorno privados; no guardar secretos en el repositorio.

## 4. Levantar bridge local

```bash
cd scripts
# Copia un archivo .env local y carga las variables en tu shell sin subirlo a GitHub.
export TELEGRAM_BOT_TOKEN='...'
export BRIDGE_SHARED_KEY='...'
export ALLOWED_CHAT_ID='...'
python3 kokoro_bridge.py
```

Kokoro debe responder localmente en `http://127.0.0.1:8765/v1/audio/speech`. n8n Docker accede al bridge en `http://host.docker.internal:8766/render-and-send`. No exponer esos puertos a Internet.

## 5. Comprobar el sistema

- Ejecutar manualmente la rama de sourcing sin APIs de voz.
- Validar JSON y análisis de DeepSeek y registrar costes.
- Probar mensaje de Telegram (HTML escapado).
- Probar Kokoro con un guion breve, verificar respuesta del bridge (`ok`, `message_id`).
- Simular fallo en un nodo crítico y verificar el Error Workflow.
- Publicar en n8n y revisar la primera ejecución a las 08:00 Europe/Madrid.

## 6. Publicar

Este repositorio es público. Antes de publicar cualquier cambio, repasa [security-checklist.md](security-checklist.md) y revisa que ningún secreto haya entrado en el historial de Git.
