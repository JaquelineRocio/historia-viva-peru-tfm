# Guía de etiquetado histórico (1780–1842)

## Unidad y regla de decisión

La unidad es un segmento de 120–250 palabras (PDF) o 45–90 segundos (YouTube). Se etiqueta por la idea histórica dominante, no por una palabra aislada. Años, personas y lugares se corrigen como entidades separadas. Si dos temas tienen el mismo peso y no puede decidirse con el contexto inmediato, se marca `ambiguo`. Portadas, índices, créditos, bibliografías y texto ajeno al periodo se marcan `no_relevante`.

## Clases

### `contexto_colonial_antecedentes`

- Incluye: orden virreinal, reformas borbónicas, economía y sociedad colonial, rebeliones anteriores que explican el proceso.
- Excluye: difusión central de ideas emancipadoras y campañas militares de independencia.
- Ejemplo: descripción del sistema de tributos y sus tensiones antes de 1808.

### `crisis_ideas_emancipadoras`

- Incluye: crisis de la monarquía, juntas, liberalismo, Constitución de Cádiz, prensa e ideas independentistas.
- Excluye: biografías de líderes sin discusión ideológica y operaciones militares.
- Ejemplo: efectos políticos de la invasión napoleónica en el virreinato.

### `participacion_social_regional`

- Incluye: participación indígena, afroperuana, campesina, popular, femenina y dinámicas regionales.
- Excluye: menciones incidentales a un grupo dentro de una batalla cuyo foco sea táctico.
- Ejemplo: posición de comunidades locales ante realistas y patriotas.

### `campanias_conflictos_militares`

- Incluye: expediciones, batallas, ejércitos, estrategia, logística, guerrillas y capitulaciones militares.
- Excluye: negociación diplomática o proyecto político como idea central.
- Ejemplo: desarrollo y consecuencias inmediatas de Ayacucho.

### `liderazgos_diplomacia_proyectos`

- Incluye: actuación de líderes, correspondencia, diplomacia, protectorados, monarquismo, republicanismo y proyectos de Estado.
- Excluye: mera aparición del nombre de un personaje.
- Ejemplo: diferencias entre los proyectos políticos de San Martín y Bolívar.

### `organizacion_consecuencias_republicanas`

- Incluye: constituciones, congresos, ciudadanía, caudillismo, fiscalidad, fronteras y organización de la República hasta 1842.
- Excluye: antecedentes coloniales sin consecuencia republicana explícita.
- Ejemplo: inestabilidad institucional y presidencias tempranas.

### `no_relevante`

- Incluye: paratextos, publicidad, referencias, ruido de extracción, contenido fuera de alcance o sin valor temático.
- Excluye: fragmentos breves pero históricamente interpretables.

## Procedimiento de calidad

1. Primera revisión humana completa, sin convertir predicciones en gold automáticamente.
2. Segunda revisión estratificada del 20%, conservando la decisión independiente.
3. Calcular Cohen’s Kappa global y por clase; objetivo mínimo 0.70.
4. Resolver desacuerdos y registrar la decisión y el motivo.
5. Congelar el snapshot; las correcciones posteriores pertenecen a otra versión.

## Aplicación real en la versión v1

El protocolo anterior representa el procedimiento objetivo. En el experimento
entregado, la revisión de contraste fue asistida por IA porque no se contó con un
segundo historiador independiente. El acuerdo obtenido fue Cohen’s Kappa 0.651,
por debajo del objetivo 0.70. Esta limitación se informa explícitamente y no se
presentan las predicciones automáticas como anotación humana independiente.
