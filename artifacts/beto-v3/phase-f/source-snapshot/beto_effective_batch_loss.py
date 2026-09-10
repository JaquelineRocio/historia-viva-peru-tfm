"""Save declared epochs from one uninterrupted local training trajectory."""
from __future__ import annotations

import gc
from itertools import islice
import json
import math
import os
import time
from pathlib import Path

# Debe establecerse antes de importar Transformers, también desde otro runner.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]


def accumulation_batches(loader, accumulation, weights):
    """Yield unchanged CPU microbatches with one target-weight sum per actual group.

    Only target indices are copied to the weights device; no logits or graphs
    are retained across microbatches. Loader must have deterministic transforms
    and its own generator, as the project TensorDataset loader does.
    """
    import torch
    iterator = iter(loader)
    step = 0
    while group := list(islice(iterator, accumulation)):
        targets = torch.cat([batch[-1] for batch in group]).to(weights.device)
        denominator = weights[targets].sum()
        for batch in group:
            yield step, batch, denominator
            step += 1


def train_epoch_trajectory(train, labels, params, config, output, checkpoint_epochs=(2, 3)):
    """Normalize weighted CE over each effective accumulation group.

    Separate module keeps the historical trainer and its frozen hashes intact.
    Epoch snapshots do not reset model, optimizer, scaler, scheduler or loader.
    """
    target = Path(output).resolve()
    if not target.is_relative_to((ROOT / "outputs").resolve()) or target.exists():
        raise ValueError("Usa una carpeta nueva dentro de outputs/; no se sobrescribe")
    schedule_epochs = params["epochs"]
    if (not isinstance(checkpoint_epochs, (list, tuple)) or not checkpoint_epochs
            or isinstance(schedule_epochs, bool) or not isinstance(schedule_epochs, int)
            or any(isinstance(e, bool) or not isinstance(e, int)
                   or not 1 <= e <= schedule_epochs for e in checkpoint_epochs)
            or list(checkpoint_epochs) != sorted(set(checkpoint_epochs))):
        raise ValueError("Declare unique increasing epochs within the scheduler horizon")
    checkpoint_epoch = max(checkpoint_epochs)
    if not train or not labels or len(set(labels)) != len(labels):
        raise ValueError("Se requieren entrenamiento y etiquetas únicas")
    counts = [sum(row["label"] == label for row in train) for label in labels]
    if not all(counts) or sum(counts) != len(train):
        raise ValueError("Cada etiqueta debe tener ejemplos y todas las filas una etiqueta conocida")
    accumulation = params.get("gradient_accumulation_steps", 1)
    if isinstance(accumulation, bool) or not isinstance(accumulation, int) or accumulation < 1:
        raise ValueError("gradient_accumulation_steps debe ser un entero positivo")

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed
    from app.ml.beto_experiment import _loader

    if not torch.cuda.is_available() and not config.get("allow_cpu", False):
        raise RuntimeError("BETO requiere CUDA; allow_cpu solo se admite en fixtures")
    seed = config.get("seed", 42)
    set_seed(seed)
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base = config["base_model"]
    revision = config.get("revision", "main")
    target.mkdir(parents=True, exist_ok=False)
    tokenizer = AutoTokenizer.from_pretrained(base, revision=revision, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        base, revision=revision, num_labels=len(labels),
        id2label=dict(enumerate(labels)), label2id={label: i for i, label in enumerate(labels)},
        use_safetensors=False, local_files_only=True,
    ).to(device)
    model.gradient_checkpointing_enable()
    train_loader, keys = _loader(train, tokenizer, labels, params, shuffle=True, seed=seed)
    weights = torch.tensor([len(train) / (len(labels) * n) for n in counts], device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=params["lr"], weight_decay=0.01)
    steps_per_epoch = math.ceil(len(train_loader) / accumulation)
    total_steps = steps_per_epoch * schedule_epochs
    warmup = max(1, int(total_steps * 0.1))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: min(
        (step + 1) / warmup, max(0.0, (total_steps - step) / max(1, total_steps - warmup))))
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    history = []
    saved_checkpoints = []
    optimizer_updates = skipped_updates = 0
    started = time.monotonic()
    for epoch in range(1, checkpoint_epoch + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        epoch_updates = epoch_skips = 0
        # La media se registra para diagnóstico; no decide ni altera el checkpoint.
        diagnostic_losses = torch.zeros((), device=device, dtype=torch.float64)
        for step, batch, denominator in accumulation_batches(train_loader, accumulation, weights):
            inputs = {key: batch[i].to(device) for i, key in enumerate(keys)}
            targets = batch[-1].to(device)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                logits = model(**inputs).logits
                loss = torch.nn.functional.cross_entropy(logits, targets, weight=weights, reduction="sum") / denominator
            scaler.scale(loss).backward()
            diagnostic_losses += loss.detach().to(torch.float64) * denominator / weights[targets].sum()
            if (step + 1) % accumulation == 0 or step + 1 == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                previous_scale = scaler.get_scale()
                scaler.step(optimizer)
                scaler.update()
                if scaler.get_scale() >= previous_scale:
                    scheduler.step()
                    epoch_updates += 1
                else:
                    epoch_skips += 1
                optimizer.zero_grad(set_to_none=True)
            if (step + 1) % 50 == 0:
                print(f"  epoch {epoch} batch {step + 1}/{len(train_loader)}", flush=True)
        optimizer_updates += epoch_updates
        skipped_updates += epoch_skips
        history.append({
            "epoch": epoch,
            "microbatches": len(train_loader),
            "optimizer_updates": epoch_updates,
            "skipped_updates": epoch_skips,
            "diagnostic_mean_microbatch_weighted_ce": diagnostic_losses.item() / len(train_loader),
            "learning_rate_after_epoch": optimizer.param_groups[0]["lr"],
        })
        print(f"  epoch {epoch}: fixed-epoch training completed; updates={epoch_updates}, skips={epoch_skips}", flush=True)

        if epoch in checkpoint_epochs:
            destination = target / f"epoch-{epoch}"
            destination.mkdir(exist_ok=False)
            model.save_pretrained(destination, safe_serialization=True)
            tokenizer.save_pretrained(destination)
            (destination / "labels.json").write_text(json.dumps(
                {"id2label": dict(enumerate(labels)), "max_len": params["max_len"]}), encoding="utf-8")
            saved_checkpoints.append(dict(epoch=epoch, directory=destination.relative_to(ROOT).as_posix(),
                optimizer_updates=optimizer_updates, skipped_updates=skipped_updates,
                optimizer_update_attempts=optimizer_updates + skipped_updates,
                scheduler_steps=optimizer_updates))

    details = {
        "checkpoint_selection": "all_predeclared_epochs_no_selection",
        "checkpoint_epochs": list(checkpoint_epochs),
        "saved_checkpoints": saved_checkpoints,
        "class_counts": dict(zip(labels, counts)),
        "class_weights": dict(zip(labels, weights.detach().cpu().tolist())),
        "checkpoint_epoch": checkpoint_epoch,
        "epochs_executed": checkpoint_epoch,
        "schedule_epochs": schedule_epochs,
        "steps_per_epoch": steps_per_epoch,
        "schedule_total_steps": total_steps,
        "warmup_steps": warmup,
        "optimizer_update_attempts": optimizer_updates + skipped_updates,
        "optimizer_updates": optimizer_updates,
        "skipped_updates": skipped_updates,
        "scheduler_steps": optimizer_updates,
        "history": history,
        "loss_role": "diagnostic_only_mean_of_microbatch_weighted_CE_not_a_selection_metric",
        "seconds": round(time.monotonic() - started, 2),
        "base_model": base,
        "resolved_revision": getattr(model.config, "_commit_hash", None),
        "device": torch.cuda.get_device_name() if device.type == "cuda" else "cpu",
        "seed": seed,
        "effective_batch_size": params["batch_size"] * accumulation,
        "max_len": params["max_len"],
        "optimizer": "AdamW",
        "weight_decay": 0.01,
        "class_weighting": "inverse_frequency",
        "loss_normalization": "weighted_CE_sum_per_microbatch_divided_by_target_weight_sum_of_actual_accumulation_group",
        "gradient_clipping_max_norm": 1.0,
        "gradient_checkpointing": True,
        "mixed_precision": device.type == "cuda",
        "offline": True,
        "local_files_only": True,
        "evaluation_rows_used": False,
        "predictions_performed": False,
        "checkpoint_path": str(target),
        "checkpoint_saves": len(saved_checkpoints),
    }
    del model, optimizer, scaler, train_loader
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return details
