from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from lattice.targets.specs import TargetSpec


@dataclass(slots=True)
class CompilationPlan:
    target_type: str
    sources: list[str] = field(default_factory=list)
    transforms: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    scoring_profile: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_compilation_plan(
    spec: TargetSpec,
    *,
    selected_sources: list[str],
) -> CompilationPlan:
    if spec.target_type == "rag_corpus":
        return CompilationPlan(
            target_type=spec.target_type,
            sources=selected_sources,
            transforms=[
                "record_to_entity",
                "document_to_grounded_chunk",
                "entity_linking",
                "target_ranking",
            ],
            output_files=["chunks.jsonl", "entities.jsonl", "links.jsonl"],
            scoring_profile=["base_quality", "retrieval_fitness"],
            notes=["Section-aware chunking is approximated from normalized document boundaries in phase 1."],
        )

    if spec.target_type == "pretrain_corpus":
        return CompilationPlan(
            target_type=spec.target_type,
            sources=selected_sources,
            transforms=["document_to_pretrain_span", "target_ranking"],
            output_files=["pretrain_spans.jsonl"],
            scoring_profile=["base_quality", "pretrain_fitness"],
        )

    if spec.target_type == "sft_dataset":
        return CompilationPlan(
            target_type=spec.target_type,
            sources=selected_sources,
            transforms=[
                "record_to_entity",
                "document_to_instruction_sample",
                "structured_record_to_instruction_sample",
                "target_ranking",
            ],
            output_files=["instruction_samples.jsonl"],
            scoring_profile=["base_quality", "sft_fitness"],
        )

    if spec.target_type == "preference_dataset":
        return CompilationPlan(
            target_type=spec.target_type,
            sources=selected_sources,
            transforms=[
                "record_to_entity",
                "instruction_sample_to_preference_pair",
                "target_ranking",
            ],
            output_files=["preference_pairs.jsonl"],
            scoring_profile=["base_quality", "preference_fitness"],
            notes=["Preference pairs are weakly supervised in phase 1."],
        )

    return CompilationPlan(
        target_type=spec.target_type,
        sources=selected_sources,
        transforms=[
            "record_to_entity",
            "record_to_eval_item",
            "target_ranking",
        ],
        output_files=["eval_items.jsonl"],
        scoring_profile=["base_quality", "eval_fitness"],
    )
