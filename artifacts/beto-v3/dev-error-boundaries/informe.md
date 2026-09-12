# Análisis exhaustivo de errores: 160 referencias DEV

**La evidencia apunta a una dificultad extendida de clasificación, con focos importantes de alcance histórico y dominancia temática; no permite atribuir el resultado cercano a 0,50 principalmente a unas pocas fronteras ambiguas.** Tampoco demuestra que 0,50 sea un techo del modelo: son resultados de dos trayectorias, una semilla y un DEV reutilizado.

Se conservaron el candidato de época 4 y el control AMP de época 5. Se usaron exclusivamente sus predicciones guardadas; el texto objetivo se recuperó de la referencia congelada para lectura, sin contexto externo. No hubo entrenamiento, inferencias, adjudicación, cambios de etiqueta ni acceso a V/S.

## Entregables para revisión

- [Métricas y matrices completas de ambos modelos](metricas.md): precisión, recall, F1, soporte, TP/FP/FN de las siete clases, todas las confusiones entrantes/salientes, 21 parejas y resultados por componente.
- [Cinco fronteras y ejemplos representativos](fronteras-ejemplos.md): 11 ejemplos con texto íntegro, referencia, ambas predicciones, las siete probabilidades de cada modelo, reglas explicadas y lectura descriptiva. Las categorías sin casos se declaran expresamente.
- [Catálogo de los 160 textos](catalogo-160.md): incluye los 70 aciertos compartidos y diagnóstico de los 90 casos donde falla al menos un modelo; no limita la revisión a los ejemplos destacados.
- [Inventario estructurado](inventory-160.json): probabilidades completas sin redondear, familia, componente, hash, reglas y notas. [Resumen numérico](summary.json) y [verificación](verification.json).

## Métricas por clase del candidato

| Clase | Precisión | Recall | F1 | Soporte | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Campañas militares | 0,7368 | 0,6087 | 0,6667 | 23 | 14 | 5 | 9 |
| Contexto colonial | 0,1714 | 0,4286 | 0,2449 | 14 | 6 | 29 | 8 |
| Crisis e ideas | 0,5385 | 0,5385 | 0,5385 | 13 | 7 | 6 | 6 |
| Liderazgos y diplomacia | 0,3889 | 0,3889 | 0,3889 | 18 | 7 | 11 | 11 |
| No relevante | 0,8125 | 0,5417 | 0,6500 | 48 | 26 | 6 | 22 |
| Organización republicana | 0,3600 | 0,4737 | 0,4091 | 19 | 9 | 16 | 10 |
| Participación social | 0,6667 | 0,4800 | 0,5581 | 25 | 12 | 6 | 13 |

Candidato: 81 aciertos/79 errores, macro-F1 0,493735. Control: 83 aciertos/77 errores, macro-F1 0,491838. Entre ambos: **70 aciertos compartidos, 66 errores persistentes, 11 correcciones y 13 regresiones**. Un error persistente significa que ambos fallan frente a la referencia; no exige que elijan la misma clase errónea.

Contexto colonial es el principal receptor indebido: se predice en 35 casos, pero solo seis coinciden con la referencia. Sus 29 FP provienen de las otras seis clases, especialmente no relevante (14), liderazgos (4) y participación (4). No es solo una pareja confundida. Organización republicana también recibe 16 FP de cinco clases distintas. Todos los recalls del candidato están por debajo de 0,61.

## Cinco fronteras con más errores

Se cuenta cada pareja sin dirección, sumando ambos sentidos sobre los errores del candidato. Desempate: mayor recuento en el control y después orden congelado de etiquetas. Se publica también el ranking completo para hacer visible el empate; no se eligieron fronteras por lo llamativo de sus textos.

| Frontera | Errores candidato | Control | Persistentes elegibles* | Correcciones | Regresiones |
|---|---:|---:|---:|---:|---:|
| Contexto colonial ↔ no relevante | 14 | 11 | 13 | 1 | 1 |
| Contexto colonial ↔ organización republicana | 7 | 6 | 7 | 0 | 0 |
| Contexto colonial ↔ liderazgos | 6 | 5 | 6 | 0 | 0 |
| Campañas militares ↔ liderazgos | 6 | 4 | 3 | 1 | 3 |
| No relevante ↔ participación social | 5 | 6 | 3 | 1 | 2 |

*El error del candidato pertenece a la pareja y el control también falla, posiblemente hacia otra clase. Las correcciones pertenecen a la pareja del error del control; las regresiones, a la del candidato. Por ello no deben sumarse las tres columnas como si fueran exclusivamente errores del candidato.*

El quinto puesto empata en cinco errores con ideas↔organización, contexto↔participación y liderazgos↔organización. La regla de desempate selecciona no relevante↔participación; las otras tres no desaparecen del análisis. Las cinco seleccionadas suman **38/79 errores (48,1 %)**; las ocho, incluyendo todos esos empates, suman 53/79 (67,1 %). Quedan errores en las 21 parejas posibles.

### Qué muestran los textos de esas fronteras

**Contexto/no relevante: alcance, más que ambigüedad temática pura.** Los 14 errores del candidato son NR→COL y todos proceden de video-9Hmi1MIKBWI (casos G15). Suelen desarrollar reformas, comercio o política imperial de otros territorios, sin explicitar relación causal con independencia peruana. Son históricamente interesantes, pero R1 no significa cualquier historia colonial. G15-u030 se predice como contexto con confianza 0,8649, aunque desarrolla manufactura catalana/reglamentos, sin ese nexo. G15-u039 es una corrección y G15-u035 una regresión. Algunas entradas fragmentadas requieren cautela: la ausencia de nexo visible no permite inventar el contenido que las precedía.

**Contexto/organización: orden colonial frente a ejercicio republicano.** Se reparten entre cuatro componentes: no es solo una fuente. En bVrm2pJw4SA-b01-017, los dos modelos toman la crisis de subsistencia virreinal por organización republicana, aun cuando el objeto está antes de la llegada libertadora. Otros fragmentos mezclan aplicación de Cádiz y tránsito a 1823. G32-3 obliga a identificar el acto y el régimen, no a decidir por la palabra constitución. No existen correcciones ni regresiones en esta pareja; todos sus errores actuales son persistentes.

**Contexto/liderazgos: estructura como escenario frente a actuación de diputados.** Los seis errores actuales proceden de video-WI0PNN9G_-g (G08). En G08-u033, la resistencia administrativa de Abascal se desarrolla junto con denuncia y solicitud de destitución por Morales; las predicciones privilegian estructura. G08-u030 es distinto: una valoración de Morales y su presidencia hace que la referencia colonial necesite fundamentación adicional. No todos los desacuerdos de esta pareja se deben cargar al modelo como si la referencia fuera incuestionable. Tampoco hay correcciones ni regresiones aquí.

**Campañas/liderazgos: mandato militar, logística y proyecto político.** R3/R4 se aproximan en narraciones biográficas. bVrm2pJw4SA-b01-022 se selecciona como persistente: contratación y oficio de un almirante sostienen débilmente una referencia de operación militar. La corrección bVrm2pJw4SA-b01-023 sí desarrolla un proyecto monárquico. La regresión bVrm2pJw4SA-b01-013 mezcla relación San Martín/O’Higgins y éxitos militares. Como contraste claro adicional, S03-seg0042-s00577 desarrolla condiciones de un acuerdo diplomático, pero ambos predicen campaña. Está incluido íntegramente en el catálogo.

**No relevante/participación: pertinencia histórica antes que género o grupo mencionado.** G15-u024 desarrolla agencia femenina en una secuencia dinástica sin nexo peruano visible; los pronombres dificultan contextualizarla. G15-u023 es una corrección de alcance. La regresión bVrm2pJw4SA-b01-016 es el caso opuesto: sí explica aspiraciones de los integrantes de la expedición, pero el candidato lo descarta como NR. R7 no es un recipiente para fragmentos coloquiales difíciles.

## Lectura descriptiva de todos los errores

Se leyó el objetivo completo de cada uno de los 90 casos con error en al menos un modelo y se registró **una hipótesis principal**, no una etiqueta nueva. Los aciertos compartidos se inventarían como validados si se les asignara corrección histórica automática: aquí solo se registra acuerdo con la referencia.

| Hipótesis principal posible | Unión de errores (90) | Errores actuales candidato (79) |
|---|---:|---:|
| Solapamiento semántico | 35 | 32 |
| Evidencia débil para la referencia | 9 | 8 |
| Insuficiencia de contexto | 10 | 10 |
| Error claro del modelo según la guía y objetivo | 36 | 29 |

La **posible variación entre familias** se registra como señal secundaria, no como causa exclusiva: para cada error se informa cuántos errores de su pareja vienen del mismo componente. Un indicador descriptivo de concentración ≥75 %, con al menos tres errores en la pareja, aparece en 29 de los 90 casos. El umbral sirve para organizar revisión, no es un contraste estadístico ni una regla de adjudicación. Algunas parejas están concentradas en una fuente, pero familia, tema, formato ASR y referencia están confundidos.

Los tres componentes grandes de video suman 105/160 textos (65,6 %) y 55/79 errores (69,6 %). Por ello, muchos errores allí no prueban por sí solos un efecto de fuente. Los errores alcanzan a los diez componentes DEV, incluidos escritos: work-9154… pasa de 3/16 errores del control a 7/16 del candidato. Los componentes con uno o dos textos no permiten inferencias estables sobre rendimiento familiar.

Estas categorías son una **lectura IA única, posterior y expuesta a referencia/predicciones**, no juicios ciegos independientes ni gold experto. “Solapamiento” no equivale al estado administrativo ambiguous: no se comprobaron en nuevas pasadas las condiciones conjuntas para adjudicarlo. “Evidencia débil” tampoco invalida por sí sola la referencia. El ASR defectuoso se registra donde impide reconocer referentes o el argumento; no se normalizó ni reparó el texto.

Se aplicaron [v3.1](../../../docs/beto-v3/guia-etiquetado-v3.1.md) y sus [enmiendas v3.2](../../../docs/beto-v3/guia-etiquetado-v3.2-propuesta.md). Se conservaron literalmente sus encabezados históricos; el contexto de aprobación/revisión de referencia existente prevalece sobre el rótulo antiguo “propuesta”. En particular, G32-2/G32-3 sustituyen la lectura automática de temporalidad en F2. La autorización actual permite ver predicciones para diagnóstico; no se presenta esta lectura como una sesión de anotación ciega bajo el contrato original.

## ¿Pocas fronteras ambiguas o dificultad generalizada?

La lectura más sustentada es **dificultad extendida, con concentración temática y por fuente que merece revisión focalizada**:

1. Más de la mitad de los errores actuales está fuera de las cinco fronteras principales, y todas las clases tienen falsos negativos.
2. Solo ocho de los 38 errores de esas cinco fronteras se describieron principalmente como solapamiento semántico; 15 parecen claros según el objetivo/guía, diez presentan carencia contextual y cinco debilidad de referencia. No son 38 casos homogéneos de ambigüedad.
3. Fuera de esas cinco fronteras quedan otros 24 posibles solapamientos, 14 errores claros y tres referencias débiles. La dificultad de dominancia no está confinada a las parejas seleccionadas.
4. Las modificaciones entre modelos son pequeñas en conjunto: 66 errores persisten y las 11 correcciones se compensan con 13 regresiones.

Como comprobación puramente aritmética, sustituir por la referencia **todos** los 38 errores de las cinco fronteras, sin perder ningún otro acierto, daría macro-F1 0,700912. Este es un **oráculo calculado con las etiquetas conocidas**, no resultado del modelo, intervención aplicada ni cumplimiento de la meta. Requeriría resolver el 100 % de esos errores sin regresiones; no demuestra que una revisión de ambigüedad pueda hacerlo. No se recalculó un supuesto “F1 limpio” eliminando referencias incómodas.

## Evidencia necesaria antes de justificar otro entrenamiento

Primero, recuperar las justificaciones y citas originales ya existentes de las nueve referencias señaladas como débiles y de las fronteras R2/R5/R4, para comprobar si sostienen los requisitos positivos sobre el objetivo. Esa comprobación debe hacerse sin cambiar esta referencia ni usar las predicciones como criterio de corrección.

Después, una revisión IA independiente y ciega de un subconjunto fijado de errores y aciertos comparables, ocultando modelos/resultados y separando principal, alternativa y suficiencia contextual. Debe comprobar citas/offsets y estabilidad de reglas. No se ejecutó aquí; requeriría su propio alcance y presupuesto, y su acuerdo seguiría sin equivaler a corrección histórica experta. No hay experto disponible ni se exige uno para continuar.

Para la hipótesis de fuente, hacen falta contrastes de la misma frontera y clase en más de una familia, con soportes suficientes, y controles de formato/periodo. Antes de crear más datos, puede comprobarse qué cobertura ofrecen los casos existentes; no se ha autorizado adquirir fuentes nuevas. Una prueba de invariancia futura tendría que mantener contenido histórico y referencia, variar un rasgo superficial identificable y registrar predicciones emparejadas; requiere permiso de inferencia, no se ha ejecutado ni se presupone inocua una edición del texto.

Solo si esa evidencia distingue un error de representación/aprendizaje de una referencia incierta, tendría sentido preregistrar una intervención única, comparación y criterio de parada. Una mejora debe evaluarse con referencia y partición congeladas, sin elegir parámetros en V/S ni reutilizar como independiente este DEV expuesto. El entrenamiento no soluciona por sí solo objetivos sin clase única o sin evidencia suficiente.

## Integridad

El script reconstruye métricas desde probabilidades, valida IDs/etiquetas/hashes y comprueba sumas de soporte, FP/FN. Se verificaron sin cambios los dos checkpoints seleccionados, predicciones, referencias, partición, guías y ledger. La referencia archivada compartida incluye otras particiones; solo se seleccionaron textos DEV y no se analizaron filas retrospectivas. Los IDs que empiezan S03/S10 son identificadores de fuente presentes en DEV: no se abrió el split S.

Reproducción: ejecutar scripts/analyze_beto_v32_dev_errors.py con el Python ML. Reutiliza las notas de lectura guardadas; reproduce cálculos y documentos, no convierte una interpretación IA en un juicio independiente. Los hashes y el inventario revisado se conservan en verification.json.
