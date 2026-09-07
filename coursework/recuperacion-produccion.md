# Recuperación de la API pública

## Estado actualizado: servicio accesible

El 7 de septiembre de 2026 a las 03:30 UTC (6 de septiembre, 22:30 en Lima),
las seis comprobaciones de producción pasaron: API/ML, login inválido rechazado,
login válido, acceso al proyecto, abstención sin evidencias y HTML del frontend.
Modal confirmó BETO v1 `ready: true` y embeddings cargados.

La URL de `ML_SERVICE_URL` aportada desde Render coincide con la URL desplegada.
No se cambió esa variable, no se reemplazó el modelo ni se volvió a desplegar.
El servicio volvió a responder después de una petición autenticada de diagnóstico
a Modal. Las credenciales temporales creadas para esas comprobaciones se eliminaron
al terminar. El 404 inicial no pudo reproducirse con autenticación válida; no se
ha demostrado una causa definitiva ni que el problema no pueda reaparecer.

Evidencia: [smoke recuperado](../artifacts/experiments/course-u1/evidence/production-smoke-recovered.json)
y [salud de Modal](../artifacts/experiments/course-u1/evidence/modal-health-recovered.json).
Se conserva por separado el informe de timeout inicial.

## Hallazgos del diagnóstico inicial

- La web de Vercel responde HTTP 200.
- Desde este equipo, la API de Render completaba DNS/TCP/TLS pero no devolvía respuesta HTTP dentro de 25–30 segundos, antes de la recuperación indicada arriba.
- Los registros aportados desde Render muestran que NestJS arranca en el puerto 10000, aplica la evolución de la base y configura la cola PostgreSQL.
- En esos registros, la llamada de NestJS a ML `/health` devuelve **404**.
- La sesión local de Modal permite consultar el despliegue: `historia-viva-peru-ml` está `deployed`, versión v6. La función `ml_api` publica la URL indicada abajo.
- La llamada anónima al endpoint de Modal devolvió **401**, esperado por su autenticación de proxy. Esa prueba por sí sola no verificaba la carga de BETO; esta se comprobó después con la petición autenticada documentada arriba.

URL base verificada mediante el SDK de Modal:

```text
https://jaquelineramosvargas--historia-viva-peru-ml-ml-api.modal.run
```

## Configuración que se debe contrastar en Render

`ML_SERVICE_URL` debe contener exactamente la URL base anterior, sin `/api`, `/health` ni `/infer` añadidos. El adaptador ya añade las rutas. Las variables `MODAL_PROXY_TOKEN_ID`, `MODAL_PROXY_TOKEN_SECRET` y `ML_INTERNAL_TOKEN` deben estar configuradas; sus valores no se deben copiar al informe ni al chat.

El valor remoto ya fue contrastado y coincide; una diferencia en esa URL no explica el fallo observado.

## Corrección preventiva preparada localmente

Se añadió `GET /api/health/live`, que responde sin consultar servicios externos, y se actualizó `healthCheckPath` en `render.yaml`. `GET /api/health` mantiene el diagnóstico de API y ML para monitorización.

Motivo: [Render exige una respuesta en cinco segundos](https://render.com/docs/health-checks), mientras el diagnóstico ML puede esperar hasta quince segundos. Un despertar lento de Modal no debe reiniciar la API. Este riesgo está demostrado por el código; no se ha confirmado como causa de la caída observada.

Pruebas locales: 31 tests de API y compilación correctos. Los tres tests nuevos comprueban liveness con ML sin respuesta, visibilidad del fallo ML en diagnóstico y diagnóstico saludable.

Actualización posterior al push, 7 de septiembre de 2026, 04:08 UTC: la nueva ruta respondió HTTP 200 desde Render. Las seis comprobaciones de producción también pasaron; [evidencia posterior](../artifacts/experiments/course-u1/evidence/production-smoke-post-push.json). Falta confirmar el SHA exacto desplegado y que el panel de Render utilice `/api/health/live` como health check.

## Criterio para dar por recuperado el servicio

1. `/api/health` devuelve `ml: ok` desde el despliegue público.
2. El login de demo y acceso al proyecto funcionan.
3. La pregunta fuera de alcance produce abstención sin evidencias.
4. Se verifica una predicción real con el modelo v1 de producción.
5. Se archiva el resultado de `scripts/smoke_deployment.py` y se comprueba el nuevo liveness cuando esté desplegado.

No se ha reentrenado ni reemplazado el modelo de producción durante este diagnóstico.
