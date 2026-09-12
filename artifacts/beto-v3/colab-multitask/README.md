# BETO multitarea en Colab

> Entrega GitHub: los datos TRAIN/DEV y el baseline con datos incrustados se conservan localmente. Un clon no incluye esos archivos. V?ase [publicaci?n](../../../docs/aprendizaje/publicacion-github.md).

Notebook independiente: `beto_multitarea_colab.ipynb`. No sustituye al baseline plano ni al jerárquico.

Carga manual:
- `../contrastive-subset-experiment/train-experimental.jsonl`: 758 ejemplos.
- `../colab-baseline/portable/dev.jsonl`: 160 ejemplos.

Cada registro requiere `id`, `text`, `label` como strings no vacíos. Conserva metadatos sin usarlos como features. Los resultados anteriores son opcionales.

En Colab con GPU, ejecuta primero con `RUN_SMOKE_TEST = True`. Luego cambia a `False` y ejecuta desde configuración. Guarda las salidas antes de cerrar la sesión. El notebook impide sobrescribir carpetas de resultados/checkpoints preexistentes; una nueva ejecución requiere una sesión limpia.

Un encoder base y dos cabezas; pesos independientes calculados solo en TRAIN, normalización por batch efectivo y cabeza, masking según referencia real, soft gating, selección por máximo estricto de macro-F1 final DEV. Empates conservan época anterior; incrementos de hasta 1e-4 no reinician paciencia, comparada con el máximo anterior. Tres semillas sin seleccionar ganadora. Padding dinámico exigido aquí; el baseline usa padding fijo.

Corrección del smoke AMP: conserva el GradScaler y repite el batch de prueba hasta lograr una actualización efectiva, con el límite existente de 20 omisiones consecutivas. Una primera omisión recuperable ya no aborta el smoke. Scheduler avanza solo al actualizar; se verificaron recuperación y persistencia con fixtures CUDA, sin BETO. Se desactiva el pooler no utilizado (`add_pooling_layer=False`); las cabezas reciben `last_hidden_state[:, 0, :]`.

Validación local: sintaxis, nbformat, ausencia de variables no definidas, mappings, probabilidades, masking, batch sin relevantes, acumulación ponderada y gradientes con cola, early stopping y datos congelados. No se cargó BETO ni se entrenó; smoke GPU y ejecución completa en Colab quedan para la ejecución manual. DEV es referencia expuesta, no prueba independiente ni gold experto. V/S y presupuesto intactos.
