"""Focused CPU checks for D restrictions and bounded retention."""
import tempfile
from pathlib import Path
from unittest.mock import patch
import beto_phase_c_core_v3 as core
import run_beto_phase_c_v3 as runner


def main():
    for recipe, seed in [('all',43),('R1',43),('R3',44),('R0',45)]:
        with patch.object(runner, 'preflight') as preflight:
            try:
                runner.run(recipe,seed)
            except ValueError:
                pass
            else:
                raise AssertionError('Unapproved D run accepted')
            preflight.assert_not_called()
    with tempfile.TemporaryDirectory(dir=runner.ROOT/'outputs') as temporary:
        root = Path(temporary)
        dest = root/'outputs/beto-v3/phase-c/seed-43/R2'
        dest.mkdir(parents=True)
        for epoch in (1,2):
            (dest/f'resume-epoch-{epoch}.pt').write_bytes(b'test-state')
            (dest/f'checkpoint-{epoch}').mkdir()
            (dest/f'checkpoint-{epoch}/model').write_bytes(b'test-model')
        protocol = dict(execution=dict(retention='best_and_latest'))
        with patch.object(core,'ROOT',root):
            core.retain_latest(dest,2,1,protocol,[dict(epoch=1),dict(epoch=2)])
            assert (dest/'checkpoint-1/model').exists()
            assert not (dest/'checkpoint-2').exists()
            assert (dest/'resume-epoch-2.pt').exists()
            assert not (dest/'resume-epoch-1.pt').exists()
            assert len(core.read(dest/'history.json')) == 2
            old = root/'outputs/beto-v3/phase-c/seed-42/R2'
            old.mkdir(parents=True)
            try:
                core.retain_latest(old,2,1,protocol,[])
            except ValueError:
                pass
            else:
                raise AssertionError('Retention allowed on seed 42')
    print('PASS: only R0/R2 seeds 43/44 admitted; latest resume and earlier best retained; seed 42 protected. No training.')


if __name__ == '__main__':
    main()
