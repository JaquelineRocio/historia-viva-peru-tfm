"""Portable three-seed baseline. Only train.jsonl and dev.jsonl are consumed."""
import argparse
import gc
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
from collections import Counter
from itertools import islice
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def validate_data(root):
    root = Path(root)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        assert sha(root / name) == expected, f'Changed portable file: {name}'
    rows = {split: [json.loads(s) for s in (root / f'{split}.jsonl').read_text(encoding='utf-8').splitlines()]
            for split in ('train', 'dev')}
    labels = manifest['labels']
    assert len(labels) == len(set(labels)) == 7
    for split, items in rows.items():
        assert len(items) == manifest['scope'][split]
        for key in ('id', 'text_sha256'):
            assert len({r[key] for r in items}) == len(items)
        for r in items:
            assert r['split'] == split and r['label'] in labels
            assert hashlib.sha256(r['text'].encode('utf-8')).hexdigest() == r['text_sha256']
    overlap = {}
    for key in ('id', 'text_sha256', 'family', 'component', 'source_id'):
        overlap[key] = sorted({r[key] for r in rows['train']} & {r[key] for r in rows['dev']})
        assert not overlap[key], f'TRAIN/DEV overlap: {key}'
    counts = Counter(r['label'] for r in rows['train'])
    assert dict(counts) == manifest['class_counts']
    return manifest, rows, overlap


class Stopping:
    def __init__(self):
        self.best = -math.inf
        self.anchor = -math.inf
        self.bad = 0
        self.best_epoch = None

    def update(self, score, epoch):
        assert math.isfinite(score)
        improved = score > self.best
        if improved:
            self.best, self.best_epoch = score, epoch
        if score > self.anchor + 1e-4:
            self.anchor, self.bad = score, 0
        else:
            self.bad += 1
        return improved, self.bad >= 2


def amp_update(model, optimizer, scaler, scheduler):
    """Let GradScaler observe nonfinite gradients and recover its scale normally."""
    import torch
    scaler.unscale_(optimizer)
    params = [p for p in model.parameters() if p.grad is not None]
    finite = all(bool(torch.isfinite(p.grad).all()) for p in params)
    # Do not clip NaNs/Infs: scaler.step will skip after unscale_ detected them.
    norm = None
    if finite:
        # Float64 norm avoids overflow of the norm of finite float32 gradients.
        norm = torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(p.grad.double()) for p in params]))
        coefficient = min(1., 1. / (float(norm) + 1e-6))
        for p in params:
            p.grad.mul_(coefficient)
    previous = scaler.get_scale()
    scaler.step(optimizer)
    scaler.update()
    current = scaler.get_scale()
    skipped = current < previous
    if not skipped:
        scheduler.step()
    optimizer.zero_grad(set_to_none=True)
    return {'skipped': skipped, 'scale_before': previous, 'scale_after': current,
            'finite_gradients': finite, 'gradient_norm': float(norm) if norm is not None else None}


def train_epoch(model, loader, keys, weights, optimizer, scaler, scheduler, device, emit, epoch):
    import torch
    model.train()
    optimizer.zero_grad(set_to_none=True)
    iterator = iter(loader)
    numerator_sum = denominator_sum = 0.
    nonfinite_losses = skipped = attempts = 0
    while group := list(islice(iterator, 8)):
        denominator = weights[torch.cat([b[-1] for b in group]).to(device)].sum()
        ids = []
        for batch in group:
            ids.extend(batch[-2].tolist())
            inputs = {key: batch[i].to(device) for i, key in enumerate(keys)}
            y = batch[-1].to(device)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == 'cuda'):
                logits = model(**inputs).logits
            numerator = torch.nn.functional.cross_entropy(logits.float(), y, weight=weights, reduction='sum')
            # No early abort on AMP overflow: backward -> unscale -> step -> update.
            scaler.scale(numerator / denominator).backward()
            if bool(torch.isfinite(numerator)):
                numerator_sum += float(numerator.detach())
                denominator_sum += float(weights[y].sum())
            else:
                nonfinite_losses += 1
        event = amp_update(model, optimizer, scaler, scheduler)
        attempts += 1
        skipped += int(event['skipped'])
        emit({'epoch': epoch, 'attempt_in_epoch': attempts, 'train_row_indices': ids,
              'lr_after': optimizer.param_groups[0]['lr'], **event})
    return {'loss': numerator_sum / denominator_sum if denominator_sum else None,
            'loss_definition': 'sum weighted CE / sum target weights; finite observed microbatches',
            'nonfinite_loss_microbatches': nonfinite_losses, 'attempts': attempts,
            'updates': attempts - skipped, 'amp_skips': skipped}


def scores(truth, probs):
    import numpy as np
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
    probs = np.asarray(probs)
    assert probs.shape == (len(truth), 7) and np.isfinite(probs).all()
    assert np.allclose(probs.sum(1), 1., atol=1e-6)
    p, r, f, n = precision_recall_fscore_support(truth, probs.argmax(1), labels=list(range(7)), zero_division=0)
    return {'macro_f1': float(f.mean()), 'accuracy': float(accuracy_score(truth, probs.argmax(1))),
            'per_class': [{'precision': float(p[i]), 'recall': float(r[i]), 'f1': float(f[i]), 'support': int(n[i])} for i in range(7)],
            'confusion_matrix': confusion_matrix(truth, probs.argmax(1), labels=list(range(7))).tolist(),
            'nll': float(-np.log(np.maximum(probs[np.arange(len(truth)), truth], 1e-15)).mean())}


def predict(model, loader, keys, device):
    import torch
    model.eval()
    probs, truth = [], []
    # FP32 DEV, matching the control; no stochastic dropout or AMP evaluation.
    with torch.inference_mode():
        for batch in loader:
            logits = model(**{key: batch[i].to(device) for i, key in enumerate(keys)}).logits
            probs.extend(logits.float().softmax(-1).cpu().tolist())
            truth.extend(batch[-1].tolist())
    return truth, probs


def summarize(results, labels):
    import numpy as np
    assert [r['seed'] for r in results] == [42, 123, 2026]
    f = [r['metrics']['macro_f1'] for r in results]
    return {'seeds': [42, 123, 2026], 'seed_selection': 'none', 'labels': labels,
            'macro_f1_mean': float(np.mean(f)), 'macro_f1_sample_std_ddof1': float(np.std(f, ddof=1)),
            'per_class_mean': {label: {key: float(np.mean([r['metrics']['per_class'][i][key] for r in results]))
                                      for key in ('precision', 'recall', 'f1')} for i, label in enumerate(labels)},
            'results': results, 'interpretation': 'Exposed DEV, checkpoint selection on DEV; not independent generalization or expert gold.'}


def run(data, output):
    # Set before importing torch / initializing CUDA.
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    import numpy as np
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed
    manifest, rows, overlap = validate_data(data)
    assert torch.cuda.is_available(), 'En Colab: Entorno de ejecución > Cambiar tipo > GPU.'
    assert transformers.__version__ == '4.57.6' and torch.__version__.split('+')[0] == '2.7.1'
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'manifest.json', manifest)
    write(output / 'run-status.json', {'status': 'running', 'planned_seeds': [42, 123, 2026]})
    write(output / 'environment.json', {'python': sys.version, 'platform': platform.platform(),
          'torch': torch.__version__, 'transformers': transformers.__version__, 'cuda': torch.version.cuda,
          'gpu': torch.cuda.get_device_name(), 'runtime_sha256': sha(__file__), 'overlap': overlap,
          'pip_freeze': subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)})
    base = Path(snapshot_download(manifest['base_model'], revision=manifest['revision'],
                                 allow_patterns=list(manifest['base_hashes'])))
    for name, expected in manifest['base_hashes'].items():
        assert sha(base / name) == expected, f'Base/tokenizer hash mismatch: {name}'
    tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True, use_fast=True)
    assert tokenizer.is_fast and not tokenizer.do_lower_case
    labels = manifest['labels']
    encoded = {s: tokenizer([r['text'] for r in items], padding='max_length', truncation=True,
                            max_length=384, return_tensors='pt') for s, items in rows.items()}
    keys = list(encoded['train'])
    datasets = {s: torch.utils.data.TensorDataset(*[enc[k] for k in keys], torch.arange(len(rows[s])),
                torch.tensor([labels.index(r['label']) for r in rows[s]])) for s, enc in encoded.items()}
    weights = torch.tensor([len(rows['train']) / (7 * manifest['class_counts'][l]) for l in labels], device='cuda')
    dev_loader = torch.utils.data.DataLoader(datasets['dev'], batch_size=2, shuffle=False, num_workers=0)
    device = torch.device('cuda')
    results = []
    for seed in [42, 123, 2026]:
        start = time.monotonic()
        destination = output / f'seed-{seed}'
        destination.mkdir()
        write(destination / 'status.json', {'status': 'running', 'seed': seed})
        set_seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        loader = torch.utils.data.DataLoader(datasets['train'], batch_size=2, shuffle=True,
                    generator=torch.Generator().manual_seed(seed), num_workers=0)
        # BertForSequenceClassification: pooled CLS = tanh(W*CLS+b), dropout .1, Linear(768,7).
        model = AutoModelForSequenceClassification.from_pretrained(base, local_files_only=True,
                    use_safetensors=False, num_labels=7, classifier_dropout=.1,
                    id2label=dict(enumerate(labels)), label2id=dict(zip(labels, range(7)))).to(device)
        assert model.dropout.p == .1 and model.classifier.out_features == 7
        model.gradient_checkpointing_enable()
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=.01)
        horizon = 8 * math.ceil(len(loader) / 8)
        warmup = math.floor(.1 * horizon)
        assert (horizon, warmup) == (manifest['recipe']['horizon'], manifest['recipe']['warmup_steps'])
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer,
             lambda step: step / warmup if step < warmup else max(0., (horizon - step) / (horizon - warmup)))
        scaler = torch.amp.GradScaler('cuda')
        stopper, history = Stopping(), []
        with (destination / 'amp-events.jsonl').open('w', encoding='utf-8') as events:
            def emit(event):
                events.write(json.dumps(event, allow_nan=False) + '\n')
                events.flush()
                if event['skipped']:
                    print(f"seed={seed} AMP skip: {event}", flush=True)
            for epoch in range(1, 9):
                train = train_epoch(model, loader, keys, weights, optimizer, scaler, scheduler, device, emit, epoch)
                truth, probs = predict(model, dev_loader, keys, device)
                metrics = scores(truth, probs)
                improved, stop = stopper.update(metrics['macro_f1'], epoch)
                history.append({'epoch': epoch, 'train': train, 'dev': metrics, 'early_stop': stop})
                write(destination / 'history.json', history)
                if improved:
                    model.save_pretrained(destination / 'best', safe_serialization=True)
                    tokenizer.save_pretrained(destination / 'best')
                    write(destination / 'best' / 'labels.json', {'labels': labels, 'max_length': 384})
                    write(destination / 'dev-probabilities.json', {'seed': seed, 'epoch': epoch, 'labels': labels,
                        'items': [{'id': r['id'], 'text_sha256': r['text_sha256'], 'family': r['family'],
                                   'component': r['component'], 'label': r['label'], 'label_id': y,
                                   'probabilities': p} for r, y, p in zip(rows['dev'], truth, probs)]})
                print(json.dumps({'seed': seed, 'epoch': epoch, 'train_loss': train['loss'],
                                  'dev_macro_f1': metrics['macro_f1'], 'amp_skips': train['amp_skips'], 'stop': stop}), flush=True)
                if stop:
                    break
        total_updates = sum(h['train']['updates'] for h in history)
        if not total_updates:
            raise RuntimeError('No optimizer updates in this seed; not a valid trained baseline.')
        del model, optimizer, scheduler, scaler
        gc.collect()
        torch.cuda.empty_cache()
        model = AutoModelForSequenceClassification.from_pretrained(destination / 'best', local_files_only=True).to(device)
        truth, probs = predict(model, dev_loader, keys, device)
        saved = json.loads((destination / 'dev-probabilities.json').read_text(encoding='utf-8'))
        previous = np.asarray([r['probabilities'] for r in saved['items']])
        assert np.allclose(probs, previous, atol=1e-6, rtol=0)
        assert np.array_equal(np.argmax(probs, axis=1), previous.argmax(1))
        result = {'seed': seed, 'selected_epoch': stopper.best_epoch, 'metrics': scores(truth, probs),
                  'amp_skips': sum(h['train']['amp_skips'] for h in history), 'successful_updates': total_updates,
                  'training_and_reload_seconds': time.monotonic() - start,
                  'reload_max_probability_difference': float(np.abs(np.asarray(probs) - previous).max()),
                  'checkpoint_hashes': {p.name: sha(p) for p in (destination / 'best').iterdir() if p.is_file()}}
        write(destination / 'result.json', result)
        write(destination / 'status.json', {'status': 'complete', 'seed': seed})
        results.append(result)
        del model
        gc.collect()
        torch.cuda.empty_cache()
    summary = summarize(results, labels)
    write(output / 'summary.json', summary)
    write(output / 'run-status.json', {'status': 'complete', 'seeds_completed': [42, 123, 2026],
          'total_training_and_reload_seconds': sum(r['training_and_reload_seconds'] for r in results),
          'new_trajectories': 3, 'local_ledger_modified': False})
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        run(Path(args.data), Path(args.output))
    except BaseException as exc:
        dest = Path(args.output)
        if dest.exists() and not (dest / 'summary.json').exists():
            write(dest / 'failure.json', {'status': 'incomplete', 'error': repr(exc), 'no_partial_three_seed_mean': True})
        raise
