# Plan operativo de BETO después de la fase F

**Decisión principal:** conservar R2 con H+T, comprobar una sola vez las carencias concretas de las entradas de entrenamiento y ejecutar como máximo dos pilotos distintos. Confirmar únicamente la candidata que justifique el gasto. La prioridad es mejorar la generalización entre obras, con BETO como clasificador y sin alterar la evaluación para obtener una cifra favorable.

El objetivo sigue siendo F1 macro ≥ 0,70, F1 ≥ 0,50 en cada clase y superar el baseline del protocolo, en la evaluación final independiente. No existe evidencia que permita garantizar ese resultado ni identificar una receta óptima antes de probarla en estos datos. Esta es una estrategia para reducir gasto y elegir experimentos informativos; no una predicción de mejora.

Este documento es una propuesta posterior a F. Sus nuevos experimentos y ampliaciones de anotación requieren adoptar explícitamente el alcance correspondiente mediante los prompts incluidos. No modifica retroactivamente el protocolo ni acredita ejecuciones nuevas. Los informes suministrados son la evidencia del estado local; no se han inspeccionado aquí todos los datos, pesos ni el runner actual.

**1. Estado que debe conservarse**

| Elemento | Resultado documentado |
|---|---|
| R2 H+T, tres semillas | F1 macro V = 0,524606 ± 0,008453 |
| Solo T, tres semillas | F1 macro V = 0,425612 ± 0,011457 |
| Diferencia T−H+T | −0,098994; retroceso en las tres semillas |
| Control para un piloto con semilla 42 | R2/42 = 0,532392 |
| Baseline TF-IDF H+T | 0,459166 sobre V |
| Entrenamiento | H = 590; T = 426; H+T = 1.016 unidades |
| Validación | V = 444 unidades resolubles de ocho familias |
| Reserva final | S cerrada; 200 entradas de anotación reservadas |
| Ajustes consumidos | 11 de 18 trayectorias |
| Tiempo de entrenamiento consumido | 9.595,94 de 28.800 segundos |
| Tiempo restante | 19.204,06 segundos, aproximadamente 5 h 20 min |
| Anotación registrada | 999 de 1.200; una entrada de desarrollo y 200 para S |

Los resultados de C, D y F son de desarrollo: V se utiliza para seleccionar condiciones y checkpoints. La variación entre tres semillas no estima por sí sola la incertidumbre frente a obras nuevas. F compara recetas prácticas: quitar H también cambia número de actualizaciones y pesos de clase; no aísla causalmente el efecto del origen de los textos.[^1]

No se debe presentar el F1 antiguo de otra población como punto inicial directamente comparable a V3. Tampoco la puntuación softmax de una frase de prueba equivale al F1 global. La prueba del SSD verificó un checkpoint y la Junction; no certificó toda la migración ni un respaldo independiente.

**2. Qué explica la prioridad del plan**

R2 y T-only alcanzan F1 de entrenamiento 1,0, con resultados retenidos muy inferiores. Esto es compatible con sobreajuste y generalización limitada; no demuestra por sí solo qué etiquetas están mal ni que falte una cantidad determinada de datos. La literatura distingue fallos de optimización de diferencias de generalización: aquí el ajuste alto y la estabilidad relativa de R2 hacen menos prioritario volver a investigar entrenamientos que no aprenden.[^2]

El diagnóstico de D encontró 133 errores persistentes en las tres semillas y examinó 12 casos. Identificó mezclas de temas, problemas ASR, dependencia de contexto previo y alusiones a diapositivas. Esa muestra es deliberada: no permite estimar la tasa de esos problemas en todo el corpus. Se debe reutilizar y contrastar con entrenamiento, no repetir otra inspección extensa de V.[^1]

| Clase | F1 medio R2 | Prioridad diagnóstica |
|---|---:|---|
| Campañas y conflictos militares | 0,7425 | Conservar desempeño; distinguir campañas de participación |
| Contexto colonial y antecedentes | 0,3613 | Cronología y distinción entre instituciones coloniales y republicanas |
| Crisis e ideas emancipadoras | 0,5146 | Confusión con organización y liderazgo; revisar también recall |
| Liderazgos, diplomacia y proyectos | 0,4106 | Distinguir acción/proyecto personal de estructura institucional |
| No relevante | 0,8182 | Evitar descartar fragmentos con contenido histórico mezclado |
| Organización y consecuencias republicanas | 0,4418 | Exceso de falsos positivos documentado en D |
| Participación social y regional | 0,3833 | Agencia colectiva frente a biografía, institución o campaña |

Las cuatro clases con F1 inferior a 0,50 promedian 0,3992. Si las otras tres se mantuvieran exactamente igual, esas cuatro tendrían que promediar aproximadamente 0,7062 para que el macro total llegara a 0,70. Es una identidad aritmética, no una proyección. Muestra que el salto pendiente es considerable y debe incluir las distinciones históricas difíciles.

**3. Qué respalda la investigación y qué no**

| Evidencia externa | Aplicación al proyecto | Límite |
|---|---|---|
| Las curvas por tamaño de entrenamiento ayudan a estudiar el beneficio de más datos.[^3] | La cantidad debe relacionarse con resultados y cobertura, no con GB descargados. | H, T y H+T no forman una curva limpia de tamaño: cambian mezcla y entrenamiento. |
| Dataset Cartography utiliza dinámicas de aprendizaje para examinar ejemplos.[^4] | Reutilizar información por ejemplo si ya fue guardada. | F1 agregado por época no basta para reconstruir cartografía; dificultad no significa etiqueta falsa. |
| Los errores de referencia pueden alterar comparaciones de modelos.[^5] | Las sospechas de etiquetado requieren evidencia y revisión separada. | No demuestra una tasa de error en BETO; no autoriza ajustar V al modelo. |
| Ajustes de optimización y duración mejoran ciertos escenarios de BERT con pocos datos.[^6] | Mantener la receta verificada y evitar repetir ensayos equivalentes. | Los estudios no justifican trasladar automáticamente sus ganancias a siete temas históricos en español. |
| El contexto puede cambiar la interpretación de textos en clasificación.[^7] | Probar contexto auténtico solo si hay evidencia de información ausente. | El estudio citado es de lenguaje abusivo; no prueba una ganancia para BETO ni que contexto siempre ayude. |
| Dropout es un mecanismo de regularización; BERT expone dropout de la cabeza.[^8][^9] | Permite un piloto pequeño, de bajo costo de implementación. | Ninguna fuente identifica 0,20 como óptimo para este corpus ni garantiza una mejora. |
| TAPT/DAPT puede mejorar tareas de clasificación en otros dominios.[^10] | Mantenerlo como alternativa futura si existe un corpus limpio y presupuesto. | No es la primera opción: necesita preparación y añade otra fase de entrenamiento. |

No se recomienda empezar con más épocas, otro barrido de pesos, reanotar todo, producir cientos de textos sintéticos o cambiar de arquitectura. La auditoría histórica ya registra ensayos de longitud, normalización y limpieza; sus resultados pertenecen a poblaciones anteriores y deben leerse antes de repetir hipótesis.[^11]

**4. Primera decisión: una comprobación acotada**

Preparar estadísticas con scripts sobre los datos existentes: ejemplos y familias por clase, concentración por fuente, duplicación ya documentada, longitudes y truncamiento real. Consultar verificaciones previas del orden de etiquetas y del aislamiento de fuentes; repetirlas solo ante una discrepancia nueva. No reconstruir auditorías completas ni descargar nuevamente transcripciones.

Inspeccionar como máximo 32 entradas de entrenamiento: ocho por cada una de las cuatro clases difíciles, procurando cuatro H y cuatro T y distintas familias. Seleccionar con semilla y orden predeclarados, antes de ver predicciones. Si no existen suficientes familias o entradas, registrar esa carencia; no sustituir silenciosamente la muestra.

Para cada entrada, comparar texto de origen, fragmento preparado y contenido que recibe BETO. Registrar pérdida observable de información, límites entre temas y señales de problemas de transcripción. No emitir nuevas referencias ni cambiar etiquetas. Si se necesita una adjudicación o corrección, queda como trabajo propuesto y contabilizable, no como una corrección gratuita o encubierta.

La salida debe ser un diagnóstico de hasta 500 palabras, una tabla de evidencias y una decisión: contexto, calidad/cobertura de entrenamiento o regularización. Puede declarar que la evidencia es insuficiente. No se permite convertirlo en revisiones sucesivas de 32 ejemplos ni presentar proporciones de la muestra como prevalencia del corpus.

**5. Pilotos priorizados y condiciones de uso**

**Piloto de contexto: preferente solo si el diagnóstico muestra información recuperable que falta.** Utilizar el mismo objetivo y su misma etiqueta, con un contexto anterior auténtico de la misma obra. La regla de extracción debe ser uniforme, independiente de predicciones y etiquetas, y reproducible en inferencia.

Una implementación candidata es una pareja BERT: secuencia A con exactamente los tokens de contenido que usaba R2 para el objetivo; secuencia B con hasta 128 tokens anteriores inmediatos, reducidos al espacio disponible dentro de 512 tokens incluyendo especiales. Con un objetivo de 382 tokens caben como máximo 127 de contexto en el formato de tres especiales. No recortar más el objetivo para introducir contexto. Si no hay contexto verificable, usar la representación sin contexto y registrar cobertura por origen y clase.[^9]

Esto cambia la representación y longitud máxima, por lo que requiere una enmienda prospectiva y un manifiesto propio. Los textos objetivo, IDs, etiquetas y familias de V se conservan. Su contexto no puede convertirse en datos de entrenamiento: se extrae dentro de cada partición y solo se utiliza como entrada de inferencia en V. No utilizar S durante preparación. Evitar duplicar cues del objetivo dentro del contexto y no introducir títulos de clase, justificaciones, fechas inferidas ni texto generado.

Se prueba el pipeline completo con contexto, no un efecto causal puro del contexto separado de la longitud. Antes de entrenar, comprobar con un lote pequeño la memoria de la RTX 3050. Si hay que cambiar microbatch, conservar batch efectivo y normalización; registrar las diferencias. No escalar a una compra de GPU. Que una entrada dependa de diapositivas no implica que texto vecino vaya a resolverla.

**Piloto de regularización: alternativa si las entradas son utilizables y no hay un cambio de contexto bien sustentado.** Cambiar únicamente el dropout de la cabeza clasificadora a 0,20, si el valor efectivo del control es 0,10 y ese contraste no existe ya. Mantener dropout del encoder, pérdida, pesos, longitud, datos, learning rate y demás receta R2. Verificar los módulos efectivos, no solo `config.json`.[^8][^9]

El valor 0,20 es una elección de ingeniería para un único contraste económico. No es una recomendación óptima derivada de un paper. Si ya se probó, no duplicar ni abrir una cuadrícula de valores. Tampoco acumular este cambio con contexto en el mismo piloto.

**Ruta de datos: prioritaria si hay carencias confirmadas de cobertura o referencias de entrenamiento.** Preparar una ampliación pequeña y dirigida, con hasta 80 entradas únicas intervenidas como primer techo propuesto: nuevas o revisadas, no 80 aceptadas obligatorias. La admisión y revisión determinan cuántas se incorporan. Priorizar errores de distinción entre clases y familias independientes; conservar casos claros y casos difíciles resolubles. Las cuotas por clase se calculan después del diagnóstico, sin rellenarlas con etiquetas forzadas.

Reutilizar primero fuentes de entrenamiento ya adquiridas. Si faltan fuentes, buscar solo las necesarias para los temas detectados y preferir transcripciones verificables. Una obra larga de una institución reconocida no asegura fragmentos útiles; la evidencia está en el contenido, cronología, límites y procedencia. No copiar ni parafrasear V/S como entrenamiento. No reemplazar todos los textos orales por resúmenes limpios, porque se cambiaría la distribución de uso.

Esta ruta necesita una ampliación explícita del presupuesto de anotación. El ledger actual no tiene 80 entradas de desarrollo disponibles: tiene una. La propuesta sería elevar el techo acumulado a 1.280 y mantener las 200 reservadas para S, documentando pasadas y costos. No ejecutar esa ampliación sin adoptar el prompt específico. El tamaño propuesto es un piloto de adquisición, no una cantidad científicamente suficiente para lograr 0,70.

Corregir o ampliar entrenamiento puede hacerse en una versión nueva, preservando el original y las justificaciones. Si el problema exige cambiar las definiciones de las siete clases, no tratarlo como una simple limpieza: cambia el problema de evaluación y exige un protocolo nuevo.

**6. Regla de gasto y presupuesto**

Reservar tres de las siete trayectorias restantes para el cierre del protocolo. Quedan como máximo cuatro de desarrollo: hasta dos pilotos con semilla 42 y dos réplicas de una sola candidata. No son cuatro entrenamientos obligatorios. Cada intento nuevo iniciado se registra, incluidos fallos, sin resetear contadores al cambiar de fase.

| Paso | Techo adicional | Regla |
|---|---:|---|
| Comprobación acotada | 0 entrenamientos | Una sola muestra de hasta 32 entradas; usar resultados existentes |
| Primer piloto | 1 entrenamiento | Intervención elegida antes de mirar sus resultados |
| Segundo piloto, opcional | 1 entrenamiento | Solo si el primero no pasa y existe otra hipótesis distinta, justificada y predefinida |
| Confirmación | 2 entrenamientos | Semillas 43 y 44 de una única candidata; reutilizar su semilla 42 |
| Cierre final | Hasta 3 entrenamientos reservados | Protocolo final vigente; no se ejecuta en esta campaña |

Puerta propuesta para confirmar: F1 macro V de semilla 42 ≥ **0,552392**, equivalente a +0,02 sobre R2/42. Se conserva también precisión, recall y F1 por clase; superar la puerta no permite ocultar un retroceso ni declarar cumplido el mínimo por clase. La puerta es una decisión de gasto, no significancia estadística. Una semilla puede descartar una opción prometedora o favorecer una poco estable: las réplicas y S son necesarias para limitar esa incertidumbre.

Confirmada una candidata, informar las tres diferencias emparejadas y su media; conservarla como mejora de desarrollo únicamente si la media supera al control y al menos dos diferencias son positivas, reportando cualquier deterioro por clase. Es una regla de selección práctica, no evidencia de que generalice universalmente. Si no supera al control, mantener R2 y cerrar esta campaña; no activar nuevos trucos por defecto.

Las ejecuciones R2 H+T existentes duraron aproximadamente 26 minutos cada una. Un piloto de tamaño y representación similares podría ser de ese orden, más preparación, pero los guardados, SSD, longitud y tamaño de datos pueden cambiarlo. No prometer una hora fija. Asignar como propuesta hasta 7.200 segundos nuevos al desarrollo, dentro del límite global; quedarían al menos 12.004,06 segundos si se consume ese techo. Comprobar que el cierre estimado cabe antes de gastar. Un intento incompleto no compite como si hubiera completado su receta.

La comparación debe conservar 20 épocas y el scheduler correspondiente para R2 y sus variantes. No extrapolar desde la primera época ni parar por una caída temprana de F1. Cuando un límite operativo impida continuar, guardar un estado recuperable y declarar la ejecución incompleta. No acortar una receta y presentarla como idéntica.

**7. Ahorro de tokens y almacenamiento**

Mantener un estado breve con fase, intervención, datos/configuración, resultado, presupuesto y comando de reanudación. Las tablas extensas y métricas van a JSON/CSV; el asistente recibe un resumen y ejemplos limitados. Los scripts hacen conteos, extracción y comparación. No enviar otra vez miles de fragmentos a la IA conversacional, repetir investigación web durante cada entrenamiento ni crear subagentes para duplicar diagnósticos.

Preparar una ejecución reanudable, registrar por época y revisar al cierre o ante un fallo. No pedir a la IA una interpretación nueva por cada época. Si se cambia a Claude, continuar con el estado y los archivos del mismo repositorio, verificando primero si existe un proceso activo. No iniciar un segundo entrenamiento equivalente. Esta organización reduce trabajo repetido; no permite prometer un consumo exacto de la cuota del proveedor.

Para las ejecuciones nuevas, conservar las métricas/predicciones de todas las épocas, el mejor checkpoint y el último estado reanudable. Utilizar nombres temporales y comprobar que el guardado nuevo terminó antes de retirar el estado temporal previo de esa misma ejecución. No borrar checkpoints históricos, `outputs_respaldo` ni otros archivos existentes como parte de este plan.

F conservó todos los estados por época: conviene evitar repetir ese crecimiento en la siguiente campaña. E: resuelve capacidad de salidas, pero los procesos deben conservar cachés y temporales en E: según la configuración verificada. No reformatear, cambiar particiones ni modificar la Junction durante entrenamientos.

En MLOps, CI puede comprobar el contrato de datos, configuración, lectura y una inferencia pequeña; no necesita entrenar BETO en cada push. El entrenamiento costoso debe ser explícito y producir artefactos versionados. Esa es una propuesta para el proyecto, no una afirmación sobre su CI actual. No subir cientos de GB a Git ni desplegar automáticamente un checkpoint experimental.

**8. Prompts de ejecución**

Usar el prompt 1 ahora. El prompt 2 corresponde al piloto preparado; el prompt 3 es opcional y autoriza explícitamente un pequeño presupuesto nuevo de datos. No ejecutar los tres como una cadena automática.

**Prompt 1 — decisión y preparación, sin entrenamiento**

```text
Continúa BETO V3 después de F usando plan-beto-post-f.md como propuesta operativa. Lee development-current.json, el ledger vigente, los informes D/F y solo los antecedentes necesarios para evitar repetir experimentos.

Conserva R2 H+T (F1 V medio 0,524606; semilla 42: 0,532392). S sigue cerrada. No entrenes ni reanotes en este encargo.

Reutiliza las comprobaciones ya hechas. Obtén por script cobertura de clases/familias H/T, concentración y truncamiento real. Inspecciona hasta 32 entradas de entrenamiento con selección fijada antes de ver predicciones: ocho por cada clase débil, procurando cuatro H y cuatro T y diversidad de familias. Compara texto de origen, fragmento y tokens que recibe BETO. Reutiliza los 12 casos de D como diagnóstico previo, sin ampliar la inspección de V. No emitas etiquetas nuevas ni extrapoles prevalencias desde la muestra.

Termina con UNA decisión: contexto auténtico, datos específicos o regularización. Si hay evidencia insuficiente, dilo. No hagas otra ronda de auditoría.

Si puede probarse sin nuevos datos/adjudicaciones, prepara el piloto correspondiente de la sección 5: contexto solo si falta información recuperable, o classifier_dropout=0,20 si el control efectivo es 0,10 y no se probó. No combines cambios. Deja configuración, manifiestos, comando ejecutable y prueba mínima de carga/memoria sin actualizaciones de entrenamiento. Documenta las enmiendas prospectivas necesarias; no las presentes como ya autorizadas.

Si se requieren datos, prepara un lote propuesto de hasta 80 intervenciones únicas de entrenamiento, indicando exactamente qué falta y qué costos tendría. No lo anotes ni uses la reserva de S.

Guarda un único diagnóstico breve, evidencia tabular y actualiza el estado/continuidad. No crees informes redundantes, descargas masivas, entrenamientos, subagentes ni despliegues. No borres archivos. Tu respuesta final debe indicar decisión, evidencia, costo y el siguiente comando o bloqueo concreto.
```

**Prompt 2 — piloto y confirmación condicional**

```text
Ejecuta la candidata concreta preparada en el diagnóstico posterior a F y las secciones 5–6 de plan-beto-post-f.md. Este encargo autoriza esa condición adicional de desarrollo y registrar prospectivamente la extensión 23+23 a ella, conservando la limitación original. Si la candidata es contexto, autoriza la nueva representación uniforme, preservando textos objetivo, etiquetas y familias de V. S continúa cerrada.

Primero confirma que la candidata no exige nuevas anotaciones y que no existe una ejecución equivalente completa o activa. Si requiere datos nuevos, entrega el lote concreto y no uses este prompt como autorización de anotación. Reutiliza los controles y contadores actuales.

Entrena una sola vez con semilla 42 desde BETO base, con la receta R2 de 20 épocas y horizonte completo, cambiando únicamente la intervención registrada y sus consecuencias explícitas. No pruebes otros valores. Conserva métricas/predicciones por época, mejor checkpoint y último estado reanudable de la ejecución nueva; no borres resultados anteriores.

Compara con R2/42=0,532392 sobre V íntegra de siete clases. Si F1 macro alcanza 0,552392, ejecuta exactamente las réplicas 43 y 44 de la misma condición, sujetas al presupuesto. Si no alcanza, termina con el resultado; no cambies el criterio para repetirla.

Máximo de este encargo: tres trayectorias nuevas, techo de desarrollo de 7.200 segundos acumulados desde esta campaña y límite global vigente. Reserva tres trayectorias para el cierre. Registra también intentos fallidos y tiempo consumido; no presentes ejecuciones incompletas como comparaciones terminadas. Verifica recarga y reporta errores por clase además del F1 macro.

Si hay tres semillas, informa media, dispersión y diferencias emparejadas. Solo conserva la candidata como mejora de desarrollo si su media supera R2 y mejora en al menos dos semillas; informa todos los retrocesos por clase. No declares alcanzado el objetivo final mirando V. Actualiza un único estado y ledger. No inicies un segundo piloto, S, TAPT ni despliegue automáticamente.
```

**Prompt 3 — solo si el diagnóstico exige una ampliación de entrenamiento**

```text
Ejecuta el lote concreto de entrenamiento propuesto tras el diagnóstico, con máximo 80 entradas únicas intervenidas entre nuevas y revisadas. Autorizo una enmienda prospectiva que eleve el techo acumulado de anotación de 1.200 a 1.280; las 200 entradas reservadas para S permanecen intactas. Registra cada entrada y cada pasada según el ledger existente, sin resetear contadores ni confundir propuestas con referencias aceptadas. Servicios adicionales de pago: US$0.

Prioriza material de familias de entrenamiento ya adquirido. Busca fuentes nuevas únicamente para carencias concretas que ese material no cubra. Conserva cronología y procedencia, y excluye familias o reproducciones de V/S. No adquieras más material solo para alcanzar una cuota.

Aplica la guía vigente y su revisión/adjudicación con evidencia, sin mostrar predicciones BETO a quienes deciden referencias. Usa los mecanismos de revisión autorizados en la sesión; si una capacidad falta, deja el lote preparado y describe la necesidad concreta. El acuerdo entre IA no se presenta como gold experto. Conserva desacuerdos irresolubles fuera de nuevas incorporaciones; no fuerces etiquetas.

Versiona el train nuevo preservando el anterior. No alteres V, S, las siete clases ni la representación a la vez. Si resolver el problema exige cambiar la taxonomía, detén esta ampliación y explica el cambio metodológico necesario.

Al cerrar el lote, prepara un único piloto R2 con semilla 42 sobre el train ampliado/corregido. Recalcula pesos y pasos por las mismas fórmulas y registra que cambian. Incluye el baseline TF-IDF comparable, presupuestos y configuración. No entrenes en este encargo; el siguiente paso será el prompt 2, adaptando explícitamente la condición a los datos versionados que acabas de preparar.
```

**9. Cierre y límites de la conclusión**

Si los pilotos no muestran una mejora suficiente, terminar la campaña y conservar R2. Eso no prueba que 0,70 sea imposible; indica que no está justificado seguir gastando con estas hipótesis y este presupuesto. Una ampliación posterior necesitaría evidencia nueva, un cambio de alcance documentado o datos mejor supervisados.

Si una candidata mejora, aún no se acredita el objetivo final. Congelar la receta y evaluar S según el protocolo de cierre, con la semilla de entrega predefinida y sin elegirla mirando S. Una media favorable entre semillas no sustituye el desempeño del artefacto entregado. Si S no puede alcanzar las cuotas originales dentro de la reserva de 200 anotaciones, documentar el problema antes de inferir; no forzar etiquetas ni ampliar silenciosamente el presupuesto.

Las referencias asistidas por IA permiten una evaluación reproducible contra esas referencias, pero no reemplazan la validación histórica independiente. No cambiar la verdad de referencia para que coincida con BETO. Tampoco excluir predicciones difíciles o clases del macro para obtener 0,70. La utilidad docente y la calidad de los límites temporales son resultados distintos del F1 de clasificación.

**Fuentes y notas**

[^1]: Informes suministrados: `phase-f-results.md`, secciones «Resultado de desarrollo», «Curvas y conservación» y «Baselines, presupuesto y límites»; `phase-d-results.md`, tablas de semillas y clases; `phase-d-analysis.md`, «Muestra acotada: 12 errores persistentes». Archivos locales aportados para esta revisión; no se ha verificado su ejecución íntegra en la laptop.
[^2]: Mosbach, M., Andriushchenko, M. y Klakow, D. (2021; preprint inicial 2020). [On the Stability of Fine-tuning BERT: Misconceptions, Explanations, and Strong Baselines](https://arxiv.org/abs/2006.04884). Investigación sobre optimización y generalización en BERT, RoBERTa y ALBERT.
[^3]: Scikit-learn. [Validation curves: plotting scores to evaluate models](https://scikit-learn.org/stable/modules/learning_curve.html), apartados de sobreajuste y curvas por tamaño. Documentación consultada el 10 de septiembre de 2026; se utiliza el principio metodológico, no se propone actualizar el entorno local.
[^4]: Swayamdipta, S. et al. (2020). [Dataset Cartography: Mapping and Diagnosing Datasets with Training Dynamics](https://aclanthology.org/2020.emnlp-main.746/). EMNLP, 9275–9293. DOI: 10.18653/v1/2020.emnlp-main.746.
[^5]: Northcutt, C. G., Athalye, A. y Mueller, J. (2021). [Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks](https://arxiv.org/abs/2103.14749). Sus resultados son sobre otros benchmarks, no sobre el corpus de este proyecto.
[^6]: Zhang, T., Wu, F., Katiyar, A., Weinberger, K. Q. y Artzi, Y. (2021; versión inicial 2020). [Revisiting Few-sample BERT Fine-tuning](https://arxiv.org/html/2006.05987v3). Secciones de optimización, duración y métodos de regularización; el estudio también limita la extrapolación de técnicas a todos los conjuntos.
[^7]: Menini, S., Palmero Aprosio, A. y Tonelli, S. (2021). [Abuse is Contextual, What about NLP? The Role of Context in Abusive Language Annotation and Detection](https://arxiv.org/abs/2103.14916). Evidencia de otra tarea sobre el papel del contexto, no una validación del piloto histórico.
[^8]: Srivastava, N., Hinton, G., Krizhevsky, A., Sutskever, I. y Salakhutdinov, R. (2014). [Dropout: A Simple Way to Prevent Neural Networks from Overfitting](https://jmlr.org/papers/v15/srivastava14a.html). Journal of Machine Learning Research, 15, 1929–1958.
[^9]: Hugging Face. [BERT, documentación de Transformers 4.57.1](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/bert), `BertConfig`, `classifier_dropout` y formato de parejas. Es una versión cercana a 4.57.6 documentada en la auditoría; comprobar la implementación instalada y el checkpoint, sin actualizar dependencias por este informe.
[^10]: Gururangan, S. et al. (2020). [Don’t Stop Pretraining: Adapt Language Models to Domains and Tasks](https://aclanthology.org/2020.acl-main.740/). ACL, 8342–8360. DOI: 10.18653/v1/2020.acl-main.740. Resultados sobre ocho tareas de cuatro dominios, no garantía de mejora para BETO histórico.
[^11]: Archivos suministrados `01-auditoria.md`, apartados «Qué ya se ha probado» y «Tokens y pérdida por truncamiento»; `06-pesos-clase.md`, contraste de vectores A/B. El ensayo de pesos de V2 no equivale a comparar pérdida ponderada y no ponderada en V3. `plan-beto-f1-070.md` se utiliza como antecedente de límites y cierre; las extensiones aquí propuestas no se presentan como parte ya ejecutada del plan original.
