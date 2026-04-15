from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from lattice.training.model import TinyCausalLM, TrainingState
from lattice.training.tokenization import CharTokenizer


class TextDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer: CharTokenizer, max_length: int) -> None:
        self.samples = [tokenizer.encode(text, max_length=max_length) for text in texts if text.strip()]
        self.pad_id = tokenizer.pad_id

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> list[int]:
        return self.samples[index]


def _collate(batch: list[list[int]], pad_id: int) -> torch.Tensor:
    max_len = max(len(item) for item in batch)
    padded = [item + [pad_id] * (max_len - len(item)) for item in batch]
    return torch.tensor(padded, dtype=torch.long)


@dataclass(slots=True)
class LoopConfig:
    learning_rate: float = 3e-4
    epochs: int = 1
    batch_size: int = 2
    max_length: int = 192
    hidden_size: int = 96


def train_model(
    *,
    texts: list[str],
    tokenizer: CharTokenizer,
    model: TinyCausalLM,
    config: LoopConfig,
    device: str = "cpu",
) -> list[TrainingState]:
    dataset = TextDataset(texts, tokenizer, max_length=config.max_length)
    loader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        collate_fn=lambda batch: _collate(batch, tokenizer.pad_id),
    )
    model.to(device)
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_id)
    history: list[TrainingState] = []

    for epoch in range(config.epochs):
        running_loss = 0.0
        steps = 0
        for batch in loader:
            batch = batch.to(device)
            logits = model(batch)
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = batch[:, 1:].contiguous()
            loss = criterion(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item())
            steps += 1

        epoch_loss = running_loss / max(steps, 1)
        history.append(TrainingState(epoch=epoch + 1, loss=epoch_loss))

    return history

