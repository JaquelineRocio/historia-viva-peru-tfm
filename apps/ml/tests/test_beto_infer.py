"""La inferencia devuelve la etiqueta principal y las tres más probables."""
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from app.ml import beto  # noqa: E402


class _Tokenizer:
    def __call__(self, batch, **_kwargs):
        return {"input_ids": torch.zeros((len(batch), 1), dtype=torch.long)}


class _Model:
    def __init__(self, logits):
        self.logits = torch.tensor(logits)

    def __call__(self, input_ids):
        return SimpleNamespace(logits=self.logits[: input_ids.shape[0]])


def test_infer_returns_top3_in_order(monkeypatch):
    id2label = {0: "a", 1: "b", 2: "c", 3: "d"}
    model = _Model([[0.0, 3.0, 1.0, 2.0]])
    monkeypatch.setattr(beto, "_active", beto._LoadedModel(model, _Tokenizer(), id2label, 16))

    [pred] = beto.infer(["texto"])

    assert pred["label"] == "b"
    assert [item["label"] for item in pred["top"]] == ["b", "d", "c"]
    assert pred["confidence"] == pred["top"][0]["confidence"]
    assert pred["top"][0]["confidence"] > pred["top"][1]["confidence"] > pred["top"][2]["confidence"]
