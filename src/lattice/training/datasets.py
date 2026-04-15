from __future__ import annotations

import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _views_dir(dataset_dir: str | Path) -> Path:
    root = Path(dataset_dir)
    candidate = root / "views"
    return candidate if candidate.exists() else root


def load_pretrain_texts(dataset_dir: str | Path) -> list[str]:
    views_dir = _views_dir(dataset_dir)
    rows = _load_jsonl(views_dir / "pretrain_view.jsonl")
    return [str(row.get("text", "")) for row in rows if row.get("text")]


def load_supervised_texts(dataset_dir: str | Path) -> list[str]:
    views_dir = _views_dir(dataset_dir)
    texts: list[str] = []

    for row in _load_jsonl(views_dir / "instruction_view.jsonl"):
        instruction = str(row.get("instruction", "")).strip()
        inp = str(row.get("input", "")).strip()
        output = str(row.get("output", "")).strip()
        if output:
            prompt = f"Instruction: {instruction}\nInput: {inp}\nOutput: {output}"
            texts.append(prompt)

    for row in _load_jsonl(views_dir / "qa_view.jsonl"):
        question = str(row.get("question", "")).strip()
        answer = str(row.get("answer", "")).strip()
        if answer:
            texts.append(f"Question: {question}\nAnswer: {answer}")

    for row in _load_jsonl(views_dir / "knowledge_view.jsonl"):
        subject = str(row.get("subject", "")).strip()
        predicate = str(row.get("predicate", "")).strip()
        obj = str(row.get("object", "")).strip()
        if obj:
            texts.append(f"Knowledge: {subject} {predicate} {obj}")

    return texts


def load_posttrain_texts(dataset_dir: str | Path) -> list[str]:
    views_dir = _views_dir(dataset_dir)
    rows = _load_jsonl(views_dir / "posttrain_view.jsonl")
    if rows:
        return [
            f"Prompt: {row.get('prompt', '')}\nPreferred: {row.get('response', '')}"
            for row in rows
            if row.get("response")
        ]
    return load_supervised_texts(dataset_dir)

