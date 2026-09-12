# Diagnóstico y decisión con evidencia existente

12 de septiembre de 2026. Síntesis documental: sin nuevas auditorías, juicios, inferencias, entrenamientos, cambios de etiquetas ni acceso al contenido V/S. Las pruebas faltantes se identifican como límites causales, no como tareas encargadas. No se reanudan procesos preparados.

La decisión más defendible es priorizar la cobertura conceptual de TRAIN. El patrón es compatible con asociaciones temáticas que no transfieren bien; no está probado que BETO use específicamente la identidad de fuente como atajo. Orden de plausibilidad como limitantes actuales: H3 > H1 > H2, con confianza moderada en el orden y sin porcentajes causales estimables. H3 no debe confundirse con una demostración de atajo documental.

El resultado actual es 0,491838 frente a 0,493735 sobre el mismo DEV de 160 textos. Es un estancamiento observado, no un techo demostrado. Los resultados históricos sobre otras particiones se usan solo como antecedentes, sin comparar directamente sus F1.

## H1 — Ruido, ambigüedad o inconsistencias de referencia TRAIN

- A favor: la revisión histórica v3.2 aplicó 37 cambios de principal y retiró 28 referencias únicas del TRAIN anterior. Son 65/385 casos TRAIN revisados (16,9%) en una selección dirigida; no una tasa poblacional ni errores históricos certificados. La lectura actual de siete TRAIN documenta fronteras de dominancia. En DEV, 32/79 errores del candidato se describen como solapamiento y 8/79 como referencia débil; la revisión exploratoria del asistente discrepa en 17/51 respuestas con clase única.
- En contra: los cambios anteriores ya están incorporados en la referencia actual; no son defectos pendientes de los 746 TRAIN. Los 137 registros con auditoría v3.2 pasan los controles documentales. La revisión del asistente es DEV, con guía resumida y posible exposición: no estima ruido TRAIN. Hay 29/79 errores actuales descritos como claros del modelo. La auditoría histórica de pares comparables también contiene estratos de acuerdo alto, aunque eso no certifica corrección histórica.
- Magnitud: residual desconocida. 609/746 sin auditoría v3.2 localizada significa cobertura documental incompleta, no 81,6% de ruido. Los 40/79 indicios DEV de solapamiento o referencia débil no son 40 etiquetas erróneas ni una estimación de pérdida de F1.
- Clases/familias: colonial/no relevante; ideas/organización/liderazgo; participación/militar. Antecedentes G08 y G15; posibles fronteras en los históricos. No hay prevalencia residual estimada por familia TRAIN.
- Prueba que falta: medición representativa e independiente de discrepancias semánticas sobre los 746 TRAIN actuales, con la misma guía completa y evidencia, distinguiendo ambigüedad de error. Consenso IA no sería gold experto.
- Veredicto: **moderada** como limitante residual; fuerte evidencia de incidencias históricas ya tratadas.

Fuentes: [aplicación v3.2](reference-revision-v3.2/informe.md), [censo actual](train-quality-audit/informe.md), [errores DEV](dev-error-boundaries/informe.md), [comparación del asistente](dev-blind-review-56/comparacion-asistente/informe.md).

## H2 — Contexto o segmentación insuficiente

- A favor: 10/79 errores del candidato están descritos principalmente como insuficiencia contextual. Hay pronombres sin antecedente, transiciones cortadas y mezcla de focos. La revisión de 56 DEV dejó dos pending_extraction y tres unresolved, sin que estos últimos equivalgan automáticamente a falta de contexto.
- En contra: DEV no pierde texto por el límite del tokenizador: 0/160 truncados; TRAIN solo 1/746, ocho tokens. 72/77 errores del control aparecen sin UNK. La intervención histórica G añadió contexto previo y no mejoró el F1 de su evaluación: 0,526266 frente a 0,532392. Era otro corpus/protocolo, con contexto solo en 414/1016 TRAIN, por lo que no descarta una reparación focalizada.
- Magnitud: señal directa descrita en 10/160 DEV (6,25%), equivalente a 12,7% de los errores actuales. Es una lectura expuesta, no una prevalencia exhaustiva: puede coexistir con otros problemas. No sustenta una explicación dominante del estancamiento.
- Clases/familias: alcance colonial/no relevante y no relevante/participación, especialmente G15; liderazgos/colonial en G08 y transiciones narrativas del componente video-bVrm2pJw4SA. Existen defectos históricos de extracción; los ya excluidos no cuentan como problemas TRAIN actuales.
- Prueba que falta: comparación emparejada del mismo objetivo con y sin su contexto auténtico mínimo, conservando el objeto de clasificación, que separe recuperación de evidencia de cambio de tema.
- Veredicto: **moderada como problema localizado**, débil como explicación principal. El truncamiento generalizado queda **descartado**.

Fuentes: [errores DEV](dev-error-boundaries/informe.md), [tokenización](reference-v32-truncation-diagnostic/informe.md), [diagnóstico funcional histórico](checkpoint-diagnostic/informe.md), [cobertura G](phase-g/representation-coverage.json), resumen histórico G en [AGENT.md](../../AGENT.md).

## H3 — Atajos de fuente/familia frente al concepto histórico

- A favor: organización republicana concentra 92/100 TRAIN en historical-basadre-hampe y militares 67/92. Los 14 errores actuales no relevante→colonial proceden de G15; los seis de la pareja colonial/liderazgo, de G08. El sobreajuste tardío aumenta confianza equivocada. El diagnóstico funcional histórico muestra competencia entre vocabulario y función: grupos sociales frente a doctrina de ciudadanía, vocabulario militar frente a postura colectiva.
- En contra: concentración no implica causalidad: militares mantiene F1 0,706 en el control pese a 72,8% de concentración. Los tres grandes componentes de video aportan 65,6% de DEV y 69,6% de los errores: su volumen explica buena parte del recuento. Históricamente, los checkpoints acertaban 56/56 pasajes usados, pero solo 15–17/27 nuevos de familias conocidas: el cambio de familia no es necesario para fallar. La muestra era dirigida y no emparejada por dificultad.
- Magnitud: concentración severa en organización, pero fracción de errores causada por atajos desconocida. El indicador descriptivo de concentración familiar aparece en 29/90 casos de la unión de errores, no en 29 casos causalmente atribuidos a fuente. Reponderar produjo apenas +0,001897 F1, IC95 [-0,086932; +0,060103], 11 correcciones y 13 regresiones. No demuestra mejora ni equivalencia; solo redujo la masa dominante de organización de 92% a 84%, sin aportar diversidad.
- Clases/familias: organización y militares en historical-basadre-hampe; colonial/no relevante en G15; colonial/liderazgo en G08. Las confusiones de función también aparecen dentro de familias conocidas y en componentes escritos.
- Prueba que falta: contraste que conserve contenido histórico y cambie exclusivamente una pista de fuente, junto con ejemplos de distinta función y vocabulario parecido dentro de una misma familia. No existe ese aislamiento causal para los checkpoints actuales; las pruebas de espacios con tokens idénticos no lo sustituyen.
- Veredicto: **moderada**. Fuerte evidencia de concentración y transferencia insuficiente; evidencia solo moderada e indirecta del mecanismo específico de atajo de fuente.

Fuentes: [diagnóstico AMP](reference-v32-amp-dev-diagnostic/informe.md), [resultado de pesos familiares](reference-v32-family-ready/execution-result/informe.md), [errores DEV](dev-error-boundaries/informe.md), [diagnóstico funcional histórico](checkpoint-diagnostic/informe.md).

## Decisión única

La causa actualmente más probable es **cobertura insuficiente de las distinciones históricas en TRAIN, que permite aprender asociaciones temáticas poco transferibles**, agravada por concentración documental y ambigüedad residual. Es la interpretación de H3 mejor sustentada; atribuirlo específicamente a identidad de fuente excedería la evidencia.

La única intervención siguiente que priorizaría es **una ampliación contrastiva de TRAIN**: pasajes completos de procedencias diversas que compartan vocabulario pero expresen funciones históricas distintas, especialmente alcance colonial/no relevante y doctrina/proyecto/ejercicio republicano. Se trata de aportar evidencia supervisada discriminante, no simplemente más cantidad o más familias nominales. Las ampliaciones anteriores y sus dificultades de estabilidad no demuestran que esta intervención vaya a mejorar F1; es una elección razonada, no un beneficio medido.

Esta recomendación no activa adquisición, anotación, modificación del corpus ni entrenamiento, y no reanuda los lotes detenidos. No hay evidencia suficiente para entrenar otra variante ahora ni para prometer 0,70. Se conservan candidato época 4 y control AMP. No se prepara otro proceso ni se convierte la incertidumbre causal en una auditoría indefinida.
