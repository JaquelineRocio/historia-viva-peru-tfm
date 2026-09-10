"""Check weighted accumulation gradients and the full trainer against full batches."""
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
from beto_effective_batch_loss import accumulation_batches, train_epoch_trajectory
from beto_epoch_trajectory import train_epoch_trajectory as reference_train


def main():
    import torch
    import transformers
    from app.ml import beto_experiment
    destination = ROOT / 'outputs/beto-loss-normalization-v1-preflight.json'
    assert not destination.exists(), 'Do not overwrite a recorded preflight'
    checks = []
    torch.set_num_threads(4)
    weights = torch.tensor([.3, 2., 5.], dtype=torch.float64)
    for name, targets, batch_size, accumulation in [
        ('mixed', [0, 1, 2, 0, 1, 2, 2, 0], 2, 4),
        ('homogeneous_microbatches', [0, 0, 1, 1, 2, 2], 2, 3),
        ('singletons', [0, 1, 2, 0, 2], 1, 4),
        ('odd_partial_last_group', [0, 1, 2, 0, 2, 1, 0, 0, 2, 1, 2], 2, 4),
    ]:
        targets = torch.tensor(targets)
        torch.manual_seed(19)
        source = torch.randn(len(targets), 3, dtype=torch.float64)
        data = torch.utils.data.TensorDataset(torch.arange(len(targets)), targets)
        for weight_scale in (1., 7.):
            w = weights * weight_scale
            logits = source.clone().requires_grad_()
            reference = source.clone().requires_grad_()
            loader = torch.utils.data.DataLoader(data, batch_size=batch_size)
            candidate_loss = torch.zeros((), dtype=torch.float64)
            for _, batch, denominator in accumulation_batches(loader, accumulation, w):
                loss = torch.nn.functional.cross_entropy(logits[batch[0]], batch[-1], weight=w, reduction='sum') / denominator
                candidate_loss += loss.detach()
                loss.backward()
            reference_loss = torch.zeros((), dtype=torch.float64)
            for start in range(0, len(targets), batch_size * accumulation):
                end = start + batch_size * accumulation
                loss = torch.nn.functional.cross_entropy(reference[start:end], targets[start:end], weight=w)
                reference_loss += loss.detach()
                loss.backward()
            torch.testing.assert_close(candidate_loss, reference_loss, rtol=1e-12, atol=1e-12)
            torch.testing.assert_close(logits.grad, reference.grad, rtol=1e-12, atol=1e-12)
            if weight_scale == 1:
                unscaled_grad = logits.grad.clone()
            else:
                torch.testing.assert_close(logits.grad, unscaled_grad, rtol=1e-12, atol=1e-12)
        checks.append(name + ': loss, gradients, weight-scale invariance')

    x = torch.tensor([[2., 0., -1.], [0., 1., 2.], [0., 1., 0.], [2., 0., 1.]], dtype=torch.float64, requires_grad=True)
    y = torch.tensor([0, 0, 2, 2])
    legacy = sum(torch.nn.functional.cross_entropy(x[i:i+2], y[i:i+2], weight=weights) / 2 for i in (0, 2))
    full = torch.nn.functional.cross_entropy(x, y, weight=weights)
    legacy_grad = torch.autograd.grad(legacy, x, retain_graph=True)[0]
    full_grad = torch.autograd.grad(full, x)[0]
    assert not torch.allclose(legacy_grad, full_grad)
    checks.append('Historical formula differs in mixed-class accumulation group')

    # Prefetch must not alter row order or the model RNG stream for our loader.
    def sequence(prefetch):
        torch.manual_seed(42)
        data = torch.utils.data.TensorDataset(torch.arange(35), torch.arange(35) % 3)
        loader = torch.utils.data.DataLoader(data, batch_size=2, shuffle=True,
            generator=torch.Generator().manual_seed(42), num_workers=0)
        batches = accumulation_batches(loader, 8, weights) if prefetch else ((i, b, None) for i, b in enumerate(loader))
        return [(b[0].tolist(), torch.rand(4).tolist()) for _, b, _ in batches]
    assert sequence(False) == sequence(True)
    checks.append('Prefetch preserves seeded TensorDataset order and model RNG stream')

    models, optimizers = [], []
    adamw = torch.optim.AdamW

    class Optimizer(adamw):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.rates, self.gradients = [], []
            optimizers.append(self)

        def step(self, *args, **kwargs):
            self.rates.append(self.param_groups[0]['lr'])
            self.gradients.append([p.grad.clone() for group in self.param_groups for p in group['params']])
            return super().step(*args, **kwargs)

    class Tokenizer:
        def __call__(self, texts, **kwargs):
            return dict(input_ids=torch.tensor([[int(t) % 17 + 1] * 8 for t in texts]),
                attention_mask=torch.ones(len(texts), 8, dtype=torch.long))

        def save_pretrained(self, path):
            (Path(path) / 'fixture-tokenizer.json').write_text('{}', encoding='utf-8')

    class Model(torch.nn.Module):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.embedding = torch.nn.Embedding(19, 6)
            self.head = torch.nn.Linear(6, kwargs['num_labels'])
            self.config = SimpleNamespace(_commit_hash='synthetic')
            self.saved = None
            models.append(self)

        def gradient_checkpointing_enable(self):
            pass

        def forward(self, input_ids, attention_mask):
            return SimpleNamespace(logits=self.head(self.embedding(input_ids).mean(1)))

        def save_pretrained(self, path, safe_serialization):
            self.saved = {k: v.detach().clone() for k, v in self.state_dict().items()}

    labels = ['a', 'b', 'c']
    rows = [dict(text=str(i), label=labels[0 if i < 3 else 1 if i < 12 else 2]) for i in range(35)]
    params = dict(lr=2e-5, epochs=3, batch_size=2, gradient_accumulation_steps=8, max_len=8)
    config = dict(base_model='fixture', revision='fixture', seed=42, allow_cpu=True)
    folder = Path(tempfile.mkdtemp(prefix='beto-loss-fixture-', dir=ROOT / 'outputs'))
    with patch.object(torch.cuda, 'is_available', return_value=False), \
         patch.object(transformers.AutoTokenizer, 'from_pretrained', side_effect=lambda *a, **kw: Tokenizer()), \
         patch.object(transformers.AutoModelForSequenceClassification, 'from_pretrained', side_effect=Model), \
         patch.object(torch.optim, 'AdamW', Optimizer), \
         patch.object(beto_experiment, '_predict', side_effect=AssertionError('No training inference')):
        candidate = train_epoch_trajectory(rows, labels, params, config, folder / 'candidate', (2,))
        reference = reference_train(rows, labels, dict(params, batch_size=16, gradient_accumulation_steps=1), config, folder / 'reference', (2,))
    assert optimizers[0].rates == optimizers[1].rates and len(optimizers[0].rates) == 6
    for ga, gb in zip(optimizers[0].gradients, optimizers[1].gradients):
        for a, b in zip(ga, gb):
            torch.testing.assert_close(a, b, rtol=2e-5, atol=2e-7)
    for key in models[0].saved:
        torch.testing.assert_close(models[0].saved[key], models[1].saved[key], rtol=2e-5, atol=2e-7)
    for key in ('class_counts', 'class_weights', 'optimizer_updates', 'skipped_updates',
                'schedule_total_steps', 'warmup_steps', 'checkpoint_epochs', 'effective_batch_size'):
        assert candidate[key] == reference[key], key
    checks.append('Full CPU trainer: gradients, final weights, six updates and schedule match physical batches of16 including final3 rows; dropout absent')
    write(destination, dict(status='passed', checks=checks, torch_version=torch.__version__,
        trainer_sha256=sha(ROOT / 'scripts/beto_effective_batch_loss.py'),
        checker_sha256=sha(Path(__file__)), historical_formula_loss=legacy.item(),
        effective_group_loss=full.item(), limitation='CPU fixtures establish objective equivalence for fixed logits. No claim of bitwise CUDA AMP/dropout equivalence or improved historical classification.'))
    print(json.dumps(dict(status='passed', checks=checks), indent=2))


if __name__ == '__main__':
    main()
