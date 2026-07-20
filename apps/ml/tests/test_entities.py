import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.entities import _model_entities


def test_merges_adjacent_person_fragments_from_original_text():
    text = "Scarlett O'Phelan explicó la rebelión."
    entities = [
        {"entity_group": "PER", "word": "Scar", "start": 0, "end": 4, "score": 0.99},
        {"entity_group": "PER", "word": "##lett O'Phelan", "start": 4, "end": 17, "score": 0.96},
    ]
    result = _model_entities(text, entities)
    assert len(result) == 1
    assert result[0]["text"] == "Scarlett O'Phelan"


def test_rejects_known_broken_standalone_tokens():
    text = "Gran Colombia"
    entities = [{"entity_group": "LOC", "word": "Gran", "start": 0, "end": 4, "score": 0.99}]
    assert _model_entities(text, entities) == []


def test_preserves_historical_aliases():
    text = "San Martín llegó al Perú"
    entities = [{"entity_group": "PER", "word": "San Martín", "start": 0, "end": 10, "score": 0.99}]
    assert _model_entities(text, entities)[0]["text"] == "José de San Martín"
