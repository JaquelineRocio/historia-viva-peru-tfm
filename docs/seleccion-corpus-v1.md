# Selección y estado final del corpus v1

## Regla de inclusión

Una fuente entra al corpus si está procesada, aporta contenido de 1780–1842,
tiene autor y procedencia identificables, no duplica otra edición y mejora la
diversidad temática o de formato. La aplicación conserva los estados
`candidate`, `included` y `excluded`; una fuente nueva en la demo no entra
automáticamente al dataset académico.

## Cifras que deben citarse en el TFM

- Corte inicial procesado: **11 fuentes y 1,577 segmentos**.
- Snapshot congelado `gold-v1-source-aware`: **814 segmentos revisados**.
- Fuentes representadas en el snapshot: **10**.
- Formatos: **670 segmentos PDF y 144 de YouTube**.
- Split agrupado por fuente: **596 train, 81 validation y 137 test**.
- Distribución: todas las siete clases tienen al menos 100 ejemplos.
- Acuerdo de revisión asistida por IA: **Cohen’s Kappa 0.651**.

Las fuentes completas permanecen en un único split. Los recursos incorporados
después del corte pertenecen a la demo operativa, no al snapshot reproducible.

## Fuentes del corte académico

El conjunto combina ocho PDF y dos videos institucionales: trabajos de Scarlett
O'Phelan, Nelson Pereyra Chávez, Juan Fonseca Ariza, Claudia Guarisco, Juan Luis
Orrego Penagos, Carmen Villanueva, Susy Sánchez Rodríguez y Jorge Basadre; y
videos de Ciencias Sociales PUCP e Historia PUCP. Sus metadatos completos y sus
identificadores están conservados en el snapshot exportado.

Basadre fue limitado para evitar que una sola obra dominara el conjunto. Se
controlaron PDF cifrados o sin texto, duplicados, videos mayores de dos horas,
ventanas solapadas y paratextos sin valor histórico.

## Limitaciones académicas

El objetivo inicial de Kappa ≥ 0.70 no se alcanzó. La segunda revisión fue
asistida por IA y no participó un historiador independiente; ambos hechos deben
declararse como limitaciones. BETO v1 se mantiene como experimental y sus
predicciones nunca sustituyen la revisión humana del gold.
