# Checklist de publicación segura

Antes de hacer `git push`, comprobar:

- [ ] Los JSON proceden de **la versión viva y actual** de n8n.
- [ ] Eliminar o anonimizar los campos `credentials` con ID/nombre de credencial.
- [ ] Eliminar `pinData`, `staticData`, outputs de ejecución y respuestas de API.
- [ ] Sustituir Chat IDs privados, correos, teléfonos, IP privadas y URLs con tokens.
- [ ] Revisar `jsCode`, `jsonBody`, `headers`, campos `Authorization` y `X-Bridge-Key`.
- [ ] Nunca subir `N8N_ENCRYPTION_KEY`, `TELEGRAM_BOT_TOKEN`, `BRIDGE_SHARED_KEY` ni una clave DeepSeek.
- [ ] No incluir `.env`, archivos de bases de datos ni logs personales.
- [ ] Comprobar que capturas no incluyan Chat ID, tokens o información sensible.
- [ ] No subir podcasts ni textos completos extraídos de medios protegidos sin permisos.
- [ ] Citar el repositorio inspirador y revisar licencias de componentes de terceros.
- [ ] Verificar nuevamente el ZIP o carpeta final después de limpiarla.

**Importante:** Si un secreto entra por error en el historial de Git, eliminar el archivo en un commit posterior no es suficiente. Revoca o rota la credencial y limpia el historial antes de la publicación.
