"""Editorial QA and explicit caveats; frozen folds/models/results stay unchanged."""
import re
from datetime import datetime,timezone
from run_beto_first_training_v2 import *

def main():
    p,rows=inputs()
    doc=ROOT/'docs/beto-v2/04-primer-entrenamiento.md'
    before=filehash(doc);content=doc.read_text(encoding='utf-8')
    fixes={'a29':'a 29','+49':'+ 49','=591':'= 591','De613':'De 613','excluyeron69':'excluyeron 69','concatenaron18':'concatenaron 18','Semilla42':'Semilla 42','efectivo16':'efectivo 16','En591':'En 591','exceden384':'exceden 384','GPU,4':'GPU, 4','semilla42+época':'semilla 42 + época','p95= ':'p95 = ','de50.000':'de 50.000','de2.000':'de 2.000','son7':'son 7','de las fases01–03':'de las fases 01–03','palabras1–2':'palabras 1–2'}
    for a,b in fixes.items():content=content.replace(a,b)
    content=re.sub(r'(?<=\d)s\b',' s',content)
    content=re.sub(r'(?<=\d)min\b',' min',content)
    content=content.replace('Basadre/Hampe/S15','Basadre/Orrego/S15')
    explanation=('Aclaración de identidad: el ID congelado `historical-basadre-hampe` conserva un nombre heredado, pero la fuente `9f60a031-0183-478c-a1f8-a3bdd37d7b0b` corresponde a **Juan Luis Orrego Penagos**, según el registro previo y el propio texto. El agrupamiento con Basadre se sostiene conservadoramente por citas y reproducción explícita de su obra en `historical-v4-0004`, `historical-v4-0040` y `historical-v4-0618`; no se atribuye ese texto a Hampe. Esta aclaración documental no cambia ninguna familia, fila, etiqueta o resultado congelado.')
    content=content.replace('Los demás conservan su obra completa. La independencia absoluta', 'Los demás conservan su obra completa. La independencia absoluta',1)
    anchor='La independencia absoluta de documentos primarios, paráfrasis o autores no queda certificada.'
    content=content.replace(anchor,anchor+'\n\n'+explanation)
    report=read(ART/'report.json')
    skipped=[{'fold':f['id'],'condition':c,'skipped_updates':sum(e['amp_skips'] for e in f['results'][c]['history'])} for f in report['folds'] for c in ['A','B']]
    amp='AMP omitió dos actualizaciones por overflow en A del fold-2; las demás ejecuciones no omitieron ninguna. El scheduler respetó la regla congelada de avanzar sólo tras actualizaciones aplicadas. Los detalles por época se conservan en cada resultado; no se repitieron entrenamientos para eliminar esta variación.'
    anchor='La misma fórmula puede producir pesos de clase y números de pasos diferentes por el tamaño A/B.'
    content=content.replace(anchor,anchor+'\n\n'+amp)
    content=content.replace('| Verdad |','| Etiqueta conservada |')
    anchor='B mejora el promedio exploratorio.'
    content=content.replace(anchor,'B mejora el promedio exploratorio en **0,0080 puntos de F1** (aproximadamente **0,80 puntos porcentuales**), con mejora en dos folds y retroceso en uno. Las29 correcciones frente a30 regresiones implican un acierto neto menos sobre las591 filas, aunque suba F1 macro; la señal depende de cómo se distribuyen los errores entre clases.'.replace('Las29','Las 29').replace('a30','a 30').replace('las591','las 591'))
    content=content.replace('# Reutilizar pass-a.json/pass-b.json y sus cachés; no repetir anotaciones idénticas.','# Copiar pass-a.json/pass-b.json archivados; el finalizador deriva cachés sin reanotar.')
    content=content.replace('outputs/venv-ml/Scripts/python.exe scripts/report_beto_first_training_v2.py\n```','outputs/venv-ml/Scripts/python.exe scripts/report_beto_first_training_v2.py\noutputs/venv-ml/Scripts/python.exe scripts/finalize_beto_first_training_delivery_v2.py\n```')
    # Table source excerpts and IDs are intentionally unchanged.
    doc.write_text(content,encoding='utf-8')
    details={'created_at_utc':datetime.now(timezone.utc).isoformat(),'document_before_sha256':before,'document_after_sha256':filehash(doc),'identity_clarification':explanation,'identity_evidence':['artifacts/beto-v2/corpus/class-work-author-format-v2.csv','outputs/beto-v2/first-training/canonical-dataset.json#historical-v4-0004'],'amp_updates':skipped,'frozen_partitions_and_results_changed':False,'full_beto_runs':6,'metrics_verification':'artifacts/beto-v2/first-training/verification.json'}
    save(ART/'documentation-clarifications.json',details)
    with (ART/'journal.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'at':details['created_at_utc'],'event':'final_editorial_verification','evidence':'documentation-clarifications.json','no_new_training':True},ensure_ascii=False)+'\n')
    manifest=read(ART/'delivery-manifest.json')
    manifest['files'].update({path.relative_to(ROOT).as_posix():filehash(path) for path in [doc,ART/'documentation-clarifications.json',ART/'journal.jsonl',Path(__file__).resolve()]})
    manifest['finalized_at_utc']=details['created_at_utc']
    (ART/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(filehash(ROOT/path)==h for path,h in manifest['files'].items())
    assert all(f"{report['mean_f1_macro']['combined'][c]:.6f}" in content for c in ['A','B'])
    print('Final document, manifest and frozen input integrity verified')

if __name__=='__main__':main()
