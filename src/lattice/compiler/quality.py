from __future__ import annotations

import re
from collections import Counter

from lattice.models import Record, record_text
from lattice.utils import normalize_whitespace, stable_hash, word_count


BOILERPLATE_PATTERNS = (
    "cookie policy",
    "subscribe now",
    "all rights reserved",
    "accept cookies",
)


def compute_quality(record: Record) -> dict[str, float | int | bool | str]:
    text = normalize_whitespace(record_text(record)).lower()
    tokens = re.findall(r"\b\w+\b", text)
    total_tokens = len(tokens)
    unique_ratio = len(set(tokens)) / max(total_tokens, 1)
    alpha_chars = sum(char.isalpha() for char in text)
    alnum_ratio = alpha_chars / max(len(text), 1)
    has_boilerplate = any(pattern in text for pattern in BOILERPLATE_PATTERNS)
    quality = {
        "word_count": total_tokens,
        "unique_ratio": round(unique_ratio, 4),
        "alpha_ratio": round(alnum_ratio, 4),
        "has_boilerplate": has_boilerplate,
        "content_hash": stable_hash(text),
    }
    return quality


def retrieval_fitness(
    *,
    text: str,
    entity_count: int,
    has_title: bool,
    has_citation: bool,
) -> float:
    title_bonus = 0.15 if has_title else 0.0
    entity_bonus = min(0.3, 0.1 * entity_count)
    citation_bonus = 0.15 if has_citation else 0.0
    length_bonus = min(0.4, len(text.split()) / 200.0)
    return round(title_bonus + entity_bonus + citation_bonus + length_bonus, 4)


def retrieval_fitness_breakdown(
    *,
    text: str,
    entity_count: int,
    has_title: bool,
    has_citation: bool,
) -> dict[str, float]:
    title_bonus = 0.15 if has_title else 0.0
    entity_bonus = min(0.3, 0.1 * entity_count)
    citation_bonus = 0.15 if has_citation else 0.0
    length_bonus = min(0.4, len(text.split()) / 200.0)
    score = round(title_bonus + entity_bonus + citation_bonus + length_bonus, 4)
    return {
        "score": score,
        "title_bonus": round(title_bonus, 4),
        "entity_bonus": round(entity_bonus, 4),
        "citation_bonus": round(citation_bonus, 4),
        "length_bonus": round(length_bonus, 4),
    }


def filter_records(records: list[Record]) -> tuple[list[Record], Counter[str]]:
    kept: list[Record] = []
    dropped: Counter[str] = Counter()
    seen_hashes: set[str] = set()
    for record in records:
        quality = compute_quality(record)
        record.quality = quality
        content_hash = str(quality["content_hash"])
        if record.schema_type in {"Document", "InstructionTrace"} and quality["word_count"] < 12:
            dropped["too_short"] += 1
            continue
        if quality["has_boilerplate"]:
            dropped["boilerplate"] += 1
            continue
        if record.schema_type == "Document" and float(quality["unique_ratio"]) < 0.30:
            dropped["low_information_density"] += 1
            continue
        if content_hash in seen_hashes:
            dropped["duplicate"] += 1
            continue
        seen_hashes.add(content_hash)
        record.metadata.dedup_id = content_hash
        kept.append(record)
    return kept, dropped
