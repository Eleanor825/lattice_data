from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


class TinyCausalLM(nn.Module):
    def __init__(self, vocab_size: int, hidden_size: int = 96, num_layers: int = 2) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size, num_layers=num_layers, batch_first=True)
        self.norm = nn.LayerNorm(hidden_size)
        self.lm_head = nn.Linear(hidden_size, vocab_size)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        hidden = self.embedding(input_ids)
        hidden, _ = self.gru(hidden)
        hidden = self.norm(hidden)
        return self.lm_head(hidden)


@dataclass(slots=True)
class TrainingState:
    epoch: int
    loss: float

