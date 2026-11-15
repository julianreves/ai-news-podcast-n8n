# Workflows n8n

| Archivo | Qué es |
|---|---|
| `podcast-daily.json` | Workflow editorial principal: RSS → selección → análisis → guion → auditoría → Telegram, con rama opcional de voz mediante el bridge Kokoro. 35 nodos. |
| `error-alerts.json` | Workflow independiente con *Error Trigger* que avisa por Telegram cuando falla el principal. 6 nodos. |

Ambos son exportaciones del n8n en uso (15 nov 2026), sanitizadas: sin referencias a credenciales, sin Chat ID, sin datos pinneados. Se importan **inactivos**.

Para actualizarlos con una exportación nueva:

```bash
python3 scripts/sanitize_n8n_export.py /ruta/al/export-actual.json workflows/podcast-daily.json
python3 scripts/sanitize_n8n_export.py /ruta/al/export-alertas.json workflows/error-alerts.json
```

Después revisa a mano el contenido del nodo `CONFIG` y los nodos `Code`: el script automatiza solo una parte del trabajo (ver [security-checklist.md](../docs/security-checklist.md)).
