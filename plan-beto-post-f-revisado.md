# Plan operativo revisado de BETO después de la fase F

**Dictamen: el plan original es razonable para limitar el gasto y obtener evidencia, pero no permite anticipar que se alcanzará F1 macro de 0,70. Conviene adoptarlo con correcciones antes de entrenar.** La prioridad debe ser resolver carencias observables de información y de ejemplos de entrenamiento en las distinciones históricas. Cambiar el dropout sigue siendo un experimento posible, con menor respaldo específico en los errores documentados.

Este documento revisa `plan-beto-post-f(2).md` y contrasta sus cifras con `phase-f-results.md`, `phase-d-analysis.md` y el antecedente `plan-beto-f1-070(1).md`. Es una propuesta operativa nueva: no acredita entrenamientos, inspección del corpus completo ni verificación de pesos o código en la laptop. Los informes permiten evaluar el razonamiento del plan; los manifiestos y el registro local deberán confirmar el estado efectivo antes de ejecutarlo.[^1]

**1. Qué resultados se pueden esperar razonablemente**

Hay tres resultados distintos que conviene separar. El primero es producir un experimento informativo dentro del presupuesto; el plan revisado está diseñado para eso. El segundo es conseguir una mejora reproducible en validación; es plausible, pero sigue sin demostrarse para las intervenciones propuestas. El tercero es alcanzar 0,70 en videos independientes y mantener todas las clases por encima de 0,50; ese resultado continúa abierto.

No es defendible asignar ahora un porcentaje de probabilidad de éxito ni prometer una cantidad de ejemplos suficiente. Falta conocer la cobertura real de entrenamiento por familia y clase, la proporción de entradas cuya información es recuperable y la consistencia de las referencias históricas. Una revisión de 32 casos sirve para elegir una hipótesis; no permite estimar un techo de rendimiento.

| Indicador documentado | Valor | Implicación práctica |
|---|---:|---|
| R2 H+T, F1 macro medio en V | 0,524606 ± 0,008453 | Es el control de desarrollo que debe conservarse. |
| R2/42 | 0,532392 | Comparador del primer piloto con semilla 42. |
| Solo T, media | 0,425612 ± 0,011457 | Retirar H perjudicó la receta probada en las tres semillas. |
| TF-IDF H+T | 0,459166 | BETO lo supera en desarrollo; falta la prueba final. |
| Brecha entre 0,70 y la media R2 | 0,175394 | Faltan aproximadamente 17,54 puntos de F1. |
| F1 final de entrenamiento de R2 | 1,0 en las tres semillas | El modelo logra ajustar train; no demuestra por sí solo la causa de la brecha. |
| V evaluable / inventario de V | 444 / 489, aproximadamente 90,80 % | El F1 está condicionado a las referencias resolubles. |
| Familias de V | 8 | La estabilidad entre semillas no equivale a estabilidad entre obras nuevas. |

Si las tres clases con F1 superior a 0,50 conservaran sus resultados, las otras cuatro tendrían que pasar de una media de **0,399233 a 0,706173** para alcanzar el macro de 0,70. Es una identidad aritmética, no una predicción. Un piloto que pase de 0,53 a 0,55 puede justificar confirmación, pero todavía dejaría una distancia grande hasta el objetivo.[^1]

**2. Qué conservar y qué corregir del plan**

| Elemento | Evaluación | Cambio operativo |
|---|---|---|
| Mantener R2 H+T | Correcto para las condiciones probadas. | Reutilizar controles y checkpoints; no repetir T-only. |
| Separar familias y mantener S cerrada | Esencial para el objetivo de generalizar entre obras. | Conservar particiones y evitar reproducciones o contexto que cruce entre ellas. |
| Una comprobación de hasta 32 entradas | Adecuada como diagnóstico barato. | Incluir Crisis e ideas y controles de relevancia, sin aumentar el tamaño. |
| Contexto anterior auténtico | Hipótesis razonable cuando aporta información ausente. | Demostrar trazabilidad y disponibilidad en uso real; no asumir que todo error se resuelve con contexto. |
| Hasta 80 entradas nuevas o revisadas | Adecuado como piloto de datos. | Elegirlas por carencias y contrastes, no por una cuota genérica. |
| Dropout de cabeza 0,20 | Contraste económico, sin ganancia predecible. | Mantenerlo como alternativa justificada, no como salida automática de un diagnóstico inconcluso. |
| Puerta de +0,02 | Útil para decidir gasto; no es significancia estadística. | Añadir una comprobación de progreso en clases históricas y en el grupo objetivo. |
| Tres semillas | Mejora la descripción de sensibilidad a entrenamiento. | Añadir sensibilidad por familia usando predicciones guardadas, sin nuevos ajustes. |
| Reserva de 200 para S | Puede ser insuficiente para las cuotas de clases. | Examinar la viabilidad del diseño antes de gastar desarrollo, sin abrir contenido de S. |
| Veinte épocas | Conserva la comparación con R2. | Mantenerlas en estos pilotos; no convertirlas en una regla universal de BERT. |

**3. El diagnóstico debe incluir Crisis e ideas**

La propuesta original selecciona ocho entradas de cada una de las cuatro clases con F1 inferior a 0,50. Eso deja fuera una dificultad importante: **Crisis e ideas tiene F1 0,514577, pero recall cercano a 0,4089 y 34 errores persistentes**. Participación también acumula 34. Juntas reúnen 68 de los 133 errores persistentes, aproximadamente 51,13 %. Las cantidades no sustituyen el peso igual de las clases en macro-F1, pero justifican incluir ambas en el diagnóstico.[^1]

| Clase | Soporte V | F1 medio R2 | Evidencia que orienta la intervención |
|---|---:|---:|---|
| Campañas y conflictos militares | 63 | 0,742488 | Proteger desempeño; revisar la frontera con participación. |
| Contexto colonial y antecedentes | 23 | 0,361290 | Confusión con instituciones republicanas y cronología poco clara. |
| Crisis e ideas emancipadoras | 75 | 0,514577 | Bajo recall; se deriva hacia organización y liderazgos. |
| Liderazgos, diplomacia y proyectos | 32 | 0,410572 | Confusión entre actuación/proyecto e institución. |
| No relevante | 168 | 0,818244 | Contenido histórico mezclado con introducciones o despedidas puede descartarse. |
| Organización y consecuencias republicanas | 23 | 0,441819 | Recall alto y precisión baja: recibe falsos positivos. |
| Participación social y regional | 60 | 0,383251 | Se confunde con campañas, antecedentes, liderazgos o irrelevancia. |

También importa la composición de la mejora anterior: el informe D atribuye aritméticamente el 55,7 % del aumento macro R2−R0 a la mejora de No relevante. Esto no invalida R2, pero impide interpretar todo el progreso como mejor discriminación entre temas históricos.[^1]

Como indicador secundario, la media de los seis F1 históricos actuales es **0,475666**. Debe calcularse a partir de las siete clases sobre **todas las filas de V**, promediando después los seis F1 históricos. No se eliminan filas con referencia No relevante: sus falsas predicciones históricas deben seguir penalizando la precisión. Este indicador nunca sustituye al macro principal de siete clases.[^2]

**4. Qué dice la investigación y dónde deja de aplicar**

Mosbach, Andriushchenko y Klakow distinguen fallos de optimización y diferencias de generalización durante el ajuste de BERT. Su estudio incluso muestra escenarios en los que una pérdida de entrenamiento casi nula no viene acompañada de deterioro de validación. Por tanto, train F1=1,0 no demuestra automáticamente que aumentar regularización resolverá el problema. En este proyecto, las curvas y los errores justifican investigar información, cobertura y generalización antes de alargar nuevamente el entrenamiento.[^3]

Cohan y colaboradores estudian clasificación secuencial de oraciones con BERT y muestran cómo el contexto de oraciones vecinas ayuda a interpretar una oración. Es evidencia más cercana al mecanismo propuesto que un estudio exclusivo de lenguaje abusivo. Sin embargo, utilizan tareas y representaciones distintas; sus resultados no validan específicamente una pareja objetivo/contexto de 382+127 tokens en transcripciones históricas peruanas.[^4]

Dropout tiene fundamento como regularización, pero la publicación original no determina que 0,20 sea apropiado para esta cabeza clasificadora. La documentación de Transformers distingue dropout de cabeza, capas internas y atención. Verificar el módulo efectivo es necesario para saber qué cambia; que un parámetro exista no prueba que sea la intervención con mayor beneficio esperado aquí.[^5][^6]

La literatura de aprendizaje activo respalda combinar información del modelo y diversidad para seleccionar ejemplos. No respalda escoger únicamente fragmentos de máxima incertidumbre ni trasladar automáticamente una cuota de 80. Para este proyecto se recomienda una selección simple por carencias de familias y contrastes temáticos, aprovechando artefactos existentes y sin implementar un nuevo sistema de adquisición.[^7]

Las anotaciones con LLM pueden permitir entrenar clasificadores útiles: Horych y colaboradores lo estudian en sesgo mediático con evaluación en benchmarks externos. Eso no convierte el acuerdo entre dos modelos en verdad histórica. La independencia de las familias evaluadas y la independencia de la referencia semántica son propiedades diferentes.[^8]

La reutilización de un conjunto para elegir recetas introduce riesgo de sobreajuste a la selección. Limitar candidatos y conservar S tiene respaldo metodológico; tres semillas en la misma V no eliminan ese riesgo.[^9] TAPT/DAPT sigue siendo una posibilidad futura respaldada en otros dominios, pero agrega preparación y otro entrenamiento. La evidencia local todavía no obliga a preferirlo frente a corregir un problema concreto de entrada.[^10]

**5. Secuencia operativa revisada**

**Paso A. Recuperar el estado y decidir una sola vez.** Leer el estado vigente, ledger, receta R2 y los informes D/F. Si una comprobación de etiquetas, duplicados o recarga ya pasó y no hay cambios que la invaliden, reutilizarla. Confirmar que no existe un entrenamiento equivalente activo o completado.

Obtener mediante scripts conteos por clase, familia y origen H/T; concentración de cada clase; longitudes; truncamiento efectivo; y disponibilidad de contexto anterior verificable. H designa aquí el conjunto histórico elegible y T las unidades audiovisuales incorporadas en V3: no asumir que H significa automáticamente anotación humana o que todos sus textos tienen una única procedencia.[^1]

Seleccionar una sola muestra de entrenamiento de hasta 32 entradas, fijando semilla y orden antes de mirar predicciones: cinco de cada una de las cinco clases históricas prioritarias —colonial, crisis, liderazgos, organización y participación—, cuatro de No relevante y tres de campañas. Procurar diversidad de familias y presencia de H/T cuando exista. Son cuotas de inspección propuestas, no un diseño para estimar prevalencias. Si faltan entradas, registrar el faltante sin nuevas rondas.

Comparar texto original, fragmento preparado y tokens que recibe BETO. Registrar qué información se perdió, si el texto anterior realmente contiene el referente que falta, si hay mezcla de temas o si existe una carencia documental observable. No emitir nuevas etiquetas dentro de una inspección sin presupuesto de anotación. Si hace falta decidir la referencia correcta, separar ese trabajo como revisión contabilizable.

La salida debe contener hasta 500 palabras y una tabla breve: evidencia concreta, mecanismo plausible, intervención, indicador objetivo y costo. Un diagnóstico insuficiente puede terminar en conservar R2; no activa dropout por defecto.

**Paso B. Elegir una intervención mediante esta tabla.**

| Evidencia encontrada | Primera intervención | Condición para ejecutarla |
|---|---|---|
| Falta un referente textual disponible inmediatamente antes; extracción trazable en varias entradas/familias. | Contexto auténtico. | Mantener el objetivo y poder construir la misma entrada en entrenamiento e inferencia. |
| Hay pocas familias para una distinción, errores verificables en train o ausencia de ejemplos contrastivos resolubles. | Versión corregida/ampliada de entrenamiento. | Lote concreto y presupuesto de anotación adoptado antes de intervenir. |
| Las entradas son utilizables, no hay carencia concreta prioritaria y queda una hipótesis de regularización no probada. | Dropout de cabeza 0,10→0,20. | Verificar el valor efectivo y mantener el resto de R2. |
| La distinción depende de diapositivas ausentes, o la guía no permite una etiqueta única estable. | Delimitar el problema antes de entrenar. | No inventar contexto ni redefinir las siete clases dentro de la comparación V3. |
| La evidencia no permite elegir. | Conservar R2 y cerrar este diagnóstico. | Registrar la incertidumbre; no prolongar auditorías. |

Esta prioridad es condicional. El corpus no ha sido inspeccionado íntegramente y no se puede afirmar todavía si contexto o datos debe ser la primera candidata.

**Paso C. Si corresponde contexto, probar una representación fija.** Mantener la propuesta de secuencia A con los tokens de contenido del objetivo R2 y secuencia B con hasta 128 tokens anteriores, limitada por el máximo de 512 incluyendo especiales. Con 382 tokens objetivo y tres especiales caben 127 de contexto. Retener los tokens anteriores más próximos, en su orden original; no sustituirlos por resúmenes ni explicaciones.[^6]

El objetivo sigue siendo clasificar A. El contexto B no recibe la etiqueta de A como nuevo ejemplo. Si no existe contexto verificable, conservar la entrada sin contexto y registrar cobertura. No saltar huecos de transcripción como si fueran continuidad, ni usar un bloque anterior que ya esté solapado dentro del objetivo. La extracción no debe consultar etiquetas o predicciones, y debe respetar familias y particiones.

Las etiquetas e IDs de V permanecen fijos. Cambia su representación de entrada mediante la misma regla, lo que debe quedar registrado como una condición nueva. Hacer controles baratos de longitud, segmentos, correspondencia de IDs y memoria. Una inferencia sola no acredita memoria suficiente para backward y estados del optimizador; contabilizar cualquier prueba de entrenamiento de acuerdo con el ledger y no esconderla como revisión gratuita.

Si esta representación mejora, la aplicación necesitará construirla también para nuevos videos. Entrenar con contexto y servir únicamente el fragmento aislado sería un cambio de distribución. La adaptación de producción se prepara después de elegir la receta, antes de sustituir un modelo publicado.

**Paso D. Si corresponde datos, intervenir hasta 80 entradas únicas.** Los 80 son un techo de trabajo, no una cantidad obligatoria de aceptadas. Reutilizar primero fuentes ya adquiridas de entrenamiento. Buscar obras nuevas únicamente cuando esas fuentes no cubran la carencia identificada. No incorporar reproducciones, paráfrasis ni derivados de V o S.

| Contraste de adquisición | Qué buscar en material real |
|---|---|
| Colonial / organización | Instituciones coloniales frente a instituciones republicanas, con el marco temporal explícito en el texto. |
| Crisis / organización | Legitimidad, soberanía o ruptura frente a funcionamiento institucional. |
| Liderazgos / organización | Actuación y proyectos de personajes frente a funcionamiento de instituciones. |
| Participación / campañas | Agencia colectiva frente a descripción de operaciones militares. |
| Histórico / No relevante | Casos de introducción o despedida con contenido histórico y otros sin él, según la guía vigente. |

Buscar ejemplos de ambos lados del contraste y de distintas familias cuando sea posible. Los pares son una ayuda para adquisición y revisión; el entrenamiento continúa con la pérdida de clasificación R2. No introducir simultáneamente pérdida contrastiva, sobremuestreo, cambios de pesos manuales o nuevos resúmenes sintéticos.

Versionar cada corrección con fuente, antes/después y criterio. Aplicar el mecanismo vigente de revisión sin mostrar predicciones BETO a quien adjudica. No presentar un etiquetado asistido por IA como revisión experta independiente. Mantener los desacuerdos sin resolver fuera de las nuevas incorporaciones.

El presupuesto actual deja una entrada para desarrollo y 200 para S. Elevar el techo de unidades a 1.280 permitiría como máximo 81 adicionales de desarrollo si el ledger cuenta unidades únicas. **No demuestra que quepan 80 unidades más todas sus pasadas si la unidad de gasto fuera cada intervención.** Confirmar la definición existente y llevar por separado unidades, propuestas, revisiones, adjudicaciones, tokens y tiempo; no cambiar el significado del contador para hacer caber el lote.

Con el train versionado, reutilizar R2 desde BETO base y recalcular pesos y pasos con las mismas fórmulas. Informar que esas cantidades cambian con los datos. Ajustar TF-IDF una vez sobre la misma versión, sin búsqueda adicional. Este piloto estima el efecto práctico del lote, no un efecto causal aislado del número de ejemplos.

**Paso E. Ejecutar y confirmar solo si corresponde.** Conservar 20 épocas y el horizonte del scheduler para los pilotos comparables. Los mejores checkpoints R2 fueron de épocas 8, 14 y 9; detener todas las ejecuciones a ocho perdería una mejora ya observada. No elegir un nuevo número de épocas mirando las primeras fluctuaciones de cada piloto.[^1]

Entrenar una candidata con semilla 42 desde el mismo BETO base. Comparar su checkpoint elegido con R2/42 sobre V íntegra. Mantener la puerta principal **F1 macro ≥0,552392**, equivalente a +0,02.

La revisión añade dos condiciones prácticas para gastar las réplicas: que aumente la media de los seis F1 históricos y que mejore la media de F1 del grupo de clases objetivo definido antes del piloto. Para contexto o regularización general, usar las cinco clases prioritarias; para un lote dirigido, registrar su grupo concreto antes de entrenar. Ambas medias se calculan conservando todas las filas y predicciones. Son reglas propuestas de asignación de presupuesto, no umbrales estadísticos validados.

Estas puertas conservadoras pueden descartar una candidata que funcionaría mejor con otra semilla. Se acepta ese riesgo para limitar gasto: un piloto rechazado no demuestra que la intervención sea inútil. Las mismas semillas facilitan una comparación emparejada, pero no garantizan perturbaciones aleatorias idénticas si cambian datos, longitud o consumo de aleatoriedad.

Si pasa, ejecutar semillas 43 y 44 de esa misma candidata, si caben. Conservarla como mejora de desarrollo cuando la media macro supere a R2 y al menos dos diferencias emparejadas sean positivas; además, las mejoras medias históricas y del grupo objetivo deben mantenerse sobre las tres semillas. Mostrar todas las pérdidas por clase. No llamar «objetivo cumplido» a esta decisión de desarrollo.

Si falla el piloto, un segundo contraste solo procede cuando ya estaba documentado como hipótesis distinta y cabe con sus dos réplicas. No cambiar la primera candidata ni su puerta después de ver el resultado. Si falla la confirmación de tres semillas, cerrar esta campaña y mantener R2, como propone el plan original.

**6. Evaluación económica de la generalización**

No comparar directamente el macro de siete clases entre obras como si todas tuvieran el mismo techo. El informe F explica que impone siete etiquetas y `zero_division=0` por obra: cuando una obra carece de clases, incluso un resultado perfecto para las presentes puede tener un macro bajo.[^1][^2]

Para la candidata confirmada, reutilizar predicciones y recalcular la diferencia de macro agrupado al excluir, sucesivamente, cada una de las ocho familias. Informar los ocho resultados y soportes restantes. Esto pregunta si la conclusión cambia cuando falta una obra; no constituye validación cruzada con reentrenamiento ni ocho experimentos independientes. Si desaparece una clase al excluir una familia, destacar que cambia la interpretación.

Reportar cuánto depende la mejora de una familia, sin convertir esta sensibilidad en otra búsqueda de checkpoints. No añadir un bootstrap complejo o nuevos folds solo para producir un intervalo aparentemente preciso con ocho familias. La evaluación final independiente sigue siendo necesaria.

**7. Presupuesto y viabilidad del cierre**

| Recurso | Estado después de F | Regla revisada |
|---|---:|---|
| Trayectorias | 11 de 18 consumidas | Máximo cuatro nuevas de desarrollo; conservar tres para cierre. |
| Tiempo de entrenamiento | 9.595,94 de 28.800 s | Restan 19.204,06 s. |
| Desarrollo posterior a F | Hasta 7.200 s propuestos | Aplicar también el límite global y reservar tiempo de cierre antes de lanzar. |
| Tiempo tras consumir ese techo | 12.004,06 s | Es saldo aritmético, no estimación del cierre. |
| Anotación | 999 de 1.200 | Una unidad de desarrollo y 200 reservadas; confirmar la unidad de contabilidad. |
| Servicios adicionales | US$0 | No contratar GPU, API ni almacenamiento. |

Cuatro ejecuciones de 26 minutos ocuparían aproximadamente 104 minutos, cerca del techo de dos horas. Una variante de mayor longitud, un train ampliado o guardados más lentos pueden superar esa previsión. Estimar el costo de completar el piloto y sus réplicas con medidas del runner; el máximo de cuatro trayectorias no obliga a realizarlas. Registrar fallos y tiempo real sin reiniciar contadores.[^1]

Hay una tensión concreta en S: siete clases con al menos 25 referencias requieren **175 referencias resolubles**. Dentro de 200 unidades queda un margen de solo 25 para irrelevancia sobrerrepresentada, distribución desigual y casos irresolubles. Además, 25 por clase es una meta de diseño del protocolo, no garantía de precisión estadística.[^1]

Como comprobación ilustrativa, si 200 unidades reprodujeran la distribución observada en las 444 referencias de V, una clase con soporte 23 aportaría aproximadamente **10,36 unidades**, lejos de 25. Esto no predice S: su distribución es desconocida. Sí muestra por qué no basta decir «hay 200 reservadas» para dar por viable el cierre.

Antes de entrenar, revisar únicamente el diseño y metadatos de reserva ya autorizados; no leer S para orientar pilotos. Si la cobertura no puede acreditarse sin anotar, dejar el riesgo explícito. Una eventual ampliación del test requiere un diseño prospectivo independiente de las predicciones. No equilibrar S después de ver errores, quitar clases ni forzar etiquetas. La excepción «23+23» de V —23 referencias en colonial y 23 en organización frente a la meta de 25— no satisface automáticamente las cuotas de S.

En el cierre, conservar la regla vigente: congelar receta, corpus y representación; fijar la semilla 42 para entrega; usar 43/44 para describir sensibilidad; y aplicar la duración final definida antes de abrir S. El antecedente propone la mediana de mejores épocas y permite incorporar V al train final. Ese modelo final cambia datos y scheduler respecto al checkpoint de desarrollo; su rendimiento debe comprobarse, no darse por heredado.[^1]

El criterio final continúa siendo F1 macro ≥0,70, F1 ≥0,50 en cada clase y superar TF-IDF sobre el mismo S y corpus final de entrenamiento. Una media favorable entre semillas no sustituye el resultado del artefacto de entrega. Si no se cumple, el resultado debe conservarse sin volver a optimizar contra S.

**8. Instrucción lista para preparar el siguiente piloto en Codex**

Este encargo prepara una candidata concreta. No ejecuta entrenamiento ni consume nuevas anotaciones. Así permite conocer la intervención y su costo antes de iniciar una campaña.

```text
Reevalúa operativamente BETO V3 después de F y prepara UNA candidata usando este plan revisado. No vuelvas a investigar en la web ni rehagas auditorías completas.

Lee development-current.json, el ledger vigente, la receta R2 y los informes D/F. Reutiliza verificaciones existentes. Si el estado local difiere del informe, usa el estado comprobado y explica la discrepancia antes de decidir. Conserva R2 H+T, sus tres controles y S cerrada. No entrenes, anotes, cambies etiquetas ni despliegues en este encargo.

Obtén por script cobertura clase/familia/H/T, concentración, truncamiento real y disponibilidad de contexto anterior trazable. Inspecciona como máximo 32 entradas de entrenamiento, con selección fijada antes de ver predicciones: cinco por cada clase colonial, crisis, liderazgos, organización y participación; cuatro No relevante; tres campañas. Procura diversidad de familias y H/T; registra faltantes. No repitas rondas. Compara fuente, fragmento y tokens efectivos; no adjudiques referencias nuevas.

Incluye Crisis: tiene recall cercano a 0.4089 y 34 errores persistentes. Reutiliza los 12 ejemplos de D sin ampliar la inspección cualitativa de V.

Elige contexto si falta información textual anterior recuperable con una regla disponible en inferencia. Elige datos si hay carencias concretas de cobertura o referencias de train que requieren revisión. Considera dropout de cabeza 0.20 solo si el control efectivo es 0.10, el contraste no existe y hay una justificación específica. Si la evidencia es insuficiente, conserva R2; no actives un experimento por descarte. No combines intervenciones.

Para contexto, conserva los tokens objetivo de R2 y añade solo contexto anterior auténtico dentro de 512 tokens totales. La etiqueta sigue correspondiendo al objetivo. Evita solapamientos, saltos de huecos y cruces entre particiones. Registra cobertura y prueba el contrato de entrada sin actualizaciones. Distingue memoria de inferencia de memoria de entrenamiento.

Para datos, prepara hasta 80 entradas únicas propuestas, nuevas o revisadas, con familias, carencia y costo. No las anotes. Conserva la reserva de S. Aclara cómo el ledger cuenta unidades y pasadas antes de proponer un techo nuevo; no interpretes esta instrucción como aprobación del incremento.

Deja una configuración y un comando realmente ejecutable en este repositorio. Declara antes del piloto el grupo de clases objetivo. Conserva R2, 20 épocas y scheduler; documenta consecuencias inevitables del cambio. Prepara las métricas: macro siete clases; F1/precision/recall/soporte por clase; media de seis F1 históricos sobre todas las filas; media F1 del grupo objetivo. No filtres filas No relevante para estos promedios.

Para confirmación, deja registrada la puerta propuesta: semilla 42 >=0.552392 y aumento de los dos promedios secundarios frente a R2/42. Solo entonces corresponden 43/44 si caben. La comparación final requiere media macro superior a R2, al menos dos diferencias positivas y mejoras secundarias medias conservadas. Son reglas de gasto, no significancia estadística.

Preserva máximo cuatro trayectorias de desarrollo, tres reservadas para cierre, techo adicional de desarrollo 7200 s y límite global 28800 s. Verifica saldos reales y estima costo antes de cualquier futura ejecución. Suma fallos, no reinicies contadores. Servicios adicionales US$0. Prepara la enmienda prospectiva de evaluación 23+23 cuando corresponda, manteniendo declarada la limitación; no la presentes como ejecutada ni extiendas esa excepción a S.

Entrega un diagnóstico de hasta 500 palabras, evidencia tabular y UNA decisión. Incluye candidata, costo, grupo objetivo, configuración, comando y necesidad concreta pendiente. Si una segunda hipótesis distinta queda justificada, regístrala solo como alternativa al fallo del primer piloto. No crees subagentes ni informes repetidos; no borres archivos.
```

**9. Instrucción para ejecutar la candidata ya preparada**

Usar cuando la preparación haya identificado una candidata realizable con los datos y presupuesto vigentes. Si requiere el lote de anotación, completar primero esa intervención bajo su presupuesto adoptado; este texto no autoriza el incremento de anotaciones.

```text
Ejecuta la candidata concreta y congelada en el diagnóstico posterior a F, conforme a plan-beto-post-f-revisado.md. Este encargo adopta las reglas revisadas de selección de la sección 5, la condición de desarrollo documentada y la extensión prospectiva 23+23 exclusivamente para esa condición. Mantén S cerrada, V con los mismos IDs y referencias, siete clases y limitaciones declaradas. Si es contexto, aplica únicamente la representación documentada. Si exige anotación no completada bajo presupuesto adoptado, no entrenes: identifica esa necesidad concreta.

Comprueba estado, saldos, procesos activos y resultados equivalentes. Usa los controles R2 existentes. Entrena una vez desde BETO base con semilla 42, receta de 20 épocas y horizonte completo, cambiando solo la intervención registrada y sus consecuencias documentadas. No pruebes valores alternativos. Conserva métricas y predicciones por época, mejor checkpoint y último estado reanudable; verifica recarga. No borres resultados históricos.

Compara con R2/42=0.532392 sobre toda V. Ejecuta 43 y 44 de la misma condición únicamente si cumple las tres puertas registradas: macro >=0.552392, media histórica superior y media del grupo objetivo superior. Antes de lanzarlas confirma que ambas caben dentro de los límites de tiempo y trayectorias. Si no pasa, termina; no ajustes la puerta después del resultado.

Con tres semillas, informa diferencias emparejadas y aplica la regla revisada de conservación. Calcula sensibilidad por exclusión sucesiva de familias usando predicciones guardadas; no reentrenes ni selecciones otro checkpoint con ese análisis. Reporta todos los retrocesos y clases ausentes. No declares alcanzada la meta final mirando V.

Máximo tres trayectorias nuevas en este encargo y cuatro de desarrollo acumuladas en esta campaña, conservando tres para cierre; máximo 7200 s nuevos de desarrollo y 28800 s globales. Los fallos cuentan. No inicies un segundo piloto, anotación, TAPT, S ni despliegue automáticamente. Actualiza un único estado y ledger y entrega el resultado con su comando de reanudación cuando corresponda.
```

**10. Límites para interpretar los resultados en la tesis**

El F1 de clasificación mide la asignación de temas a unidades previamente definidas. No acredita por sí solo que los límites temporales de los segmentos sean correctos. Si la tesis afirma calidad de segmentación, necesita referencias de límites y una evaluación separada, por ejemplo WindowDiff cuando sea adecuado al diseño. Añadir esa medición no sustituye el F1 ni debe consumir silenciosamente la reserva de anotación.[^11]

La utilidad percibida por docentes tampoco certifica las etiquetas históricas. Una revisión experta de referencias y una encuesta de utilidad responden a preguntas distintas. Cuando solo haya referencias asistidas por IA, declarar ese alcance. Si se consigue revisión experta parcial, informar selección, cobertura y desacuerdos sin extender la certificación al corpus completo.

El resultado defendible de esta campaña puede ser una mejora modesta o la conservación de R2 con evidencia clara sobre qué no funcionó. La decisión más razonable ahora es **preparar una intervención fundamentada y medirla**, evitando presentar el límite de dos pilotos como una receta suficiente para alcanzar 0,70.

**Fuentes**

[^1]: Evidencia del proyecto consultada: `plan-beto-post-f(2).md`, secciones 1–9; `phase-f-results.md`, resultados, curvas y presupuesto; `phase-d-analysis.md`, confusiones, curvas y muestra de errores; `plan-beto-f1-070(1).md`, fases A–G y protocolo de cierre. Archivos privados facilitados en esta conversación o recuperados entre los documentos disponibles; sin URL pública inventada. Se contrastaron los informes, no su ejecución completa. Los porcentajes adicionales de este documento son cálculos a partir de sus tablas.

[^2]: Scikit-learn. [f1_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html). Documentación oficial, consultada el 10 de septiembre de 2026. Definición de macro, selección de etiquetas y clases ausentes. Se utiliza la definición de la métrica, sin proponer actualizar dependencias.

[^3]: Mosbach, M., Andriushchenko, M. y Klakow, D. (2021). [On the Stability of Fine-tuning BERT: Misconceptions, Explanations, and Strong Baselines](https://arxiv.org/abs/2006.04884). ICLR 2021. Secciones 5–6; distinción entre optimización y generalización.

[^4]: Cohan, A., Beltagy, I., King, D., Dalvi, B. y Weld, D. S. (2019). [Pretrained Language Models for Sequential Sentence Classification](https://arxiv.org/abs/1909.04054). EMNLP-IJCNLP 2019. Secciones 1–2 y análisis; contexto para clasificación secuencial en textos científicos.

[^5]: Srivastava, N., Hinton, G., Krizhevsky, A., Sutskever, I. y Salakhutdinov, R. (2014). [Dropout: A Simple Way to Prevent Neural Networks from Overfitting](https://jmlr.org/papers/v15/srivastava14a.html). Journal of Machine Learning Research, 15, 1929–1958. Fundamento general de regularización; no valida un valor para BETO histórico.

[^6]: Hugging Face. [BERT — Transformers 4.57.1](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/bert). Documentación de BertConfig y tokenizador. El piloto debe verificar su implementación instalada; la representación propuesta y el reparto de tokens son decisiones de ingeniería.

[^7]: Margatina, K., Vernikos, G., Barrault, L. y Aletras, N. (2021). [Active Learning by Acquiring Contrastive Examples](https://arxiv.org/abs/2109.03764). EMNLP 2021. Selección de ejemplos mediante incertidumbre y diversidad; no valida las cuotas del presente plan.

[^8]: Horych, T., Mandl, C., Ruas, T., Greiner-Petter, A., Gipp, B., Aizawa, A. y Spinde, T. (2025). [The Promises and Pitfalls of LLM Annotations in Dataset Labeling: a Case Study on Media Bias Detection](https://aclanthology.org/2025.findings-naacl.75/). Findings of NAACL, 1370–1386. DOI: 10.18653/v1/2025.findings-naacl.75. Estudio de otro dominio, con evaluación externa y limitaciones de transferencia.

[^9]: Cawley, G. C. y Talbot, N. L. C. (2010). [On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation](https://jmlr.org/papers/v11/cawley10a.html). Journal of Machine Learning Research, 11, 2079–2107. Riesgo de ajustar decisiones al conjunto de selección.

[^10]: Gururangan, S., Marasović, A., Swayamdipta, S., Lo, K., Beltagy, I., Downey, D. y Smith, N. A. (2020). [Don’t Stop Pretraining: Adapt Language Models to Domains and Tasks](https://aclanthology.org/2020.acl-main.740/). ACL, 8342–8360. DOI: 10.18653/v1/2020.acl-main.740. Adaptación de dominio/tarea en ocho tareas de cuatro dominios.

[^11]: Pevzner, L. y Hearst, M. A. (2002). [A Critique and Improvement of an Evaluation Metric for Text Segmentation](https://aclanthology.org/J02-1002/). Computational Linguistics, 28(1), 19–36. DOI: 10.1162/089120102317341756. Evaluación de límites mediante WindowDiff.
