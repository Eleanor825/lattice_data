from __future__ import annotations

from typing import Any

from lattice.models import Record
from lattice.utils import chunk_text, slugify, stable_hash


def _shared_view_metadata(record: Record, dataset_name: str) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "source_record_id": record.record_id,
        "source_id": record.metadata.source_id,
        "domain": record.metadata.domain,
        "provenance_chain": list(record.metadata.provenance_chain),
        "dedup_id": record.metadata.dedup_id,
    }


def document_to_pretrain(record: Record, dataset_name: str, chunk_size: int) -> list[dict[str, Any]]:
    title = record.payload["title"]
    text = record.payload["text"]
    rows = []
    for index, chunk in enumerate(chunk_text(text, max_chars=chunk_size), start=1):
        rows.append(
            {
                "view_id": f"pre-{stable_hash(record.record_id + str(index))}",
                "view_type": "pretrain",
                "title": title,
                "text": chunk,
                "chunk_index": index,
                **_shared_view_metadata(record, dataset_name),
            }
        )
    return rows


def document_to_qa(record: Record, dataset_name: str) -> list[dict[str, Any]]:
    text = record.payload["text"]
    title = record.payload["title"]
    sentences = [segment.strip() for segment in text.split(".") if segment.strip()]
    answer = sentences[0] if sentences else text[:200]
    return [
        {
            "view_id": f"qa-{stable_hash(record.record_id)}",
            "view_type": "qa",
            "question": f"What is the main contribution of '{title}'?",
            "answer": answer,
            **_shared_view_metadata(record, dataset_name),
        }
    ]


def document_to_instruction(record: Record, dataset_name: str) -> list[dict[str, Any]]:
    text = record.payload["text"]
    title = record.payload["title"]
    summary = " ".join(text.split()[:80]).strip()
    return [
        {
            "view_id": f"ins-{stable_hash(record.record_id)}",
            "view_type": "instruction",
            "instruction": f"Summarize the scientific source '{title}' for a domain model.",
            "input": title,
            "output": summary,
            "tool_trace": [],
            **_shared_view_metadata(record, dataset_name),
        }
    ]


def document_to_knowledge(record: Record, dataset_name: str) -> list[dict[str, Any]]:
    title = record.payload["title"]
    text = record.payload["text"]
    statement = " ".join(text.split()[:40]).strip()
    return [
        {
            "view_id": f"kg-{stable_hash(record.record_id)}",
            "view_type": "knowledge",
            "subject": title,
            "predicate": "describes",
            "object": statement,
            "evidence": statement,
            **_shared_view_metadata(record, dataset_name),
        }
    ]


def structured_to_knowledge(record: Record, dataset_name: str) -> list[dict[str, Any]]:
    entity = record.payload["entity"]
    fields = record.payload["fields"]
    rows = []
    for key, value in fields.items():
        rows.append(
            {
                "view_id": f"kg-{stable_hash(record.record_id + key)}",
                "view_type": "knowledge",
                "subject": entity,
                "predicate": slugify(key).replace("-", "_"),
                "object": value,
                "evidence": record.payload.get("description", ""),
                **_shared_view_metadata(record, dataset_name),
            }
        )
    return rows


def structured_to_qa(record: Record, dataset_name: str) -> list[dict[str, Any]]:
    entity = record.payload["entity"]
    fields = record.payload["fields"]
    rows = []
    for key, value in fields.items():
        rows.append(
            {
                "view_id": f"qa-{stable_hash(record.record_id + key)}",
                "view_type": "qa",
                "question": f"What is the {key.replace('_', ' ')} of {entity}?",
                "answer": value,
                **_shared_view_metadata(record, dataset_name),
            }
        )
    return rows


def structured_to_instruction(record: Record, dataset_name: str) -> list[dict[str, Any]]:
    entity = record.payload["entity"]
    fields = record.payload["fields"]
    output = "; ".join(f"{key}: {value}" for key, value in fields.items())
    return [
        {
            "view_id": f"ins-{stable_hash(record.record_id)}",
            "view_type": "instruction",
            "instruction": f"List the known properties of {entity}.",
            "input": entity,
            "output": output,
            "tool_trace": [],
            **_shared_view_metadata(record, dataset_name),
        }
    ]


def build_views(records: list[Record], dataset_name: str, chunk_size: int = 1200) -> dict[str, list[dict[str, Any]]]:
    views = {
        "pretrain_view": [],
        "qa_view": [],
        "instruction_view": [],
        "knowledge_view": [],
    }
    for record in records:
        if record.schema_type == "Document":
            views["pretrain_view"].extend(document_to_pretrain(record, dataset_name, chunk_size))
            views["qa_view"].extend(document_to_qa(record, dataset_name))
            views["instruction_view"].extend(document_to_instruction(record, dataset_name))
            views["knowledge_view"].extend(document_to_knowledge(record, dataset_name))
        elif record.schema_type == "StructuredRecord":
            views["qa_view"].extend(structured_to_qa(record, dataset_name))
            views["instruction_view"].extend(structured_to_instruction(record, dataset_name))
            views["knowledge_view"].extend(structured_to_knowledge(record, dataset_name))
    return views

