"""Actual first-pass Codex reading decisions, 2026-09-09 UTC.

Each line is unit number | exact new start near the old boundary | proposed
class | alternative | flags (A ambiguity, E extraction) | literal evidence |
brief guide rationale. These are not keyword-generated labels or model calls.
"""
LABELS={'C':'contexto_colonial_antecedentes','I':'crisis_ideas_emancipadoras',
        'M':'campanias_conflictos_militares','L':'liderazgos_diplomacia_proyectos',
        'O':'organizacion_consecuencias_republicanas','S':'participacion_social_regional','N':'no_relevante'}
RULES={'C':'R1','I':'R2','M':'R3','L':'R4','O':'R5','S':'R6','N':'R7'}

LONG={
'0Dgk3uh0ziE':r'''
1|^|N|-|E|presentación de libros|Presentación editorial y biográfica; nombres y cierre biográfico deteriorados por ASR.
2|reconocidos tres huecos|N|-|E|profesor principal|Continúa la presentación de comentaristas; ASR impide reconstruir con seguridad los nombres, que se conservan.
3|buenas noches a todos y todas|N|S|-|está organizado en tres partes|Describe estructura y enfoque del libro; aún no desarrolla una explicación histórica concreta.
4|el autor también encuentra|O|L|A|el tema de la educación|Discute asuntos institucionales pensados al origen republicano; frontera entre diseño y funcionamiento sin resolución única.
5|también me parece que el autor logra demostrar|S|C|-|los criollos van a plantear|Explica reivindicación del poder por la élite criolla y su desplazamiento borbónico.
6|entonces ellos ya tenían un reclamo previo|S|L|-|quitarles ese derecho|Explica intereses del grupo criollo frente a los libertadores, con continuidad desde la independencia.
7|los criollos liberales de acuerdo|S|L|-|ellos son el grupo educado|Representación de grupos sociales y justificación del predominio criollo.
8|me parece que lo interesante del trabajo|L|N|-|contra el protectorado de san martín|La descripción metodológica da paso al conflicto político concreto contra el proyecto monárquico.
9|un libro de debate|S|L|-|los indios fueron incorporados a la nación|Explica inclusión discursiva de indígenas y relaciones con otros actores.
10|así el liberalismo indigenista sostiene|S|O|-|participación activa de los indígenas|Predominan inclusión y participación indígena, no la mecánica electoral.
11|otro tema que me parece también bien importante|O|S|-|símbolos emblemáticos|Construcción republicana de símbolos mediante referentes andinos.
12|también otro tema relevante|N|O|-|la década los sesentas del siglo 19|Ejemplo institucional posterior al alcance y cierre editorial, sin desarrollar implantación temprana.
13|muy bien buenas noches a todos|N|-|-|investigar más sobre la independencia|Agradecimientos y llamado contemporáneo a investigar, no contenido histórico sustantivo.
14|segundo entonces voy|N|-|-|la capacidad de editar|Evalúa escritura, revisión editorial y agenda historiográfica del libro.
15|entonces lo que voy a hacer aquí|S|L|-|los padres de la patria no imaginaron|Discute inclusión y exclusión indígena en la concepción de nación durante la independencia.
16|en un brillante trabajo biblioteca|S|L|-|indígenas de comienzos de siglo|Desarrolla la consideración de indígenas como sujetos políticos en el período estudiado.
17|ahora mi duda|S|L|-|incorporando los indígenas|Expone proyectos de educación e integración indígena, con observaciones críticas.
18|pero la pregunta entonces sería|N|S|A|retórica política cortoplacista|Discusión sobre valor probatorio del discurso; frontera con análisis de inclusión indígena.
19|eso nos lleva a la pregunta|O|S|A|movimientos de abolición de esclavitud|Pregunta por aplicación y debilidad del liberalismo abolicionista; cronología 1830–1850 parcialmente fuera del alcance.
20|bueno entonces un comentario|S|I|-|se limitó a la ciudad|Contrasta alcance social y regional del liberalismo y poder rural.
21|más bien yo tengo la duda|I|S|A|las ideas liberales que venían de arequipa|Circulación regional de ideas; el fragmento no determina bien qué tramo del siglo XIX trata.
22|entonces este libro da pautas|O|S|-|la creación de una república muy jerárquica|Explica reproducción de jerarquías y desigualdades tras la colonia.
23|bueno voy a empezar agradeciendo|N|-|-|agradecer a todos ustedes|Agradecimientos del autor y anuncio de la intervención.
24|bueno quiero decir sobre este libro dos cosas|N|-|-|una tesis de maestría|Historia de elaboración de la tesis y publicación.
25|yo he hecho mis estudios doctorales|N|-|-|gracias raúl por estar aquí|Trayectoria académica y agradecimientos personales.
26|bueno ahora diré|N|L|-|los historiadores le exigían|Explica una decisión metodológica frente a otras interpretaciones.
27|y esa digamos|N|L|-|fue el hilo conductor de este libro|Describe método y anuncia programa político sin exponer aún sus elementos.
28|primero lo que lo que se mencionó|S|L|-|tenían un lugar como ciudadanos|Explica incorporación indígena a la nación liberal.
29|en segundo lugar en él|I|N|A|los periódicos de los años de la independencia|Discute origen de una interpretación política contemporánea al proceso; frontera con metahistoriografía.
30|bueno como ven|N|L|-|la mejor manera de acabar|Comentario editorial y analogía sobre utopías; el ejemplo histórico concreto viene después.
31|para poner un ejemplo cuando se da|O|S|-|la libertad de vientres|Aplicación frustrada de la ley de 1821 por resistencia conservadora, con desenlace posterior conectado.
32|y eso en segundo lugar|S|N|A|no tiene bases materiales|Explica bases sociales del liberalismo del siglo XIX; período concreto insuficientemente delimitado.
33|luego el liberalismo y las ciudades|N|S|-|la segunda mitad del siglo 19|Revuelta de Bustamante explícitamente posterior a 1842 y comentario sobre investigación rural.
34|agradecerles nuevamente por estar aquí|N|-|-|están todos invitados|Despedida y convocatoria a conversar fuera de la presentación.
''',
'bVrm2pJw4SA':r'''
1|^|N|-|-|debido a la pandemia|Introducción contemporánea sobre producción del programa.
2|en septiembre de 1820|M|N|AE|desembarcó la expedición libertadora|Mezcla anuncio del desembarco y visita biográfica; el audio subtitulado corta la frase sobre la calle.
3|debido a la pandemia el bicentenario|N|-|-|8 de septiembre de 1920|Conmemoraciones de 1920 y 2020, fuera del alcance sin explicar un acontecimiento temprano.
4|desde fines del siglo 18|I|-|-|detonante del proceso de independencia|Revoluciones e invasión napoleónica como antecedentes de ruptura política.
5|pero antes de eso en 1807|I|M|-|la familia real portuguesa se trasladó|Reorganización de la monarquía por la invasión; conexión causal con el proceso hispanoamericano.
6|portugal se convierte|M|I|-|la lucha entonces por la independencia se traslada|Explica cambio de escenario bélico y aprendizaje estratégico.
7|volvamos a málaga esa hermosa ciudad|N|L|-|la famosa catedral de málaga|Itinerario familiar y descripción turística; nombrar al líder no basta para R4.
8|y en málaga sanmartín estudió|N|L|-|aprendió a leer y escribir|Educación infantil y transición del programa, sin actuación política desarrollada.
9|san martín fue un soldado del rey|I|L|-|había tomado un compromiso por américa|Conversión política y circulación de asociaciones secretas emancipadoras.
10|en 1812 en buenos aires|M|L|-|la ruta del alto perú no es la ruta adecuada|Decisión estratégica sobre rutas de la campaña.
11|en 1814 san martín fue nombrado|M|-|-|organizar una máquina militar|Preparación de ejército y defensa de frontera revolucionaria.
12|fue aquí donde se produjo|M|I|-|el famoso cruce de los andes|Operación andina y condiciones internacionales adversas que enmarcan la campaña.
13|en mendoza se habían incorporado|M|L|-|victorias de chacabuco y maipú|Alianzas personales al servicio de la campaña y sus victorias.
14|después de 1818|M|L|-|pagar a los marineros|Financiación y sostenimiento logístico de la expedición.
15|y la amistad entre san martín|L|-|-|no podía ocupar ningún cargo|Condiciones políticas pactadas con Chile y autonomía del liderazgo de San Martín.
16|y si tú te acuerdas el término|L|O|-|posiciones de poder|Búsqueda de cargos y posición política de los miembros de la expedición.
17|en el perú el contexto|C|I|-|crisis de subsistencia|Explica condiciones económicas y sanitarias del virreinato antes de la llegada patriota.
18|antes de que la expedición tocase|I|-|-|una guerra de la opinión|Circulación de propaganda e ideas antes del desembarco.
19|i en el momento del desembarco|I|-|-|proclamas por la causa de la independencia|Campaña persuasiva a pobladores, mujeres y ejército real.
20|la expedición libertadora llegó al perú|M|C|-|bloqueos y bombardeos|Bloqueo y guerra de desgaste como mecanismo de debilitamiento realista.
21|no se vayan porque regresamos|M|S|-|desembarco en paracas el 8 de septiembre|Cronología del desembarco y composición/logística de la fuerza expedicionaria.
22|el conductor flota naval|M|L|-|un almirante muy entrenado|Reclutamiento y experiencia del jefe naval en el marco de la expedición.
23|al cabo de tres semanas del desembarco|L|-|-|una monarquía constitucional|Negociación y propuesta de régimen para el Perú.
24|el 21 de octubre de 1820|O|N|-|se fijaban los símbolos provisionales|Establecimiento de símbolos estatales y distinción entre decreto y leyenda posterior.
25|luego de pisco el ejército libertador|M|C|-|1.200 soldados del ejército|Itinerario, cuartel y epidemia que afecta al ejército.
26|cuando el ejército descendió|M|-|-|la sierra central|Expedición de Arenales y penetración militar en la sierra central.
27|existen pocas fuentes que nos cuenten|M|S|A|reprimidas por las fuerzas españoles|Participación social seguida de operaciones y control estratégico de Huamanga; frontera temática mixta.
28|como estamos viendo la participación popular|S|M|-|sacudirse de la servidumbre|Motivaciones y respuestas campesinas a la llegada patriota.
29|y como decía alguna vez|S|M|-|gente de las comunidades|Diversidad y condiciones de participación popular en guerrillas y montoneras.
30|a inicios de diciembre de 1820|M|L|-|batallón numancia se pasó|Cambio de bando y consolidación territorial patriota en el norte.
31|la era de la independencia desde|I|L|-|aparato de propaganda|Redes y difusión política por proclamas, rumores y logias.
32|a puertas del bicentenario|S|L|-|actores nacionales|Explica agencia peruana simultánea en provincias, Lima y sierra.
33|un personaje importante en el norte|M|L|-|batalla de higos urko|Cambio de bando de autoridades y desarrollo de campaña en Amazonas.
34|van a ver a muchas mujeres|S|-|-|van a utilizar armas|Acción de mujeres e indígenas en combate y abastecimiento.
35|mientras tanto en la capital|I|L|-|ese vacío de poder|Colapso de legitimidad y aparato virreinal que favorece el protectorado.
36|un asunto crucial que trajo|L|O|-|propuestas republicanas|Disputa entre monarquía constitucional y proyecto republicano.
37|muchas veces en una visión eurocentrista|O|-|-|se establecen|Implantación y solidez de repúblicas americanas como experiencia institucional.
38|en julio de 1821|O|M|-|establecer tu sistema electoral|Balance del proceso centrado en la tarea de organizar y administrar la república.
39|como hemos visto a lo largo de este programa|N|-|-|nos vemos en la próxima|Recapitulación mínima y despedida del programa.
''',
}

LONG['rKbC4guGhRY']=r'''
1|^|N|-|-|cuando yo estudiaba en el colegio|Presentación sobre enseñanza e interpretación de historia.
2|la historia así como la realidad|N|-|-|cada generación tiene su propia aproximación|Explicación general de interpretación histórica.
3|la historiografía y esta es una palabra|N|-|-|el estudio de cómo se ha escrito|Definición y funcionamiento de la historiografía.
4|queda una interpretación de la generación|N|-|-|luego de la pandemia|Generaciones de historiadores y agendas de investigación contemporáneas.
5|que motiva a las generaciones intelectuales|N|S|-|cada generación intelectual responde a su época|Demandas contemporáneas de representación que modifican la historiografía.
6|abordar la historia de la independencia|N|C|A|ofrecer una interpretación patriota|Dificultades de narrar desde Perú; el papel colonial aparece subordinado a la discusión historiográfica.
7|el 28 de julio de 1821|L|I|-|puestos claves|Disputa sobre conducción del poder y acceso de criollos al gobierno protector.
8|otro tema importante en el nacimiento|O|-|-|establecimiento de fechas celebratorias|Fijación estatal de un calendario republicano.
9|yo diría que esa fecha|O|-|-|la instalación del congreso constituyente|Consenso y controversia sobre celebraciones oficiales.
10|desde el principio cuando se establece|O|-|-|un calendario cívico|Organización de conmemoraciones y desplazamiento de festividades coloniales.
11|incluso la propia constitución|O|-|-|la educación como un derecho|Disposiciones de la primera constitución sobre educación y memoria estatal.
12|no se mueva volvemos en seguida|I|-|-|la independencia fue una revolución|Concepción de ruptura revolucionaria entre actores contemporáneos.
13|de hecho en monteagudo|I|L|-|teorías del progreso|Fundamento ideológico de la revolución hispanoamericana.
14|en 1818 josé de la riva-agüero|I|-|-|las 28 causas|Justificación de separación frente a dominación española, absolutista o liberal.
15|en 1822 tras la salida de san martín|O|-|-|los primeros decretos|Reconocimiento institucional temprano de luchas previas.
16|como sabemos los primeros 50 años|L|I|-|reclamaban refundar la nación|Proyectos de legitimación política de caudillos, con referencia a la Confederación.
17|toda revolución cambia los nombres|O|I|-|lima fue rebautizada|Implantación de nueva nomenclatura republicana en ciudades y fortificaciones.
18|pero los cambios en hombres|I|O|-|constitución de cádiz|Ruptura simbólica liberal de 1812 y revolución del Cusco de 1814, anterior al Estado republicano.
19|es más yo encontré evidencias|S|O|-|reclamaban la exoneración de tributos|Campesinos invocan su acción patriota para demandar derechos en 1827.
20|no se sabe muy bien cuándo|N|-|-|nunca en el colegio me enseñaron|Comparación contemporánea de vocabulario escolar y conmemorativo.
21|a lo largo del tiempo se han producido relatos|N|O|A|discurso oficial|Discute relatos regionales y enseñanza; breve ejemplo de la Confederación no fija una dominancia inequívoca.
22|al volver hablaremos de la obra|N|-|-|en el año 1860 publicó|Presentación bibliográfica de Vicuña Mackenna.
23|vicuña mackenna era un político liberal|N|-|-|exiliado al perú|Contexto de producción de una obra en la década de 1850 y crítica historiográfica.
24|lo que hizo vicuña mackenna fue destacar|I|S|-|juntas autonomistas|Explica participación peruana en formación de juntas y ruptura política antes de San Martín.
25|vicuña mackenna no sólo se remonta|I|L|-|conspiración aportada de aguilar|Conspiraciones y conexiones entre focos de oposición al orden español.
26|en realidad trata de rescatar|I|S|-|juntas y manifiestos|Explica juntas y voluntad de ruptura, con antecedentes coloniales conectados.
27|es muy interesante el trabajo de vicuña|N|-|-|historia oral|Métodos, testimonios y dificultades documentales del historiador.
28|va a ser un libro en base|N|-|-|uso de fuentes|Comparación de métodos y fuentes entre dos historiadores.
29|en cambio mariano paz soldán utilizó|N|-|-|fuentes documentales|Discusión sobre oralidad y documento como pruebas históricas.
30|en el siglo 19 este la visión|N|-|-|corriente positivista|Historiografía positivista y valoración posterior de sus autores.
31|volvemos con lo último del programa|N|O|-|en 1868|Historia de publicación y lectura de Paz Soldán.
32|el inicia su libro básicamente|N|M|A|los libros del colegio|Discusión de narración escolar, con una explicación breve de la fuerza realista; frontera metahistoriográfica.
33|en otros países de américa latina|O|I|A|una cura de independencia|Fechas conmemorativas comparadas con juntas de 1810 y cierre militar en 1824; mezcla de planos.
34|paso al campo es el primer historiador|S|M|A|el perú había dado repetidas|Contrasta valoración de agencia peruana y limitaciones de sus esfuerzos; mezcla cita histórica y comentario.
35|en 1869 un año después|N|S|-|anotaciones a la historia|Publicación y crítica posterior de Mariátegui a Paz Soldán.
36|el historiador que realmente introduce|N|S|-|el año 1869 escribe una refutación|Describe el debate historiográfico y su recepción sin desarrollar todavía el argumento citado.
37|asevera el señor paz soldán|I|S|-|formada estaba desde el año 1810|La cita explica opinión política emancipadora anterior al desembarco y represión de sus partidarios.
38|inicios del siglo 20|N|-|-|en 1912|Producción de monografías conmemorativas y concursos escolares del siglo XX.
39|llamado al cusco pumacahua|S|L|A|solidaridad fraternal|Cita sobre solidaridad y vinculación de Pumacahua a la rebelión; frontera agencia social y liderazgo.
40|lo que hoy hemos podido comprender|N|-|-|nos vemos en la próxima|Balance de aprendizaje historiográfico y despedida, incluidos créditos musicales.
'''

SHORT={
'HuT0aI_mDqM':r'''
1|^|S|O|-|aprenden los valores cívicos|La experiencia de guerra forma conciencia y libertades de las personas; no se describen operaciones militares.
2|[Música]|N|-|-|[Música]|Interludio musical sin desarrollo histórico.
3|el título del libro trata|S|M|A|los peruanos no habrían luchado|Contrasta agencia peruana e intervención extranjera; requiere adjudicar dominancia frente a interpretación historiográfica.
4|no más recientemente|I|-|-|revoluciones liberales|Liberalismo hispánico como causa de liberación de las colonias.
5|nación peruana Y el nacionalismo|I|S|A|las Cortes de Cádiz|Crisis imperial y formación social de conciencia nacional reciben desarrollo comparable.
6|precisamente porque|N|-|-|los centenarios tienen la función|Reflexión actual sobre conmemoración y responsabilidad académica.
''',
'lrV0mu1iZCI':r'''
1|^|N|-|-|problemas iniciales con la conexión|Presentación, comprobación técnica y agradecimientos del congreso.
2|yo voy a hablar un poco|N|-|-|recuperación documental|Presenta la historia de un debate y la recuperación documental de 1971.
3|y él sostiene más o menos|S|O|E|indígenas negros esclavos se unifican|Explica unión social en la independencia; la fecha 1920 requiere cotejo del audio, sin corrección conjetural.
4|entonces este este era una visión|N|-|-|aprovechada por los militares en el 71|Uso político de la interpretación independentista en 1971, fuera del alcance histórico.
5|tienes que responder a tu bonilla|S|M|AE|unificación de sectores sociales|Contraste entre agencia local e intervención externa; transición deteriorada en los subtítulos.
6|entonces esto como sabemos|I|N|AE|construyen una propia narrativa|Anuncia narrativas políticas de los actores, pero el video acaba con la oración incompleta.
'''}
