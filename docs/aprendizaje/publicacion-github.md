# Selección de archivos para GitHub

Preparada el 12 de septiembre de 2026; reducida a una entrega compacta. El repositorio conserva código, configuración,
guías metodológicas, informes de síntesis, métricas, manifiestos, decisiones y
presupuestos. Los resultados negativos y los intentos fallidos forman parte de la
evidencia; excluir un archivo de Git no significa invalidarlo ni autoriza borrarlo.

La selección de los artefactos nuevos excluye copias completas del corpus, vistas
detalladas que reproducen esos textos, paquetes y respuestas individuales de
anotación, correspondencias privadas, capturas de fuentes, registros brutos de
sesiones y archivos intermedios. Las rutas concretas están en `.gitignore`.
Los 128 bloques NPZ del análisis exhaustivo se conservan localmente junto con su
manifiesto de hashes; no se vuelve a ejecutar la enumeración para publicar.

Los archivos originales permanecen en sus ubicaciones. Un clon contiene informes
que enlazan evidencia local deliberadamente ausente: esos enlaces no implican que
el archivo esté disponible en GitHub. Los verificadores históricos pueden requerir
esa evidencia, los corpus o los checkpoints locales. Este repositorio no es una
distribución autónoma de todos los datos experimentales.

El código y los manifiestos del [pipeline de modelos](despliegue-modelo-automatico.md)
también se versionan. Los paquetes de pesos y recibos generados en
`outputs/model-releases/` permanecen locales; el comando de publicación sube solo
los archivos de inferencia y la ficha a Hugging Face. La revisión publicada se
selecciona en `configs/production-model.json` para el despliegue posterior a CI.

## Notebooks

- Baseline: el notebook autónomo, el ZIP y TRAIN/DEV quedan locales porque incluyen
  el dataset. Se conservan el generador `scripts/prepare_colab_beto_baseline.py`,
  el runtime, el manifiesto y las verificaciones existentes. El generador también
  necesita las entradas locales originales; un clon por sí solo no basta.
- Jerárquico y multitarea: se versionan los notebooks sin salidas. Requieren cargar
  manualmente TRAIN experimental758 y DEV160; esos archivos no se distribuyen en
  esta selección. No se han ejecutado entrenamientos para preparar GitHub.

V permanece congelada y S cerrada. No se modificaron corpus, etiquetas, hashes de
evidencia ni presupuesto experimental. El consenso IA no constituye gold experto.

## Alcance de la revisión

La selección se realizó sobre los cambios pendientes mediante inventario de rutas,
inspección estructural de JSON/CSV, detección de textos reproducidos y revisión de
los tipos de artefacto. No es una certificación de licencias ni una auditoría
completa del contenido de todos los commits históricos. Los datos y el seed demo
ya versionados conservan su tratamiento previo; no se reescribe el historial.

Los archivos locales excluidos necesitan respaldo separado: un commit no los
respalda. Los planes personales y los directorios de herramientas bajo `outputs/`
tampoco forman parte de la entrega.

## Entrega compacta vigente

Se incorporan los dos notebooks publicables, su preparaci?n y comprobaci?n multitarea,
las gu?as de etiquetado, la evaluaci?n sin experto y seis informes finales. Los
scripts hist?ricos adicionales, m?tricas intermedias y documentos de trabajo nuevos
quedan locales mediante rutas exactas en `.gitignore`. El c?digo y los resultados
ya versionados se conservan. Esta selecci?n reduce los archivos nuevos, no elimina
la historia de Git. Los dos registros de estado y presupuesto vigentes conservan
sus modificaciones; parte de la evidencia detallada que referencian es local.
