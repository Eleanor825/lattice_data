# Training Workflows

Lattice now includes four local reference training workflows:

- `pretrain`
- `continue`
- `finetune`
- `posttrain`

These workflows are intentionally lightweight and local-first. They are designed to prove that the platform can connect Phase 1 compiled data to executable model training steps.

## Commands

```bash
PYTHONPATH=src python3 -m lattice train-pretrain \
  --input examples/training/demo_dataset \
  --output training-runs/pretrain-demo \
  --run-name pretrain-demo
```

```bash
PYTHONPATH=src python3 -m lattice train-continue \
  --input examples/training/demo_dataset \
  --output training-runs/continue-demo \
  --run-name continue-demo \
  --checkpoint-dir training-runs/pretrain-demo
```

```bash
PYTHONPATH=src python3 -m lattice train-finetune \
  --input examples/training/demo_dataset \
  --output training-runs/finetune-demo \
  --run-name finetune-demo \
  --checkpoint-dir training-runs/continue-demo
```

```bash
PYTHONPATH=src python3 -m lattice train-post \
  --input examples/training/demo_dataset \
  --output training-runs/post-demo \
  --run-name post-demo \
  --checkpoint-dir training-runs/finetune-demo
```

## Current Implementation

The current implementation is a compact local reference stack:

- character-level tokenizer
- tiny causal language model
- local PyTorch training loop
- manifest-backed outputs

This is not meant to be the final large-scale trainer. It is meant to make the workflow executable and debuggable now.
