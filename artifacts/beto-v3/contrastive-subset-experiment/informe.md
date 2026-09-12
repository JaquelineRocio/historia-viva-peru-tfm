# Ampliación parcial: un experimento defendible con 12 candidatos

**SÍ existe un subconjunto defendible bajo el margen de materialidad fijado antes de optimizar.** Se crea TRAIN experimental de **758 filas**, con las 746 originales intactas y 12 candidatos existentes. Se preregistra **un único entrenamiento**; no se ejecutó. La vía de ampliación no se declara agotada en este punto, pero tampoco se afirma que el modelo haya mejorado.

Esta es una siguiente prueba razonable dentro de las restricciones de la autora: aprovecha evidencia ya pagada y separa utilidad parcial de cobertura global. No está demostrado que sea la mejor intervención posible frente a BETO jerárquico. La conclusión es sensible al margen aceptable de asociación, como se muestra abajo.

## Criterio anterior al resultado

El [protocolo sellado](protocol.json) se escribió antes de enumerar combinaciones. Sus hashes y el del script constan en [protocol-freeze.json](protocol-freeze.json).

- Incremento máximo absoluto de **0,005** en cada índice: NMI y V de Cramér. Es una tolerancia operativa, no un umbral científico universal ni una prueba estadística de equivalencia.
- Conservar al menos dos pares válidos en dos fronteras y al menos dos familias argumentativas nuevas.
- Cada candidato seleccionado debe participar en un par conservado: sin objetivos aislados para favorecer artificialmente los índices.
- Reducir al menos **un punto porcentual** la cuota de la familia dominante en dos clases históricas. NR no satisface por sí sola esta condición.
- Orden de selección: más fronteras con dos pares y dos familias por lado; después más fronteras representadas, más pares, más clases históricas mejoradas, mayor reducción conjunta de cuotas; desempates por menor incremento de asociación, menos entradas y máscara menor.

No se exige cubrir las siete fronteras. Se conservan la taxonomía, los textos, las etiquetas, los pares validados y la agrupación argumentativa previa. No se utilizaron predicciones BETO para seleccionar candidatos. Los agregados del control AMP se consultaron después de terminar la selección para registrar el futuro contraste.

## Búsqueda exhaustiva y sensibilidad

Se calcularon **8.388.608 combinaciones**, incluida la vacía: **8.388.607 subconjuntos no vacíos**. La enumeración tardó aproximadamente 36,35 segundos en CPU. No hubo entrenamiento, inferencias ni anotaciones.

| Tolerancia absoluta por índice | Subconjuntos que cumplen también el criterio de diversidad | Mejor tamaño según orden fijado |
|---|---:|---:|
| 0 | 0 | — |
| 0,001 | 0 | — |
| 0,0025 | 1 | 9 |
| **0,005** | **228** | **12** |
| 0,010, solo sensibilidad | 10.433 | 18 |

El subconjunto de nueve casos baja NMI a 0,264700 y eleva V a 0,427147; conserva cinco pares y una frontera con cobertura suficiente. El de doce gana dos fronteras suficientes y dos pares adicionales dentro de la tolerancia predefinida. No se eligió el de dieciocho porque necesita una tolerancia mayor. **Ningún subconjunto con la mejora de diversidad exigida evita por completo aumentar V de Cramér.** La conclusión favorable se refiere a aumento no material según el margen registrado, no a disminución de ambos índices.

## Subconjunto elegido

| Familia nueva | Candidatos |
|---|---|
| Sala i Vila | Q1-001, Q1-006, Q1-015 |
| Chassin | Q2-001, Q2-005 |
| Petit-Breuilh | Q2-002, Q2-016 |
| Andaur | Q2-011 |
| Política Internacional 129, un solo dossier | Q3-002, Q3-009, Q3-016 |
| Paniagua | Q3-025 |

La selección añade tres COL, uno IDE, tres REP, tres SOC y dos NR. No añade MIL ni LID. Se mantienen seis familias nuevas con funciones históricas distintas: financiación frente a resistencia fiscal; estructura de alcaldes frente a agencia comunal; administración frente a descripción metodológica; legitimidad jurídica frente a creación ministerial; procedimientos de representación frente a decisiones de adhesión territorial. Los controles NR aportan pertinencia y vocabulario compartido, no un mecanismo histórico nuevo.

## Dependencia y diversidad

| Índice | TRAIN 746 | Experimental 758 | Cambio absoluto |
|---|---:|---:|---:|
| NMI | 0,265389046 | 0,265431255 | **+0,000042209** |
| V de Cramér | 0,424752195 | 0,429500701 | **+0,004748507** |

Ambos cambios están dentro de 0,005. En términos relativos corresponden aproximadamente a +0,016 % y +1,118 %. V queda cerca del límite; esto se declara, no se presenta como reducción de asociación.

| Clase | Cuota máxima antes | Cuota máxima después | Familias antes | Familias después |
|---|---:|---:|---:|---:|
| COL | 56,94 % | 54,67 % | 4 | 7 |
| IDE | 50,00 % | 49,12 % | 6 | 7 |
| MIL | 72,83 % | 72,83 % | 5 | 5 |
| LID | 54,65 % | 54,65 % | 9 | 9 |
| REP | 92,00 % | 89,32 % | 5 | 8 |
| SOC | 32,26 % | 31,50 % | 10 | 13 |
| NR | 21,76 % | 21,56 % | 9 | 11 |

COL y REP reducen concentración en 2,28 y 2,68 puntos porcentuales, respectivamente. REP sigue muy concentrada y MIL no cambia. Contar una familia con uno o dos textos no acredita amplitud de aprendizaje: la ganancia es acotada y debe probarse.

NMI usa normalización aritmética y V de Cramér la versión sin corrección, exactamente como en el cierre anterior. TRAIN conserva sus once componentes; se añaden seis familias, sin dividir ni reagrupar fuentes después de ver resultados. Los índices dependen del tamaño y de esta granularidad conservadora; no son medidas directas de generalización ni de corrección histórica.

## Fronteras y pares conservados

| Frontera | Pares | Familias por lado en esos pares | Cobertura suficiente de nueva evidencia |
|---|---:|---:|---|
| COL–NR | 2 | 2/2 | SÍ |
| IDE–LID | 0 | 0/0 | NO |
| IDE–REP | 1 | 1/1 | Parcial |
| LID–REP | 0 | 0/0 | NO |
| MIL–LID | 0 | 0/0 | **No resuelta** |
| COL–SOC | 2 | 2/2 | SÍ |
| REP–SOC | 2 | 2/2 | SÍ |

Se conservan **7 de los 18 pares válidos** de los 23 candidatos: PAIR-001, 002, 003, 004, 020, 024 y 025. Son siete relaciones, no siete observaciones independientes. No se afirma conservar las seis fronteras cubiertas por el lote completo: reducir el subconjunto también reduce esa cobertura. La tabla describe evidencia contrastiva nueva; el TRAIN original conserva toda su cobertura, que no fue reanotada ni inferida mediante productos cartesianos de clases.

## Entrenamiento preregistrado, no ejecutado

El [registro completo](training-preregistration.json) fija una sola trayectoria desde BETO base y comparación contra **AMP v2, semilla 42, época 5**, cuyo checkpoint se verificó por hash. No se usa R2 histórico como control ni el candidato de ponderación por familia de la época 4.

Se mantiene la receta AMP: semilla 42, longitud 384, microbatch 2, acumulación 8, AdamW, LR 2e-5, weight decay 0,01, clipping 1 y las mismas reglas de omisiones numéricas. Pesos de clase inversos recalculados únicamente desde TRAIN, con la misma fórmula. El tamaño nuevo determina 48 pasos por época, horizonte 384 y warmup 38, sin búsqueda de hiperparámetros.

Máximo ocho épocas; early stopping en los mismos 160 DEV, paciencia 2 y min_delta 0,0001. Se elige el mayor macro-F1 DEV, con época más temprana en empate exacto. Comparación emparejada posterior y bootstrap por componente; no nuevas anotaciones. El criterio exploratorio fijado exige delta macro-F1 ≥0,02 contra AMP, ninguna caída por clase >0,05 y aumento de NLL ≤0,02. DEV selecciona época y ya está expuesto: superar este criterio no demuestra generalización externa ni autoriza promoción automática. V sigue congelada y S cerrada.

El presupuesto propuesto es 900 segundos de entrenamiento + 60 de comparación, dentro de los 1004,344858 segundos de desarrollo registrados. Hay cero trayectorias de desarrollo libres: ejecutar requeriría una nueva trayectoria, con techo propuesto 27→28, sin tocar las tres reservadas para cierre. **Este encargo preregistra; no autoriza ni ejecuta el entrenamiento y no modifica el ledger.** No se ha creado un lanzador ejecutable: el trabajador anterior fija 746 filas y su contrato debe adaptarse de forma aislada a las 758 y sus constantes derivadas antes de ejecución. El registro ya fija esos valores y no permite resolverlos después según resultados.

Si la única trayectoria falla o no cumple el criterio registrado, se cierra la vía de ampliación; la intervención siguiente será BETO jerárquico, sin otra ronda ni prueba automática de un segundo subconjunto.

## Entrega y verificación

- [TRAIN experimental JSONL](train-experimental.jsonl), [versión con metadatos](train-experimental.json) y [12 candidatos con evidencia existente](selected-candidates.json).
- [Siete pares](selected-pairs.json), [matriz antes](clase-familia-antes.csv), [matriz experimental](clase-familia-experimental.csv), [comparación por clase](comparacion-clases.csv) y [cobertura](cobertura-fronteras.csv).
- [Resultados y sensibilidad](result.json), [verificación independiente](verification.json) y [sello experimental](experiment-freeze.json).
- `all-subsets/`: 128 bloques NPZ comprimidos con métricas para **cada** combinación; [esquema y orden de bits](protocol.json) y [hashes de todos los bloques](enumeration-manifest.json). Cada fila guarda máscara de candidatos, NMI, V, cuota máxima y número de familias en siete clases, familias por lado y pares por frontera, máscara de pares y resultado del criterio de diversidad. La máscara 2695551 identifica la selección.

Se contrastaron 128 subconjuntos, incluidos vacía, completa y las selecciones de 9/12 filas, usando sklearn y SciPy con tablas reconstruidas independientemente; discrepancia máxima 1,67e-15. Se verificaron todos los hashes de bloques, las 8.388.608 máscaras consecutivas, los recuentos de factibilidad, las etiquetas y la identidad de las 746 filas originales. El cruce contra metadatos de partición no encuentra solapamiento por ID, hash, fuente, familia ni componente. No se leyó contenido de V/S ni se hicieron búsquedas, adquisiciones, anotaciones o inferencias nuevas. El ledger conserva 52 entradas de desarrollo y 200 de S.

Scripts: `scripts/optimize_contrastive_subset.py` y `scripts/prepare_contrastive_subset_experiment.py`. La enumeración evita sobrescribir un protocolo existente; una reproducción completa requiere una copia de trabajo sin el directorio de resultados de este experimento. Los NPZ permiten volver a consultar cualquier subconjunto sin enumerar ni entrenar de nuevo.
