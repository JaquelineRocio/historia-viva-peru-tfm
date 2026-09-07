"""Fine-tuning BETO con acumulación de gradientes para una GPU de 4 GB."""
from __future__ import annotations

import gc
import json
import math
import time
from pathlib import Path

from app.ml.baselines import _metric_report


def _loader(rows, tokenizer, labels, params, *, shuffle=False, seed=42):
    import torch
    encoded = tokenizer([r["text"] for r in rows], truncation=True, padding="max_length",
                        max_length=params["max_len"], return_tensors="pt")
    targets = torch.tensor([labels.index(r["label"]) for r in rows])
    keys = list(encoded)
    dataset = torch.utils.data.TensorDataset(*(encoded[k] for k in keys), targets)
    generator = torch.Generator().manual_seed(seed)
    loader = torch.utils.data.DataLoader(dataset, batch_size=params["batch_size"], shuffle=shuffle,
                                         generator=generator, num_workers=0)
    return loader, keys


def _predict(model, loader, keys, labels, device):
    import torch
    model.eval()
    result = []
    with torch.inference_mode():
        for batch in loader:
            inputs = {key: batch[i].to(device) for i, key in enumerate(keys)}
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                predicted = model(**inputs).logits.argmax(dim=-1).cpu().tolist()
            result.extend(labels[i] for i in predicted)
    return result


def fit_beto(train, val, labels, params, config, output: Path):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed

    if not torch.cuda.is_available() and not config.get("allow_cpu", False):
        raise RuntimeError("BETO requiere CUDA en este perfil. Usa un runner GPU o allow_cpu explícito.")
    seed = config.get("seed", 42)
    set_seed(seed)  # antes de inicializar también la cabeza de clasificación
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base = config["base_model"]
    revision = config.get("revision", "main")
    tokenizer = AutoTokenizer.from_pretrained(base, revision=revision)
    model = AutoModelForSequenceClassification.from_pretrained(
        base, revision=revision, num_labels=len(labels),
        id2label=dict(enumerate(labels)), label2id={label: i for i, label in enumerate(labels)},
        # El BETO base fijado por revisión publica pytorch_model.bin.
        # Transformers + torch >= 2.6 usan carga restringida weights_only.
        use_safetensors=False,
    ).to(device)
    model.gradient_checkpointing_enable()
    train_loader, keys = _loader(train, tokenizer, labels, params, shuffle=True, seed=seed)
    val_loader, _ = _loader(val, tokenizer, labels, params)
    counts = [sum(r["label"] == label for r in train) for label in labels]
    weights = torch.tensor([len(train) / (len(labels) * n) for n in counts], device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=params["lr"], weight_decay=0.01)
    accumulation = params.get("gradient_accumulation_steps", 1)
    steps_per_epoch = math.ceil(len(train_loader) / accumulation)
    total_steps = steps_per_epoch * params["epochs"]
    warmup = max(1, int(total_steps * 0.1))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: min(
        (step + 1) / warmup, max(0.0, (total_steps - step) / max(1, total_steps - warmup))))
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    best_score, best_pred, best_epoch = -1.0, [], 0
    history = []
    started = time.monotonic()
    for epoch in range(1, params["epochs"] + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        for step, batch in enumerate(train_loader):
            inputs = {key: batch[i].to(device) for i, key in enumerate(keys)}
            targets = batch[-1].to(device)
            # El último grupo puede contener menos microbatches.
            group_size = min(accumulation, len(train_loader) - (step // accumulation) * accumulation)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(**inputs).logits
                loss = torch.nn.functional.cross_entropy(logits, targets, weight=weights) / group_size
            scaler.scale(loss).backward()
            if (step + 1) % accumulation == 0 or step + 1 == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                previous_scale = scaler.get_scale()
                scaler.step(optimizer)
                scaler.update()
                if scaler.get_scale() >= previous_scale:
                    scheduler.step()
                optimizer.zero_grad(set_to_none=True)
            if (step + 1) % 50 == 0:
                print(f"  epoch {epoch} batch {step + 1}/{len(train_loader)}", flush=True)
        predicted = _predict(model, val_loader, keys, labels, device)
        score = _metric_report([r["label"] for r in val], predicted, labels)["f1_macro"]
        history.append({"epoch": epoch, "validation_f1_macro": score})
        print(f"  epoch {epoch}: validation F1={score:.5f}", flush=True)
        if score > best_score:
            best_score, best_pred, best_epoch = score, predicted, epoch
            model.save_pretrained(output, safe_serialization=True)
            tokenizer.save_pretrained(output)
            (output / "labels.json").write_text(json.dumps(
                {"id2label": dict(enumerate(labels)), "max_len": params["max_len"]}), encoding="utf-8")
    details = {"best_epoch": best_epoch, "history": history, "seconds": round(time.monotonic() - started, 2),
               "base_model": base, "resolved_revision": getattr(model.config, "_commit_hash", None),
               "device": torch.cuda.get_device_name() if device.type == "cuda" else "cpu",
               "effective_batch_size": params["batch_size"] * accumulation,
               "optimizer": "AdamW", "weight_decay": 0.01, "warmup_steps": warmup,
               "class_weighting": "inverse_frequency", "gradient_checkpointing": True, "mixed_precision": device.type == "cuda"}
    del model, optimizer, scaler, train_loader, val_loader
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return best_pred, details


def predict_beto(path: Path, rows, labels, params):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path, use_safetensors=True).to(device)
    loader, keys = _loader(rows, tokenizer, labels, params)
    predicted = _predict(model, loader, keys, labels, device)
    del model, loader
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return predicted
