"""CPU-only contract checks; no model construction, training or S content access."""
import ast
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import torch

import beto_phase_c_core_v3 as core
import run_beto_phase_c_v3 as runner
from beto_effective_batch_loss import accumulation_batches


def function(source, name):
    return ast.dump(next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name))


def main():
    source = (runner.ROOT / 'scripts/run_beto_first_training_v2.py').read_text(encoding='utf-8')
    expected = source[source.index('def train_run('):source.index('\ndef inputs():')]
    changes = {
        'lr=2e-5,weight_decay=.01': "lr=protocol['execution']['lr'],weight_decay=.01",
        'total=steps*4;': "total=steps*protocol['execution']['epochs'];",
        "sorted(dest.glob('resume-epoch-*.pt'))": "sorted(dest.glob('resume-epoch-*.pt'), key=lambda p:int(p.stem.rsplit('-',1)[1]))",
        'range(start_epoch,5)': "range(start_epoch,protocol['execution']['epochs']+1)",
        '        train_loader,_=loader': '        budget_check()\n        train_loader,_=loader',
        '            targets=batch[-1].cuda()': '            budget_check()\n            targets=batch[-1].cuda()',
        "        history.append({'epoch':epoch": "        train_eval,train_keys=loader(train,tok,protocol['max_length'])\n        train_metrics=metrics(train,predict(model,train_eval,train_keys))\n        history.append({'train_metrics_eval':train_metrics,'epoch':epoch",
        "            save(checkpoint/'labels.json',": "            persist(checkpoint/'labels.json',",
        "        print(f'{dest.name}: epoch {epoch} F1(7)={score:.6f}',flush=True)": "        retain_latest(dest, epoch, best_epoch, protocol, history)\n        print(f'{dest.name}: epoch {epoch} F1(7)={score:.6f}',flush=True)",
    }
    for before, after in changes.items():
        assert expected.count(before) == 1, before
        expected = expected.replace(before, after)
    current = Path(core.__file__).read_text(encoding='utf-8')
    assert function(expected, 'train_run') == function(current, 'train_run'), 'Unexpected core drift'
    old_predict = source[source.index('def predict('):source.index('\ndef train_run(')]
    old_predict = old_predict.replace('        for batch in batches:\n', '        for batch in batches:\n            budget_check()\n')
    assert function(old_predict, 'predict') == function(current, 'predict')
    checks = ['AST core equals corrected V2 plus eight documented changes',
              'Prediction helper equals V2 plus budget polling']

    # An uneven final group is the case where division by fixed accumulation fails.
    targets = torch.tensor([0, 0, 1, 2, 3, 4, 5, 6, 6, 2, 1, 0, 5, 6, 4, 3, 2, 6, 1])
    weights = torch.tensor([.1, .5, .7, 1., 2., 3., 7.], dtype=torch.float64)
    logits = torch.arange(len(targets) * 7, dtype=torch.float64).reshape(-1, 7).sin()
    accumulated = logits.clone().requires_grad_()
    reference = logits.clone().requires_grad_()
    data = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.arange(len(targets)), targets), batch_size=2)
    for _, batch, denominator in accumulation_batches(data, 8, weights):
        (torch.nn.functional.cross_entropy(accumulated[batch[0]], batch[-1], weight=weights, reduction='sum') / denominator).backward()
    for start in range(0, len(targets), 16):
        torch.nn.functional.cross_entropy(reference[start:start+16], targets[start:start+16], weight=weights).backward()
    torch.testing.assert_close(accumulated.grad, reference.grad, rtol=1e-12, atol=1e-12)
    checks.append('Weighted accumulated gradients match full 16 + partial 3 batches to 1e-12')

    item = dict(segment_id='synthetic-check', family_id='synthetic-work', source_id='synthetic-source',
                text='synthetic check', input_sha256=hashlib.sha256(b'synthetic check').hexdigest(),
                accepted_label=runner.LABELS[0], partition='V', training_eligible=False, reference_eligible=True)
    row = runner.normalized_rows(dict(frozen=True, partition='V', items=[item]), 'V')[0]
    assert row['training_eligible'] is False
    for bad in ({**item, 'input_sha256': 'wrong'}, {**item, 'accepted_label': None}, {**item, 'reference_eligible': False}):
        try:
            runner.normalized_rows(dict(frozen=True, partition='V', items=[bad]), 'V')
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid reference accepted')
    checks.append('Hash corruption, unresolved labels and unadmitted references rejected; V remains nontraining')
    with patch.object(runner, 'FREEZE', runner.ART / 'never-created-contract-test.json'):
        with patch.object(core, 'train_run') as train:
            try:
                runner.frozen_inputs()
            except ValueError as exc:
                assert 'closed' in str(exc)
            else:
                raise AssertionError('Missing freeze accepted')
            train.assert_not_called()
    checks.append('Missing freeze rejected without training')
    _, environment = runner.preflight(False)
    return dict(status='passed', checks=checks, environment=environment,
                model_loaded=False, GPU_training_executed=False, S_opened=False,
                limitations=['No frozen dataset supplied: data admission unverified',
                             '20-epoch CUDA trajectory and checkpoint resume not executed',
                             'Budget interruption checked structurally, not by GPU fault injection'])


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
