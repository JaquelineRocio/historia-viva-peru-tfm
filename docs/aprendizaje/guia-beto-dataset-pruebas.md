# Comprender y mejorar BETO en Historia Viva Perú

La tarea de BETO en este proyecto es asignar una de siete categorías históricas a un fragmento. Una mejora útil debe funcionar sobre fuentes distintas de las utilizadas para aprender y respetar criterios de calidad definidos previamente. Los últimos experimentos ya muestran que aprender perfectamente los ejemplos de entrenamiento no basta para conseguirlo.

La recomendación inmediata es medir el procedimiento de anotación y la robustez mediante el [plan de evaluación sin experto](evaluacion-sin-experto.md), conservando las versiones actuales. La autora confirmó el 11 de septiembre de 2026 que no habrá experto para valorar etiquetas: ese plan sustituye las recomendaciones de revisión humana que aparecen en el resto de esta guía. El comparador de etiquetas todavía exige referencia humana y debe adaptarse antes de usarlo en el nuevo piloto; no falsear su procedencia. No hay evidencia suficiente para recomendar otra tasa de aprendizaje o más épocas como solución. El laboratorio permite aprender con los datos y resultados existentes, sin entrenar ni abrir la reserva S.

## 1. Dónde están los 1095 fragmentos y qué significan R2, H e I

Los **1095 fragmentos** están en la lista `items` de [train-h80-v1.json](../../artifacts/beto-v3/phase-h-data80/train-h80-v1.json). Cada objeto de esa lista es una unidad; su campo `text` contiene el texto y `label` la categoría. No son 1095 documentos completos. El recuento local identifica **36 fuentes y 30 familias documentales**.

En este archivo hay 541 filas con `split: "train"` y 554 con `split` nulo o ausente, heredadas de formatos anteriores. La pertenencia al entrenamiento se determina por el archivo congelado, su `partition: "train"`, el manifiesto y su hash. No debe deducirse que una fila con `split: null` quedó fuera del entrenamiento. El script didáctico verifica el hash del snapshot antes de leer sus unidades.

| Nombre | Qué representa | Datos y cambio |
|---|---|---|
| BETO | Modelo base en español | `dccuchile/bert-base-spanish-wwm-cased`. |
| R2 | Receta experimental y modelos obtenidos con ella | Corpus histórico H + lote T300; 20 épocas, lr 2e-5. R2/42 es la referencia con semilla 42. |
| H, fase experimental | Intervención posterior sobre los datos | Mantiene la receta y añade 79 unidades aceptadas de un lote de 80; train pasa de 1016 a 1095. |
| I, fase experimental | Intervención sobre la pérdida | Utiliza exactamente los mismos 1095 de la fase H; cambia la ponderación por familia. |
| H, corpus histórico | Un componente de datos anterior | Archivo `outputs/beto-v3/datasets/H.json`: 590 unidades. Es un uso distinto de la misma letra. |
| T300 | Nombre histórico de un lote | El archivo congelado contiene 426 unidades; el nombre no es su recuento actual. |
| V | Conjunto de validación | 444 unidades, ocho familias; permite comparar experimentos. |
| S | Reserva para evaluación final | Permanece cerrada durante desarrollo. |

La composición comprobada es **590 + 426 = 1016** para R2 y **1016 + 79 = 1095** para H e I. “H/I” solo abrevia “los experimentos H e I”; no es otra partición. La confusión procede de nombres reutilizados, por lo que conviene escribir siempre “fase H” o “corpus histórico H”.

La semilla, por ejemplo `42`, controla parte de las decisiones aleatorias del entrenamiento. Una época es una pasada por el conjunto de entrenamiento. Un checkpoint es una copia de los parámetros aprendidos en un momento determinado. Entrenar 20 épocas produce varios checkpoints; el mejor por validación no tiene por qué ser el último.

Fuentes locales: [congelado de C](../../artifacts/beto-v3/phase-c-freeze.json), [congelado de H](../../artifacts/beto-v3/phase-h-data80/checkpoint-04-data-freeze.json), [lector real de H/I](../../scripts/prepare_beto_phase_i.py) y [resumen medido](../../artifacts/aprendizaje-beto/resumen.json).

## 2. Qué contiene el dataset y qué debe aprender el modelo

El problema es clasificación supervisada de una sola etiqueta: para un texto de entrada, el entrenamiento proporciona una categoría de referencia. “Supervisada” significa que hay respuestas de referencia con las que comparar las predicciones. Las etiquetas son decisiones de anotación; su presencia en un JSON no prueba que sean históricamente correctas.

| Categoría | Ejemplos en TRAIN H/I | Familias con esa clase | Ejemplos en V |
|---|---:|---:|---:|
| Campañas y conflictos militares | 132 | 10 | 63 |
| Contexto colonial y antecedentes | 99 | 12 | 23 |
| Crisis e ideas emancipadoras | 85 | 11 | 75 |
| Liderazgos, diplomacia y proyectos | 129 | 19 | 32 |
| No relevante | 319 | 21 | 168 |
| Organización y consecuencias republicanas | 142 | 14 | 23 |
| Participación social y regional | 189 | 24 | 60 |
| **Total** | **1095** | **30 familias únicas** | **444** |

Las familias por categoría se superponen y no deben sumarse. En organización republicana, 92 de los 142 ejemplos pertenecen a `historical-basadre-hampe`: aproximadamente el 64.8 %. Esto describe concentración documental; no prueba, por sí solo, que sea la causa de los errores. Dos párrafos de una misma obra pueden aportar menos diversidad que dos pasajes independientes de estilos y subtemas distintos.

El modelo recibe el texto tokenizado. La fuente, la familia, los hashes y la procedencia sirven para organizar, verificar y analizar los ejemplos. En I, la familia interviene en el peso de la pérdida; no se convierte automáticamente en texto de entrada. Años, personajes y lugares se gestionan también como entidades en el producto, pero no son las siete clases del clasificador.

La [guía v3.1](../beto-v3/guia-etiquetado-v3.1.md) exige distinguir el argumento central de una mención incidental. Un texto que menciona una constitución podría explicar una crisis de legitimidad, un proyecto político o el funcionamiento institucional. La palabra “constitución” no determina por sí sola la clase.

## 3. Qué aprender para entender BERT y BETO

El orden de estudio más útil es: tarea y etiquetas; tokens y vectores; predicción y pérdida; ajuste de parámetros; separación de datos y generalización. Se puede comenzar sin dominar cálculo diferencial. Después conviene aprender vectores, matrices, producto escalar, probabilidades, media ponderada y la idea de una derivada como sensibilidad de una función.

**BERT** significa *Bidirectional Encoder Representations from Transformers*. Es un codificador que calcula representaciones considerando contexto a ambos lados. Su preentrenamiento original incluyó predecir tokens ocultos y una tarea de relación entre oraciones; después se adapta a tareas concretas con una capa de salida. **BETO** sigue esta familia de arquitectura y fue preentrenado en español. El proyecto reutiliza esos parámetros en vez de aprender el idioma desde cero.[^1][^2]

| Concepto | Explicación para este proyecto |
|---|---|
| Token | Unidad del vocabulario: puede ser una palabra, parte de ella o un signo. |
| ID de token | Número que identifica esa unidad dentro del vocabulario. |
| Embedding | Vector de números que representa un token; después las capas lo transforman según el contexto. |
| Atención | Operación que combina información de posiciones del texto para construir representaciones contextuales. No constituye una verificación histórica. |
| Clasificador | Capa que transforma la representación del fragmento en siete puntuaciones. |
| Logits y softmax | Los logits son puntuaciones sin normalizar; softmax puede transformarlas en valores que suman uno. Esa suma no garantiza confianza bien calibrada. |
| Fine-tuning | Ajuste de parámetros de BETO y de su clasificador para aprender la tarea etiquetada. |
| Inferencia | Obtener una predicción con parámetros ya aprendidos, sin actualizarlos. |

La implementación utiliza `AutoModelForSequenceClassification` con siete etiquetas. El codificador y la capa de clasificación participan en el ajuste. Los IDs, las máscaras que distinguen relleno y texto y las representaciones internas tienen funciones distintas.[^3]

```text
Texto → tokens → IDs → vectores contextuales de BETO → siete puntuaciones → categoría
                                                                         │
En entrenamiento: referencia → pérdida ←─────────────────────────────────┘
                                  │
                       actualización de parámetros
```

La **pérdida** es la función numérica que orienta el aprendizaje. La entropía cruzada penaliza asignar baja probabilidad a la clase de referencia; los pesos de clase o familia modifican cuánto contribuye cada ejemplo. El optimizador utiliza gradientes para actualizar parámetros. La tasa de aprendizaje regula el tamaño de las actualizaciones; no es una probabilidad de acertar. F1 es una medida de evaluación distinta de esa pérdida.[^4]

Ejemplo conceptual: si la referencia dice “campañas” y el modelo favorece “liderazgos”, se calcula una pérdida y se ajustan los parámetros. Si la referencia fuera incorrecta, el mismo mecanismo empujaría al modelo hacia esa referencia equivocada. Por eso la calidad de las etiquetas influye en qué aprende.

## 4. Los números de entrada no son el SHA256

El tokenizador asigna IDs mediante un vocabulario. En el primer fragmento real se comprobó esta secuencia inicial:

| Token | ID real |
|---|---:|
| `[CLS]` | 4 |
| `LA` | 3655 |
| `DE` | 1982 |
| `##CL` | 17540 |
| `##ARA` | 26845 |
| `##TOR` | 14737 |
| `##IA` | 5427 |

Los prefijos `##` indican continuaciones de subpalabras en esta tokenización. No son caracteres que se agreguen al texto original. El primer fragmento produce **161 tokens contando los especiales**, y no se recorta al límite de 384. Son resultados del [ejemplo ejecutado](../../artifacts/aprendizaje-beto/tokens-ejemplo.json), no números inventados.[^5]

El **SHA256** es una huella del contenido expresada normalmente como 64 caracteres hexadecimales. Ayuda a detectar cambios y fijar versiones. No representa el significado y no se utiliza como embedding. Dos frases casi idénticas pueden tener hashes completamente distintos. Tampoco confundir los bytes UTF-8 que guardan letras con los IDs del tokenizador.

Para comprobar otro fragmento:

```powershell
& outputs/venv-ml/Scripts/python.exe -X utf8 -B scripts/aprender_beto.py tokens --indice 1
```

El índice empieza en 0. Este comando carga solo el tokenizador local, no los pesos de BETO, y no descarga modelos. Si falta la caché local, informa del error.

## 5. Tildes, ñ, UTF-8 y errores de extracción

Hay que separar tres fenómenos. Un texto correcto puede mostrarse mal si una consola interpreta sus bytes con otra codificación. También puede existir corrupción real en el archivo. Finalmente, una extracción PDF o transcripción puede producir palabras equivocadas aunque el archivo sea UTF-8 válido. Guardar en UTF-8 resuelve la consistencia de codificación, pero no corrige por sí mismo el OCR o la transcripción.[^6]

La regla permanente quedó incorporada en [AGENT.md](../../AGENT.md): lectura y escritura explícitas en UTF-8; conservación de tildes y ñ; verificación posterior; reparación versionada de corpus. En Python se utiliza `encoding="utf-8"`, y `ensure_ascii=False` conserva caracteres legibles al escribir JSON. Los escapes JSON como `\u00f1` son otra representación válida de ñ; no son necesariamente corrupción.

El resumen didáctico no encontró en TRAIN las secuencias sospechosas específicas que busca y todos los textos estaban en NFC. Esto **no certifica ausencia de errores**: el detector es parcial. Un ejemplo como “el20” o una palabra mal transcrita necesita cotejo con la fuente. No eliminar acentos ni reemplazar todas las apariciones de un carácter por intuición. Cambiar normalización o texto modifica el hash y exige una nueva versión.

## 6. ¿1095 fragmentos son suficientes? Cómo decidir una cantidad

Son suficientes para ejecutar fine-tuning, y las corridas completadas lo demuestran. No se ha demostrado que sean suficientes para el nivel de generalización deseado. La cantidad necesaria depende de la dificultad de las fronteras, la diversidad de fuentes, la consistencia de las etiquetas, la distribución de clases y el rendimiento exigido. No existe un mínimo universal de “N fragmentos para BETO”.

La pregunta útil es cuánto mejora el desempeño al incorporar **más información fiable y diversa**. La curva de aprendizaje por tamaño de muestra compara el rendimiento para distintas cantidades de entrenamiento. No es lo mismo que la curva por épocas ya guardada, que mantiene los mismos ejemplos y cambia cuántas veces se aprenden.[^7]

Una propuesta futura sería comparar 25 %, 50 %, 75 % y 100 % del train elegible, usando subconjuntos anidados y cobertura de clases/familias. Mantener evaluación, receta y criterio de selección; registrar cómo cambia el número de actualizaciones. Si se quiere aislar solo el efecto de la información frente al coste computacional, añadir un control con presupuesto de actualizaciones comparable. Eso es un nuevo diseño, no una propiedad automática de una curva.

Si el resultado sigue subiendo con datos nuevos, ampliarlos resulta prometedor. Si se estanca, estudiar calidad, cobertura o representación. Si solo mejora train, no asumir que basta con añadir duplicados. Si las clases pequeñas siguen fallando, aumentar el total en la clase mayoritaria no atiende necesariamente su problema.

No se propone ejecutar ahora esa batería: cuatro tamaños por tres semillas equivaldrían a doce ajustes si ninguno pudiera reutilizarse. El presupuesto vigente conserva una sola trayectoria libre de desarrollo. Primero se deben aprovechar los contrastes históricos y definir qué información adicional justificaría una enmienda presupuestaria.

El tamaño de la **evaluación** también importa. En V hay solo 23 referencias de colonial y 23 de organización; un acierto adicional cambia el recall de cada una aproximadamente 4.35 puntos porcentuales. La precisión de una conclusión depende además de las familias independientes, no solo de sumar párrafos. No usar una fórmula de encuesta para fijar automáticamente el tamaño de entrenamiento de una red.

## 7. Precisión, recall y F1 con números pequeños

Una métrica resume un aspecto de la comparación entre referencias y predicciones. Para entenderlas, consideremos “crisis e ideas” frente a todas las demás clases. Este ejemplo es sintético: hay 20 fragmentos, de los cuales 10 son realmente “ideas”.

| | Predice ideas | Predice otra clase | Total real |
|---|---:|---:|---:|
| Referencia: ideas | 6 | 4 | 10 |
| Referencia: otra | 2 | 8 | 10 |
| Total predicho | 8 | 12 | 20 |

**TP = 6**, verdaderos positivos: reconoce seis ideas. **FP = 2**, falsos positivos: llama ideas a dos textos que no lo son. **FN = 4**, falsos negativos: deja escapar cuatro ideas. Los otros ocho son verdaderos negativos respecto a esa categoría.

La **precisión** responde: “De lo que presentó como ideas, ¿qué proporción era correcta?”. Aquí es `TP / (TP + FP) = 6 / 8 = 0.75`, o 75 %. Para una búsqueda temática, una precisión baja obliga al docente a descartar muchos resultados incorrectos.[^8]

El **recall** responde: “De todas las ideas que debía encontrar, ¿qué proporción encontró?”. Aquí es `TP / (TP + FN) = 6 / 10 = 0.60`, o 60 %. Con recall bajo, quedan fragmentos pertinentes escondidos bajo otras categorías.[^8]

**F1** combina precisión y recall con la media armónica:

```text
F1 = 2 × precisión × recall / (precisión + recall)
   = 2 × TP / (2 × TP + FP + FN)
   = 12 / 18 = 0.6667
```

La media armónica penaliza que una de las dos cantidades sea muy baja. No equivale al porcentaje total de aciertos. En la tabla se acertaron 14 de 20: la exactitud, o *accuracy*, es 70 %, mientras que F1 de ideas es 66.67 %.[^9]

Un modelo muy conservador puede emitir pocas predicciones de ideas, casi todas correctas: alta precisión y bajo recall. Uno que llame ideas a casi todo puede encontrar la mayoría, pero incluir muchos falsos positivos. El objetivo práctico decide qué errores pesan más; F1 da un equilibrio convencional.

Para **F1 macro**, calcular F1 por separado para cada una de las siete clases y promediar:

```text
F1 macro = (F1 campañas + F1 colonial + ... + F1 participación) / 7
```

Cada clase pesa lo mismo. El promedio *weighted* pesa según cuántas referencias tiene cada clase; puede ocultar peor rendimiento de clases pequeñas. Macro no es el F1 calculado a partir de la precisión macro y el recall macro. Se fija además qué hacer con denominadores cero; el proyecto utiliza siete etiquetas fijas y `zero_division=0`.[^9]

Ejemplo real de H: había **75** referencias de ideas; acertó **29**, predijo ideas **45** veces, tuvo **16 FP** y **46 FN**. Por tanto, precisión `29/45 = 0.6444`, recall `29/75 = 0.3867` y F1 `58/120 = 0.4833`. El problema visible es que se le escapan muchas ideas, además de incluir algunas predicciones incorrectas. Esto orienta el diagnóstico, pero no decide la causa.

Para reproducir la explicación, sin volver a inferir:

```powershell
& outputs/venv-ml/Scripts/python.exe -X utf8 -B scripts/aprender_beto.py metricas
```

Fuente del ejemplo real: [evaluación guardada R2/H](../../artifacts/beto-v3/phase-i-family/evaluation.json). Su estado textual es anterior a I; para el resultado final de I utilizar [gate-seed-42.json](../../artifacts/beto-v3/phase-i-family/gate-seed-42.json).

## 8. Cómo se realiza la validación en este proyecto

Durante entrenamiento se toman lotes de TRAIN, se calcula la pérdida y se actualizan parámetros. Al evaluar V se desactivan las actualizaciones y se usa modo de evaluación. Se comparan las predicciones con las etiquetas de referencia y se calculan las métricas. En el runner actual, la categoría es la de mayor logit. Se guarda el checkpoint de mayor F1 macro en V; ante empate se conserva el primero.

En H se eligió la época 4 de 20; en I, la 10 de 20. Ese proceso utiliza V para seleccionar: por tanto, sus cifras son resultados de desarrollo, no una evaluación final independiente. Cuantas más decisiones se toman mirando V, más necesario resulta reconocer esa reutilización.[^10]

| Conjunto | Intervención permitida durante desarrollo | Uso |
|---|---|---|
| TRAIN | Aprender; proponer versiones nuevas trazables | Actualización de parámetros. |
| V | Inferencia y selección según el protocolo congelado | Comparación de candidatos. No corregir retrospectivamente para rescatar una corrida. |
| S | Mantener su contenido cerrado | Evaluación final con receta y referencias cerradas. |

Para documentos relacionados, una división aleatoria de párrafos puede compartir estilo, contenido y fuente entre entrenamiento y evaluación. La división por grupos mantiene obras o familias completas separadas. La validación cruzada por grupos repite ajustes reteniendo distintos grupos; cuesta varios entrenamientos. Retirar una familia de predicciones ya guardadas solo es análisis de sensibilidad: no es validación cruzada con reentrenamiento.[^10]

En I se ejecutaron permutaciones y bootstrap por familias usando predicciones guardadas. Esos análisis cuantifican variabilidad bajo sus supuestos; no convierten ocho familias en miles de fuentes independientes ni eliminan el efecto de haber seleccionado con V. El [informe I](../../artifacts/beto-v3/phase-i-family/informe-I42.md) conserva esos límites.

## 9. Qué evaluaciones convienen a BETO

La evaluación se elige por la tarea y el uso previsto, no por el nombre BETO. Para este clasificador conviene una combinación:

| Evaluación | Qué aporta | Límite |
|---|---|---|
| F1 macro y métricas de las siete clases | Balance entre categorías y clases que fallan | Un promedio no explica causas. |
| Matriz de confusión | Qué pares intercambia | Necesita referencias fiables. |
| Desglose por familia, fuente y PDF/video | Transferencia y concentración de fallos | Grupos pequeños generan estimaciones inestables. |
| Comparación pareada e intervalos por familias | Magnitud y variación de diferencias | Depende de los grupos y del diseño. |
| Evaluación final en fuentes reservadas | Desempeño tras cerrar decisiones | Se pierde su independencia si se usa para ajustar. |
| Pruebas de comportamiento | Casos mínimos, invariancias y fronteras concretas | Un conjunto diseñado no estima frecuencia real de errores. |
| Prueba con docentes | Utilidad, errores de uso, tiempo de corrección | No sustituye la evaluación estadística. |

CheckList propone pruebas de comportamiento complementarias a una métrica agregada. Aquí podrían incluir conservar la predicción al cambiar espacios inocuos, distinguir una mención incidental de un argumento central y reconocer pasajes claramente ajenos al alcance. Las transformaciones deben preservar o cambiar el significado de forma controlada y revisada; eliminar tildes no siempre preserva significado.[^11]

Si el producto muestra confianza o permite abstenerse, evaluar además si esa confianza corresponde al error observado y publicar **cobertura**: qué porcentaje de casos recibe respuesta. Un sistema que rechaza casi todo puede parecer preciso entre lo poco que responde. No presentar abstención como mejora de F1 sin explicar cómo se cuentan los casos rechazados.

## 10. Cómo mejorar el etiquetado por IA y qué puede aportar un prompt

Un mejor prompt puede aclarar reglas, mostrar ejemplos y exigir evidencia. No convierte automáticamente las respuestas en verdad histórica. La investigación muestra resultados dependientes de la tarea: Gilardi y colaboradores obtuvieron resultados favorables frente a anotadores de plataforma en tareas sobre tuits; Fonseca y Cohen observaron beneficios de definiciones junto con límites de seguimiento de guías; Gu y colaboradores encontraron ventajas de asistencia a expertos sobre anotación completamente automática en un flujo de eventos. Ninguno mide directamente este corpus peruano.[^12][^13][^14]

La primera intervención recomendada es **comparar dos procedimientos de anotación frente a una referencia humana**, sobre TRAIN, antes de crear otra versión de datos. La [plantilla candidata](prompt-etiquetado-candidato.md) concreta: argumento central, categoría alternativa, regla de frontera, evidencia literal corta y estados de ambigüedad/extracción. Mantiene la guía actual; no añade contexto invisible al objetivo.

La guía v3.1 ya incluye muchas de esas exigencias. Repetirlas con palabras más solemnes no es una mejora demostrada. El aporte decisivo sería saber cuáles de sus decisiones confirman o corrigen personas competentes y medir si una plantilla nueva reduce esos errores. Un acuerdo entre dos sesiones del mismo modelo puede repetir el mismo sesgo.

Procedimiento propuesto:

1. Separar ejemplos de TRAIN para desarrollar el prompt y otros para comprobarlo, sin mostrar en los segundos su etiqueta humana a la IA.
2. Mantener texto, guía, modelo anotador y opciones comparables; variar primero solo la plantilla.
3. Revisar también acuerdos, no solo discrepancias. Si solo se inspeccionan errores notorios, no se estima la tasa global de etiquetas defectuosas.
4. Comparar métricas por clase, cobertura, evidencia válida y casos corregidos/empeorados. Registrar incertidumbre y coste de revisión.
5. Si el candidato mejora de forma convincente, adjudicar cambios concretos en una copia de TRAIN. Guardar original, propuesta, decisión, persona revisora y motivo.
6. Evaluar después BETO con ese train revisado y receta fija. Mejorar al anotador y mejorar al clasificador son experimentos distintos.

Los ejemplos few-shot deben proceder de desarrollo de TRAIN y estar adjudicados. No usar referencias de S ni los 56 casos de V como demostraciones para luego presentar esa misma V como evaluación ajena al diseño. Si hace falta contexto adicional para estudiar una fuente, registrarlo como una revisión distinta: cambia la información disponible y no es directamente comparable con la pasada v3.1 de objetivo solo.

## 11. Qué pasó con los 56 casos y qué otros métodos existen

Los **56** son fragmentos de una muestra dirigida: unión de 37 errores H de tres pares priorizados y 23 referencias de organización, con cuatro casos solapados. No constituyen una muestra aleatoria del corpus. Dos sesiones aisladas del mismo modelo revisaron los 56: **112 revisiones de ítem**, cero nuevos entrenamientos y cero nuevas inferencias BETO en ese bloque.

Hubo 48 consensos y ocho casos sin resolución. Nueve consensos discreparon de V; eso constituye señal para revisión, no nueve errores humanos confirmados. No se cambiaron las referencias congeladas. La [consolidación](../../artifacts/beto-v3/phase-i-family/ai-review-summary.json) y el [informe de revisión](../../artifacts/beto-v3/phase-i-family/informe-cierre-P2.md) documentan el procedimiento.

La secuencia “texto → referencia → predicción → diferencia → acción” es una forma pedagógica de organizar un caso. No hace falta repetirla manualmente para todos los ejemplos en cada corrida. Las métricas se calculan automáticamente; la revisión manual se dirige a preguntas concretas y se complementa con muestreo representativo.

Hay otros métodos: aprendizaje activo para priorizar ejemplos informativos; análisis de grupos; pruebas de comportamiento; evaluación de desacuerdos entre anotadores; curvas por tamaño; ablaciones; auditoría de duplicados y extracción. El aprendizaje activo puede combinar incertidumbre y diversidad, pero seleccionar únicamente lo incierto puede concentrar casos ambiguos.[^15]

Confident Learning utiliza probabilidades para identificar posibles problemas de etiquetas. En este proyecto sería una ayuda de priorización, no una autorización para sustituir referencias por predicciones. Usar predicciones fuera del ajuste de cada ejemplo, idealmente separadas por familia, evita confiar en probabilidades de un modelo que ya memorizó ese train. No es una auditoría gratuita si faltan esas predicciones.[^16]

## 12. Hipótesis, búsqueda eficiente y parámetros

Para aprender no hace falta escribir una hipótesis formal antes de cada comando de lectura. Para un experimento que consume recursos o pretende demostrar mejora, sí conviene definir una pregunta, una intervención, una comparación y un criterio. También se puede hacer exploración con un espacio de búsqueda predefinido, dejando claro que se busca una configuración y no que se demuestra una causa.

La recomendación anterior de cambiar una variable se refería a interpretar causalmente una comparación pequeña. **Es posible variar varios hiperparámetros con un diseño adecuado.** Un diseño factorial mide efectos e interacciones de combinaciones. La búsqueda aleatoria es una referencia eficiente frente a rejillas extensas; las técnicas adaptativas intentan concentrar presupuesto en configuraciones prometedoras.[^17]

| Método | Uso | Precaución para este proyecto |
|---|---|---|
| Ablación controlada | Aislar el efecto de datos, pesos o contexto | Mantener el resto comparable. |
| Búsqueda aleatoria | Explorar combinaciones de parámetros | Cada ajuste sigue consumiendo trayectoria y tiempo. |
| TPE/optimización bayesiana | Proponer configuraciones a partir de resultados previos | Requiere suficientes ensayos y un espacio razonable. |
| Successive halving/Hyperband | Dar pocos recursos al principio y ampliar a candidatos prometedores | Un modelo que aprende más lento puede descartarse demasiado pronto. |
| Caché y evaluación de predicciones guardadas | Ahorrar inferencias repetidas | Solo reutilizar si entrada, modelo y configuración coinciden. |

Hyperband combina asignación adaptativa de recursos y parada temprana. Optuna ofrece muestreadores y estrategias de poda para organizar búsquedas; no proporciona una garantía de mejora ni sustituye la separación de evaluación. Aquí son opciones para un protocolo futuro, no comandos que deban ejecutarse sobre las corridas cerradas.[^18][^19]

La longitud máxima controla cuánto texto entra. Aumentarla ayuda solo si recuperar contenido útil compensa coste y posible ruido. Debe medirse cuántos ejemplos se recortan y si se pierde la parte decisiva. El límite incluye tokens especiales; cambiarlo no repara un fragmento que ya estaba incompleto en la extracción.[^20]

## 13. Qué cambiaría ahora, y qué no está demostrado

**Cambio recomendado ahora:** sustituir el criterio de aceptar etiquetas por consenso de IA como principal evidencia por un piloto contrastado con revisión humana, usando la plantilla candidata si difiere sustancialmente de la existente. El producto de ese piloto será una lista trazable de decisiones, no una promesa de subir F1. Reutilizar las revisiones existentes y registrar el esfuerzo adicional.

Si se confirman defectos corregibles en TRAIN, el siguiente experimento propuesto sería **J-datos-revisados**: partir de BETO base con la receta H, aplicar únicamente correcciones adjudicadas a TRAIN, mantener 384 tokens y lr 2e-5, y no aplicar la ponderación por familia de I. Comparar con H para estudiar el efecto del cambio de datos y con R2 para las puertas de aceptación. Es una propuesta condicionada a encontrar correcciones materiales y definir presupuesto; no existe una corrida J ejecutada.

La corrección histórica anterior de TRAIN ya se probó sin mejora suficiente. Esta propuesta solo se justifica si aporta evidencia nueva, por ejemplo adjudicación humana de problemas concretos. Si la nueva revisión no identifica cambios defendibles, no relabelar por obligación ni consumir la última corrida repitiendo la estrategia.

| Parámetro o recurso | Decisión propuesta | Razón |
|---|---|---|
| Etiquetas | Medir su calidad con referencia humana; después versionar cambios confirmados | Actualmente no hay gold experto y hay desacuerdos pendientes. |
| Texto/UTF-8 | Verificar; reparar solo defectos reales, conservando originales | Visualización errónea y corrupción no son lo mismo. |
| Familias | Medir cobertura de subtemas y procedencia | Reponderarlas en I ya incumplió las puertas. |
| Longitud | Conservar 384 de momento | 192→384 ya se probó; no hay evidencia nueva para aumentar. |
| Tasa | Conservar 2e-5 para aislar el cambio de datos | El ensayo 4e-5 no dio una mejora conjunta suficiente. |
| Épocas | Conservar la receta comparable si se autoriza J | I ya alcanzó F1 train=1; más épocas no aseguran transferencia. |
| Modelo base | Conservar BETO para este contraste | Cambiar arquitectura simultáneamente impediría aislar los datos. |

No hay una manera conocida de garantizar una mejora contundente en este corpus. Una mejora convincente tendría magnitud útil, consistencia entre fuentes/semillas, ninguna regresión grave y confirmación en la evaluación final. Puede resultar de mejor información y etiquetas, otra representación o arquitectura, pero también puede requerir redefinir una tarea cuya frontera sea inherentemente ambigua. Esa redefinición tendría otro protocolo y no permitiría comparar F1 sin más con las siete clases originales.

## 14. Qué scripts ejecutar y por qué

Todos los comandos siguientes se ejecutan desde la raíz del proyecto en PowerShell. El prefijo `-X utf8` fija el modo UTF-8 de Python; `-B` evita crear caché de bytecode. Se usa el intérprete existente, sin instalar dependencias.

**Paso 1: comprender la composición.**

```powershell
& outputs/venv-ml/Scripts/python.exe -X utf8 -B scripts/aprender_beto.py resumen
```

Lee el train congelado, muestra clases, fuentes, familias y señales parciales de codificación. Ya se ejecutó; [resultado](../../artifacts/aprendizaje-beto/resumen.json). Se puede leer ese JSON en vez de repetir el comando.

**Paso 2: entender los números que ve BETO.**

```powershell
& outputs/venv-ml/Scripts/python.exe -X utf8 -B scripts/aprender_beto.py tokens --indice 0
```

Tokeniza un solo texto en CPU usando la caché local. [Resultado guardado](../../artifacts/aprendizaje-beto/tokens-ejemplo.json). Cambiar `--indice` permite un ejercicio distinto sin entrenar.

**Paso 3: practicar las métricas.**

```powershell
& outputs/venv-ml/Scripts/python.exe -X utf8 -B scripts/aprender_beto.py metricas
```

Muestra el ejemplo de 20 casos y métricas H existentes. [Resultado guardado](../../artifacts/aprendizaje-beto/metricas.json).

**Paso 4: comprobar una modificación real del etiquetado.**

```powershell
& outputs/venv-ml/Scripts/python.exe -X utf8 -B scripts/aprender_beto.py comparar-etiquetas --referencia artifacts/aprendizaje-beto/entradas-etiquetado/referencia.json --antes artifacts/aprendizaje-beto/entradas-etiquetado/antes.json --despues artifacts/aprendizaje-beto/entradas-etiquetado/despues.json --salida comparacion-etiquetas-01.json
```

Primero deben existir esas tres entradas reales, con el [formato explicado en la plantilla](prompt-etiquetado-candidato.md). Este paso está preparado y probado con datos sintéticos; **no se ejecutó una comparación de prompts reales ni una revisión humana nueva**. El programa exige IDs de TRAIN, hashes iguales y cobertura exacta. No llama a un LLM ni aplica etiquetas.

`--salida` escribe un JSON nuevo únicamente en `artifacts/aprendizaje-beto/` y rechaza sobrescrituras. Para guardar otro resultado se elige otro nombre. Sin esa opción solo imprime. El código está en [aprender_beto.py](../../scripts/aprender_beto.py).

Los scripts científicos existentes tienen otro alcance:

| Script | Función real | Uso recomendado |
|---|---|---|
| `verify_beto_phase_i.py` | Contratos de pérdida/gradientes y guardas de I; refresca su recibo | Solo ante cambio relevante; ya existe evidencia de 9/9. |
| `analyze_beto_phase_i.py --self-test` | Comprobar el evaluador estadístico con datos sintéticos | Solo si cambia ese evaluador. |
| `analyze_beto_phase_i.py` sin opción | Regenerar análisis de la corrida I cerrada | No usar como laboratorio: opera sobre artefactos científicos. |
| `train_beto_phase_i.py run --approval ...` | Ejecutar la corrida específica I con sus guardas | No relanzar I ni reutilizar su autorización para J. |
| `prepare_beto_phase_i.py` | Preparación del experimento I y sus archivos fijados | No es un generador genérico de nuevos experimentos. |

El ledger tras I registra **1695.88 s de desarrollo**, una trayectoria libre y tres reservadas para cierre. El intento I consumió **1885.39 s**, más que el saldo actual de desarrollo. Por tanto, no sería responsable recomendar una nueva corrida equivalente sin conciliar coste y alcance. No se ha creado un comando ficticio de entrenamiento J ni alterado las guardas. Fuente: [conciliación](../../artifacts/beto-v3/phase-i-family/budget-reconciliation.json).

## 15. Ruta breve de aprendizaje y criterio de avance

Primera práctica: abrir `items[0]`, explicar su etiqueta, ejecutar o leer el ejemplo de tokens y distinguir token ID, embedding y SHA256. La comprobación de comprensión es poder explicar qué campo alimenta a BETO y cuáles documentan su procedencia.

Segunda práctica: reconstruir a mano precisión, recall y F1 de la tabla de 20 casos. Después explicar por qué H puede tener precisión 0.6444 y recall 0.3867 en ideas. La comprobación es distinguir falsos positivos de falsos negativos y no traducir F1 como porcentaje de aciertos.

Tercera práctica: leer el informe de los 56 casos y separar consenso, verdad de referencia y corrección confirmada. Comparar la plantilla candidata con la guía existente y diseñar una revisión humana de TRAIN con recursos explícitos.

Cuarta práctica: redactar una ficha experimental con pregunta, cambio único o diseño multivariable, comparación, particiones, métrica, criterio, presupuesto y condición de parada. Solo después implementar un runner nuevo cuando la intervención esté justificada. Un experimento negativo correctamente medido permite descartar una ruta; no debe ocultarse ni repetirse buscando una semilla favorable.

## Fuentes

Las fuentes externas sustentan conceptos y métodos; los resultados del proyecto proceden de los archivos locales enlazados. Las páginas de bibliotecas consultadas describen métodos generales; no se actualizaron las versiones instaladas para seguir ejemplos de versiones recientes.

[^1]: Devlin, J., Chang, M.-W., Lee, K. y Toutanova, K. (2019). [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://aclanthology.org/N19-1423/). NAACL-HLT, pp. 4171–4186. Preentrenamiento y adaptación a tareas.
[^2]: Cañete, J. y colaboradores (2020). [Spanish Pre-trained BERT Model and Evaluation Data](https://users.dcc.uchile.cl/~jperez/papers/pml4dc2020.pdf), PML4DC/ICLR; [modelo cased de DCC UChile](https://huggingface.co/dccuchile/bert-base-spanish-wwm-cased). Identidad y origen de BETO.
[^3]: Hugging Face. [BERT: documentación de Transformers](https://huggingface.co/docs/transformers/model_doc/bert). Entradas y clasificación de secuencias; consulta 11-09-2026.
[^4]: PyTorch 2.7. [CrossEntropyLoss](https://docs.pytorch.org/docs/2.7/generated/torch.nn.CrossEntropyLoss.html). Función de pérdida; para la semántica concreta del proyecto consultar también `scripts/beto_phase_c_core_v3.py` y `scripts/beto_family_loss.py`.
[^5]: Hugging Face. [Tokenization algorithms](https://huggingface.co/docs/transformers/main/en/tokenizer_summary). Subpalabras y representación; consulta 11-09-2026.
[^6]: Unicode Consortium. [UTF-8, UTF-16, UTF-32 & BOM](https://www.unicode.org/faq/utf_bom.html) y [Normalization](https://www.unicode.org/faq/normalization.html). Codificación y normalización; consulta 11-09-2026.
[^7]: scikit-learn. [Validation curves and learning curves](https://scikit-learn.org/stable/modules/learning_curve.html). Tamaño de entrenamiento y curvas; consulta 11-09-2026.
[^8]: scikit-learn. [precision_recall_fscore_support](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html). Definiciones y soporte; consulta 11-09-2026.
[^9]: scikit-learn. [f1_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html). Fórmula, promedios y denominadores cero; consulta 11-09-2026.
[^10]: scikit-learn. [Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html). Selección, test y grupos; consulta 11-09-2026.
[^11]: Ribeiro, M. T., Wu, T., Guestrin, C. y Singh, S. (2020). [Beyond Accuracy: Behavioral Testing of NLP Models with CheckList](https://aclanthology.org/2020.acl-main.442/). ACL, pp. 4902–4912.
[^12]: Gilardi, F., Alizadeh, M. y Kubli, M. (2023). [ChatGPT Outperforms Crowd-Workers for Text-Annotation Tasks](https://arxiv.org/abs/2303.15056). Versión publicada en PNAS 120(30), e2305016120. Resultados sobre tuits; no evidencia directa para historia peruana.
[^13]: Fonseca, M. y Cohen, S. B. (2024). [Can Large Language Models Follow Concept Annotation Guidelines?](https://aclanthology.org/2024.findings-acl.478/). Findings of ACL, pp. 8027–8042. Beneficios y límites de las definiciones en prompts.
[^14]: Gu, F. y colaboradores (2026, versión 3). [Large Language Models Are Effective Human Annotation Assistants, But Not Good Independent Annotators](https://arxiv.org/abs/2503.06778v3). Registro con referencia a Findings ACL 2026. Flujo de anotación de eventos, distinto del presente corpus.
[^15]: Settles, B. (2009). [Active Learning Literature Survey](https://burrsettles.com/pub/settles.activelearning.pdf). University of Wisconsin–Madison, Technical Report 1648.
[^16]: Northcutt, C., Jiang, L. y Chuang, I. (2021). [Confident Learning: Estimating Uncertainty in Dataset Labels](https://research.google/pubs/confident-learning-estimating-uncertainty-in-dataset-labels/). JAIR 70, pp. 1373–1411.
[^17]: Bergstra, J. y Bengio, Y. (2012). [Random Search for Hyper-Parameter Optimization](https://www.jmlr.org/beta/papers/v13/bergstra12a.html). JMLR 13, pp. 281–305.
[^18]: Li, L., Jamieson, K., DeSalvo, G., Rostamizadeh, A. y Talwalkar, A. (2018). [Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization](https://www.jmlr.org/beta/papers/v18/16-558.html). JMLR 18(185), pp. 1–52.
[^19]: Optuna. [Efficient Optimization Algorithms](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html). Muestreo y poda; consulta 11-09-2026.
[^20]: Hugging Face. [Padding and truncation](https://huggingface.co/docs/transformers/main/en/pad_truncation). Longitud máxima y truncamiento; consulta 11-09-2026.
