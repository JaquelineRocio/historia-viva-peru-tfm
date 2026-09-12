# Cierre de tres rondas reales de adquisición

Se completaron las tres rondas autorizadas sin entrenar. La ampliación no cumple el criterio conjunto: no se incorpora ningún dato y TRAIN continúa con 746 filas. No se inicia una cuarta ronda ni se consume el saldo para prolongar la búsqueda.

Se revisaron 73 objetivos activos, se cargaron 74 entradas únicas y se emitieron 146 juicios. Hay 23 propuestas individuales condicionadas al gate global, nunca admitidas automáticamente; los restantes 50 objetivos quedan fuera de propuesta. Una corrección de oración en ronda 1, anterior a las revisiones, conserva y cobra un hash adicional. Saldo 52 desarrollo + 200 S; techo 1478. El incremento +124 ya fue autorizado por la autora antes de adquirir.

| Ronda | Objetivos | Juicios | Acuerdo entre aceptados | κ | Elegibles antes de revisión conceptual |
|---|---:|---:|---:|---:|---:|
| 1 | 20 | 40 | 20/20 | 1.0000 | 4 |
| 2 | 21 | 42 | 19/20 | 0.9396 | 15 |
| 3 | 32 | 64 | 32/32 | 1.0000 | 14 |

Acuerdo agregado 71/72, κ=0.9832; 179 citas literales verificadas. No es corrección histórica ni gold experto. Las sesiones no vieron cuotas, etiquetas buscadas, predicciones BETO ni respuestas ajenas. Se mantienen las cautelas y el unresolved.

| Frontera | Pares válidos | Familias por lado en esos pares | Cumple |
|---|---:|---:|---|
| COL-NR | 2 | 2/2 | SÍ |
| IDE-LID | 4 | 2/2 | SÍ |
| IDE-REP | 3 | 2/3 | SÍ |
| LID-REP | 3 | 2/2 | SÍ |
| MIL-LID | 1 | 1/1 | NO |
| COL-SOC | 2 | 2/2 | SÍ |
| REP-SOC | 3 | 2/3 | SÍ |

Carencias restantes: MIL-LID. La mera presencia de dos familias por clase en el lote no certifica dos réplicas de una frontera. En MIL–LID hay textos militares de Sala y Chassin, pero el contraste estrecho limpio con negociación solo se obtiene en Rospide. Vincular Huaytará con cualquier proyecto político por compartir la palabra guerra no cierra esa carencia.

El aporte conceptual sí existe: resistencia fiscal frente a financiación colonial; agencia comunal frente a estructura de autoridad; justificación jurídica de soberanía frente a negociación o creación ministerial; doctrina centro/local frente a fragmentación electoral efectiva. Hay controles de pertinencia de nuevas familias, cuyo valor no se presenta como un nuevo mecanismo histórico.

Se fusionaron las exposiciones dependientes de las cartas de Sánchez Carrión como una familia argumentativa. Se descartaron paráfrasis de uti possidetis/Confederación ya desarrolladas en TRAIN y pasajes prestados de autores previamente utilizados. La comparación usa vecinos TFIDF y lectura conceptual: baja similitud lexical por sí sola no prueba novedad.

| Asociación clase–fuente | TRAIN actual | Hipótesis con propuestas |
|---|---:|---:|
| nmi | 0.265389 | 0.270703 |
| cramers_v_uncorrected | 0.424752 | 0.442947 |

La hipótesis contiene 769 filas; no se creó ni usó como TRAIN. Ambas asociaciones disminuyen: NO. Las matrices antes/después reales son idénticas. Las cuotas dominantes por clase se detallan a continuación; no sustituyen los dos indicadores globales.

| Clase | Familia dominante TRAIN | Cuota antes | Cuota hipotética |
|---|---|---:|---:|
| contexto_colonial_antecedentes | historical-basadre-hampe | 56.9% | 54.7% |
| crisis_ideas_emancipadoras | historical-ophelan-huamanga | 50.0% | 46.7% |
| campanias_conflictos_militares | historical-basadre-hampe | 72.8% | 72.0% |
| liderazgos_diplomacia_proyectos | historical-basadre-hampe | 54.7% | 52.2% |
| organizacion_consecuencias_republicanas | historical-basadre-hampe | 92.0% | 86.8% |
| participacion_social_regional | historical-ophelan-huamanga | 32.3% | 31.5% |
| no_relevante | video-T6gALo8Ydgk | 21.8% | 21.6% |

Los indicadores dependen de la granularidad de familias y del tamaño desigual; son descriptivos, no una prueba de mejora de generalización. No hubo inferencia ni entrenamiento BETO. V permaneció congelada y no se leyó; S permaneció cerrada. No se exige revisión experta ni se presenta consenso IA como gold.

Fuentes: ronda 1 aporta Sala; Salazar/Pereyra/Santos fueron excluidos al detectar su adquisición previa NF05/NF08/NF09, aunque ya habían consumido revisión. Ronda 2 aporta Andaur, D’Medina, Petit-Breuilh y Chassin. Ronda 3 incorpora Paniagua, De la Haza, el dossier Política Internacional 129 y Rospide. Nueve familias documentales nuevas investigadas, no nueve independencias argumentativas garantizadas para cada frontera. Cada carpeta conserva fuentes, páginas, URLs, hashes, fallos de descarga y procedencia.

En Política Internacional 129 se verificaron índice y portadas: la ficha OJS/17 mezclaba autor/resumen/páginas de Situ Chang con el título de García Caffi. Los fragmentos usados son de Espinoza y García Caffi y cuentan juntos como un solo dossier. No se transfiere la licencia de una ficha equivocada. Las descargas TLS que fallaron en requests se realizaron con la validación predeterminada de Windows, sin desactivarla.

Entregables: [decisiones](decisiones.csv), [propuestas individuales no incorporadas](propuestas-individuales-no-incorporadas.json), [rechazados/unresolved](rechazados-ambiguous-unresolved.json), [pares y motivos](pares-contrastivos.json), [matriz frontera×familia](frontera-familia-final.csv), [TRAIN antes](clase-familia-antes.csv), [TRAIN después real](clase-familia-despues-real.csv), [hipótesis](clase-familia-hipotetica.csv), [dependencia](dependencia-clase-fuente.json), [verificación](verification.json). Cada decisión JSON conserva texto, citas, reglas, respuestas, vecinos TRAIN y observación conceptual.

A. ¿Aporta diversidad conceptual real? **SÍ**, como aportes candidatos, sin afirmar mejora medida de BETO.

B. ¿Cumple 2–3 familias independientes por cada frontera? **NO**.

C. ¿Está justificado incorporar esta ampliación a TRAIN? **NO**.

D. ¿Está justificado realizar un único nuevo entrenamiento? **NO**.

Parada final por tres rondas terminadas. Los C/D negativos de rondas intermedias no detuvieron la adquisición. No se prepara una versión nueva de TRAIN al no superar el gate global.
