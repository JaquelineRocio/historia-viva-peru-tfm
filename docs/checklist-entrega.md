# Checklist de publicación y entrega

## Código y calidad

- [x] API compila y supera 14/14 pruebas.
- [x] Web compila y el lint no tiene errores.
- [x] ML supera 24/24 pruebas.
- [x] CI ejecuta API, web y suite ML completa con dependencias aisladas.
- [x] Seed académico comprimido, sanitizado y sin usuarios (12.6 MB).
- [x] GitHub Actions en verde en el repositorio público.

## Producto

- [x] Login correcto e incorrecto verificados localmente.
- [x] La cuenta `docente` tiene rol colaborador, no administrador.
- [x] YouTube produce segmentos, timestamps y subtemas.
- [x] Corrección docente persiste localmente.
- [x] Página/minuto exactos se conservan en los segmentos.
- [x] “Apolo 11” produce abstención sin evidencias.
- [x] Dos fuentes aprobadas aparecen en explorar.
- [x] PDF persiste en Supabase Storage después de reiniciar la API pública.
- [ ] Repetir el smoke test completo en producción.

## Infraestructura externa

- [x] Modelo publicado en Hugging Face Hub.
- [x] Servicio Modal saludable y BETO restaurado al despertar.
- [x] Neon creado e importado.
- [x] Supabase Storage privado y archivos de demo subidos.
- [x] API desplegada en Render.
- [x] Web desplegada en Vercel.
- [x] CORS limitado al dominio de Vercel.
- [ ] Contraseña administrativa aleatoria guardada como secreto.

## Entregables del máster

- [x] Repositorio GitHub público.
- [ ] Incorporar la URL pública del vídeo en el README.
- [x] Presentación PPTX creada y revisada.
- [x] Guion de vídeo de 7–9 minutos creado.
- [ ] Vídeo grabado por la autora y publicado.
- [ ] Enlaces probados en ventana privada.
- [ ] Formulario del máster completado antes del cierre.

No declarar la aplicación “publicada y lista” hasta completar todos los elementos
externos. El F1 macro 0.425 y el Kappa 0.651 deben presentarse como resultados
experimentales, no como un modelo robusto o validado por historiadores.
