# Resultado de la trayectoria AMP v2 autorizada

La autora autorizó «lo autorizo». Se ejecutó una sola trayectoria desde BETO base, semilla 42, con la partición congelada 746 TRAIN / 160 DEV / 160 evaluación retrospectiva. **La ejecución terminó y pasó las verificaciones, pero el nuevo modelo no alcanzó macro-F1 > 0,70. No se promueve ni se inicia otro entrenamiento.** R2/42 se conserva; V y S permanecieron cerrados.

## Resultados

Early stopping detuvo el entrenamiento al finalizar la época 7. La época 5 se seleccionó exclusivamente por DEV y se verificó por recarga antes de abrir la evaluación retrospectiva.

| Época | Pérdida TRAIN ponderada | Macro-F1 DEV | NLL DEV |
|---|---:|---:|---:|
| 1 | 1,8884 | 0,1728 | 1,7007 |
| 2 | 1,3581 | 0,3561 | 1,5516 |
| 3 | 0,8582 | 0,3889 | 1,5240 |
| 4 | 0,5207 | 0,4390 | 1,4327 |
| 5 | 0,3083 | **0,4918** | 1,4951 |
| 6 | 0,1778 | 0,4843 | 1,6525 |
| 7 | 0,1013 | 0,4547 | 1,7676 |

La pérdida TRAIN incluye los lotes omitidos, según la política preregistrada; su ponderación difiere de la NLL DEV. Se interpretan sus tendencias, no la magnitud de la brecha entre ambas pérdidas.

| Métrica retrospectiva, 160 casos | Nuevo | R2/42 |
|---|---:|---:|
| Macro-F1 de siete clases | **0,3970** | 0,8641 |
| Exactitud | 0,4938 | 0,8938 |
| NLL | 1,5602 | 0,6008 |

Bootstrap de 2000 réplicas por componente, semilla 42: intervalo percentil 95 % del macro-F1 nuevo **[0,2334; 0,4476]**. Diferencia nuevo menos R2: −0,4671, intervalo emparejado **[−0,4928; −0,2949]**. El 17,6 % de las réplicas carece de alguna clase; se conservan las siete en el cálculo, conforme al protocolo. Son ocho componentes y una muestra retrospectiva: estos intervalos no corrigen exposición previa ni incertidumbre de las etiquetas.

R2 había estado expuesto al conjunto histórico del que procede esta evaluación. Su 0,8641 **no certifica generalización ni cumple por sí solo la meta**. La comparación es descriptiva y asimétrica, no una estimación causal del efecto de la guía o de AMP. Frente a R2, el nuevo modelo mejora el acierto en dos casos, empeora en 66 y mantiene el estado de acierto/error en 92.

| Clase | Soporte | F1 nuevo |
|---|---:|---:|
| campanias_conflictos_militares | 18 | 0,6207 |
| contexto_colonial_antecedentes | 15 | 0,1000 |
| crisis_ideas_emancipadoras | 11 | 0,1818 |
| liderazgos_diplomacia_proyectos | 17 | 0,2667 |
| no_relevante | 50 | 0,7755 |
| organizacion_consecuencias_republicanas | 18 | 0,3750 |
| participacion_social_regional | 31 | 0,4595 |

Matrices, precisión/recobrado/F1 por clase, resultados por componente y cambios individuales están en `outputs/beto-v3/reference-v32/amp-v2-42/evaluation/comparison.json`.

## Qué demuestra y qué queda incierto

**Problema numérico observado y controlado:** hubo dos omisiones por gradientes no finitos. Se redujo la escala sin actualizar optimizador ni scheduler en esos pasos. El registro completo verifica 329 intentos efectivos, 327 actualizaciones válidas y 327 pasos del scheduler en siete épocas; se respetaron los límites de cinco omisiones totales y tres consecutivas. El control permitió completar esta trayectoria, pero no prueba la causa exacta del fallo previo ni explica por sí solo la clasificación deficiente.

**Evidencia compatible con sobreajuste tardío:** después de la época 5 la pérdida TRAIN continúa bajando mientras el macro-F1 DEV baja y la NLL DEV sube. El early stopping evita elegir esas épocas posteriores. Esto no demuestra memorización literal ni identifica una causa única. La selección por F1 también explica que se elija la época 5 aunque la NLL mínima sea la de la época 4: no se cambió el criterio después de observar resultados.

**Dificultad temática desigual:** contexto colonial y crisis/ideas tienen F1 especialmente bajo; no basta con resolver AMP o prolongar entrenamiento. La referencia sigue siendo asistida por IA y no gold experto. Una trayectoria, pocos componentes y exposición histórica no separan de forma causal señales de fuente, ambigüedad residual, cobertura y regularización.

La intervención justificada es conservar el baseline y el early stopping y, antes de proponer otra trayectoria, acotar un análisis de los errores y cobertura en TRAIN/DEV con la evidencia ya guardada. La evaluación retrospectiva ahora está expuesta: no debe reutilizarse como conjunto independiente para ajustar parámetros o demostrar mejora posterior. No se justifican más épocas, TAPT/DAPT ni un cambio de etiquetas solamente con este resultado. No se requiere un experto para continuar el proyecto, ni se presenta consenso IA como corrección histórica probada.

## Verificación y presupuesto

`scripts/verify_beto_v32_amp_result.py` pasó: hashes de entradas congeladas y aprobación, recibos liquidados, selección/recarga DEV, integridad y contadores del registro numérico, identidad de los 160 casos, 320 predicciones finitas y reproducción exacta de métricas/bootstrap desde archivos guardados. No realizó inferencias adicionales. Recibo: [verification.json](verification.json).

Tiempo real: **351,562 s de entrenamiento + 15,625 s de evaluación = 367,187 s**. Saldo de desarrollo: **1310,0168577 s**. Cargo único: 22→23 trayectorias, techo autorizado 25→26. Las tres trayectorias de cierre y las 200 anotaciones de S permanecen reservadas; ambas reservas temporales se liquidaron a cero. Autorización consumida, sin reintento automático ni otra trayectoria de desarrollo autorizada.
