"""Verify a frozen external-development artifact; never trains or predicts."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = sorted([
    "contexto_colonial_antecedentes", "crisis_ideas_emancipadoras",
    "participacion_social_regional", "campanias_conflictos_militares",
    "liderazgos_diplomacia_proyectos", "organizacion_consecuencias_republicanas",
    "no_relevante",
])


def fingerprint(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def workspace_file(relative: str) -> Path:
    path = Path(relative)
    target = (ROOT / path).resolve()
    require(not path.is_absolute() and target.is_relative_to(ROOT), "Input path outside workspace")
    require(target.is_file(), f"Missing input: {relative}")
    return target


def verify(payload: dict, *, check_local_inputs: bool = False) -> dict:
    require(payload.get("schema_version") == 1, "Unsupported schema")
    require(payload.get("purpose") == "external_development", "Not external development")
    require(payload.get("status") == "frozen", "Artifact is not frozen")
    body = {k: v for k, v in payload.items() if k != "content_sha256"}
    require(payload.get("content_sha256") == fingerprint(body), "Frozen content hash differs")
    require(payload.get("labels") == LABELS, "Taxonomy differs from 1780–1842 v1")
    require(payload.get("scope_years") == [1780, 1842], "Historical scope differs")
    require(bool(payload.get("frozen_at_utc")), "Missing freeze time")
    protocol = payload.get("selection_protocol", {})
    require(protocol.get("sha256") == fingerprint(protocol.get("content")),
            "Selection protocol hash differs")
    require(protocol.get("content", {}).get("predictions_performed") is False,
            "Protocol must predate model predictions")
    items = payload.get("items", [])
    sources = payload.get("sources", {})
    require(bool(items), "Empty external development")
    review_ref = payload.get("review_artifact", {})
    review_path = workspace_file(review_ref.get("path", ""))
    require(hashlib.sha256(review_path.read_bytes()).hexdigest() == review_ref.get("sha256"),
            "Adjudication artifact hash differs")
    adjudication = json.loads(review_path.read_text(encoding="utf-8"))
    approved_rows = [r for r in adjudication.get("decisions", []) if r["decision"] == "include"]
    approved = {r["id"]: r for r in approved_rows}
    require(len(approved) == len(approved_rows), "Duplicate adjudication ID")
    require(set(approved) == {r.get("id") for r in items}, "Items differ from approved inventory")
    identifiers, texts = set(), set()
    for row in items:
        identifier = row.get("id")
        require(isinstance(identifier, str) and bool(identifier), "Missing item ID")
        require(identifier not in identifiers, f"Duplicate ID: {identifier}")
        identifiers.add(identifier)
        require(row.get("split") == "val", f"Non-validation row: {identifier}")
        require(row.get("sourceType") == "pdf", f"Unexpected source type: {identifier}")
        text = row.get("text")
        require(isinstance(text, str) and bool(text.strip()), f"Empty text: {identifier}")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        require(row.get("text_sha256") == digest, f"Text hash differs: {identifier}")
        normalized = " ".join(text.casefold().split())
        require(normalized not in texts, f"Duplicate text: {identifier}")
        texts.add(normalized)
        require(120 <= len(text.split()) <= 250, f"Word limit: {identifier}")
        require(row.get("word_count") == len(text.split()), f"Word count differs: {identifier}")
        require(row.get("label") in LABELS, f"Unknown label: {identifier}")
        resource_id = row.get("resourceId")
        require(resource_id in sources, f"Unknown source: {identifier}")
        source = sources[resource_id]
        require(source.get("role") == "external_development_only",
                f"Source not reserved: {identifier}")
        require(source.get("license") == "CC BY 4.0", f"Unverified source license: {identifier}")
        for field in ("author", "title", "year", "url", "license_url", "pdf_sha256"):
            require(bool(source.get(field)), f"Missing source {field}: {identifier}")
        provenance = row.get("provenance", {})
        for field in ("printed_pages", "pdf_pages_1_based"):
            page_numbers = provenance.get(field)
            require(isinstance(page_numbers, list) and bool(page_numbers),
                    f"Missing {field}: {identifier}")
            require(all(isinstance(n, int) and n > 0 for n in page_numbers),
                    f"Invalid {field}: {identifier}")
        require(bool(provenance.get("paragraph_id")), f"Missing paragraph: {identifier}")
        require(bool(provenance.get("extraction_evidence")), f"Missing raw evidence: {identifier}")
        decision = approved[identifier]
        require(decision.get("text_sha256") == digest and decision.get("label") == row["label"]
                and decision.get("source_id") == resource_id
                and decision.get("provenance") == provenance,
                f"Item differs from adjudicated paragraph: {identifier}")
        review = row.get("label_review", {})
        require(review.get("final_decision") == "include", f"Unresolved review: {identifier}")
        require(review.get("human_independent_validation") is False,
                f"Misstated review type: {identifier}")
    counts = Counter(row["label"] for row in items)
    present = [label for label in LABELS if counts[label]]
    require(payload.get("metric_labels") == present, "Primary metric labels differ from support")
    require(payload.get("unassessed_labels") == [label for label in LABELS if not counts[label]],
            "Absent-class declaration differs")
    require(payload.get("class_counts") == dict(counts), "Class counts differ")
    actual_sources = Counter(row["resourceId"] for row in items)
    require(payload.get("source_counts") == dict(actual_sources), "Source counts differ")
    local_count = 0
    if check_local_inputs:
        guarded = {}
        for entry in payload.get("local_input_guards", []):
            target = workspace_file(entry["path"])
            require(hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"],
                    f"Local input hash differs: {entry['path']}")
            guarded[entry["path"]] = entry["sha256"]
            local_count += 1
        require(local_count > 0, "Missing local input guards")
        for source in sources.values():
            require(guarded.get(source.get("local_pdf")) == source["pdf_sha256"],
                    "Source PDF not linked to a verified local guard")
        for row in items:
            evidence_path = row["provenance"]["extraction_evidence"]
            require(evidence_path in guarded, f"Unguarded extraction: {row['id']}")
            evidence = json.loads(workspace_file(evidence_path).read_text(encoding="utf-8"))
            paragraphs = evidence.get("paragraphs", evidence.get("items", []))
            matches = [p for p in paragraphs if p["id"] == row["provenance"]["paragraph_id"]]
            require(len(matches) == 1, f"Extraction paragraph missing or repeated: {row['id']}")
            paragraph = matches[0]
            require(paragraph["text"] == row["text"]
                    and paragraph["text_sha256"] == row["text_sha256"]
                    and paragraph["printed_pages"] == row["provenance"]["printed_pages"]
                    and paragraph["pdf_pages_1_based"] == row["provenance"]["pdf_pages_1_based"],
                    f"Text/page differs from source extraction: {row['id']}")
    return dict(passed=True, content_sha256=payload["content_sha256"], rows=len(items),
                sources=len(actual_sources), class_counts=dict(counts), metric_labels=present,
                unassessed_labels=payload["unassessed_labels"], local_inputs_checked=local_count,
                training_performed=False, predictions_performed=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path,
                        default=ROOT / "artifacts/datasets/external-development-v1.json")
    parser.add_argument("--check-local-inputs", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.dataset.read_text(encoding="utf-8"))
    result = verify(payload, check_local_inputs=args.check_local_inputs)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
