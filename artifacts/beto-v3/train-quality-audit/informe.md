# Auditoría de calidad TRAIN: censo documental y diagnóstico dirigido

Fecha: 2026-09-12. Alcance ejecutado: censo de los 746 textos realmente usados, comprobaciones documentales, muestreo reproducible y siete observaciones semánticas expuestas. **La auditoría semántica ciega aún no está ejecutada.** Referencias y checkpoints intactos; sin entrenamiento ni inferencia BETO.

El corpus pasa las comprobaciones de identidad y separación examinadas. **Todavía no queda acreditada la calidad semántica de todo TRAIN.** Hay referencias heredadas sin auditoría v3.2 localizada y concentración marcada de algunas clases por componente documental. Ninguno de esos hallazgos demuestra por sí solo etiquetas equivocadas ni la causa del F1 actual.

|Comprobación|Resultado|Interpretación|
|---|---:|---|
|Identidad contra manifiesto y pesos de la ejecución|746/746|Coinciden ID, hash, clase y componente.|
|Fuentes con registro local enlazado|16/16 fuentes, 746 textos|Procedencia documental localizada; no nuevo cotejo integral con originales.|
|Componentes TRAIN|11|Unidad de agrupación final, no necesariamente una sola obra por componente.|
|Duplicados normalizados dentro de TRAIN|0|No descarta paráfrasis ni redundancia conceptual.|
|Auditoría v3.2 localizada y concordante|137/746 (18,4%)|Cita, offsets, regla, motivo, principal y alternativa pasan comprobaciones documentales. No es nueva validación semántica independiente.|
|Referencia heredada sin auditoría v3.2 en el índice|609/746 (81,6%)|No equivale a “sin ninguna revisión anterior” ni a “incorrecta”.|
|Localizador directo en el registro de base|239/746|El resto necesita recuperar página/intervalo en archivos anteriores.|
|Algún token desconocido|376/746|Reutilización del diagnóstico congelado.|
|Token desconocido que afecta alguna superficie con carácter de palabra|65/746|Alerta léxica; no tasa de pérdida de significado ni de error de etiqueta.|
|Truncamiento|1/746, ocho tokens|No justifica una limpieza masiva.|

Para 507 casos, el registro de base no proporciona directamente página/intervalo; muchos remiten al snapshot y al mapa de filas. Se inspeccionó el esquema del snapshot v4 y su mapa: localizan filas del dataset, no páginas originales. La localización bibliográfica fina sigue pendiente; no se declara perdida o irrecuperable. Los archivos archivados se cargaron para enlazar exclusivamente TRAIN; no se seleccionaron textos reservados.

## Cobertura documental por clase

|Clase|TRAIN|Componentes|Con auditoría v3.2|Mayor componente|
|---|---:|---:|---:|---:|
|Campañas militares|92|5|9|72,8%|
|Contexto colonial|72|4|10|56,9%|
|Crisis e ideas|56|6|19|50,0%|
|Liderazgos y proyectos|86|9|12|54,7%|
|No relevante|216|9|34|21,8%|
|Organización republicana|100|5|9|92,0%|
|Participación social|124|10|44|32,3%|

En organización republicana, 92/100 ejemplos pertenecen al componente conservador historical-basadre-hampe. Ese nombre heredado no atribuye todos sus textos a un solo autor. La concentración limita diversidad de procedencia; no prueba aprendizaje de atajos. El caso de militares también merece atención: 67/92 pertenecen a ese componente. El detalle completo está en [inventario-746.md](inventario-746.md) y [JSON con textos y evidencia](inventario-746.json).

Las alertas históricas reutilizadas incluyen 137 casos con alternativa registrada, nueve con desacuerdo y cuatro con estado ambiguo/unresolved previo. Son antecedentes: las referencias vigentes de esos casos ya están aceptadas. No se reinterpretan como conflictos actuales ni se repiten sus juicios automáticamente.

## Lectura cualitativa ejecutada

Se examinó un caso por clase entre los que no tienen auditoría v3.2 localizada, excluyendo la muestra futura de 70. La selección fue determinista por hash, sin elegir ejemplos por conveniencia después de leerlos. Esta lectura **vio las referencias** y sirve para describir mecanismos, no para medir acuerdo ciego ni prevalencia.

- historical-v4-0064: la descripción demográfica termina explicando apoyo campesino a la rebelión; posible frontera R1/R6 bajo R0.
- historical-v4-0087: operaciones militares seguidas de reacción popular; revisar dominancia R3/R6.
- historical-v4-0609: evidencia positiva de legitimidad y opresión, junto con experiencia de exclusión de grupos; ruido OCR no anula toda evidencia R2/R6.
- historical-v4-0731: diplomacia del Congreso de Panamá desarrollada, pero nexo peruano poco explícito en el objetivo; separar tema de alcance.
- G10-u022: R7 tiene sustento visible porque desarrolla 1956–1963 sin vínculo con el alcance histórico de la tarea.
- historical-v4-0030: tabla desestructurada, pero prosa con comercio republicano efectivo; no excluir el pasaje por el daño tabular solamente.
- historical-v4-0622: experiencia laboral coercitiva junto con condiciones económicas de la minería; revisar R6/R5.

Véanse [textos, citas, reglas y explicaciones](revision-dirigida-7.md). Las siete citas se verificaron con offsets sobre el original. Una primera cita falló por un guion blando OCR; se sustituyó por una subcadena literal más corta, preservando el texto original y sin convertirla por sí sola en prueba de la etiqueta. No se adjudicó ni cambió ninguna etiqueta.

## Siguiente etapa preparada

La [ronda de 70](ronda-1-70.md) contiene únicamente IDs opacos y textos, con respuestas pendientes. Entregar junto con [guía completa](guía-completa.md), sin inventario, resumen, clave ni diagnósticos. La clave está separada en .local-experiments/train-quality-audit/sample-key.json, no cifrada. El preparador no puede borrar su exposición al corpus ni presentarse como nuevo anotador ciego.

Diseño fijado: semilla 20260912746; diez textos por clase, uno por cada componente ocupado dentro de la clase y resto proporcional a la capacidad remanente por mayores residuos. Selección aleatoria dentro de cada celda clase×componente y orden final aleatorio. Cubre las siete clases y los once componentes. Se guardan tamaños e inclusiones por celda. El objetivo es exploratorio; diez por clase no certifican calidad poblacional.

Para estimar tasas globales se usarán probabilidades de inclusión; no promediar sin ponderar los 70. Las celdas con un solo caso impiden estimar directamente su varianza interna: no prometer intervalos precisos por familia. El lote dirigido de siete se analiza separado, nunca añadido al denominador probabilístico.

Contrato pendiente de ejecución de sesiones: dos anotaciones iniciales aisladas por caso (140 juicios), una valoración de los pares etiqueta–justificación por caso en segunda ronda (70), y repetición oculta de siete textos por anotador inicial (14): máximo propuesto 224 juicios, sin reintentos automáticos. La repetición conserva diez casos únicos por clase; no aumenta tamaño muestral. Comparar principal, alternativa, cobertura, validez de evidencia y estabilidad por separado. Las sesiones del mismo modelo comparten dependencia; no constituyen gold experto.

No se lanzaron sesiones pagadas: el contrato técnico de esa nueva ejecución y su coste máximo todavía no están cerrados. El ledger cuenta entradas únicas, no todos los juicios repetidos; su saldo 222 (200 reservadas a S) no puede interpretarse como 222 llamadas disponibles, ni como prohibición automática de revisar entradas existentes. Requiere contabilización específica antes de ejecutar. La autorización “procede” se conserva; no se pide de nuevo para continuar preparación reversible de esta auditoría.

## Conclusión de esta etapa

Está demostrada la identidad de los datos usados, la cobertura documental desigual y la concentración por componente. La lectura dirigida identifica posibles conflictos de dominancia y defectos de segmentación/extracción cuya importancia varía por caso. Sigue incierta la proporción de referencias semánticamente incorrectas y su contribución al desempeño de BETO.

La intervención justificada ahora es completar evidencia y evaluación semántica con guía íntegra. No se justifica aún cambiar etiquetas masivamente, eliminar difíciles, ampliar longitud o entrenar. Se conserva el candidato época 4 y el control AMP, con V congelada y S cerrada. [Sustento científico](../train-quality-evidence/informe.md).
