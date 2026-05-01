# Target Compiler Quickstart

## Build a RAG Corpus

```bash
PYTHONPATH=src python3 -m lattice build-target \
  --input examples/materials/raw \
  --output outputs/target-rag-demo \
  --target-spec examples/targets/rag_corpus.yaml \
  --source openalex \
  --source pubchem
```

## Build an SFT Dataset

```bash
PYTHONPATH=src python3 -m lattice build-target \
  --input examples/materials/raw \
  --output outputs/target-sft-demo \
  --target-spec examples/targets/sft_dataset.yaml
```

## Build an Eval Dataset

```bash
PYTHONPATH=src python3 -m lattice build-target \
  --input examples/materials/raw \
  --output outputs/target-eval-demo \
  --target-spec examples/targets/eval_dataset.yaml
```

## Outputs

Each target build emits:

- `outputs/` target-specific dataset files
- `reports/manifest.json`
- `reports/dataset_card.md`

## Example Target Specs

- [RAG](./../examples/targets/rag_corpus.yaml)
- [Pretrain](./../examples/targets/pretrain_corpus.yaml)
- [SFT](./../examples/targets/sft_dataset.yaml)
- [Preference](./../examples/targets/preference_dataset.yaml)
- [Eval](./../examples/targets/eval_dataset.yaml)
