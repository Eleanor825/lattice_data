from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from lattice.compiler.quality import retrieval_fitness_breakdown
from lattice.models import Record
from lattice.targets.artifacts import Artifact
from lattice.targets.specs import TargetSpec
from lattice.utils import chunk_text, normalize_whitespace, slugify, stable_hash


TransformFn = Callable[[list[Artifact], TargetSpec], list[Artifact]]


@dataclass(slots=True)
class Transform:
    name: str
    input_types: tuple[str, ...]
    output_type: str
    supported_targets: set[str] = field(default_factory=set)
    runner: TransformFn | None = None

    def run(self, inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
        if self.runner is None:
            raise RuntimeError(f"Transform '{self.name}' has no runner.")
        return self.runner(inputs, spec)


def record_to_artifact(record: Record) -> Artifact:
    source_ref = {
        "source_record_id": record.record_id,
        "source_id": record.metadata.source_id,
        "source_type": record.metadata.source_type,
        "source_ref": record.metadata.url_or_ref,
        "license": record.metadata.license,
        "provenance_chain": list(record.metadata.provenance_chain),
        "dedup_id": record.metadata.dedup_id,
    }
    return Artifact(
        artifact_id=f"art-{record.record_id}",
        artifact_type=record.schema_type,
        domain=record.metadata.domain,
        payload=dict(record.payload),
        source_refs=[source_ref],
        license_status=record.metadata.license,
        quality=dict(record.quality),
        policy={"license_policy": "unknown"},
        lineage=[record.record_id],
    )


def build_base_artifacts(records: list[Record]) -> list[Artifact]:
    return [record_to_artifact(record) for record in records]


def _entity_names(artifact: Artifact) -> list[str]:
    if artifact.artifact_type == "StructuredRecord":
        entity = str(artifact.payload.get("entity", "")).strip()
        return [entity] if entity else []
    if artifact.artifact_type == "KnowledgeRecord":
        subject = str(artifact.payload.get("subject", "")).strip()
        return [subject] if subject else []
    if artifact.artifact_type == "Document":
        title = str(artifact.payload.get("title", "")).strip()
        return [title] if title else []
    return []


def entity_transform(inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
    del spec
    grouped: dict[str, Artifact] = {}
    for artifact in inputs:
        for entity_name in _entity_names(artifact):
            canonical = slugify(entity_name)
            entity_id = f"ent-{stable_hash(canonical)}"
            existing = grouped.get(entity_id)
            if existing is None:
                grouped[entity_id] = Artifact(
                    artifact_id=entity_id,
                    artifact_type="Entity",
                    domain=artifact.domain,
                    payload={
                        "entity_id": entity_id,
                        "canonical_name": entity_name,
                        "aliases": [entity_name],
                        "formula": "",
                        "source_ids": [ref["source_id"] for ref in artifact.source_refs],
                        "record_ids": list(artifact.lineage),
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality={},
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            else:
                aliases = existing.payload.setdefault("aliases", [])
                if entity_name not in aliases:
                    aliases.append(entity_name)
                for ref in artifact.source_refs:
                    if ref["source_id"] not in existing.payload["source_ids"]:
                        existing.payload["source_ids"].append(ref["source_id"])
                    if ref not in existing.source_refs:
                        existing.source_refs.append(ref)
                for record_id in artifact.lineage:
                    if record_id not in existing.payload["record_ids"]:
                        existing.payload["record_ids"].append(record_id)
                    if record_id not in existing.lineage:
                        existing.lineage.append(record_id)
    return sorted(grouped.values(), key=lambda artifact: artifact.artifact_id)


def grounded_chunk_transform(inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
    chunk_size = int(spec.target_config.get("chunk_size", spec.constraints.get("chunk_size", 1200)))
    min_chunk_words = int(spec.target_config.get("min_chunk_words", spec.constraints.get("min_chunk_words", 20)))
    entity_artifacts = [artifact for artifact in inputs if artifact.artifact_type == "Entity"]
    entity_aliases = {
        artifact.payload["entity_id"]: list(artifact.payload.get("aliases", []))
        for artifact in entity_artifacts
    }
    rows: list[Artifact] = []
    seen_chunk_hashes: set[str] = set()
    for artifact in inputs:
        if artifact.artifact_type != "Document":
            continue
        title = str(artifact.payload.get("title", "")).strip()
        text = str(artifact.payload.get("text", "")).strip()
        sections = list(artifact.payload.get("sections", []))
        if not text:
            continue
        matched_entities: list[str] = []
        lowered_text = f"{title}\n{text}".lower()
        for entity_id, aliases in entity_aliases.items():
            if any(alias and alias.lower() in lowered_text for alias in aliases):
                matched_entities.append(entity_id)
        chunk_sources: list[tuple[str, str]]
        if sections:
            chunk_sources = []
            for section in sections:
                section_title = str(section.get("title", "body")).strip() or "body"
                section_text = str(section.get("text", "")).strip()
                if not section_text:
                    continue
                for chunk in chunk_text(section_text, max_chars=chunk_size):
                    chunk_sources.append((section_title, chunk))
        else:
            chunk_sources = [("body", chunk) for chunk in chunk_text(text, max_chars=chunk_size)]

        for index, (section_name, chunk) in enumerate(chunk_sources, start=1):
            normalized = normalize_whitespace(chunk)
            if len(normalized.split()) < min_chunk_words:
                continue
            chunk_hash = stable_hash(normalized.lower())
            if chunk_hash in seen_chunk_hashes:
                continue
            seen_chunk_hashes.add(chunk_hash)
            source_ref = artifact.source_refs[0]
            citation_payload = {
                "title": title,
                "source_ref": source_ref["source_ref"],
                "source_type": source_ref["source_type"],
                "source_id": source_ref["source_id"],
            }
            rows.append(
                Artifact(
                    artifact_id=f"chunk-{stable_hash(artifact.artifact_id + str(index))}",
                    artifact_type="GroundedChunk",
                    domain=artifact.domain,
                    payload={
                        "chunk_id": f"chunk-{stable_hash(artifact.artifact_id + str(index))}",
                        "text": normalized,
                        "title": title,
                        "section": section_name,
                        "entity_ids": matched_entities,
                        "citation_payload": citation_payload,
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality=_with_score_breakdown(
                        score_name="retrieval_fitness",
                        breakdown=retrieval_fitness_breakdown(
                            text=normalized,
                            entity_count=len(matched_entities),
                            has_title=bool(title),
                            has_citation=bool(source_ref["source_ref"]),
                        ),
                        extra={"citation_completeness": 1.0 if source_ref["source_ref"] and source_ref["source_type"] else 0.0},
                    ),
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            )
    return rows


def pretrain_span_transform(inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
    chunk_size = int(spec.target_config.get("chunk_size", spec.constraints.get("chunk_size", 1800)))
    min_span_words = int(spec.target_config.get("min_span_words", spec.constraints.get("min_span_words", 20)))
    rows: list[Artifact] = []
    for artifact in inputs:
        if artifact.artifact_type != "Document":
            continue
        text = str(artifact.payload.get("text", "")).strip()
        if not text:
            continue
        for index, chunk in enumerate(chunk_text(text, max_chars=chunk_size), start=1):
            normalized = normalize_whitespace(chunk)
            if len(normalized.split()) < min_span_words:
                continue
            rows.append(
                Artifact(
                    artifact_id=f"pre-{stable_hash(artifact.artifact_id + str(index))}",
                    artifact_type="PretrainSpan",
                    domain=artifact.domain,
                    payload={
                        "span_id": f"pre-{stable_hash(artifact.artifact_id + str(index))}",
                        "text": normalized,
                        "title": str(artifact.payload.get("title", "")),
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality=_with_score_breakdown(
                        score_name="pretrain_fitness",
                        breakdown=_pretrain_fitness(normalized),
                        extra={"source_balance_hint": artifact.source_refs[0].get("source_type", "")},
                    ),
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            )
    return rows


def instruction_sample_transform(inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
    min_output_words = int(spec.target_config.get("min_output_words", spec.constraints.get("min_output_words", 8)))
    rows: list[Artifact] = []
    for artifact in inputs:
        if artifact.artifact_type == "Document":
            title = str(artifact.payload.get("title", "")).strip()
            text = str(artifact.payload.get("text", "")).strip()
            output = " ".join(text.split()[:80]).strip()
            evidence = text[:400]
            if not output or len(output.split()) < min_output_words:
                continue
            rows.append(
                Artifact(
                    artifact_id=f"ins-{stable_hash(artifact.artifact_id)}",
                    artifact_type="InstructionSample",
                    domain=artifact.domain,
                    payload={
                        "sample_id": f"ins-{stable_hash(artifact.artifact_id)}",
                        "task_type": "grounded_summarization",
                        "instruction": f"Summarize the materials-science source '{title}' using grounded evidence.",
                        "input": title,
                        "output": output,
                        "evidence": evidence,
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality=_with_score_breakdown(
                        score_name="sft_fitness",
                        breakdown=_sft_fitness(output, bool(evidence)),
                        extra={"evidence_completeness": 1.0 if evidence else 0.0},
                    ),
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            )
        elif artifact.artifact_type == "StructuredRecord":
            entity = str(artifact.payload.get("entity", "")).strip()
            fields = dict(artifact.payload.get("fields", {}))
            output = "; ".join(f"{key}: {value}" for key, value in fields.items())
            evidence = str(artifact.payload.get("description", ""))
            if not output or len(output.split()) < max(1, min_output_words // 2):
                continue
            rows.append(
                Artifact(
                    artifact_id=f"ins-{stable_hash(artifact.artifact_id)}",
                    artifact_type="InstructionSample",
                    domain=artifact.domain,
                    payload={
                        "sample_id": f"ins-{stable_hash(artifact.artifact_id)}",
                        "task_type": "property_listing",
                        "instruction": f"List the known properties of {entity}.",
                        "input": entity,
                        "output": output,
                        "evidence": evidence,
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality=_with_score_breakdown(
                        score_name="sft_fitness",
                        breakdown=_sft_fitness(output, bool(evidence)),
                        extra={"evidence_completeness": 1.0 if evidence else 0.5},
                    ),
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            )
    return rows


def preference_pair_transform(inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
    del spec
    rows: list[Artifact] = []
    for artifact in inputs:
        if artifact.artifact_type != "InstructionSample":
            continue
        output = str(artifact.payload.get("output", "")).strip()
        if not output:
            continue
        words = output.split()
        rejected = " ".join(words[: max(1, len(words) // 2)]).strip()
        if rejected == output:
            rejected = output[: max(1, len(output) // 2)].strip()
        rows.append(
            Artifact(
                artifact_id=f"pref-{stable_hash(artifact.artifact_id)}",
                artifact_type="PreferencePair",
                domain=artifact.domain,
                payload={
                    "pair_id": f"pref-{stable_hash(artifact.artifact_id)}",
                    "instruction": artifact.payload["instruction"],
                    "input": artifact.payload["input"],
                    "chosen": output,
                    "rejected": rejected,
                    "reason_code": "more_complete_grounded_answer",
                },
                source_refs=list(artifact.source_refs),
                license_status=artifact.license_status,
                quality=_with_score_breakdown(
                    score_name="preference_fitness",
                    breakdown={
                        "score": round(float(artifact.quality.get("sft_fitness", 0.0)), 4),
                        "source_sft_score": round(float(artifact.quality.get("sft_fitness", 0.0)), 4),
                    },
                    extra={"pair_validity": 1.0 if output and rejected and output != rejected else 0.0},
                ),
                policy=dict(artifact.policy),
                lineage=list(artifact.lineage),
            )
        )
    return rows


def eval_item_transform(inputs: list[Artifact], spec: TargetSpec) -> list[Artifact]:
    del spec
    rows: list[Artifact] = []
    for artifact in inputs:
        if artifact.artifact_type == "Document":
            title = str(artifact.payload.get("title", "")).strip()
            text = str(artifact.payload.get("text", "")).strip()
            if not text:
                continue
            answer = next((segment.strip() for segment in text.split(".") if segment.strip()), text[:200])
            evidence = text[:300]
            rows.append(
                Artifact(
                    artifact_id=f"eval-{stable_hash(artifact.artifact_id)}",
                    artifact_type="EvalItem",
                    domain=artifact.domain,
                    payload={
                        "eval_id": f"eval-{stable_hash(artifact.artifact_id)}",
                        "eval_type": "grounded_qa",
                        "prompt": f"What is the main contribution of '{title}'?",
                        "gold_answer": answer,
                        "gold_evidence": evidence,
                        "rubric": "Answer should be grounded in the source text and capture the main contribution.",
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality=_with_score_breakdown(
                        score_name="eval_fitness",
                        breakdown=_eval_fitness(answer, bool(text)),
                        extra={
                            "judgeability": 1.0 if answer and evidence else 0.0,
                            "evidence_coverage": 1.0 if evidence else 0.0,
                        },
                    ),
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            )
        elif artifact.artifact_type == "StructuredRecord":
            entity = str(artifact.payload.get("entity", "")).strip()
            fields = dict(artifact.payload.get("fields", {}))
            for key, value in fields.items():
                evidence = str(artifact.payload.get("description", ""))
                rows.append(
                    Artifact(
                        artifact_id=f"eval-{stable_hash(artifact.artifact_id + key)}",
                        artifact_type="EvalItem",
                        domain=artifact.domain,
                        payload={
                            "eval_id": f"eval-{stable_hash(artifact.artifact_id + key)}",
                            "eval_type": "property_extraction",
                            "prompt": f"What is the {key.replace('_', ' ')} of {entity}?",
                            "gold_answer": value,
                            "gold_evidence": evidence,
                            "rubric": "Answer should exactly match the normalized property value.",
                        },
                        source_refs=list(artifact.source_refs),
                        license_status=artifact.license_status,
                        quality=_with_score_breakdown(
                            score_name="eval_fitness",
                            breakdown=_eval_fitness(str(value), bool(evidence)),
                            extra={
                                "judgeability": 1.0 if value else 0.0,
                                "evidence_coverage": 1.0 if evidence else 0.5,
                            },
                        ),
                        policy=dict(artifact.policy),
                        lineage=list(artifact.lineage),
                    )
                )
        elif artifact.artifact_type == "KnowledgeRecord":
            subject = str(artifact.payload.get("subject", "")).strip()
            predicate = str(artifact.payload.get("predicate", "")).strip()
            obj = str(artifact.payload.get("object", "")).strip()
            evidence = str(artifact.payload.get("evidence", "")).strip()
            if not subject or not obj:
                continue
            rows.append(
                Artifact(
                    artifact_id=f"eval-{stable_hash(artifact.artifact_id)}",
                    artifact_type="EvalItem",
                    domain=artifact.domain,
                    payload={
                        "eval_id": f"eval-{stable_hash(artifact.artifact_id)}",
                        "eval_type": "knowledge_grounding",
                        "prompt": f"What is known about {subject}?",
                        "gold_answer": f"{subject} {predicate} {obj}".strip(),
                        "gold_evidence": evidence or obj,
                        "rubric": "Answer should preserve the grounded knowledge statement and remain faithful to the source fact.",
                    },
                    source_refs=list(artifact.source_refs),
                    license_status=artifact.license_status,
                    quality=_with_score_breakdown(
                        score_name="eval_fitness",
                        breakdown=_eval_fitness(obj, bool(evidence or obj)),
                        extra={
                            "judgeability": 1.0,
                            "evidence_coverage": 1.0 if (evidence or obj) else 0.0,
                        },
                    ),
                    policy=dict(artifact.policy),
                    lineage=list(artifact.lineage),
                )
            )
    return rows


def register_default_transforms() -> dict[str, Transform]:
    transforms = [
        Transform(
            name="record_to_entity",
            input_types=("Document", "StructuredRecord", "KnowledgeRecord"),
            output_type="Entity",
            supported_targets={"rag_corpus", "sft_dataset", "preference_dataset", "eval_dataset"},
            runner=entity_transform,
        ),
        Transform(
            name="document_to_grounded_chunk",
            input_types=("Document", "Entity"),
            output_type="GroundedChunk",
            supported_targets={"rag_corpus"},
            runner=grounded_chunk_transform,
        ),
        Transform(
            name="document_to_pretrain_span",
            input_types=("Document",),
            output_type="PretrainSpan",
            supported_targets={"pretrain_corpus"},
            runner=pretrain_span_transform,
        ),
        Transform(
            name="record_to_instruction_sample",
            input_types=("Document", "StructuredRecord"),
            output_type="InstructionSample",
            supported_targets={"sft_dataset", "preference_dataset"},
            runner=instruction_sample_transform,
        ),
        Transform(
            name="instruction_sample_to_preference_pair",
            input_types=("InstructionSample",),
            output_type="PreferencePair",
            supported_targets={"preference_dataset"},
            runner=preference_pair_transform,
        ),
        Transform(
            name="record_to_eval_item",
            input_types=("Document", "StructuredRecord"),
            output_type="EvalItem",
            supported_targets={"eval_dataset"},
            runner=eval_item_transform,
        ),
    ]
    return {transform.name: transform for transform in transforms}


def register_transform(registry: dict[str, Transform], transform: Transform) -> dict[str, Transform]:
    registry[transform.name] = transform
    return registry


def _with_score_breakdown(*, score_name: str, breakdown: dict[str, float], extra: dict[str, object] | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        score_name: breakdown["score"],
        f"{score_name}_breakdown": breakdown,
    }
    if extra:
        payload.update(extra)
    return payload


def _pretrain_fitness(text: str) -> dict[str, float]:
    unique_words = len(set(text.lower().split()))
    total_words = max(len(text.split()), 1)
    unique_ratio = unique_words / total_words
    length_bonus = min(total_words / 300.0, 0.5)
    score = round(min(1.0, unique_ratio + length_bonus), 4)
    return {
        "score": score,
        "unique_ratio": round(unique_ratio, 4),
        "length_bonus": round(length_bonus, 4),
    }


def _sft_fitness(output: str, has_evidence: bool) -> dict[str, float]:
    evidence_bonus = 0.2 if has_evidence else 0.0
    completeness = min(0.6, len(output.split()) / 80.0)
    score = round(evidence_bonus + completeness, 4)
    return {
        "score": score,
        "evidence_bonus": round(evidence_bonus, 4),
        "completeness": round(completeness, 4),
    }


def _eval_fitness(answer: str, has_evidence: bool) -> dict[str, float]:
    evidence_bonus = 0.25 if has_evidence else 0.0
    answer_bonus = min(0.5, len(str(answer).split()) / 50.0)
    score = round(evidence_bonus + answer_bonus, 4)
    return {
        "score": score,
        "evidence_bonus": round(evidence_bonus, 4),
        "answer_bonus": round(answer_bonus, 4),
    }
