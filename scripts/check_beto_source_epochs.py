"""Synthetic CPU checks of trajectory preservation and TRAIN group isolation."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'apps/ml')]
from compare_beto_length import sha, write
import compare_beto_source_epochs as runner
from beto_epoch_trajectory import train_epoch_trajectory
from beto_fixed_epoch import train_fixed_epoch


def main():
    import torch
    import transformers
    from app.ml import beto_experiment
    destination = ROOT / 'outputs/beto-source-epochs-v1-preflight.json'
    if destination.exists():
        raise ValueError('Preflight already recorded; do not overwrite')
    folder = Path(tempfile.mkdtemp(prefix='beto-source-epochs-fixture-', dir=ROOT / 'outputs'))
    models, optimizers, checks = [], [], []
    adamw = torch.optim.AdamW

    class Optimizer(adamw):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.rates = []
            optimizers.append(self)

        def step(self, *args, **kwargs):
            self.rates.append(self.param_groups[0]['lr'])
            return super().step(*args, **kwargs)

    class Tokenizer:
        def __call__(self, texts, **kwargs):
            assert kwargs == dict(truncation=True, padding='max_length', max_length=8, return_tensors='pt')
            return dict(input_ids=torch.tensor([[int(text) % 17 + 1] * 8 for text in texts]),
                        attention_mask=torch.ones(len(texts), 8, dtype=torch.long))

        def save_pretrained(self, path):
            (Path(path) / 'fixture-tokenizer.json').write_text('{}', encoding='utf8')

    class Model(torch.nn.Module):
        def __init__(self, *args, **kwargs):
            super().__init__()
            assert kwargs['local_files_only'] is True
            self.embedding = torch.nn.Embedding(19, 6)
            self.dropout = torch.nn.Dropout(.3)
            self.head = torch.nn.Linear(6, kwargs['num_labels'])
            self.config = SimpleNamespace(_commit_hash='synthetic')
            self.epoch = 0
            self.saved = {}
            models.append(self)

        def gradient_checkpointing_enable(self):
            self.checkpointing = True

        def train(self, mode=True):
            assert mode, 'Trainer must not perform inference'
            self.epoch += 1
            return super().train(mode)

        def forward(self, input_ids, attention_mask):
            return SimpleNamespace(logits=self.head(self.dropout(self.embedding(input_ids).mean(1))))

        def save_pretrained(self, path, safe_serialization):
            assert safe_serialization
            self.saved[self.epoch] = {k: v.detach().clone() for k, v in self.state_dict().items()}

    labels = [runner.IDEAS, 'other']
    train = [dict(text=str(i), label=labels[int(i % 4 != 0)]) for i in range(35)]
    params = dict(runner.PARAMS, max_len=8)
    config = dict(seed=42, base_model='synthetic', revision='synthetic', allow_cpu=True)
    with patch.object(torch.cuda, 'is_available', return_value=False), \
         patch.object(transformers.AutoTokenizer, 'from_pretrained', side_effect=lambda *a, **kw: Tokenizer()), \
         patch.object(transformers.AutoModelForSequenceClassification, 'from_pretrained', side_effect=Model), \
         patch.object(torch.optim, 'AdamW', Optimizer), \
         patch.object(beto_experiment, '_predict', side_effect=AssertionError('No inference in trajectory')):
        old2 = train_fixed_epoch(train, labels, params, config, folder / 'old2', 2)
        old3 = train_fixed_epoch(train, labels, params, config, folder / 'old3', 3)
        with patch.object(beto_experiment, '_loader', wraps=beto_experiment._loader) as loader:
            new = train_epoch_trajectory(train, labels, params, config, folder / 'new', (2, 3))
            assert loader.call_count == 1
        assert list(models[2].saved) == [2, 3] and len(optimizers) == 3
        for epoch, baseline in [(2, 0), (3, 1)]:
            assert all(torch.equal(tensor, models[2].saved[epoch][key])
                       for key, tensor in models[baseline].saved[epoch].items())
        checks.append('epoch2_and_epoch3_weights_bitwise_equal_to_unmodified_trainer')
        assert optimizers[0].rates == optimizers[2].rates[:6]
        assert optimizers[1].rates == optimizers[2].rates and len(optimizers[2].rates) == 9
        assert new['history'][:2] == old2['history'] and new['history'] == old3['history']
        checks.append('same_optimizer_learning_rates_losses_and_update_counts')
        assert new['checkpoint_saves'] == 2 and new['scheduler_steps'] == 9
        assert new['skipped_updates'] == 0 and new['schedule_total_steps'] == 9
        assert all(x['microbatches'] == 18 for x in new['history'])
        checks.append('odd_last_microbatch_and_incomplete_accumulation_group_preserved')
        assert all(m.checkpointing for m in models)
        checks.append('single_loader_optimizer_and_no_inference_between_epochs')
        before = len(models)
        for bad in [(), (3, 2), (2, 2), (True, 3), (2, 4)]:
            try:
                train_epoch_trajectory(train, labels, params, config, folder / 'invalid', bad)
            except ValueError:
                pass
            else:
                raise AssertionError('Accepted invalid epochs')
        assert len(models) == before and not (folder / 'invalid').exists()
        checks.append('invalid_epoch_declarations_rejected_before_model_load')

    # These rows carry only synthetic text, including the held documentary partner.
    rows = [dict(split='train', resourceId=source, text=f'unique row {j} label {i}', label=label)
            for j, source in enumerate([runner.OPHELAN, runner.HUAMANGA, runner.MORAN, 'remaining'])
            for i, label in enumerate(labels)]
    folds = runner.make_folds(rows, labels)
    assert folds[0]['held_indices'] == [0, 1, 2, 3] and folds[0]['primary_indices'] == [0, 1]
    assert not {runner.OPHELAN, runner.HUAMANGA} & {rows[i]['resourceId'] for i in folds[0]['fit_indices']}
    checks.append('whole_dependent_work_group_is_excluded_and_primary_separate')
    sentinel = dict(split='test')
    assert runner.train_only(dict(items=rows + [sentinel])) == list(enumerate(rows))
    checks.append('evaluation_content_not_accessed_by_train_filter')
    for name, broken in [
        ('non_train_rejected', [dict(rows[0], split='val')] + rows[1:]),
        ('cross_partition_duplicate_rejected', rows[:-1] + [dict(rows[-1], text=rows[0]['text'])]),
        ('absent_fit_class_rejected', [dict(r, label=labels[0]) if r['resourceId'] not in
                                      [runner.OPHELAN, runner.HUAMANGA] else r for r in rows]),
    ]:
        try:
            runner.make_folds(broken, labels)
        except ValueError:
            checks.append(name)
        else:
            raise AssertionError(name)
    with patch.object(runner, 'OUTPUT', folder), patch.object(runner, 'inputs') as load:
        try:
            runner.run()
        except ValueError:
            pass
        else:
            raise AssertionError('Existing run accepted')
        load.assert_not_called()
    checks.append('existing_run_rejected_before_loading_or_training')
    # Fixed decision branches must use primary-work ideas, not secondary work gains.
    def fake(fit, primary):
        return {'epochs': {str(e): {s: {'labels': labels, 'confusion_matrix': [[v, 0], [0, 0]]}
                                   for s, v in [('fit', fit[e - 2]), ('primary', primary[e - 2])]}
                           for e in [2, 3]}}
    assert runner.decision({'a': fake([1, 2], [0, 1]), 'b': fake([1, 2], [0, 1])})['status'].startswith('exploratory')
    assert runner.decision({'a': fake([1, 2], [1, 0]), 'b': fake([1, 2], [1, 1])})['status'] == 'transfer_difficulty_persists'
    assert runner.decision({'a': fake([1, 1], [0, 1]), 'b': fake([1, 2], [0, 1])})['status'] == 'inconclusive_or_work_dependent'
    checks.append('predeclared_decision_branches_use_fit_and_primary_work')
    result = dict(status='passed', checks=checks, check_count=len(checks), synthetic_rows=35,
                  real_BETO_training_performed=False, historical_texts_used=False, network_calls=False,
                  limits='CPU synthetic checks do not certify CUDA numerical equality or AMP overflow behavior.',
                  trainer_sha256=sha(ROOT / 'scripts/beto_epoch_trajectory.py'),
                  runner_sha256=sha(ROOT / 'scripts/compare_beto_source_epochs.py'))
    write(folder / 'report.json', result)
    write(destination, result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
