"""Fine-tuning de BETO para clasificación de subtemas (núcleo del TFM).

Recibe un dataset ya dividido (train/val/test) desde NestJS, fine-tunea BETO
(o una versión padre para entrenamiento incremental), calcula métricas con
scikit-learn y guarda el artefacto. Reporta progreso al registro de jobs.

Dependencias PESADAS importadas de forma perezosa (torch, transformers,
datasets, scikit-learn) → el servicio arranca sin ellas; solo se requieren al
entrenar. El entrenamiento pesado real se hace en Colab/Kaggle (mismo código).
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

from app.config import resolve_storage_path
from app.ml import jobs
from app.ml.beto import BETO_BASE


def _split(items: List[dict], name: str) -> List[dict]:
    return [it for it in items if it.get("split") == name]


def train_job(job_id: str, req: dict) -> None:
    """Ejecuta el entrenamiento completo. Pensado para correr en un BackgroundTask."""
    try:
        jobs.update_job(job_id, status="running", progress=1)
        _run(job_id, req)
    except ImportError as exc:
        jobs.update_job(
            job_id,
            status="failed",
            error=(
                "Faltan dependencias de entrenamiento (torch/transformers/datasets/"
                "scikit-learn). Instala requirements-ml.txt o entrena en Colab. "
                f"Detalle: {exc}"
            ),
        )
    except Exception as exc:  # noqa: BLE001
        jobs.update_job(job_id, status="failed", error=str(exc))


def _run(job_id: str, req: dict) -> None:
    import numpy as np
    import torch
    from datasets import Dataset
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        precision_recall_fscore_support,
    )
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        EarlyStoppingCallback,
        Trainer,
        TrainerCallback,
        TrainingArguments,
    )

    labels: List[str] = sorted(req["labels"])
    label2id = {lab: i for i, lab in enumerate(labels)}
    id2label = {i: lab for lab, i in label2id.items()}
    num_labels = len(labels)

    hp = req.get("hyperparams") or {}
    epochs = int(hp.get("epochs", 4))
    lr = float(hp.get("lr", 2e-5))
    batch_size = int(hp.get("batch_size", 8))
    max_len = int(hp.get("max_len", 192))
    seed = int(hp.get("seed", 42))
    base_model = req.get("base_model") or BETO_BASE
    # Se escribe bajo la raíz de almacenamiento (validada, independiente del cwd),
    # pero se reporta la ruta original como artifact_path (portable entre entornos).
    output_dir = str(resolve_storage_path(req["output_dir"]))

    items = req["items"]
    train_rows = _split(items, "train")
    val_rows = _split(items, "val") or train_rows      # fallback si no hay val
    test_rows = _split(items, "test") or val_rows
    # Split real sobre el que se calcularán las métricas finales (con fallbacks).
    metrics_split = "test" if _split(items, "test") else ("val" if _split(items, "val") else "train")

    def to_ds(rows: List[dict]) -> "Dataset":
        return Dataset.from_dict(
            {"text": [r["text"] for r in rows], "label": [label2id[r["label"]] for r in rows]}
        )

    tokenizer = AutoTokenizer.from_pretrained(base_model)

    def tok(batch):
        return tokenizer(batch["text"], truncation=True, max_length=max_len)

    ds_train = to_ds(train_rows).map(tok, batched=True)
    ds_val = to_ds(val_rows).map(tok, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        base_model, num_labels=num_labels, id2label=id2label, label2id=label2id
    )

    # Class weights (desbalanceo): inverso de la frecuencia por clase.
    counts = np.bincount([label2id[r["label"]] for r in train_rows], minlength=num_labels)
    weights = torch.tensor(
        [(len(train_rows) / (num_labels * c)) if c > 0 else 0.0 for c in counts], dtype=torch.float
    )

    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels_ = inputs.pop("labels")
            outputs = model(**inputs)
            loss = torch.nn.functional.cross_entropy(
                outputs.logits, labels_, weight=weights.to(outputs.logits.device)
            )
            return (loss, outputs) if return_outputs else loss

    def compute_metrics(eval_pred):
        logits, y = eval_pred
        preds = np.argmax(logits, axis=-1)
        p, r, f1, _ = precision_recall_fscore_support(y, preds, average="macro", zero_division=0)
        return {"accuracy": accuracy_score(y, preds), "f1_macro": f1, "precision_macro": p, "recall_macro": r}

    total_epochs = epochs

    class ProgressCb(TrainerCallback):
        def on_epoch_end(self, args, state, control, **kwargs):
            ep = int(state.epoch or 0)
            jobs.update_job(
                job_id, current_epoch=ep, progress=min(95, int(ep / max(1, total_epochs) * 90) + 5)
            )

    args = TrainingArguments(
        output_dir=os.path.join(output_dir, "_checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=lr,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        seed=seed,
        logging_steps=10,
        report_to=[],
        disable_tqdm=True,
    )

    trainer = WeightedTrainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        eval_dataset=ds_val,
        compute_metrics=compute_metrics,
        callbacks=[ProgressCb(), EarlyStoppingCallback(early_stopping_patience=2)],
    )
    trainer.train()

    # ---- Métricas finales sobre test ----
    ds_test = to_ds(test_rows).map(tok, batched=True)
    pred_out = trainer.predict(ds_test)
    y_true = pred_out.label_ids
    y_pred = np.argmax(pred_out.predictions, axis=-1)

    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    pc_p, pc_r, pc_f1, pc_s = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(num_labels)), zero_division=0
    )
    per_class = [
        {
            "label": id2label[i],
            "precision": round(float(pc_p[i]), 4),
            "recall": round(float(pc_r[i]), 4),
            "f1": round(float(pc_f1[i]), 4),
            "support": int(pc_s[i]),
        }
        for i in range(num_labels)
    ]
    cm = confusion_matrix(y_true, y_pred, labels=list(range(num_labels))).tolist()

    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 5),
        "precision_macro": round(float(p), 5),
        "recall_macro": round(float(r), 5),
        "f1_macro": round(float(f1), 5),
        "per_class": per_class,
        "confusion_matrix": cm,
        "labels": labels,
        "split": metrics_split,
    }

    # ---- Guardar artefacto ----
    os.makedirs(output_dir, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    with open(os.path.join(output_dir, "labels.json"), "w", encoding="utf-8") as fh:
        json.dump({"id2label": {str(i): l for i, l in id2label.items()}, "max_len": max_len}, fh, ensure_ascii=False)

    jobs.update_job(job_id, status="done", progress=100, artifact_path=req["output_dir"], metrics=metrics)
