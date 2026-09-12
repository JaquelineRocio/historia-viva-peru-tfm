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
