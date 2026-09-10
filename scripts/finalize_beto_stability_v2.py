"""Qualitative development-error review and final conclusions; no training or relabeling."""
from report_beto_stability_v2 import *

REVIEWS={
'S01-seg0007-s04313':('error_clasificador','El objetivo desarrolla explícitamente crisis de 1808–1812, cambio ideológico e ideas liberales. El contexto previo confirma la crisis de legitimidad. La mención de ceremonial colonial no desplaza ese argumento; la referencia R2 tiene apoyo textual.'),
'S01-seg0007-s06192':('error_clasificador_con_frontera','El traslado de soberanía del rey a la nación sustenta R2. La descripción del procedimiento de juramento acerca el vocabulario a R5, pero el objetivo está fechado en 1812 y el contexto separa después los rituales republicanos. No se necesita invalidar la referencia para explicar la confusión.'),
'S05-visual-p007-01':('error_clasificador','El argumento trata del descontento, bandolerismo y violencia de clases populares como agentes. La pregunta final sobre una alternativa al colonialismo explica la atracción de R2, pero no desarrolla por sí sola un programa ideológico. El contexto siguiente mantiene el foco campesino.'),
'S10-seg0014-s00000':('error_clasificador_temporal','El objetivo y su contexto se sitúan explícitamente en los planes y catecismos de 1850–1859. No desarrollan en este pasaje un nexo con 1780–1842. Los términos opinión pública y principios democráticos parecen señales temáticas insuficientes para respetar el alcance temporal de R7.'),
'S01-seg0005-s00000':('error_clasificador','El pasaje contrapone antecedente virreinal y uso educativo desde 1821 para cohesionar la república. El contexto siguiente desarrolla herramientas culturales republicanas. R5 tiene evidencia directa; la continuidad de símbolos puede explicar la atracción de R1.'),
'S01-seg0008-s00000':('error_clasificador_con_contexto','El objetivo describe uso efectivo de rituales y prohibición de festivales coloniales después de la independencia. Su inicio depende del contexto anterior, aquí disponible. La frontera entre movilización, ideas e implantación simbólica es difícil, pero R5 resulta defendible; no se modifica.'),
'S03-seg0005-s00000':('error_clasificador','Se describe la estructura defensiva virreinal y su insuficiencia, con antecedente de 1746 y enlace contextual a 1794. No narra una campaña concreta ni una institución republicana. La referencia R1 se apoya en la función estructural del pasaje.'),
'S03-seg0044-s00991':('error_clasificador','Virrey, Real Audiencia y Real Cédula delimitan una disputa de jurisdicción colonial, también confirmada por el contexto. La forma institucional no la convierte en organización republicana. La confusión R1→R5 persiste en las seis predicciones.'),
'S01-seg0014-whole':('posible_ambiguedad_anotacion_y_contexto','La Ley fundamental y las atribuciones detalladas sostienen una lectura institucional R5; la justificación del diseño confederal y el contexto previo sobre órganos que no llegaron a constituirse sostienen R4. Es una frontera de proyecto frente a implantación que merece revisión experta futura, sin declarar incorrecta R4. BETO recibe sólo el objetivo, no el contexto adyacente archivado.'),
'historical-v4-0037':('posible_ambiguedad_anotacion','Las alianzas de los caudillos fundamentan R4, mientras la explicación del patronazgo y ascenso social admite una lectura de funcionamiento republicano o experiencia social. Falta el pasaje previo, pues empieza con una continuidad. Se registra ambigüedad de dominancia, no una etiqueta errónea demostrada.'),
'historical-v4-0175':('posible_ambiguedad_anotacion_y_contexto','Combina una cita sobre igualdad, movilización parroquial, contraste alto/bajo clero y actuación de un obispo. R4 puede apoyarse en la conducción individual; la agencia de grupos también es sustantiva. Los cambios de sección y OCR dificultan decidir dominancia sin adyacentes. Las predicciones R5 no prueban un error de referencia.'),
'historical-v4-0430':('error_clasificador_con_extraccion','La composición de la asamblea y distribución de diputados en 1823–1825 sostienen R5. La tabla aplanada intercalada y la ausencia de un antecedente para esta asamblea dificultan la lectura; los tres errores distintos sugieren sensibilidad del clasificador a esa presentación, sin demostrar causalidad del OCR.'),
'S05-visual-p007-02':('error_clasificador_con_contexto','El objetivo sitúa la movilización tupamarista en 1780 y su extensión quechua/aymara; el contexto siguiente vincula territorios y comunidades campesinas. Hay lenguaje de lucha, pero R6 tiene soporte. La predicción republicana repetida no se corresponde con el periodo descrito.'),
'S06-seg0010-s00000':('error_clasificador','La Constitución abre el pasaje, pero su argumento y la cita desarrollan indiferencia, incentivos y reacciones de plebe y grupos sociales. El contexto siguiente continúa esas respuestas. R6 resulta sustentable frente a una clasificación institucional por palabras clave.'),
'S10-seg0010-s00717':('posible_ambiguedad_anotacion','El objetivo expone una representación de la experiencia indígena y una propuesta racial, con R6 defendible por desigualdad y experiencia social. El contexto educativo republicano y la voz de un rector acercan R5/R4. Es una frontera de dominancia; no se concluye que la referencia esté equivocada.'),
'S15-seg0008-s00000':('error_clasificador','La pugna entre hacendados y acciones de esclavos es el núcleo explícito, situado después de 1821. El contexto normativo y mercantil permite entender R5 como alternativa, pero no elimina la agencia que sustenta R6. R1 confunde continuidad de esclavitud con periodo colonial.'),
'historical-v4-0467':('error_clasificador','El objetivo desarrolla soberanía, constitucionalismo gaditano, circulación periodística y propaganda separatista entre 1808 y 1814. La referencia R2 está apoyada por el argumento, aunque no haya contexto adyacente. La lectura R5 pierde la distinción temporal y política.'),
'historical-v4-0699':('falta_contexto_y_posible_ambiguedad_anotacion','La primera cita desarrolla opinión pública, pero enseguida aparece una descripción de bandera y decreto con un rótulo editorial. Son unidades temáticas diferentes y falta el origen inmediato de la cita. La mezcla exige revisar contexto/extracción antes de decidir dominancia; no se resegmenta ni se relabela aquí.'),
'historical-v4-0265':('falta_contexto','Empieza a mitad de palabra y describe minería, crédito y subordinación comercial sin una fecha inequívoca en el objetivo. La procedencia es Los primeros años del Perú republicano, pero no sustituye el contexto local ausente. R1/R5 requieren anclaje temporal; no se atribuye todo al clasificador ni se invalida R5.'),
'historical-v4-0035':('posible_ambiguedad_anotacion','Los decretos de Bolívar y sus efectos efectivos apoyan R5 como alternativa; la desintegración comunal, endeudamiento y subordinación indígena apoyan la referencia R6. El comienzo incompleto limita el contexto de dominancia. Se conserva R6 y se señala la frontera entre política y experiencia social.')}

def main():
    report=read(SART/'report.json');draft=read(SOUT/'representative-cases.json')
    errors={r['segment_id']:r for r in read(SOUT/'persistent-errors.json')}
    cases=[]
    boundaries={'historical-v4-0467':'crisis_ideas','historical-v4-0699':'crisis_ideas',
                'historical-v4-0265':'antecedentes_organizacion','historical-v4-0035':'participacion_social'}
    draft_byid={r['segment_id']:r for r in draft}
    for sid,(category,reason) in REVIEWS.items():
        row=draft_byid.get(sid) or {**errors[sid],'boundary':boundaries[sid],
            'available_annotation_context':errors[sid].get('context'),
            'context_status':'No hay pasaje adyacente en la fila canónica; se conserva procedencia.'}
        assert max(row['wrong_seed_count'].values())>=2
        cases.append({**row,'review_status':'Qualitative review complete; reference unchanged',
            'qualitative_review':{'category':category,'reason':reason,'reference_changed':False,
                                  'scope':'Hipótesis de lectura, no nueva anotación ni diagnóstico causal demostrado'}})
    assert len(cases)==20 and len({r['segment_id'] for r in cases})==20
    save(SOUT/'reviewed-cases.json',cases)
    summary=report['seed_summaries']['combined']
    conclusion={
        'B_advantage_stable':False,'B_favored_seeds':2,'total_seeds':3,
        'paired_difference_mean':summary['difference']['mean'],'paired_difference_sample_sd':summary['difference']['sample_sd'],
        'mean_over_sd':summary['difference']['mean']/summary['difference']['sample_sd'],
        'interpretation':'Ventaja media positiva muy pequeña, con inversión de signo en 43. No se confirma una mejora estable ni generalizable.',
        'reviewed_cases':20,'selection':'16 candidatos deterministas por frontera, más cuatro históricos para cubrir ideas explícitas, mezcla de unidades, anclaje temporal y efectos sociales. Selección cualitativa deliberada, no proporcional al corpus.',
        'next_experiment':{'status':'proposed_not_executed','name':'Ablación de pesos de clase dentro de B',
            'hypothesis':'Los pesos recalculados con train_B contribuyen a la redistribución inestable del F1 entre clases; mantener los pesos de train_A podría cambiar ese balance de forma consistente.',
            'comparison':'B original reutilizado frente a B con pesos calculados sólo en train_A del mismo fold. Ambos entrenan sobre las mismas filas train_B, con la misma receta, semillas y pasos planificados.',
            'new_condition':'B_weights_A','seeds':[42,43,44],'folds':3,'maximum_new_beto_runs':9,'reused_B_runs':9,
            'fixed':'Base/revisión, filas, etiquetas, validaciones, longitud384, cuatro épocas, LR, microbatch/acumulación, scheduler, AMP, selección de checkpoint.',
            'primary':'Diferencia emparejada B_weights_A−B del promedio de F1 macro de siete clases sobre tres folds, por semilla; media y DE entre semillas.',
            'secondary':'Cambios en organización, antecedentes, participación, no relevante; subconjuntos histórico/IA; omisiones AMP.',
            'decision':'Apoyo descriptivo si las tres semillas favorecen B_weights_A; informar también magnitud y DE, sin declarar significación ni evaluar reserva.',
            'limit':'Aísla la regla de pesos dentro del conjunto B; no estima por sí sola el efecto puro del contenido frente al número de actualizaciones. AMP puede cambiar pasos efectivamente aplicados y se debe registrar.'}}
    save(SART/'conclusions.json',conclusion)
    doc=ROOT/'docs/beto-v2/05-estabilidad.md';text=doc.read_text(encoding='utf-8')
    introduction='''**La ventaja de B no se confirma como estable.** B supera A en las semillas 42 y 44, pero retrocede en 43. La diferencia media es **+0,001889 F1** (0,189 puntos porcentuales), con **DE muestral 0,011479** (1,148 puntos porcentuales): la media equivale a sólo 0,165 DE. A promedia 0,396489 ± 0,017672 y B 0,398378 ± 0,023248 entre semillas. Esta dispersión es descriptiva, con sólo tres semillas.

El balance positivo medio procede sobre todo de participación social (+0,018808 de F1 de clase), no relevante (+0,017392) y liderazgos (+0,007595). Lo compensan organización republicana (−0,015184), antecedentes (−0,011827) y campañas (−0,003699); crisis/ideas permanece casi igual (+0,000137). **Ninguna clase mejora su promedio de folds en las tres semillas.** Los valores son diferencias de F1 de clase; su promedio entre las siete reproduce +0,001889.

Hay patrones locales repetidos: organización retrocede en fold 1 en las tres semillas; liderazgos retrocede en fold 3 en las tres; no relevante mejora en fold 2 en las tres. Los folds 1 y 2 favorecen A en dos semillas y el fold 3 favorece B en dos. Estos patrones describen familias retenidas distintas, no réplicas independientes.

En el subconjunto histórico la diferencia media es apenas +0,000986 (DE 0,011843). En IA es +0,030481 (DE 0,016792) y favorece B en las tres semillas, pero se apoya en sólo 49 filas distribuidas entre folds, con clases ausentes y anotación asistida por IA. No equivale a una mejora histórica general ni a evaluación experta independiente.

'''
    text=text.replace('# BETO v2: estabilidad entre semillas\n\n','# BETO v2: estabilidad entre semillas\n\n'+introduction,1)
    text=text.replace('`representative-cases.json` contiene 16 casos, hasta cuatro por frontera solicitada, priorizando persistencia y diversidad de familia/referencia/predicción.',
        '`reviewed-cases.json` contiene los 20 casos finales: 16 candidatos por frontera y cuatro históricos adicionales para cubrir ideas explícitas, mezcla de unidades, anclaje temporal y efectos sociales. Son siete históricos y trece IA; la selección deliberada no es proporcional al corpus. `representative-cases.json` conserva la selección automática inicial.')
    lines=['','## Revisión cualitativa de los 20 casos','',
        'R1 = antecedentes; R2 = crisis/ideas; R3 = campañas; R4 = liderazgos/proyectos; R5 = organización republicana; R6 = participación social; R7 = no relevante. Las ternas de predicciones siguen el orden 42, 43, 44. El archivo `outputs/beto-v2/stability/reviewed-cases.json` contiene **texto completo, contexto archivado disponible, procedencia, referencia y las seis predicciones**. Los extractos siguientes son sólo ayudas de lectura; no se alteraron los textos de entrenamiento.','',
        'Las categorías de revisión son hipótesis basadas en texto y guía. Un posible problema de anotación indica ambigüedad de dominancia que requiere revisión futura; falta de contexto identifica información no disponible para resolverla; error de clasificador indica que la referencia tiene evidencia textual defendible. Pueden coexistir y ninguna supone corregir una etiqueta en esta fase.','']
    codes=dict(zip(LABELS,['R3','R1','R2','R4','R7','R5','R6']))
    for r in cases:
        preds={c:'/'.join(codes[r['predictions'][c][str(s)]] for s in SEEDS) for c in ('A','B')}
        lines += ['### '+r['segment_id'],'',f"Referencia **{codes[r['truth']]}**; A: {preds['A']}; B: {preds['B']}. Errores en semillas: A {r['wrong_seed_count']['A']}/3, B {r['wrong_seed_count']['B']}/3. Origen: {r['role']}; familia: `{r['family_id']}`.",'',
            '> '+r['text'][:220].replace('\n',' ')+'…','',r['qualitative_review']['reason'],'']
    lines += ['## Siguiente experimento único propuesto — no ejecutado','',
        '**Ablación de pesos de clase dentro de B.** Hipótesis: el cambio de pesos asociado a los ejemplos añadidos contribuye a la redistribución inestable de F1. La persistencia de errores y los cambios de signo entre clases justifican separar este factor antes de atribuir el balance al contenido. Esta hipótesis aún no está demostrada.','',
        'Comparar los nueve B ya guardados con una condición `B_weights_A`: entrenar con exactamente train_B, pero usar los pesos calculados en train_A del mismo fold. Conservar semillas 42/43/44, base/revisión, longitud 384, cuatro épocas, learning rate, batch, scheduler, precisión y regla de checkpoint. El número planificado de pasos es el mismo entre B y B_weights_A; las posibles omisiones AMP se registran porque pueden cambiar las actualizaciones aplicadas.','',
        '**Presupuesto: máximo nueve entrenamientos nuevos** (una condición × tres folds × tres semillas), reutilizando los nueve B existentes. Medida principal: diferencia emparejada B_weights_A−B de los promedios de tres folds por semilla, con media y DE entre semillas. Examinar organización, antecedentes, participación y no relevante como desgloses secundarios; conservar soporte y clases ausentes por origen. Apoyo descriptivo a la hipótesis si las tres semillas favorecen B_weights_A, informando también tamaño y dispersión; no sería una prueba de significación.','',
        'Este contraste identifica el efecto de la regla de pesos dentro de B; mantiene el contenido y los pasos planificados de B y no separa todavía contenido añadido de mayor presupuesto de actualizaciones en A/B. No requiere nuevas fuentes, etiquetas, acceso a reserva, Optuna, DAPT ni despliegue. No se ejecutó en esta fase.','',
        '## Entregables y comprobación final','',
        '- Informe estructurado: `artifacts/beto-v2/stability/report.json` (18 resultados verificados, clases, orígenes, familias, errores y hashes).',
        '- Conclusión y propuesta: `artifacts/beto-v2/stability/conclusions.json`.',
        '- Contratos de semilla e identidad, sin fits BETO: `artifacts/beto-v2/stability/checks.json`.',
        '- Configuraciones, curvas, checkpoints y reanudación: `outputs/beto-v2/stability/seed-43/` y `seed-44/`.',
        '- Predicciones: `outputs/beto-v2/stability/predictions-by-seed.csv` (3546 filas = 591 × 3 × 2).',
        '- Inventario de 332 errores persistentes: `outputs/beto-v2/stability/persistent-errors.json`.',
        '- Veinte casos revisados: `outputs/beto-v2/stability/reviewed-cases.json`.',
        '- Reproducción del análisis en una carpeta sin informes previos: `scripts/report_beto_stability_v2.py`, seguido de `scripts/finalize_beto_stability_v2.py`. Ambos rechazan sobrescribir sus JSON; no entrenan.','']
    doc.write_text(text+'\n'.join(lines),encoding='utf-8')
    # Check the delivered records against the unchanged canonical view and saved predictions.
    p,byid=inputs();assert len(byid)==591
    for r in cases:
        assert r['text']==byid[r['segment_id']]['text'] and r['truth']==byid[r['segment_id']]['label']
    with (SOUT/'predictions-by-seed.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==3546 and len({(r['segment_id'],r['seed'],r['condition']) for r in rows})==3546
    assert len(list(SOUT.glob('seed-*/*/result.json')))==12
    assert len(report['verification'])==18
    assert abs(stats.mean(r['paired_fold_mean_difference']['mean'] for r in report['class_summary'])-summary['difference']['mean'])<1e-12
    for r in report['paired_prediction_transitions']:assert sum(v for k,v in r.items() if k!='seed')==591
    save(SART/'delivery-verification.json',{'new_runs':12,'reused_runs':6,'canonical_rows':591,'predictions':3546,
        'reviewed_cases':20,'canonical_texts_and_labels_unchanged':True,'class_contributions_reconcile':True,
        'files':{str(q.relative_to(ROOT)):filehash(q) for q in [doc,SART/'report.json',SART/'conclusions.json',SOUT/'reviewed-cases.json',SOUT/'predictions-by-seed.csv']}})
    print(json.dumps(conclusion,ensure_ascii=True,indent=2))

if __name__=='__main__':main()
