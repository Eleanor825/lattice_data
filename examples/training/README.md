# Training Demo Dataset

This dataset provides a tiny compiled-view fixture for local workflow validation.

Use it with:

```bash
PYTHONPATH=src python3 -m lattice train-pretrain \
  --input examples/training/demo_dataset \
  --output training-runs/pretrain-demo \
  --run-name pretrain-demo
```
