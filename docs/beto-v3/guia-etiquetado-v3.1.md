# Guía operativa de anotación BETO v3.1

Versión: **3.1**, 2026-09-10. Identidad de versión de este documento: **v3.1**, y ninguna otra.
Documento en vigor para la revisión de fronteras post-G. No reemplaza ni modifica ninguna otra guía
en disco: `guia-etiquetado-v3.md` (v3) y su propia base v2 conservan sus bytes y sus hashes.

Este archivo está compuesto por tres capas, en orden creciente de precedencia:

1. **Base heredada**, reproducida literalmente más abajo. Conserva su encabezado histórico
   «Guía operativa de anotación BETO v2 / Versión: 2.0» porque sus bytes no pueden tocarse sin
   invalidar los hashes anclados a ella. Ese encabezado interno es una cita, **no** la versión de
   este documento.
2. **Aplicación V3**, que prevalece sobre la base heredada.
3. **Anexo de fronteras V3.1**, que prevalece sobre ambas en caso de conflicto.

## Contrato de entrada de la revisión V3.1 (prevalece sobre toda mención anterior de contexto)

La entrada de cada ítem es **únicamente el texto objetivo** normalizado: exactamente el mismo que
recibieron las pasadas originales. No se entrega contexto adyacente, no se genera contexto nuevo y
no se consulta ninguna otra fuente, corpus ni predicción. Esta restricción existe para que el
acuerdo medido aquí sea comparable con el acuerdo ya registrado en V3; añadir contexto lo haría
incomparable.

En consecuencia, y sólo dentro de esta revisión, donde la base heredada dice «leer objetivo y
contexto adyacente» debe leerse «leer el texto objetivo», y donde R0 dice «si el texto/contexto no
resuelve la prioridad» debe leerse «si el texto objetivo no resuelve la prioridad». Ninguna regla
puede exigir información que la entrada no contiene: la ausencia de contexto no es por sí misma
motivo de `ambiguous` ni de `pending_extraction`.

---

# Guía operativa de anotación BETO v2

Versión: 2.0, 2026-09-08. Congelar el hash antes de las pasadas. Material de desarrollo exclusivamente. Etiquetas asistidas por IA, nunca gold experto.

Unidad: párrafo o conjunto de oraciones completas. Leer objetivo y contexto adyacente; etiquetar el objetivo, sin trasladarle automáticamente el tema del contexto. No reescribir el contenido. El alcance es la independencia peruana, sus antecedentes y primera república, aproximadamente 1780–1842; antecedentes anteriores son admisibles cuando el pasaje desarrolla su relación causal con ese proceso. La fecha de publicación, la fecha de una cita y la fecha del hecho histórico son cosas distintas.

## Siete clases y reglas

- `contexto_colonial_antecedentes` (R1): estructuras, relaciones, administración y condiciones coloniales que explican el proceso. Una descripción del orden colonial no se convierte en ideas emancipadoras por mencionar una rebelión.
- `crisis_ideas_emancipadoras` (R2): crisis de legitimidad, soberanía, difusión y apropiación de ideas emancipadoras, constitucionalismo como impugnación del orden imperial. Exigir desarrollo de ideas o crisis, no una fecha o un nombre aislado.
- `campanias_conflictos_militares` (R3): operaciones, logística, batallas, bloqueos, represión y desarrollo armado. Una negociación incidental dentro de una campaña sigue aquí si explica la operación militar; si el argumento principal es el acuerdo político, aplicar R4.
- `liderazgos_diplomacia_proyectos` (R4): estrategias de conducción política, diplomacia, pactos y proyectos de soberanía o régimen aún disputados. Un líder nombrado no basta. Proponer monarquía o federación corresponde aquí cuando domina el diseño/disputa del proyecto.
- `organizacion_consecuencias_republicanas` (R5): funcionamiento, implantación y consecuencias de instituciones, ciudadanía, educación, economía, constituciones y rituales estatales de la república. Distinguir ejecución y efectos de un orden establecido de propuestas políticas en competencia (R4).
- `participacion_social_regional` (R6): acción, intereses, experiencias y agencia de grupos sociales o territoriales: indígenas, afrodescendientes, mujeres, campesinos, plebe, élites como grupo, comunidades. Una batalla puede ser contexto; si el argumento explica quién participa, sus motivos o desigualdades, prima R6. Para descripción estructural colonial sin agencia o experiencia desarrollada, R1; para normas republicanas como objeto principal, R5.
- `no_relevante` (R7): contenido sin desarrollo histórico pertinente: paratexto, método general, otro periodo sin nexo desarrollado, o metahistoriografía centrada exclusivamente en publicaciones, autores y debates académicos. Una discusión historiográfica que sí desarrolla una explicación sustantiva de la independencia recibe su clase histórica; no clasificar por la fecha de publicación citada.

## Dominancia y ambigüedad

R0: formular en una oración qué explica el pasaje y localizar evidencia literal. Pesar el argumento desarrollado y sus conclusiones, no contar palabras clave. Si dos temas están conectados, elegir el que organiza la explicación y registrar el otro como alternativa. Si los dos son igualmente centrales y el texto/contexto no resuelve la prioridad, estado `ambiguous`; no inventar una octava clase ni usar `no_relevante` como descarte. Un error de extracción que impide decidir produce `pending_extraction`, no una etiqueta negativa.

## Registro y aceptación

Cada pasada conserva ID, familia, etiqueta propuesta, alternativa (o null), regla, explicación, evidencia literal y offsets sobre el objetivo, ambigüedad, modelo y versión del prompt. La entrada congelada contiene texto y contexto sin etiquetas ni inferencias BETO. Pasadas aisladas del mismo modelo miden consistencia entre sesiones, no independencia entre modelos. La versión exacta de pesos del proveedor no es observable; declararla desconocida.

Adjudicar desacuerdos con guía, texto y evidencia, nunca sólo confianza. También comprobar evidencia y fronteras en acuerdos. Un acuerdo no equivale a verdad experta. Mantener pendientes sin resolver. No asignar split ni habilitar entrenamiento. Cache por SHA256 canónico de texto, contexto, guía y configuración de la pasada; cambiar cualquiera invalida la entrada. Separar cachés de ambas pasadas.


## Aplicación V3 (prevalece sobre las instrucciones de flujo V2)

Se conservan R0–R7, las siete categorías y el alcance 1780–1842. No hay cambio de tarea.
En V3 se permite asignar fuentes a T/V/S y entrenar únicamente tras congelar datos y referencias.
La entrada inicial es únicamente el objetivo auténtico normalizado; no se añade contexto generado
ni contexto invisible para BETO. Máximo 384 tokens con especiales, truncamiento registrado.
Una mención constitucional no decide R2/R5: distinguir ruptura de legitimidad y funcionamiento
institucional. Un nombre no decide R4. Distinguir proyecto disputado R4 de implantación R5;
agencia social R6 de desarrollo militar R3 o norma como objeto R5. La fecha aislada no decide R7.
Cada pasada conserva entrada exacta, hash, evidencia, regla, alternativa y banderas.
En V/S se revisan todas las referencias antes de predicciones; en T todos los ambiguos y un 20%
aleatorio de aceptados. Si las sesiones usan el mismo modelo, declarar su dependencia.
Los casos sin referencia única quedan en el inventario y fuera del F1, con cobertura publicada.
Las referencias asistidas por IA no son gold experto. No se usa no_relevante para incertidumbre.


## Anexo de fronteras V3.1 — capa 3 de `guia-etiquetado-v3.1.md`

(prevalece sobre las secciones anteriores sólo en caso de conflicto)

Estado en el momento del congelado: **propuesta congelada**, redactada antes de abrir una sola fila. El registro y el congelado de este anexo no modifican por sí mismos ninguna etiqueta: sólo una adjudicación posterior, versionada fila por fila y sin sobrescribir la referencia original, puede hacerlo.

Se conservan R0–R7, las siete clases, su significado histórico y el alcance 1780–1842. **No hay cambio de tarea.** Este anexo no redefine ninguna clase ni crea estados nuevos: sigue habiendo etiqueta, `ambiguous` y `pending_extraction`. Las reglas que siguen **operacionalizan** distinciones que la guía ya enuncia; no sustituyen R0, lo aplican.

Motivo: las reglas existentes están formuladas como distinciones abstractas y la evidencia muestra que no discriminan en la práctica. Tres pares, además, no tienen ninguna regla de par y son justamente donde las dos pasadas de anotación discrepan. Ninguna regla de este anexo se ha elegido para subir el F1 de BETO; los criterios se derivan del objeto histórico de cada clase tal como la guía ya lo define.

### Prueba común a todas las fronteras

Aplicar R0 primero: formular en una sola oración qué explica el pasaje y localizar la evidencia literal. Sobre esa oración, y sólo sobre ella, aplicar en orden:

1. **Agente**: ¿quién es el sujeto de la explicación? Una estructura, una institución, una persona o un grupo social.
2. **Acción**: ¿qué hace ese sujeto? Impugnar, proponer, ejecutar, combatir, participar.
3. **Temporalidad**: ¿el objeto está en disputa, en instalación o ya en funcionamiento?
4. **Consecuencia**: ¿sobre qué concluye el pasaje? La conclusión pesa más que el escenario.

Un sustantivo, un nombre propio, una fecha o una cita constitucional **nunca deciden por sí solos**. Esto ya lo exige la guía: *«Pesar el argumento desarrollado y sus conclusiones, no contar palabras clave»*, *«Un nombre no decide R4»*, *«Una mención constitucional no decide R2/R5»*, *«La fecha aislada no decide R7»*.

### Fragmentos multitemáticos: regla única

Si el pasaje desarrolla dos temas conectados, elegir el que **organiza la explicación** y registrar el otro en `alternative`. La guía ya lo dice; este anexo añade el criterio de qué significa «organiza»: es el tema del que depende la conclusión. Si se suprimiera ese tema, el pasaje dejaría de sostener lo que sostiene; si se suprimiera el otro, seguiría en pie.

### Cuándo declarar `ambiguous`: regla única

Declarar `ambiguous` sólo cuando se cumplan las tres condiciones a la vez: (a) los dos temas tienen desarrollo comparable, no una mención frente a un argumento; (b) la prueba de agente/acción/temporalidad/consecuencia da resultados contradictorios entre sí; y (c) el texto del objetivo, que es la única entrada disponible, no resuelve la prioridad. La condición (c) se juzga sobre el objetivo y nada más: no se apela a contexto adyacente, porque la revisión no lo entrega, y la falta de contexto no cuenta como prueba de que el objetivo no resuelve la prioridad. No usar `ambiguous` por desconocimiento del anotador ni por dificultad de lectura, y **nunca** usar `no_relevante` como descarte. Un defecto de extracción que impide decidir produce `pending_extraction`, no una etiqueta.

---

### F1. `contexto_colonial_antecedentes` (R1) ↔ `organizacion_consecuencias_republicanas` (R5)

**Fuente**: guía v3, bullet R6 — *«Para descripción estructural colonial sin agencia o experiencia desarrollada, R1; para normas republicanas como objeto principal, R5»*; bullets R1 y R5. Origen del par: confusión del modelo (matriz de R2/42).

**Objeto principal.** R1 explica el orden colonial en tanto condición del proceso. R5 explica el funcionamiento y los efectos de la república ya instalada.

**Indicadores positivos.** R1: administración virreinal, tributo, corregimientos, reformas borbónicas, estructura estamental, rebeliones anteriores en tanto antecedente. R5: constituciones en vigor, congresos reunidos, ciudadanía ejercida, fiscalidad republicana, educación e instituciones del nuevo Estado.

**Exclusiones.** R1 excluye el pasaje cuya conclusión es un efecto republicano explícito, aunque el escenario sea colonial. R5 excluye el antecedente colonial que el pasaje no conecta con una consecuencia republicana desarrollada.

**Prueba.** Agente: institución del régimen virreinal → R1; institución republicana → R5. Temporalidad: **ésta decide este par.** Si el estado de cosas descrito es anterior a la instalación republicana y el argumento se detiene ahí, R1. Consecuencia: si el pasaje traza continuidad colonial → republicana y concluye sobre cómo funcionó la república, R5; si concluye sobre por qué se llegó a la ruptura, R1.

**Multitemático.** Institución colonial y su sucesora republicana en el mismo pasaje: decide de cuál depende la conclusión. La otra va en `alternative`.

**Desempate.** Prevalece la temporalidad del objeto cuya continuidad o ruptura se argumenta, no la del primer sustantivo que aparece.

**`ambiguous`.** Sólo si el pasaje sostiene con desarrollo equivalente que la institución colonial explica el proceso y que la republicana lo implementa, sin jerarquía textual.

**Ejemplos abstractos** (sintéticos, redactados para este anexo; no proceden de V ni de S):
- *«Un texto describe un mecanismo fiscal del régimen virreinal y concluye que esa carga explica el descontento previo a la ruptura.»* → R1.
- *«Un texto describe el mismo mecanismo fiscal y concluye que la república lo conservó y que eso condicionó sus primeras cuentas.»* → R5, `alternative` R1.

---

### F2. `crisis_ideas_emancipadoras` (R2) ↔ `organizacion_consecuencias_republicanas` (R5)

**Fuente**: guía v3, Aplicación V3 — *«Una mención constitucional no decide R2/R5: distinguir ruptura de legitimidad y funcionamiento institucional»*; bullet R5 — *«Distinguir ejecución y efectos de un orden establecido de propuestas políticas en competencia»*. Origen del par: confusión del modelo; 15 errores R2→R5 en R2/42, el par de confusión más grande.

**Objeto principal.** R2 explica la impugnación o fundación de legitimidad. R5 explica el funcionamiento de un orden ya establecido.

**Indicadores positivos.** R2: crisis de la monarquía, juntas, soberanía en disputa, difusión y apropiación de ideas, constitucionalismo **como impugnación** del orden imperial. R5: instituciones en ejercicio, aplicación de normas, efectos administrativos, rituales estatales.

**Exclusiones.** R2 excluye la descripción de una institución que ya opera sin discusión de su legitimidad. R5 excluye el debate sobre crear o legitimar una institución que todavía no actúa.

**Prueba.** Agente: quien impugna o funda legitimidad → R2; la institución que opera → R5. Acción: impugnar, proclamar, debatir, difundir → R2; aplicar, recaudar, legislar en vigor, administrar → R5. Temporalidad: **ésta decide este par.** Mientras el orden está en disputa, R2; una vez instalado y en ejercicio, R5. Consecuencia: si concluye sobre la legitimidad del orden, R2; si concluye sobre el efecto de su funcionamiento, R5.

**Regla del texto constitucional** (la trampa documentada): una constitución invocada como argumento de ruptura o de fundación de soberanía es R2; la misma constitución tratada por cómo se aplicó, a quién alcanzó o qué produjo es R5. La palabra no decide; decide el uso argumentativo.

**Multitemático.** Un debate constituyente que además describe el órgano que lo alberga: si la conclusión es sobre la disputa, R2; si es sobre el funcionamiento del órgano, R5.

**Desempate.** Prevalece la disputa sobre el funcionamiento cuando el pasaje mantiene abierta la cuestión de quién tiene derecho a mandar.

**`ambiguous`.** Sólo si el pasaje desarrolla por igual la impugnación y la operación, y la conclusión no se apoya en ninguna de las dos por encima de la otra.

**Ejemplos abstractos** (sintéticos):
- *«Un texto discute si una asamblea tenía derecho a asumir la soberanía y concluye que esa pretensión rompió el vínculo con la metrópoli.»* → R2.
- *«Un texto describe cómo esa misma asamblea organizó el cobro de un impuesto y qué efectos tuvo en una provincia.»* → R5.

---

### F3. `liderazgos_diplomacia_proyectos` (R4) ↔ `organizacion_consecuencias_republicanas` (R5)

**Fuente**: guía v3, Aplicación V3 — *«Un nombre no decide R4. Distinguir proyecto disputado R4 de implantación R5»*; bullet R5 — *«Distinguir ejecución y efectos de un orden establecido de propuestas políticas en competencia (R4)»*. Origen del par: confusión del modelo; además, R4 es la clase con menor acuerdo entre pasadas (κ 0,6695).

**Objeto principal.** R4 explica la conducción política y los proyectos de régimen **aún disputados**. R5 explica el régimen ya implantado y sus efectos.

**Indicadores positivos.** R4: estrategias de conducción, correspondencia, negociación, pactos, protectorados, monarquismo, republicanismo y diseño de Estado en competencia. R5: la institución funcionando, su alcance, su financiación, sus consecuencias.

**Exclusiones.** R4 excluye la mera aparición de un nombre propio y el pasaje cuya conclusión es sobre cómo operó una institución. R5 excluye la propuesta que todavía compite con otras.

**Prueba.** Agente: **ésta decide este par.** Si el sujeto de la explicación es una persona, o un proyecto atribuido a personas, R4; si es una institución actuando como tal, R5. Acción: proponer, negociar, disputar, diseñar → R4; ejecutar, implantar, sostener → R5. Temporalidad: mientras el proyecto compite, R4; una vez implantado, R5. Consecuencia: si concluye sobre la conducción o el diseño, R4; si concluye sobre los efectos del régimen operante, R5.

**Caso duro** (el que más se confunde): un líder que preside o funda una institución. Preguntar de qué depende la conclusión: si de la actuación de la persona, R4; si del funcionamiento del órgano, R5. El cargo no traslada la clase.

**Multitemático.** Proyecto y su implantación en el mismo pasaje: si el texto argumenta que el proyecto se impuso frente a otros, R4; si argumenta qué pasó una vez impuesto, R5.

**Desempate.** Prevalece R4 mientras el pasaje mantenga vivo el carácter disputado del proyecto; en cuanto la disputa se da por cerrada y el argumento pasa a los efectos, R5.

**`ambiguous`.** Sólo si el pasaje desarrolla con igual peso la disputa del proyecto y el funcionamiento de lo implantado, y la conclusión abarca ambos.

**Ejemplos abstractos** (sintéticos):
- *«Un texto expone las diferencias entre dos proyectos de organización del Estado y concluye que una de las dos concepciones se impuso en el debate.»* → R4.
- *«Un texto describe cómo quedó organizado el poder ejecutivo resultante y qué inestabilidad produjo en la década siguiente.»* → R5, `alternative` R4.

---

### F4. `participacion_social_regional` (R6) ↔ `campanias_conflictos_militares` (R3)

**Fuente**: guía v3, bullet R6 — *«Una batalla puede ser contexto; si el argumento explica quién participa, sus motivos o desigualdades, prima R6»*; Aplicación V3 — *«agencia social R6 de desarrollo militar R3»*. Origen del par: confusión del modelo; 10 errores R6→R3 en R2/42.

**Objeto principal.** R3 explica la operación armada. R6 explica la agencia de un grupo social o territorial.

**Indicadores positivos.** R3: expediciones, logística, batallas, bloqueos, represión, desarrollo armado. R6: acción, intereses, experiencias y desigualdades de indígenas, afrodescendientes, mujeres, campesinos, plebe, élites como grupo, comunidades.

**Exclusiones.** R3 excluye el pasaje cuyo argumento es quiénes participaron y por qué, aunque el escenario sea una batalla. R6 excluye la mención incidental de un grupo dentro de una operación cuyo foco es militar.

**Prueba.** Agente: **ésta decide este par.** Si el sujeto es una unidad militar o un mando, R3; si es un grupo social o territorial, R6. Acción: desplazar, sitiar, combatir, abastecer → R3; participar, resistir, negociar intereses, sufrir desigualdad → R6. Consecuencia: si concluye sobre el desenlace militar, R3; si concluye sobre quién participó, con qué motivos o con qué desigualdad, R6.

**Multitemático.** Un grupo dentro de una campaña: si el texto explica la campaña usando al grupo como componente, R3; si explica al grupo usando la campaña como escenario, R6.

**Desempate.** Prevalece R6 cuando el pasaje atribuye motivos, intereses o experiencia propia al grupo; prevalece R3 cuando el grupo aparece sólo como recurso o efectivo de la operación.

**`ambiguous`.** Sólo si el pasaje desarrolla con igual peso el curso de la operación y la agencia del grupo, y la conclusión no se apoya más en una que en otra.

**Ejemplos abstractos** (sintéticos):
- *«Un texto narra el avance de una columna, su abastecimiento y el resultado del encuentro.»* → R3.
- *«Un texto explica por qué una comunidad apoyó a un bando, qué esperaba obtener y qué perdió, situándolo durante ese mismo encuentro.»* → R6, `alternative` R3.

---

### F5. Fronteras sin regla de par: el eje de `participacion_social_regional` y `crisis` ↔ `liderazgos`

**Fuente**: evidencia de la auditoría post-G. Estos tres pares concentran el desacuerdo real entre las dos pasadas en V (participación↔no_relevante 6, participación↔crisis 5, crisis↔liderazgos 4) y son los únicos para los que la guía en vigor **no** enuncia regla de par. Origen: desacuerdo entre pasadas, no confusión del modelo. Se añaden porque revisar sólo las fronteras donde el modelo falla dejaría intacta la ambigüedad que la referencia sí tiene.

#### F5.a `participacion_social_regional` (R6) ↔ `no_relevante` (R7)

**Objeto principal.** R7 es ausencia de desarrollo histórico pertinente. No es una clase de descarte ni un depósito de incertidumbre: la guía lo prohíbe expresamente.

**Regla.** Asignar R7 sólo cuando **ninguna** de R1–R6 tiene un argumento desarrollado en el pasaje. Nombrar un grupo social no convierte el pasaje en R6; pero un pasaje que desarrolla un argumento histórico de otra clase tampoco es R7 por no desarrollar agencia. Orden de decisión: (1) ¿hay argumento histórico desarrollado? Si no, R7. (2) Si lo hay, ¿el sujeto de ese argumento es un grupo social o territorial y el texto le atribuye acción, interés, experiencia o desigualdad? Si sí, R6; si no, la clase que corresponda al argumento.

**`ambiguous`.** No aplica entre R6 y R7: si hay duda sobre si existe desarrollo histórico, la duda se resuelve leyendo el objetivo completo, no marcando `ambiguous`. Si el obstáculo es la extracción, `pending_extraction`.

**Ejemplo abstracto** (sintético): *«Un pasaje menciona de paso a un grupo y dedica el resto a agradecer a una institución patrocinadora.»* → R7. *«Un pasaje menciona de paso a un grupo y desarrolla por qué una región se mantuvo al margen del conflicto.»* → R6.

#### F5.b `participacion_social_regional` (R6) ↔ `crisis_ideas_emancipadoras` (R2)

**Objeto principal.** R2 explica las ideas y la crisis de legitimidad; R6 explica la agencia de un grupo.

**Regla.** Si el argumento desarrolla el contenido, la circulación o la apropiación de las ideas **como tales**, R2. Si desarrolla qué hizo un grupo con ellas, qué esperaba o qué posición tomó, R6. Recepción no es lo mismo que agencia: un grupo descrito como destinatario de un discurso sigue siendo R2 si el pasaje explica el discurso; pasa a R6 cuando el pasaje explica al grupo.

**Desempate.** Prevalece R6 cuando el sujeto gramatical y lógico de la conclusión es el grupo.

**Ejemplo abstracto** (sintético): *«Un pasaje explica cómo una idea de soberanía se difundió por la prensa.»* → R2. *«Un pasaje explica que un sector urbano adoptó esa idea para reclamar un lugar propio en el nuevo orden.»* → R6, `alternative` R2.

#### F5.c `crisis_ideas_emancipadoras` (R2) ↔ `liderazgos_diplomacia_proyectos` (R4)

**Objeto principal.** R2 explica la idea o la crisis; R4 explica la conducción y los proyectos atribuidos a personas.

**Regla.** Si el argumento desarrolla la idea, su contenido o la crisis de legitimidad, R2, aunque cite a quien la formuló: la guía ya exige *«desarrollo de ideas o crisis, no una fecha o un nombre aislado»* y *«Un líder nombrado no basta»*. Si el argumento desarrolla quién propuso qué, frente a quién y con qué estrategia, R4.

**Desempate.** Prevalece R4 cuando la explicación depende de la competencia entre proyectos concretos; prevalece R2 cuando depende del contenido de la idea o del estado de la legitimidad.

**Ejemplo abstracto** (sintético): *«Un pasaje expone en qué consistía una doctrina de soberanía popular y por qué erosionaba el orden imperial.»* → R2. *«Un pasaje expone que dos conductores defendían formas de gobierno distintas y cómo negociaron entre sí.»* → R4.

---

### Lo que este anexo no hace

No redefine ninguna de las siete clases ni altera su significado histórico. No introduce estados nuevos. No modifica ninguna etiqueta existente. No se ha ajustado a la matriz de confusión de BETO: las reglas se derivan del objeto de cada clase tal como la guía ya lo define, y los pares de F5 se añaden precisamente porque el modelo **no** los confunde, mientras que las pasadas sí discrepan en ellos. No se aplica a S. Las referencias siguen siendo asistidas por IA y no son gold experto.
