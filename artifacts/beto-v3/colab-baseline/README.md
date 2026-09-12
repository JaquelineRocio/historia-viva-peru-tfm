# Notebook BETO para Colab: TRAIN 758, DEV 160

> Entrega GitHub: los datos TRAIN/DEV y el baseline con datos incrustados se conservan localmente. Un clon no incluye esos archivos. V?ase [publicaci?n](../../../docs/aprendizaje/publicacion-github.md).

Abre `BETO_baseline_7_clases_3_semillas.ipynb` en Google Colab, selecciona GPU y ejecuta todas las celdas. Los datos y el programa están incluidos: no debes subir TRAIN/DEV por separado. `beto-baseline-portable.zip` ofrece también la exportación independiente.

La última indicación de la autora cambia TRAIN a las 758 filas experimentales congeladas. Se preservan los textos, las etiquetas y DEV160. Este baseline ampliado permite comparar futuras arquitecturas si usan los mismos datos; no es una reproducción del control AMP746. El registro histórico contrastivo de una semilla no se modifica.

Se ejecutan 42, 123 y 2026 sin seleccionar la mejor semilla. BETO y tokenizer proceden de `dccuchile/bert-base-spanish-wwm-cased`, revisión `c4d86612f51b4f46759c8390d1798c2febe71b93`, con hashes comprobados. El tokenizer fast produce exactamente los mismos tokens que el guardado por el control en los 918 textos. Orden: MIL, COL, IDE, LID, NR, REP, SOC; los nombres completos se guardan en `manifest.json`.

Optimización sin cambiar la receta: tokenización única reutilizada entre semillas, AMP, gradient checkpointing, batch efectivo 16, liberación de GPU entre semillas y almacenamiento del mejor checkpoint por semilla. Se mantienen max_length384 y padding fijo para conservar el contrato. Pesos `758/(7*n_clase)`; horizonte384 y warmup38 derivados del tamaño. GradScaler estándar recupera su escala y registra omisiones, sin abortos por contador de overflow. El scheduler avanza únicamente con updates efectivos.

Entrega macro-F1, accuracy, métricas por clase, confusiones, época seleccionada, historiales, media y desviación estándar muestral, probabilidades DEV por ID/hash y tres checkpoints. No promedia únicamente semillas exitosas cuando hay un fallo. El notebook exporta entorno, hashes, tiempos y número de trayectorias; el ledger local permanece intacto. V y S no se exportan ni se usan.

DEV ya está expuesto y selecciona épocas; estos resultados no representan una evaluación independiente ni gold experto. No se ha ejecutado entrenamiento real aquí ni se ha probado una sesión completa de Colab. `verification.json` y `runtime-checks.json` registran las verificaciones locales y las pruebas sintéticas de acumulación ponderada, early stopping y recuperación AMP.
