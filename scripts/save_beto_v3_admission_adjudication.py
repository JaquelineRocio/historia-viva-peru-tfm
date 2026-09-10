"""Persist parent judgments after reading all targets and both saved reviews."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/beto-v3/admission-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(d):return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
# Explicit judgments over exact original targets; no predictions were available.
JUDGMENTS=[
('A01-N01-w0-u01','no_relevante','La presentación explica recuperación imperial del XVIII y anuncia efectos territoriales; no desarrolla en este objetivo el vínculo causal con la independencia. Se conserva la introducción y sus errores ASR, sin heredar el tema de otras ventanas.'),
('A01-N01-w0-u02','no_relevante','El objetivo breve trata de sucesión dinástica y Felipe V; el inicio cortado no oculta una explicación pertinente de la independencia en el texto disponible.'),
('A01-N01-w0-u03','no_relevante','Domina la decadencia española bajo Carlos II y la comparación europea, anteriores al alcance y sin conexión emancipadora desarrollada.'),
('A01-N01-w0-u04','no_relevante','La guerra sucesoria europea por el trono no es una campaña del proceso peruano. No se incorpora contexto de la obra para volverla relevante.'),
('A01-N01-w0-u05','no_relevante','Las consecuencias comerciales y dinásticas de Utrecht se explican por sí mismas; la última cláusula incompleta no permite inventar su continuación emancipadora.'),
('A01-N01-w1-u01',None,'Persiste duda de alcance: se describen educación y poder jesuita y oposición de la corona, pero el objetivo no fija cuándo ocurre esa estructura ni desarrolla su nexo emancipador. La referencia a Carlos III no basta para resolver el objetivo completo; no se fuerza no_relevante.'),
('A01-N01-w1-u02','no_relevante','El poder paralelo jesuita y los episodios de 1759–1766 no desarrollan consecuencias para el proceso definido. El mecanismo estatal anterior no hereda relevancia de otra ventana.'),
('A01-N01-w1-u03','no_relevante','Se explica la expulsión de 1767 y su comunicación secreta. La enumeración de motines no constituye agencia emancipadora en este objetivo.'),
('A01-N01-w1-u04','no_relevante','El objetivo original explica el secreto de la expulsión de 1767 para evitar disturbios. El corte final se conserva; el tema anterior queda reconocible sin incorporar palabras del vecino.'),
('A01-N01-w1-u05','no_relevante','El objetivo original describe confiscaciones y traslado de jesuitas; nombrar a Vizcardo no desarrolla aquí su papel en la independencia. No se traslada etiqueta desde su biografía externa.'),
('A01-N01-w2-u01',None,'Castas y control del ocio corresponden potencialmente a estructuras coloniales, pero el comienzo fiscal está deteriorado y falta nexo temporal/causal suficiente dentro del objetivo. La fecha de Amat no se añade desde conocimiento externo para decidir.'),
('A01-N01-w2-u02','contexto_colonial_antecedentes','La explicación de control y reformas concluye explícitamente en malestar criollo y ruptura emancipadora. La agencia criolla es efecto de las estructuras descritas; por eso domina antecedentes.'),
('A01-N01-w2-u03',None,'La apertura que transmite ideas y alternativas de gobierno convive con desplazamiento de criollos y carga fiscal como causas de separación. No hay dominancia suficientemente clara entre crisis/ideas y antecedentes; discrepancia preservada sin usar la cuota para decidir.'),
('A01-N01-w2-u04','contexto_colonial_antecedentes','El balance del absolutismo y la debilidad imperial enlaza expresamente con la independencia de 1824. Inglaterra y Francia sirven al contraste del orden imperial, no a una apropiación de ideas desarrollada.'),
('A01-N01-w2-u05','contexto_colonial_antecedentes','La preferencia por peninsulares y perjuicio criollo se identifican expresamente como causas de independencia. El crédito final potencialmente espurio del ASR se conserva y se marca; no determina la clase.'),
('A01--Ma1tt97eFg-w0-u01','liderazgos_diplomacia_proyectos','La introducción sí describe una opción política concreta de Sánchez Carrión, defender la república como régimen para el país. El paratexto contemporáneo no elimina esa contribución histórica explícita.'),
('A01--Ma1tt97eFg-w0-u02',None,'La valoración del pensamiento como fundamento de la república no desarrolla sus argumentos, actuación o diseño. Se conserva la discrepancia de suficiencia entre atribución general y proyecto político, sin aceptar sólo por el nombre.'),
('A01--Ma1tt97eFg-w0-u03','liderazgos_diplomacia_proyectos','La actuación en el Congreso defiende la opción republicana cuando se disputa la forma de gobierno; no trata de funcionamiento institucional ya implantado.'),
('A01--Ma1tt97eFg-w0-u04','no_relevante','Nacimiento, lugares, propiedad y cargos del padre son datos biográficos/locales sin explicar incidencia en la independencia o una estructura colonial general. Las fechas del alcance no bastan por sí solas.'),
('A01--Ma1tt97eFg-w0-u05',None,'El único requisito de ingreso al seminario aparece al final de una secuencia familiar y patrimonial y queda abierto. No se desarrolla lo suficiente como mecanismo colonial dominante para resolver R1; se conserva pendiente por frontera/suficiencia.'),
('A01--Ma1tt97eFg-w1-u01','liderazgos_diplomacia_proyectos','La cultura servil es argumento explícito contra la monarquía constitucional en una polémica entre proyectos, y no objeto autónomo de descripción colonial.'),
('A01--Ma1tt97eFg-w1-u02','liderazgos_diplomacia_proyectos','El diagnóstico de fragmentación social fundamenta la monarquía constitucional y el ejecutivo fuerte propuestos por Monteagudo. No describe implementación de una institución republicana.'),
('A01--Ma1tt97eFg-w1-u03','liderazgos_diplomacia_proyectos','La debilidad militar y las dudas dirigentes explican la decisión de San Martín de pedir apoyo a Bolívar; no hay una secuencia operacional de campaña. El crédito ASR intercalado se marca como defecto no determinante.'),
('A01--Ma1tt97eFg-w1-u04','liderazgos_diplomacia_proyectos','Encuentro, pérdida de apoyos y bloqueo del proyecto monárquico explican una disputa de conducción política. El periódico se menciona sin desarrollar aquí doctrina o funcionamiento institucional.'),
('A01--Ma1tt97eFg-w1-u05','liderazgos_diplomacia_proyectos','La campaña periodística contra el Protectorado se explica como instrumento de oposición que contribuye a la salida de San Martín. La transferencia al Congreso cierra esa conducción disputada; no basta para organización republicana.'),
('A01--Ma1tt97eFg-w2-u01',None,'Las muertes y sospechas de complot pertenecen al periodo, pero la secuencia no termina de explicar su función política y acaba en una hipótesis incompleta. El acuerdo en null se mantiene tras revisar la frontera real.'),
('A01--Ma1tt97eFg-w2-u02','liderazgos_diplomacia_proyectos','El relato de autopsia refuta un rumor y el cierre explica su utilidad para desacreditar enemigos ligados a Bolívar. Esa función política explícita permite clasificarlo, sin certificar la exactitud médica o histórica del relato.'),
('A01--Ma1tt97eFg-w2-u03','liderazgos_diplomacia_proyectos','Dentro del homenaje se desarrolla la construcción de libertad mediante aprendizaje republicano frente a cultura servil: proyecto de sistema político, no funcionamiento o resultado institucional medido.'),
('A01--Ma1tt97eFg-w2-u04',None,'La oposición entre presidentes titulados y republicanismo liberal es muy general y su frase central está deteriorada. No se resuelve la suficiencia para distinguir proyecto explicado de evocación valorativa.'),
('A01--Ma1tt97eFg-w2-u05','liderazgos_diplomacia_proyectos','Se atribuye un programa normativo de leyes, austeridad y moderación como condiciones para ser libres. Es propuesta política y no efecto institucional; créditos y URL potencialmente espurios del ASR quedan marcados sin incorporarlos a la evidencia.')]
def main():
    units={r['segment_id']:r for r in read(OUT/'annotation-inventory.json')['items']}
    passes={stage:{r['segment_id']:r for p in sorted((OUT/stage).glob('batch-*.json')) for r in read(p)['items']} for stage in ('first-pass','second-review')}
    result=[]
    assert {j[0] for j in JUDGMENTS}==set(units)
    for sid,label,rationale in JUDGMENTS:
        u=units[sid];first=passes['first-pass'][sid];second=passes['second-review'][sid]
        assert first['input_sha256']==second['input_sha256']==u['input_sha256']
        # Evidence already read in the target and both packets; preserve the quote.
        evidence=second['evidence'];a=u['text'].index(evidence)
        result.append({'segment_id':sid,'input_sha256':u['input_sha256'],'accepted_label':label,'evidence':evidence,
                       'evidence_span':[a,a+len(evidence)],'evidence_checked':True,'boundary_checked':True,
                       'boundary_blocking':label is None,'rationale':rationale,'training_eligible':False,
                       'first-pass_sha256':digest(first),'second-review_sha256':digest(second),
                       'flags':sorted(set(first['flags']+second['flags']))})
    out={'adjudicator':'parent Codex; full exact targets and both saved responses read; no BETO predictions',
         'expert_gold':False,'items':result}
    dest=OUT/'adjudication.json'
    if dest.exists():assert read(dest)==out
    else:dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('30 explicit adjudications saved; accepted',sum(r['accepted_label'] is not None for r in result))
if __name__=='__main__':main()
