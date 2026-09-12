# Resultado: ponderación limitada por familia

**La trayectoria aprobada terminó correctamente, pero no demuestra mejora global ni alcanza macro-F1 >0,70.** La autora autorizó «aprobado», registrado con los hashes del plan y presupuesto. No se promueve el candidato ni se inicia otra trayectoria. Se conservan R2/42 y el control AMP; V/S permanecieron cerrados.

## Comparación preregistrada sobre DEV

Early stopping detuvo el candidato en la época 6 y seleccionó la época 4. Se comparó con la época 5 seleccionada del control AMP, usando los mismos 160 IDs y referencias y solo predicciones guardadas.

| Métrica | Familia, época4 | Control AMP, época5 | Diferencia |
|---|---:|---:|---:|
| Macro-F1 siete clases | **0,493735** | 0,491838 | **+0,001897** |
| Exactitud | 0,50625 | 0,51875 | −0,01250 |
| NLL sin ponderación | 1,387460 | 1,495135 | −0,107675 |

Intervalo percentil 95 % de la diferencia de F1, bootstrap emparejado por componente, 2000 réplicas/semilla42: **[−0,086932; +0,060103]**. Incluye cero y efectos de ambos signos; no demuestra superioridad ni equivalencia. El intervalo del F1 candidato es [0,325218; 0,524885]. Un 5,1 % de las réplicas carece de alguna clase; se conservan las siete al calcular macro-F1, conforme al protocolo.

Hay 11 casos que pasan de error a acierto, 13 de acierto a error y 136 sin cambio de estado de acierto/error. No se recuperó globalmente el desempeño: el pequeño aumento macro-F1 distribuye de otra forma los errores entre clases, mientras la exactitud baja dos aciertos netos. La menor NLL es un resultado descriptivo favorable en probabilidades, no prueba por sí sola de mejor calibración global.

| Clase | F1 candidato | F1 control |
|---|---:|---:|
| Campañas militares | 0,667 | 0,706 |
| Contexto colonial | 0,245 | 0,286 |
| Crisis e ideas | 0,538 | 0,385 |
| Liderazgos y diplomacia | 0,389 | 0,465 |
| No relevante | 0,650 | 0,640 |
| Organización republicana | 0,409 | 0,462 |
| Participación social | 0,558 | 0,500 |

Estos cambios por clase son exploratorios, con soportes pequeños y sin corrección por múltiples comparaciones. No justifican elegir otra ponderación observando qué clase mejoró. Ambas épocas fueron seleccionadas en este DEV, y la intervención se diseñó tras examinarlo: el contraste no es una prueba independiente de generalización ni una atribución causal definitiva a la fuente. No se abrió nuevamente la evaluación retrospectiva.

## Trayectoria y lectura del fallo

| Época | Pérdida TRAIN ponderada | F1 DEV | NLL DEV |
|---|---:|---:|---:|
| 1 | 1,9099 | 0,1998 | 1,7514 |
| 2 | 1,4408 | 0,3428 | 1,5548 |
| 3 | 0,9446 | 0,4164 | 1,5034 |
| 4 | 0,5812 | **0,4937** | **1,3875** |
| 5 | 0,3337 | 0,4638 | 1,4270 |
| 6 | 0,1886 | 0,4758 | 1,6300 |

Después de la época 4, TRAIN sigue reduciendo su pérdida mientras DEV tiene mayor NLL y menor F1. Persiste un patrón compatible con sobreajuste tardío y se justifica conservar early stopping. La pérdida TRAIN ahora incluye ponderación por familia y clase: no se compara su magnitud directamente con la del control ni con NLL DEV sin pesos.

La reponderación limitada **no resolvió el problema de clasificación** en este contraste. No demuestra que la concentración por familias sea irrelevante: la intervención solo redujo organización republicana de 92 % a 84 % de masa nominal dominante y no añadió diversidad. Tampoco prueba memorización literal ni descarta ambigüedad residual o insuficiencia de cobertura. Con una semilla y DEV reutilizado no se pueden separar todas esas causas.

Decisión: conservar los controles y detener esta rama de ponderación como mejora no demostrada. No aumentar automáticamente épocas, pesos, longitud ni gastar otra trayectoria cambiando varios parámetros. Cualquier siguiente experimento necesita una hipótesis distinta sustentada y autorización propia; el resultado actual no justifica prometer que más cómputo alcanzará 0,70.

## Verificación y consumo

`scripts/verify_beto_v32_family_result.py` pasó. Verifica inputs congelados, aprobación, recibos liquidados, selección/recarga, identidad de pesos float32 para los 746 casos TRAIN, journal numérico, correspondencia de ambas predicciones con los checkpoints elegidos y reproducción exacta de métricas/bootstrap desde guardados. Recibo [verification.json](verification.json). Comparación completa por caso/componente/matriz: `outputs/beto-v3/reference-v32/family-v1-42/evaluation/comparison.json`.

Se registraron **282 intentos efectivos, 281 actualizaciones válidas y una omisión AMP**, con 281 pasos del scheduler. Los límites numéricos no se modificaron durante la ejecución. No hubo inferencias nuevas en comparación ni verificación; las inferencias DEV durante entrenamiento/recarga estuvieron dentro del presupuesto TRAIN.

Tiempo real: **301,594 s TRAIN + 4,078 s comparación = 305,672 s**. Saldo de desarrollo **1004,3448577 s**. Cargo único 23→24, techo autorizado 26→27. Las tres trayectorias de cierre y 200 anotaciones S permanecen reservadas; las reservas temporales quedaron en cero. La autorización se consumió, sin reintento automático.
