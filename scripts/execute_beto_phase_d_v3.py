"""Exactly four sequential D trajectories using the existing C runner."""
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import run_beto_phase_c_v3 as r


def main():
    audit = r.ART / 'phase-d'
    audit.mkdir(exist_ok=True)
    for source in [r.ART/'budget-ledger-after-C.json', r.ART/'development-current.json',
                   r.ROOT/'docs/beto-v3/progress.md', r.FREEZE]:
        target = audit/'before'/source.name
        target.parent.mkdir(exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
    prior = r.read(audit/'before/budget-ledger-after-C.json')
    assert prior['new_training_trajectories'] == 4
    for entry in prior['attempts']:
        r.pinned(entry)
    _, rows = r.frozen_inputs()
    for recipe in ('R0', 'R2'):
        dest = r.OUT/'seed-42'/recipe
        r.verify_result(dest, r.read(dest/'config.json'), rows['V'])
    r.core.persist(audit/'start.json', dict(started_utc=datetime.now(timezone.utc).isoformat(),
        free_bytes=shutil.disk_usage(r.ROOT).free, before_ledger_sha256=r.filehash(audit/'before/budget-ledger-after-C.json'),
        new_runs=[[recipe, seed] for seed in (43,44) for recipe in ('R0','R2')],
        retention='New runs only: all epoch metrics, best checkpoint, latest full resume; commit resume before cleanup',
        backup='Local immutable metadata snapshots in artifacts/beto-v3/phase-d/before; model artifacts in outputs/beto-v3/phase-c. No external backup verified.', S_opened=False)) if not (audit/'start.json').exists() else None
    state = r.read(r.ART/'development-current.json')
    state.update(status='D_running', phase_D_audit='artifacts/beto-v3/phase-d', S_closed=True)
    temporary = r.ART/'development-current.json.tmp'
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(r.ART/'development-current.json')
    for seed in (43,44):
        for recipe in ('R0','R2'):
            log = audit/f'{recipe}-seed-{seed}.log'
            with log.open('a', encoding='utf-8') as handle:
                subprocess.run([sys.executable, '-X', 'utf8', str(r.ROOT/'scripts/run_beto_phase_c_v3.py'),
                                'run', '--recipe', recipe, '--seed', str(seed)],
                               stdout=handle, stderr=subprocess.STDOUT, check=True, cwd=r.ROOT)
            print(f'Completed {recipe}/{seed}', flush=True)


if __name__ == '__main__':
    main()
