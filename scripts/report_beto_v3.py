"""Compute the bounded pause report and cumulative observed usage; no model calls."""
import json
import statistics
from collections import Counter
from datetime import datetime, timezone

from prepare_beto_v3 import ART, OUT, ROOT, DOC, read, sha, write

def main():
    if (ART/'recovery-01/current.json').exists():
        from report_beto_v3_recovery import main as report_recovery
        return report_recovery()
    curves=read(ART/'prior-train-curves.json')
    summary={}
    for condition in ['A','B']:
        last=[r for r in curves if r['run'].endswith('-'+condition) and r['epoch']==4]
        summary[condition]={
            'epoch':4,'folds':len(last),
            'train_macro_f1_mean':statistics.mean(r['train_metrics_eval']['f1_macro'] for r in last),
            'validation_macro_f1_mean':statistics.mean(r['val_metrics']['f1_macro'] for r in last),
            'train_loss_mean':statistics.mean(r['weighted_train_loss'] for r in last)}
    prior=read(ART/'prior-executions.json')
    source_registry=read(ART/'source-registry.json')
    annotation=read(ART/'annotation-progress.json')
    usage={'new_training_trajectories':0,'new_training_gpu_seconds':0,'CD_training_gpu_seconds':0,
        'ASR_gpu_seconds':0,'prior_checkpoint_inference_seconds_measured':sum(r['seconds'] for r in curves),
        'new_unique_annotation_proposals':annotation['unique_new_units_with_proposal'],
        'new_historical_review_units':10,'historical_review_including_previous':30,
        'previous_successful_training_seconds':prior['known_successful_training_seconds'],
        'previous_failed_training_seconds':None,'previous_failed_time_status':'unknown; not reported as zero',
        'paid_services_used':False,'provider_token_usage':None}
    write(ART/'budget-ledger-current.json',usage)
    write(ART/'diagnosis-summary.json',{'seed':42,'epoch4':summary,
        'scope':'Six V2 A/B trajectories; 24 epoch inferences, not V3 validation',
        'interpretation':'Training performance rises well above held-out performance; generalization gap is supported. Longer fine-tuning benefit remains untested.',
        'unknowns':['Effect of longer optimization','Performance on independent videos','Historical expert accuracy of references']})
    b=read(ART/'phase-B-summary.json')
    status={
        'phase':'B_partial_access_block','A':'reviewed_base_and_diagnostics_complete; final H awaits video family exclusions',
        'B':'real_transcript_pilot_prepared; references/splits_not_final',
        'C_to_G':'not_started; data/reference gate not satisfied','goal_reached':False,
        'V3_macro_f1':None,'usage':usage,'blockers':b['blockers'],
        'completed_artifacts':{'H_initial':591,'H_reviewed':590,'transcripts':5,'candidate_units':123,
            'first_pass_annotation_proposals':12,'accepted_new_references':0,'prior_epoch_inferences':24},
        'resume_check':'outputs/venv-ml/Scripts/python.exe scripts/check_beto_v3.py --require-C'}
    write(ART/'status.json',status)
    lines=[
        '# BETO V3: estado y reanudación','',
        '**Objetivo F1 macro 0,70: no alcanzado ni evaluado en V3.** No hay un modelo V3 entrenado ni se abrió S. Las fases C–G no se ejecutaron porque faltan datos y referencias suficientes.','',
        '## Fase A','',
        'Se conservaron los 591 originales y V2. H inicial tiene 591 unidades; H revisado tiene 590: seis recortes exactos corrigen mezcla de cabeceras, pies, notas y oraciones incompletas; una unidad queda pendiente por extracción/ambigüedad. No se cambiaron etiquetas. Se cotejaron diez históricos con sus PDF (30 revisados contando los 20 anteriores, límite 60). Los no revisados mantienen procedencia heredada. H final requiere excluir cualquier familia que finalmente se asigne a V/S.','',
        'Se incorporó la fase 07: cero ejecuciones completas y fallos de memoria conservados. Se reutilizaron su manifiesto de fuentes/contextos y los checkpoints A/B. Hay 27 resultados V2 completos inventariados, 108 registros de época y 24 inferencias nuevas sobre train de los controles con semilla 42.','',
        '| Condición V2, época 4 | F1 train, media 3 folds | F1 validación, media 3 folds |',
        '| --- | ---: | ---: |',
        *[f"| {c} | {s['train_macro_f1_mean']:.6f} | {s['validation_macro_f1_mean']:.6f} |" for c,s in summary.items()],
        '', 'La brecha respalda una dificultad de generalización. No demuestra que veinte épocas ayuden ni predice el resultado de V3. Estas cifras de época 4 difieren de la selección del mejor checkpoint y de los promedios de tres semillas anteriores.','',
        '## Fase B','',
        'Se obtuvieron cinco transcripciones públicas: dos reutilizadas y tres nuevas de más de 30 minutos. Se verificó duración mediante metadatos del video, se conservaron todos los cues y se registraron comienzo, final y huecos. La cobertura temporal no acredita fidelidad del reconocimiento. El clip de Rolando Rojas termina a mitad de intervención: cubre la carga de seis minutos, no la conferencia original.','',
        'Hay 123 candidatos temporales sin solape de cues (84 T y 39 V), ninguno supera 384 tokens. Son candidatos pendientes de revisión de límites discursivos. Además se conservaron 12 propuestas reales de primera pasada en los dos clips breves: cuatro sin problema identificado y ocho con ambigüedad/extracción pendiente. No son referencias aceptadas, no se simuló una segunda pasada ni independencia entre modelos.','',
        'La cobertura conseguida es de cuatro obras T y una V; no alcanza T300 ni la diversidad prevista. Hipólito Unanue queda en S con solo metadatos, junto con las reservas V2 intactas. T300/T600/V/S definitivos no están congelados. La concentración institucional y la cobertura de las siete clases siguen pendientes.','',
        'Tres candidatos carecen de subtítulos. El piloto de audio de Cádiz falló con HTTP 403 tras habilitar red. Se conservan ambos intentos (error de red restringida y rechazo 403); no se emplearon cookies, proxies ni mecanismos de evasión. No se pudo iniciar ASR ni medir su piloto.','',
        '## Presupuesto y siguiente paso','',
        f"V3: 0 trayectorias nuevas, 0 segundos GPU de entrenamiento y ASR; {usage['prior_checkpoint_inference_seconds_measured']:.1f} segundos medidos de inferencia diagnóstica. Doce unidades nuevas con propuesta sobre el máximo de 1.200. El tiempo de fallos V2 no está documentado suficientemente y permanece desconocido, separado del presupuesto nuevo; no se reinició ni se presenta como cero. No hubo servicios de pago.",
        '',
        '1. Incorporar otras grabaciones/transcripciones públicas accesibles, con duración, cue timestamps y obra identificada; priorizar otra validación independiente y crisis/Cádiz, participación social y organización republicana. El 403 registrado no autoriza reintentos de evasión.',
        '2. Añadir las fuentes a una nueva versión del registro antes de anotarlas; conservar roles de reproducciones y todas las reservas. Los archivos congelados se preservan: una ampliación requiere nuevos nombres/versiones.',
        '3. Resolver límites discursivos de los candidatos, completar las dos pasadas y adjudicación del plan, conservar casos irresolubles y calcular soporte/cobertura antes de inferir. La primera pasada disponible se reutiliza solo si coinciden texto y guía.',
        '4. Congelar H/T300/V y fuentes S; implementar/adaptar la ejecución declarativa R0–R3 del runner verificado antes de iniciar C. El runner V2 contiene cuatro épocas y LR fijo: no sirve para R2/R3 sin esa adaptación. No hay comparaciones V3 calculadas.',
        '',
        'Comprobación reproducible del estado actual:',
        '```powershell',
        'outputs/venv-ml/Scripts/python.exe scripts/check_beto_v3.py',
        'outputs/venv-ml/Scripts/python.exe scripts/check_beto_v3.py --require-C',
        '```',
        'El primer comando comprueba integridad. El segundo termina con código 2 mientras esta versión piloto no cumpla los prerrequisitos; no entrena ni consume reservas.',
        '',
        'Los scripts prepare_beto_v3.py, infer_beto_v3_prior_curves.py, review_beto_v3_historical_sources.py, finalize_beto_v3_historical_review.py, build_beto_v3_video_units.py, annotate_beto_v3_pilot.py y report_beto_v3.py reproducen las etapas preparadas y reutilizan resultados existentes.',
        '',
        'Fuente audiovisual institucional incorporada: [presentación de La república imaginada, IEP](https://iep.org.pe/noticias/video-presentacion-del-libro-la-republica-imaginada-representaciones-culturales-discursos-politicos-la-epoca-la-independencia/). Los enlaces individuales, hashes y errores están en artifacts/beto-v3/source-registry.json y outputs/beto-v3/acquisition/.',
    ]
    write(DOC/'progress.md',('\n'.join(lines)+'\n').encode('utf-8'))
    print(json.dumps({'diagnosis':summary,'usage':usage},ensure_ascii=True))

if __name__=='__main__':
    main()
