"""Current continuation report, preserving the existing progress.md location."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    art=ROOT/'artifacts/beto-v3/admission-01';out=ROOT/'outputs/beto-v3/admission-01'
    s=read(art/'current.json');gaps=read(art/'exact-gaps.json')['items']
    first={r['segment_id']:r for p in sorted((out/'first-pass').glob('batch-*.json')) for r in read(p)['items']}
    second={r['segment_id']:r for p in sorted((out/'second-review').glob('batch-*.json')) for r in read(p)['items']}
    agreements=sum(first[k]['proposal']==second[k]['proposal'] for k in first if k in second)
    table='| Clase V | Aceptadas | Meta | Faltan |\n|---|---:|---:|---:|\n'
    for r in gaps:
        if r['partition']=='V':table+=f"| {r['class']} | {r['accepted_from_30min_works']} | {r['target']} | {r['missing_examples']} |\n"
    text=f'''# BETO V3 — admisión 01 integrada; B pendiente, C y S cerradas

Estado vigente: [current.json](../../artifacts/beto-v3/admission-01/current.json). Se conserva [plan-beto-f1-070.md](plan-beto-f1-070.md). Dataset padre recovery-01 intacto; [progreso anterior](../../artifacts/beto-v3/admission-01/progress-before-admission.md). Rama `main`, commit `74f8091`; cambios locales anteriores preservados.

## Avance guardado

Dos obras V públicas TVPerú recuperadas: Reformas Borbónicas (N01, 3071 s) y Sánchez Carrión (`-Ma1tt97eFg`, 3009 s). Pistas AAC decodificadas completas; recibos Opus defectuosos conservados. Tres ventanas continuas de 375 s por obra, fijadas antes de transcribir: comienzo, centro y final. Procedencia/roles, duración, hashes, cues y solapamientos comprobados antes de la primera pasada; 30 objetivos, máximo 236 tokens, sin coincidencias exactas/12-gramas con H/desarrollo ni solapamiento entre candidatos. Esto es muestreo de tramos, no evaluación de videos completos.

**30 primeras pasadas, 30 segundas y 30 adjudicaciones: {s['new_accepted_references']} referencias nuevas V; 7 pendientes.** {agreements} acuerdos nominales y {30-agreements} discrepancias; no equivalen a exactitud. Primera sesión GPT-6 sin historial; segunda Codex CLI sin historial autorizada expresamente, modelo predeterminado no expuesto. No se afirma independencia entre modelos ni gold experto.

Totales: **T 426 (401 de obras largas), V {s['accepted_references']['V']}, auxiliares 14**. Pendientes: {s['pending_references']}. Cobertura resoluble V: {s['coverage']['V']['accepted']}/{s['coverage']['V']['units']} = {s['coverage']['V']['fraction']:.2%}; T 93,42%. Se conserva T con 214 no_relevante largas.

{table}
## Admisión y bloqueo exacto

G16/G17 admitidos como eventos distintos de 2018/2014, ambos T. Los huecos iniciales G13 (49,5 s), G16 (30,75 s), G18 (128,429 s) no invaden objetivos aceptados. Sus audios QA devolvieron HTTP 403: no se insistió, no se presume silencio y la comprobación auditiva permanece pendiente. [Informe por obra](../../artifacts/beto-v3/admission-01/source-admission-report.json). No se retiraron referencias anteriores ni se exige certificación experta.

Faltan **2 coloniales y 2 republicanas**, sin carencia de obras. Queda **1 entrada de desarrollo**, insuficiente para cuatro referencias nuevas; los pendientes carecen de resolución segura en los textos actuales. No gastar ese margen en un intento incapaz de cerrar las cuotas ni tomar las 200 de S. H/T/V y manifiesto S aún no se congelan.

## Presupuesto y entrenamiento

- **999/1200 entradas consumidas; quedan 201: 1 desarrollo + 200 S.** Revisiones idénticas no duplican entradas.
- ASR nuevo 99,3156064 s; acumulado **{s['ASR_gpu_seconds']:.7f}/28800 s**. GPU entrenamiento C/D y V3: **0**. US$0.
- Runner R0–R3 y TF-IDF preparado, entorno/base verificados. **Ningún R0–R3 ejecutado; no hay F1 ni checkpoints V3.** [Contrato y comandos](runner-phase-c.md); [verificación](../../artifacts/beto-v3/runner-preparation-01/verification.json).

## Reanudar sin reconstruir

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_admission.py --check-only
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/check_beto_v3.py --require-C
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/run_beto_phase_c_v3.py preflight
```

El primer comando debe pasar; las puertas C deben bloquear mientras falten admisión y cuotas. Sólo después del freeze válido: `run_beto_phase_c_v3.py run --recipe all`, seguido de `report`. No ejecutar integradores antiguos para reconstruir lotes: ahora verifican su snapshot y protegen la continuación.

Respuestas, audio, ASR y dataset: `outputs/beto-v3/admission-01/`; snapshots completos, ledger y eventos: `artifacts/beto-v3/admission-01/checkpoints/`. Estos resultados siguen locales; no se verificó respaldo externo ni se publicaron.

## Incidentes conservados

- Dos fronteras se editaron concurrentemente; se restauraron los objetivos realmente leídos y se corrigieron exclusivamente metadatos de sus respuestas. Los juicios no cambiaron; las variantes editadas no recibieron revisión. [Registro y snapshot](../../outputs/beto-v3/admission-01/first-pass/metadata-mismatch-snapshot/incident.json). Inputs ahora congelados contra nuevas ediciones.
- La revisión automática rechazó inicialmente CLI; la usuaria autorizó explícitamente paquete/destino y la ejecución posterior terminó. Un intento con tubería ASCII se canceló sin respuesta; se conservó y se sustituyó por envío exacto UTF-8. Uso expuesto de la sesión exitosa: 24763 tokens entrada (11776 cacheados), 4618 salida (197 razonamiento). Uso de otras sesiones/intento cancelado desconocido.
- La búsqueda devolvió incidentalmente un resumen de `zb5zntF2kAs`, reservado. No se abrió su página/audio/transcripción/etiquetas ni se utilizó el fragmento. **S sigue excluida y sin evaluación**; no se afirma aislamiento absoluto del buscador.
'''
    (ROOT/'docs/beto-v3/progress.md').write_text(text,encoding='utf-8')
    print('Updated existing docs/beto-v3/progress.md')
if __name__=='__main__':main()
