from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import torch

from lattice.sources.common import timestamp_now
from lattice.training.datasets import load_posttrain_texts, load_pretrain_texts, load_supervised_texts
from lattice.training.loop import LoopConfig, train_model
from lattice.training.model import TinyCausalLM
from lattice.training.tokenization import CharTokenizer
from lattice.utils import ensure_dir, write_json


@dataclass(slots=True)
class TrainingConfig:
    workflow: str
    input_dir: str
    output_dir: str
    run_name: str
    checkpoint_dir: str = ""
    epochs: int = 1
    batch_size: int = 2
    learning_rate: float = 3e-4
    max_length: int = 192
    hidden_size: int = 96


@dataclass(slots=True)
class TrainingWorkflowResult:
    workflow: str
    run_name: str
    output_dir: str
    sample_count: int
    final_loss: float


def _load_texts(config: TrainingConfig) -> list[str]:
    if config.workflow == "pretrain":
        return load_pretrain_texts(config.input_dir)
    if config.workflow == "continue":
        return load_pretrain_texts(config.input_dir)
    if config.workflow == "finetune":
        return load_supervised_texts(config.input_dir)
    if config.workflow == "posttrain":
        return load_posttrain_texts(config.input_dir)
    raise ValueError(f"Unsupported workflow: {config.workflow}")


def _device() -> str:
    return "cpu"


def _save_checkpoint(
    output_dir: Path,
    *,
    config: TrainingConfig,
    tokenizer: CharTokenizer,
    model: TinyCausalLM,
    history: list,
    sample_count: int,
) -> TrainingWorkflowResult:
    ensure_dir(output_dir / "model")
    ensure_dir(output_dir / "reports")
    tokenizer.save(output_dir / "model" / "tokenizer.json")
    torch.save(
        {
            "state_dict": model.state_dict(),
            "model_config": {
                "vocab_size": tokenizer.vocab_size,
                "hidden_size": config.hidden_size,
                "num_layers": 2,
            },
        },
        output_dir / "model" / "model.pt",
    )
    manifest = {
        "generated_at": timestamp_now(),
        "workflow": config.workflow,
        "run_name": config.run_name,
        "input_dir": str(Path(config.input_dir).resolve()),
        "checkpoint_dir": str(Path(config.checkpoint_dir).resolve()) if config.checkpoint_dir else "",
        "output_dir": str(output_dir.resolve()),
        "config": asdict(config),
        "sample_count": sample_count,
        "history": [asdict(item) for item in history],
        "final_loss": history[-1].loss if history else None,
        "device": _device(),
    }
    write_json(output_dir / "reports" / "manifest.json", manifest)
    return TrainingWorkflowResult(
        workflow=config.workflow,
        run_name=config.run_name,
        output_dir=str(output_dir.resolve()),
        sample_count=sample_count,
        final_loss=float(history[-1].loss if history else 0.0),
    )


def run_training_workflow(config: TrainingConfig) -> TrainingWorkflowResult:
    texts = _load_texts(config)
    if not texts:
        raise RuntimeError(f"No training samples found for workflow '{config.workflow}' in {config.input_dir}")

    output_dir = ensure_dir(config.output_dir)
    loop_config = LoopConfig(
        learning_rate=config.learning_rate,
        epochs=config.epochs,
        batch_size=config.batch_size,
        max_length=config.max_length,
        hidden_size=config.hidden_size,
    )

    if config.workflow in {"continue", "finetune", "posttrain"} and config.checkpoint_dir:
        checkpoint = torch.load(
            Path(config.checkpoint_dir) / "model" / "model.pt",
            map_location="cpu",
            weights_only=False,
        )
        tokenizer = CharTokenizer.load(Path(config.checkpoint_dir) / "model" / "tokenizer.json")
        model = TinyCausalLM(
            vocab_size=int(checkpoint["model_config"]["vocab_size"]),
            hidden_size=int(checkpoint["model_config"]["hidden_size"]),
            num_layers=int(checkpoint["model_config"]["num_layers"]),
        )
        model.load_state_dict(checkpoint["state_dict"])
    else:
        tokenizer = CharTokenizer.build(texts)
        model = TinyCausalLM(vocab_size=tokenizer.vocab_size, hidden_size=config.hidden_size, num_layers=2)

    history = train_model(
        texts=texts,
        tokenizer=tokenizer,
        model=model,
        config=loop_config,
        device=_device(),
    )

    return _save_checkpoint(
        output_dir=Path(output_dir),
        config=config,
        tokenizer=tokenizer,
        model=model,
        history=history,
        sample_count=len(texts),
    )
