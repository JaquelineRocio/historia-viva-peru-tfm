"""Human-readable closeout from validated saved results, no training or inference."""
import json,csv,hashlib
from pathlib import Path
from datetime import datetime,timezone
from finalize_beto_v3_resume import ROOT,BASE,META,ART,read,save,digest
def main():
 if (ART/'phase-b-gap-02/review-integration.json').exists():
  from integrate_beto_v3_gap_reviews import main as integrated
  return integrated(check_only=True)
 s=read(META/'resume-summary.json');ledger=read(ART/'budget-ledger-current.json')
 coverage=list(csv.DictReader((META/'coverage-by-class.csv').open(encoding='utf-8-sig')))
 source_registry=read(META/'source-registry-final.json');new=read(BASE/'all-development-units.json')['items']
 credit_frames=['credits-1020.jpg','credits-1030.jpg','credits-1040.jpg','credits-1050.jpg','credits-1065.jpg']
 addendum={'at_utc':datetime.now(timezone.utc).isoformat(),'S_content_accessed':False,'N03_visual_credit_observations':{'director_and_writer':'Augusto Tamayo','executive_production':'Nathalie Hendrickx','production_company':'ARGOS Producciones Audiovisuales','acknowledgements_observed':['Jaime Avalos / OEI','Margarita Guerra / Instituto Riva Agüero PUCP','Amalia Castelli','Luis Cavagnaro','José Agustín de la Puente','Hugo de Zela','Alan Torrico'],'evidence':[{'path':str((BASE/'new-sources/N03'/f).relative_to(ROOT)),'sha256':digest(BASE/'new-sources/N03'/f)} for f in credit_frames],'interpretation':'No adaptation of S16 identified in sampled credits; distinct authorship observed. Same topic alone does not establish reproduction. N03 remains auxiliary and excluded from primary evaluation by duration.'},'development_text_comparison':{'path':str((META/'new-transcript-overlap.json').relative_to(ROOT)),'sha256':digest(META/'new-transcript-overlap.json'),'result':'No substantial exact eight-word overlap detected with H/current T/V or between new sources; ASR differences may conceal overlap, so this is screening, not proof.'}}
 save(META/'new-source-relations-addendum.json',addendum)
 for source in source_registry['new_candidates']:
  sid=source['source_id'];rows=[r for r in new if r['source_id']==sid]
  if not rows:continue
  source.update(ASR_units=len(rows),first_pass_units=sum('first_pass' in r for r in rows),second_review_units=sum('second_review' in r for r in rows),accepted_reference_units=sum(r['accepted_label'] is not None for r in rows),pending_reference_units=sum(r['accepted_label'] is None for r in rows),status='downloaded_transcribed_reviewed_pending_corpus_gate',final_role='auxiliary_quarantine' if sid=='N03' else ('V_provisional' if sid=='N07' else 'T_short_work_provisional'),relation_review='Metadata, development-text overlap and N03 sampled credits checked; no reproduction identified; limitations in relation receipts',training_eligible=False)
  source['next_action']='Resolve saved pending/quality cases and complete corpus coverage; N03 cannot supply primary V references'
 source_registry['continuation_report']='docs/beto-v3/fase-B-lote-completo.md';source_registry['new_source_relations_addendum']='artifacts/beto-v3/phase-b-completion-01/new-source-relations-addendum.json';save(META/'source-registry-final.json',source_registry)
 chunks=[read(p) for p in (BASE/'new-sources').glob('*/asr/*.json') if p.name.startswith(('chunk-','pilot-')) and read(p).get('complete')]
 memory={'max_process_rss_bytes':max(r['memory_peak']['rss_bytes'] for r in chunks),'max_device_used_mib_including_other_processes':max(r['memory_peak']['gpu_device_used_mib'] for r in chunks)}
 asr={'model':'Systran/faster-whisper-small','revision':'536b0662742c02347bc0e980a01041f333bce120','model_manifest_sha256':digest(META/'asr-model-manifest.json'),'completed_calls':len(chunks),'complete_sources':3,'source_audio_seconds':sum(read(BASE/'new-sources'/sid/'download.json')['duration_seconds'] for sid in ['N03','N07','N08']),'measured_transcription_wall_seconds':sum(r['wall_seconds'] for r in chunks),'cumulative_GPU_budget_seconds_including_model_loading':ledger['ASR_gpu_seconds'],'GPU_ceiling_seconds':28800,'memory':memory,'paid_USD':0,'all_audio_and_video_decode_ok':all(read(BASE/'new-sources'/sid/'download.json').get('video_decode_complete') and read(BASE/'new-sources'/sid/'download.json')['integrity_decode_ok'] for sid in ['N03','N07','N08']),'transcription_fidelity':'Automatic ASR, not a certified verbatim transcript; gaps and boundary defects preserved in quality receipts'}
 save(META/'asr-summary.json',asr)
 names={'contexto_colonial_antecedentes':'Colonial','crisis_ideas_emancipadoras':'Crisis e ideas','campanias_conflictos_militares':'Campañas','liderazgos_diplomacia_proyectos':'Liderazgos','organizacion_consecuencias_republicanas':'República','participacion_social_regional':'Participación','no_relevante':'No relevante'}
 rows={r['class']:r for r in coverage}
 table='| Clase | T aceptadas | V aceptadas | Faltan T / V* |\n|---|---:|---:|---:|\n'
 for key,name in names.items():
  r=rows[key];table+=f'| {name} | {r["T_accepted"]} | {r["V_accepted"]} | {max(0,20-int(r["T_accepted"]))} / {max(0,25-int(r["V_accepted"]))} |\n'
 report=f'''# Fase B: revisión y ASR completados; C cerrada

Los **69 pendientes originales** recibieron revisión ciega en tres contextos sin historial: 57 acuerdos y 12 discrepancias. Tras adjudicar, el lote original tiene **115 aceptados y 10 pendientes**. Ambas pasadas declaran GPT-6, con pesos desconocidos: consistencia entre sesiones, no independencia entre modelos ni exactitud experta.

Se descargaron y decodificaron audio/video completos de **N07 (1:33:57), N08 (23:19) y N03 (18:01)**. Whisper small procesó los 135 minutos. Piloto: 60 s en 2,77 s; ASR acumulado: **{ledger['ASR_gpu_seconds']:.2f} s / 28.800 s**. Memoria máxima: {memory['max_process_rss_bytes']/1048576:.1f} MiB del proceso; {memory['max_device_used_mib_including_other_processes']} MiB de GPU, incluyendo otros procesos. Huecos y defectos ASR conservados; fidelidad literal no certificada.

Las **110 unidades nuevas** (N07: 76; N08: 19; N03: 15) tienen ambas pasadas y adjudicación. Total: **93 T, 99 V y 14 auxiliares aceptadas; 29 pendientes**. N03 permanece fuera de evaluación principal. T incluye 25 referencias de obras cortas: **68 T** proceden de obras ≥30 minutos. No se rebajó esa meta ni se habilitó entrenamiento.

{table}
*Metas por clase: 20 T y 25 V; dos obras. [Carencias por clase/obra/partición](../../artifacts/beto-v3/phase-b-completion-01/exact-gaps.csv); [carencias contando solo obras ≥30 minutos](../../artifacts/beto-v3/phase-b-completion-01/exact-gaps-30min-works.csv); [cantidades por obra](../../artifacts/beto-v3/phase-b-completion-01/coverage-by-work.csv).

Faltan **207 referencias T y 101 V** para 300/200; con obras ≥30 minutos faltan 232 T. V carece de militares y tiene antecedentes coloniales de una sola obra. Cobertura resoluble: T 89,42%; V 85,34%. Obras largas transcritas: T 2/12, V 2/6; S registra 1/6. Faltan congelación y admisión final de fuentes/datasets. No se detectaron reproducciones; las limitaciones están documentadas.

**US$0. {ledger['new_unique_annotation_proposals']}/1.200 inputs acumulados; quedan {ledger['annotation_budget_remaining']}. Entrenamientos V3: 0.** `check_beto_v3.py --require-C` devolvió 2: integridad aprobada, cobertura insuficiente. R0–R3 no se ejecutaron; S cerrada.

Archivos: [29 casos pendientes](../../outputs/beto-v3/phase-b-completion-01/pending-resolution.json), [lotes externos ciegos](../../outputs/beto-v3/phase-b-completion-01/external-review/current.json) y [calidad ASR](../../outputs/beto-v3/phase-b-completion-01/ASR-quality-review.json). Transcripciones SRT/JSON: `outputs/beto-v3/phase-b-completion-01/new-sources/N*/asr/`.

Recalcular estado sin transcribir ni entrenar:
```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/finalize_beto_v3_resume.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/check_beto_v3.py --require-C
```
'''
 target=ROOT/'docs/beto-v3/fase-B-lote-completo.md';previous=target.parent/'fase-B-lote-completo-before-resume.md'
 if not previous.exists():previous.write_bytes(target.read_bytes())
 target.write_text(report,encoding='utf-8')
 progress=ROOT/'docs/beto-v3/progress.md';archive=progress.parent/'progress-before-resume.md'
 if not archive.exists():archive.write_bytes(progress.read_bytes())
 progress.write_text('# Estado V3\n\nFase B reanudada: 93 T y 99 V aceptadas, 14 auxiliares, 29 pendientes. C bloqueada por cobertura; S cerrada. 0 entrenamientos nuevos, US$0.\n\nEstado y comandos: [fase-B-lote-completo.md](fase-B-lote-completo.md). Detalle ejecutable: `artifacts/beto-v3/phase-b-completion-01/resume-summary.json`.\n',encoding='utf-8')
 print(json.dumps({'report':str(target.relative_to(ROOT)),'accepted':s['accepted_references'],'ASR_seconds':ledger['ASR_gpu_seconds'],'annotation_inputs':ledger['new_unique_annotation_proposals']}))
if __name__=='__main__':main()
