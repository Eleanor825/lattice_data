from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lattice.utils import read_json, write_json


SPECIAL_TOKENS = ["<pad>", "<bos>", "<eos>"]


@dataclass(slots=True)
class CharTokenizer:
    vocab: dict[str, int]

    @classmethod
    def build(cls, texts: Iterable[str]) -> "CharTokenizer":
        chars = sorted({char for text in texts for char in text})
        vocab = {token: index for index, token in enumerate(SPECIAL_TOKENS)}
        for char in chars:
            if char not in vocab:
                vocab[char] = len(vocab)
        return cls(vocab=vocab)

    @classmethod
    def load(cls, path: str | Path) -> "CharTokenizer":
        payload = read_json(path)
        return cls(vocab={str(key): int(value) for key, value in payload["vocab"].items()})

    @property
    def pad_id(self) -> int:
        return self.vocab["<pad>"]

    @property
    def bos_id(self) -> int:
        return self.vocab["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.vocab["<eos>"]

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def encode(self, text: str, max_length: int) -> list[int]:
        ids = [self.bos_id]
        for char in text:
            ids.append(self.vocab.get(char, self.pad_id))
        ids.append(self.eos_id)
        return ids[:max_length]

    def save(self, path: str | Path) -> None:
        write_json(path, {"vocab": self.vocab, "special_tokens": SPECIAL_TOKENS})

