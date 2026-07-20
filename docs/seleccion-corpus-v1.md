# Selección operativa del corpus v1

## Regla de inclusión

Una fuente entra al corpus únicamente si está procesada, aporta contenido central de 1780–1842, tiene autor y procedencia identificables, no duplica otra edición y mejora la diversidad temática o de formato. La pantalla **Mis fuentes** mantiene cada recurso como `candidate`, `included` o `excluded`. Solo `included` cuenta para el dataset y la muestra del 20%.

## Corpus incorporado y auditado

Estado al 19 de julio de 2026: **10 fuentes incluidas, 8 PDF y 2 YouTube**, todas procesadas correctamente. En conjunto ofrecen 1,558 segmentos candidatos; todavía no son gold hasta que exista revisión humana.

| Formato | Fuente | Cobertura principal | Clases que refuerza |
|---|---|---|---|
| PDF | Scarlett O'Phelan, [El mito de la independencia concedida](https://repositorio.pucp.edu.pe/items/854db59f-0285-4a87-880f-2f106c681717/full) | Antecedentes e ideas, 1730–1814 | contexto, crisis e ideas |
| PDF | Nelson Pereyra Chávez, [Los campesinos de Huamanga y la rebelión de 1814](https://repositorio.pucp.edu.pe/items/f2c23330-ffb6-453e-94d4-295186c63316) | Participación regional | participación social, conflictos |
| PDF | Juan Fonseca Ariza, [¿Bandoleros o patriotas?](https://repositorio.pucp.edu.pe/items/bff4f320-ad1b-4e9f-9a3a-238ac6a5d5b2) | Guerrillas y sectores populares | participación social, conflictos |
| PDF | Claudia Guarisco, [José de San Martín y el espacio político indígena](https://repositorio.pucp.edu.pe/items/83d3d6fa-7d52-400a-9236-eb25e4275177) | Política indígena, 1821–1822 | participación, liderazgos, organización |
| PDF | Juan Luis Orrego Penagos, [Los primeros años del Perú republicano](https://repositorio.pucp.edu.pe/bitstreams/ee8296f3-0d12-4f7a-9c93-fd7e61a3ce6f/download) | República temprana | organización y consecuencias |
| PDF | Carmen Villanueva, [La Constitución de 1823 y los inicios de la República](https://repositorio.pucp.edu.pe/bitstreams/77801ebd-c0bf-4d70-8f78-83f9293e3722/download) | Instituciones | organización republicana |
| PDF | Susy Sánchez Rodríguez, [1821: La celebración de la Independencia del Perú en Santiago de Chile](https://repositorio.pucp.edu.pe/items/755e082d-f569-4358-b615-b1c93e75bd4e) | Dimensión internacional | diplomacia y liderazgos |
| PDF | Jorge Basadre, *Historia de la República del Perú*, tomo inicial | Primera República, 1822–1842 | organización, liderazgos, conflictos |
| YouTube | Facultad de Ciencias Sociales PUCP, [Mesa 1: Historiografía y política en la independencia del Perú](https://www.youtube.com/watch?v=gZpo1PjY0ao) | Historiografía y proyectos políticos | contexto, ideas, liderazgos |
| YouTube | Historia PUCP, [La rebelión olvidada de Huánuco 1812](https://www.youtube.com/watch?v=N9z7pVEZSU8) | Rebelión regional y participación | contexto, participación, conflictos |

El tomo de Jorge Basadre fue reprocesado con el pipeline actual. Aunque ofrece 987 candidatos, podrá aportar **como máximo 150 segmentos gold**, distribuidos por capítulo, para evitar que una sola obra domine el conjunto.

## Validaciones realizadas

- PDF auténtico, no cifrado, menor de 50 MB y 500 páginas.
- Texto seleccionable comprobado antes de subir.
- Duplicados controlados mediante checksum o URL.
- Muestras inicial, central y final revisadas después de segmentar.
- Videos institucionales menores de dos horas.
- Subtítulos españoles con timestamps disponibles en ambos videos.
- Ventanas sin solape y descarte de aperturas musicales sin discurso suficiente.
- Autor, procedencia, estilo y declaración de uso registrados.

## Siguiente corte académico

- La campaña primaria `Corpus gold v1 — 1780–1842` quedó congelada con 700 candidatos, semilla 42 y las 10 fuentes representadas.
- Basadre aporta 129 candidatos en esta campaña; ninguna fuente supera 150.
- Etiquetar los candidatos y reponer mediante una campaña posterior los casos ambiguos o excluidos hasta alcanzar 700–900 segmentos gold.
- Completar al menos 100 ejemplos por clase.
- Etiquetar primero casos claros y reservar bibliografías, música, saludos y paratextos para `no_relevante`.
- Crear la campaña secundaria solo después de completar la primera revisión.
- Revisar una muestra estratificada del 20% y calcular Cohen's Kappa antes de congelar el snapshot.
- Mantener cada fuente exclusivamente en train, validation o test.
