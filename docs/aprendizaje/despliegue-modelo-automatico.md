# Publicación y despliegue automático de BETO

El código se despliega con el workflow existente `Deploy Modal`, después de CI
correcto en `main`. El modelo servido se selecciona mediante
`configs/production-model.json`: repositorio de Hugging Face, SHA completo de su
revisión, hashes de siete archivos, etiquetas ordenadas y longitud máxima.

La selección inicial conservaba BETO v1 fijado a
`f7742a705373640fe7dd424aa3a5d33682c970be`. La autora ya publicó R2 y el manifiesto
selecciona `Jaqueline98/historia-viva-beto-r2-42`, revisión
`31a3887ee6906c6778a4853bc76df7b7e2198282`. El despliegue depende de que CI y
Deploy Modal terminen correctamente; la publicación de los pesos ya está hecha.

## Corrección del build de Modal

El [run 34725505914](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34725505914)
falló antes de desplegar: `/bin/sh: Syntax error: Unterminated quoted string`.
El comando generado contenía un salto de línea literal que cortaba el RUN entre
comillas. Se corrigió para generar una sola línea física, conservando la
comprobación de hashes. La subida del informe se omite cuando el fallo ocurre
antes de generarlo.

Comprobaciones locales: 44 pruebas de publicación/despliegue aprobadas y regresión
con shell real (antes falla, después pasa). Evidencia:
`outputs/modal-build-fix-tests.xml` y `outputs/modal-build-shell-regression.json`.
Para aplicar la corrección, revisar y hacer commit/push de los cambios a `main`.
Reejecutar el job antiguo usa el código anterior; no incorpora esta corrección.
No hace falta volver a publicar R2 ni entrenarlo. No se ejecutó un nuevo build
remoto durante esta reparación.

## Uso desde PowerShell, en la raíz del proyecto

Corrección posterior de arranque: el run `34725763422` construyó y desplegó el
commit `d1aaa50`, pero la verificación terminó con seis `ReadTimeout`. Los logs
de Modal identificaron `IndexError: 1` al importar `/root/modal_app.py`: el módulo
buscaba el manifiesto mediante una ruta del checkout local, inexistente allí.
Ahora la receta de imagen, requirements y lectura del manifiesto se ejecutan
solo en el cliente mediante `modal.is_local()`. El worker registra FastAPI y
utiliza la imagen y las variables de versión recibidas del despliegue.

`scripts/check_modal_import.py` usa el SDK real Modal 1.5.5 para comprobar tanto
la importación local como una importación remota simulada desde una carpeta sin
checkout, rechazando lecturas de archivos locales. Se ejecuta en CI y antes del
deploy. Evidencia local: 51 pruebas de publicación/arranque/verificación y
`outputs/modal-worker-import-regression.json` (anterior falla, corregido pasa).
El verificador conserva los tiempos de espera y ahora identifica endpoint y
duración del intento. No se ejecutó un nuevo despliegue remoto en esta reparación;
aplicar mediante commit/push de la autora. R2 no necesita otra publicación.

En este equipo el entorno ML operativo es `outputs/venv-ml`. El Python del sistema
no tiene las dependencias de inferencia y el antiguo `apps/ml/.venv` no arranca.

Para comprobar el paquete sin publicar:

```powershell
.\outputs\venv-ml\Scripts\python.exe scripts/publish_model.py prepare
```

Para autenticar Hugging Face una vez, si no existe una sesión local válida:

```powershell
.\outputs\venv-ml\Scripts\hf.exe auth login
```

Usar un token con permiso de escritura para el repositorio de destino. El comando
de autenticación solicita el token; no añadirlo al código ni a los comandos del
historial. También se admite `HF_TOKEN` configurado externamente. No se necesita
un token de Hugging Face en GitHub Actions o Modal: la entrega usa un modelo
público sin restricciones de acceso.

Para publicar R2, verificarlo y dejar seleccionada la revisión publicada:

```powershell
.\outputs\venv-ml\Scripts\python.exe scripts/publish_model.py publish
```

Este comando realiza una publicación pública en
`Jaqueline98/historia-viva-beto-r2-42`. Copia únicamente pesos, tokenizer,
configuración, etiquetas adaptadas y ficha del modelo. No sube corpus, informes
privados, recibos ni archivos adicionales del checkpoint.

Después revisa los cambios en Git y haz tu commit y push a `main`, incluyendo el
código del pipeline, `configs/production-model.json` y `configs/model-releases/`.
Las operaciones de Git corresponden a la autora. Los pesos quedan fuera de Git;
las entregas y recibos locales están en `outputs/model-releases/`.

En otro equipo, usar Python 3.11 con `apps/ml/requirements.txt` y PyTorch CPU,
además del checkpoint local. La CLI `hf` viene con `huggingface-hub`. No es
necesario instalar Modal para publicar desde este comando.

## Resolver un 401 y reutilizar el paquete

Un `401 Unauthorized` en `/api/repos/create` indica que Hugging Face no aceptó
la credencial. No significa que fallara BETO. El comando ahora comprueba la sesión
antes de copiar pesos o inferir, rechaza tokens de solo lectura y muestra un
mensaje breve. Los permisos específicos de tokens fine-grained se comprueban al
escribir en el repositorio; una sesión válida no garantiza ese permiso.

Crear un token con permiso de escritura en
[Hugging Face Settings](https://huggingface.co/settings/tokens), para la cuenta
propietaria del repositorio. Iniciar sesión y comprobarla en la misma terminal:

```powershell
.\outputs\venv-ml\Scripts\hf.exe auth login
.\outputs\venv-ml\Scripts\hf.exe auth whoami
```

Pegar el token en el prompt de login, no en el chat. No es necesario guardarlo como
credencial de Git para este flujo HTTP. Si existe `HF_TOKEN` o la variable heredada
`HUGGING_FACE_HUB_TOKEN`, su valor prevalece sobre la sesión guardada; corregir o
retirar de esa terminal la variable inválida antes de repetir el login.

Para reutilizar el paquete del intento que falló en autenticación:

```powershell
.\outputs\venv-ml\Scripts\python.exe scripts/publish_model.py publish `
  --package "E:\BETO\outputs\model-releases\beto-tqxser4l"
```

`--package` requiere el recibo adyacente `beto-tqxser4l-verification.json`, una
comprobación de paridad aprobada y los siete archivos con sus hashes originales.
Reutiliza esa evidencia sin volver a inferir ni copiar pesos. Un paquete alterado
o un recibo ausente/incompleto se rechaza; no se modifica la selección de producción.
Se conserva el repositorio del recibo para evitar redirigir por accidente la subida.

Corrección comprobada el 12 de septiembre de 2026: 31 pruebas de publicación
aprobadas (`outputs/model-release-auth-tests.xml`); hashes del paquete
`beto-tqxser4l` verificados sin repetir inferencia. En el entorno del asistente no
había credencial disponible; no se publicaron pesos al comprobar esta corrección.

## Qué verifica y qué automatiza

1. **Paquete local:** comprueba hashes del original y de la copia, orden de las
   clases y longitud. Convierte `labels/max_length` a `id2label/max_len` sin
   cambiar los pesos. Una carpeta nueva por ejecución evita mezclar entregas.
2. **Paridad CPU:** compara tokenización y predicciones de cinco textos sintéticos
   entre checkpoint y servicio. Incluye un texto largo para comprobar truncamiento.
   No entrena ni evalúa corpus; V permanece congelada y S cerrada.
3. **Publicación:** sube solo los archivos permitidos y la ficha. Usa el commit
   padre para detectar publicaciones concurrentes. Conserva el SHA devuelto por
   Hugging Face y comprueba los siete archivos descargados sin autenticación.
4. **Selección:** solo tras verificar la revisión remota actualiza atómicamente
   `configs/production-model.json` y archiva las versiones anterior y nueva.
   Un fallo de subida/verificación deja intacta la selección de producción.
5. **Push:** CI prueba API, web y ML. `Deploy Modal` despliega el commit comprobado
   si sigue siendo el último de `main`, utilizando los secretos existentes.
6. **Imagen y arranque:** la imagen descarga esa revisión exacta y verifica sus
   hashes. El servicio reutiliza los archivos íntegros sin red; si faltan o están
   alterados, descarga la misma revisión y vuelve a comprobarlos. Un fallo impide
   iniciar el servicio con un modelo distinto.
7. **Comprobación remota:** `/health` y `/infer` deben identificar el mismo commit
   de código y el modelo esperado, incluidos hashes, etiquetas y longitud. La
   predicción debe pertenecer a las clases registradas. El resultado queda como
   artefacto de GitHub Actions.

La identidad declarada se vincula al modelo cargado, no solo a las variables de
entorno. Una carga manual sin manifiesto no conserva la identidad de la versión
anterior. El catálogo de entrenamientos en la base de datos no se modifica con
este comando; los endpoints ML identifican la versión que sirve inferencia.

## Publicar otra versión

```powershell
.\outputs\venv-ml\Scripts\python.exe scripts/publish_model.py publish `
  --checkpoint "ruta/al/checkpoint" `
  --repo-id "Jaqueline98/nombre-del-modelo" `
  --model-card "ruta/a/su-ficha.md"
```

La ficha es obligatoria para otro checkpoint, para no atribuirle el F1 de R2. El
comando admite el mismo contrato BETO de siete clases, pesos `model.safetensors`
y tokenizer completo; otras arquitecturas requieren su adaptación y comprobación.
No selecciona automáticamente el mejor entrenamiento ni cambia criterios de calidad.

## Volver a v1

```powershell
Copy-Item -LiteralPath "configs/model-releases/f7742a705373640fe7dd424aa3a5d33682c970be.json" `
  -Destination "configs/production-model.json"
```

Revisar, hacer commit y push. El mismo pipeline despliega esa versión. No se
borran modelos ni revisiones. Si la comprobación posterior a un despliegue falla,
Actions queda en rojo: **no hay reversión automática**; el nuevo despliegue puede
haber ocurrido ya. Restaurar una referencia comprobada y pasar de nuevo por CI.

## Evidencia local del 12 de septiembre de 2026

- R2/42, época 8: entrega `outputs/model-releases/beto-iba2_1r6/`;
  recibo `outputs/model-releases/beto-iba2_1r6-verification.json`.
- Hash de los pesos intacto:
  `e964dfbdd6010b205e619a9e7daf6558eb9b6b2a55a1a0c58d3a98b420493303`.
- Paridad en cinco textos sintéticos; esto no mide corrección histórica ni un F1 nuevo.
- Suite ML: 76 pruebas aprobadas; XML `outputs/model-release-tests.xml`.
- Publicación remota de R2 y despliegue real no ejecutados durante la implementación.
  Las pruebas de subida y fallos remotos usan un Hub simulado.

Referencias: [subida a Hugging Face](https://huggingface.co/docs/huggingface_hub/guides/upload),
[revisiones y archivos en Modal](https://modal.com/docs/guide/model-weights).
