# Checklist de publicación y entrega

## Código y calidad

- [x] API compila y supera 14/14 pruebas.
- [x] Web compila y el lint no tiene errores.
- [x] ML supera 20/20 pruebas focalizadas.
- [x] CI ejecuta API, web y suite ML completa con dependencias aisladas.
- [x] Seed académico comprimido, sanitizado y sin usuarios (12.6 MB).
- [ ] GitHub Actions en verde en el repositorio público.

## Producto

- [x] Login correcto e incorrecto verificados localmente.
- [x] La cuenta `docente` tiene rol colaborador, no administrador.
- [x] YouTube produce segmentos, timestamps y subtemas.
- [x] Corrección docente persiste localmente.
- [x] Página/minuto exactos se conservan en los segmentos.
- [x] “Apolo 11” produce abstención sin evidencias.
- [x] Dos fuentes aprobadas aparecen en explorar.
- [ ] PDF persiste en R2 después de reiniciar la API pública.
- [ ] Repetir el smoke test completo en producción.

## Infraestructura externa

- [ ] Modelo publicado en Hugging Face Hub.
- [ ] Space ML saludable y BETO restaurado al despertar.
- [ ] Neon creado e importado.
- [ ] R2 privado y archivos de demo subidos.
- [ ] API desplegada en Render.
- [ ] Web desplegada en Vercel.
- [ ] CORS limitado al dominio de Vercel.
- [ ] Contraseña administrativa aleatoria guardada como secreto.

## Entregables del máster

- [ ] Repositorio GitHub público.
- [ ] Sustituir todas las cadenas `PENDIENTE_URL` del README.
- [x] Presentación PPTX creada y revisada.
- [x] Guion de vídeo de 7–9 minutos creado.
- [ ] Vídeo grabado por la autora y publicado.
- [ ] Enlaces probados en ventana privada.
- [ ] Formulario del máster completado antes del cierre.

No declarar la aplicación “publicada y lista” hasta completar todos los elementos
externos. El F1 macro 0.425 y el Kappa 0.651 deben presentarse como resultados
experimentales, no como un modelo robusto o validado por historiadores.
