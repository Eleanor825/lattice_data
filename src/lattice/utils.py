from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "record"


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def split_paragraphs(text: str) -> list[str]:
    paragraphs = [segment.strip() for segment in text.split("\n\n")]
    return [segment for segment in paragraphs if segment]


def chunk_text(text: str, max_chars: int = 1200) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in split_paragraphs(text):
        part_len = len(paragraph) + 2
        if current and current_len + part_len > max_chars:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += part_len
    if current:
        chunks.append("\n\n".join(current))
    return chunks or [text]


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + os.linesep)


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write(os.linesep)

