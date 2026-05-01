from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from lattice.models import Record
from lattice.targets.specs import TargetSpec
from lattice.utils import chunk_text, normalize_whitespace, slugify, stable_hash


def _source_payload(record: Record) -> dict[str, Any]:
    return {
        "source_record_id": record.record_id,
        "source_id": record.metadata.source_id,
        "source_type": record.metadata.source_type,
        "source_ref": record.metadata.url_or_ref,
        "license": record.metadata.license,
        "provenance_chain": list(record.metadata.provenance_chain),
        "dedup_id": record.metadata.dedup_id,
    }


def _record_entities(record: Record) -> list[str]:
    if record.schema_type == "StructuredRecord":
        entity = str(record.payload.get("entity", "")).strip()
        return [entity] if entity else []
    if record.schema_type == "KnowledgeRecord":
        subject = str(record.payload.get("subject", "")).strip()
        return [subject] if subject else []
    if record.schema_type == "Document":
        title = str(record.payload.get("title", "")).strip()
        return [title] if title else []
    return []


def build_entities(records: list[Record], domain: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for record in records:
        for entity_name in _record_entities(record):
            canonical = slugify(entity_name)
            entity_id = f"ent-{stable_hash(canonical)}"
            row = grouped.setdefault(
                entity_id,
                {
                    "entity_id": entity_id,
                    "canonical_name": entity_name,
                    "aliases": [],
                    "formula": "",
                    "domain": domain,
                    "source_ids": [],
                    "record_ids": [],
                },
            )
            if entity_name not in row["aliases"]:
                row["aliases"].append(entity_name)
            if record.metadata.source_id not in row["source_ids"]:
                row["source_ids"].append(record.metadata.source_id)
            if record.record_id not in row["record_ids"]:
                row["record_ids"].append(record.record_id)
    return sorted(grouped.values(), key=lambda item: item["entity_id"])


def build_links(records: list[Record], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    canonical_map: dict[str, str] = {}
    for entity in entities:
        for alias in entity["aliases"]:
            canonical_map[slugify(alias)] = entity["entity_id"]

    rows: list[dict[str, Any]] = []
    for record in records:
        for entity_name in _record_entities(record):
            key = slugify(entity_name)
            entity_id = canonical_map.get(key)
            if not entity_id:
                continue
            rows.append(
                {
                    "link_id": f"link-{stable_hash(record.record_id + entity_id)}",
                    "record_id": record.record_id,
                    "entity_id": entity_id,
                    "source_id": record.metadata.source_id,
                    "source_type": record.metadata.source_type,
                }
            )
    return rows


def build_rag_chunks(records: list[Record], entities: list[dict[str, Any]], spec: TargetSpec) -> list[dict[str, Any]]:
    entity_aliases: dict[str, list[str]] = {entity["entity_id"]: list(entity["aliases"]) for entity in entities}
    chunk_size = int(spec.target_config.get("chunk_size", spec.constraints.get("chunk_size", 1200)))
    rows: list[dict[str, Any]] = []
    for record in records:
        if record.schema_type != "Document":
            continue
        title = str(record.payload.get("title", "")).strip()
        text = str(record.payload.get("text", "")).strip()
        if not text:
            continue
        matched_entities: list[str] = []
        lowered_text = f"{title}\n{text}".lower()
        for entity in entities:
            if any(alias and alias.lower() in lowered_text for alias in entity_aliases[entity["entity_id"]]):
                matched_entities.append(entity["entity_id"])
        for index, chunk in enumerate(chunk_text(text, max_chars=chunk_size), start=1):
            normalized = normalize_whitespace(chunk)
            rows.append(
                {
                    "chunk_id": f"chunk-{stable_hash(record.record_id + str(index))}",
                    "text": normalized,
                    "title": title,
                    "section": "body",
                    "entity_ids": matched_entities,
                    "citation_payload": {
                        "title": title,
                        "source_ref": record.metadata.url_or_ref,
                        "source_type": record.metadata.source_type,
                    },
                    "retrieval_score": _retrieval_fitness(record, normalized, matched_entities),
                    **_source_payload(record),
                }
            )
    return rows


def build_pretrain_spans(records: list[Record], spec: TargetSpec) -> list[dict[str, Any]]:
    chunk_size = int(spec.target_config.get("chunk_size", spec.constraints.get("chunk_size", 1800)))
    rows: list[dict[str, Any]] = []
    for record in records:
        if record.schema_type != "Document":
            continue
        text = str(record.payload.get("text", "")).strip()
        if not text:
            continue
        for index, chunk in enumerate(chunk_text(text, max_chars=chunk_size), start=1):
            normalized = normalize_whitespace(chunk)
            rows.append(
                {
                    "span_id": f"pre-{stable_hash(record.record_id + str(index))}",
                    "text": normalized,
                    "title": str(record.payload.get("title", "")),
                    "pretrain_score": _pretrain_fitness(record, normalized),
                    **_source_payload(record),
                }
            )
    return rows


def build_instruction_samples(records: list[Record], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    del entities
    rows: list[dict[str, Any]] = []
    for record in records:
        if record.schema_type == "Document":
            title = str(record.payload.get("title", "")).strip()
            text = str(record.payload.get("text", "")).strip()
            output = " ".join(text.split()[:80]).strip()
            if output:
                rows.append(
                    {
                        "sample_id": f"ins-{stable_hash(record.record_id)}",
                        "task_type": "grounded_summarization",
                        "instruction": f"Summarize the materials-science source '{title}' using grounded evidence.",
                        "input": title,
                        "output": output,
                        "evidence": text[:400],
                        "sft_score": _sft_fitness(record, output),
                        **_source_payload(record),
                    }
                )
        elif record.schema_type == "StructuredRecord":
            entity = str(record.payload.get("entity", "")).strip()
            fields = dict(record.payload.get("fields", {}))
            output = "; ".join(f"{key}: {value}" for key, value in fields.items())
            if output:
                rows.append(
                    {
                        "sample_id": f"ins-{stable_hash(record.record_id)}",
                        "task_type": "property_listing",
                        "instruction": f"List the known properties of {entity}.",
                        "input": entity,
                        "output": output,
                        "evidence": record.payload.get("description", ""),
                        "sft_score": _sft_fitness(record, output),
                        **_source_payload(record),
                    }
                )
    return rows


def build_preference_pairs(instruction_samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in instruction_samples:
        output = str(sample.get("output", "")).strip()
        if not output:
            continue
        words = output.split()
        rejected = " ".join(words[: max(1, len(words) // 2)]).strip()
        if rejected == output:
            rejected = output[: max(1, len(output) // 2)].strip()
        rows.append(
            {
                "pair_id": f"pref-{stable_hash(str(sample['sample_id']))}",
                "instruction": sample["instruction"],
                "input": sample["input"],
                "chosen": output,
                "rejected": rejected,
                "reason_code": "more_complete_grounded_answer",
                "preference_score": sample.get("sft_score", 0.0),
                "source_record_id": sample["source_record_id"],
                "source_id": sample["source_id"],
                "source_type": sample["source_type"],
                "source_ref": sample["source_ref"],
                "license": sample["license"],
                "provenance_chain": sample["provenance_chain"],
                "dedup_id": sample["dedup_id"],
            }
        )
    return rows


def build_eval_items(records: list[Record]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if record.schema_type == "Document":
            title = str(record.payload.get("title", "")).strip()
            text = str(record.payload.get("text", "")).strip()
            if not text:
                continue
            answer = next((segment.strip() for segment in text.split(".") if segment.strip()), text[:200])
            rows.append(
                {
                    "eval_id": f"eval-{stable_hash(record.record_id)}",
                    "eval_type": "grounded_qa",
                    "prompt": f"What is the main contribution of '{title}'?",
                    "gold_answer": answer,
                    "gold_evidence": text[:300],
                    "rubric": "Answer should be grounded in the source text and capture the main contribution.",
                    "eval_score": _eval_fitness(record, answer),
                    **_source_payload(record),
                }
            )
        elif record.schema_type == "StructuredRecord":
            entity = str(record.payload.get("entity", "")).strip()
            fields = dict(record.payload.get("fields", {}))
            for key, value in fields.items():
                rows.append(
                    {
                        "eval_id": f"eval-{stable_hash(record.record_id + key)}",
                        "eval_type": "property_extraction",
                        "prompt": f"What is the {key.replace('_', ' ')} of {entity}?",
                        "gold_answer": value,
                        "gold_evidence": record.payload.get("description", ""),
                        "rubric": "Answer should exactly match the normalized property value.",
                        "eval_score": _eval_fitness(record, str(value)),
                        **_source_payload(record),
                    }
                )
    return rows


def _retrieval_fitness(record: Record, text: str, entity_ids: list[str]) -> float:
    title_bonus = 0.15 if record.payload.get("title") else 0.0
    entity_bonus = min(0.3, 0.1 * len(entity_ids))
    length_bonus = min(0.4, len(text.split()) / 200.0)
    return round(title_bonus + entity_bonus + length_bonus, 4)


def _pretrain_fitness(record: Record, text: str) -> float:
    del record
    unique_words = len(set(text.lower().split()))
    total_words = max(len(text.split()), 1)
    return round(min(1.0, unique_words / total_words + min(total_words / 300.0, 0.5)), 4)


def _sft_fitness(record: Record, output: str) -> float:
    evidence_bonus = 0.2 if record.payload.get("description") or record.payload.get("text") else 0.0
    completeness = min(0.6, len(output.split()) / 80.0)
    return round(evidence_bonus + completeness, 4)


def _eval_fitness(record: Record, answer: str) -> float:
    evidence_bonus = 0.25 if record.payload.get("description") or record.payload.get("text") else 0.0
    answer_bonus = min(0.5, len(str(answer).split()) / 50.0)
    return round(evidence_bonus + answer_bonus, 4)
