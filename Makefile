.PHONY: test compile-example demo fetch-p0 phase1-release engine-check engine-local engine-pandas engine-spark engine-flink train-pretrain train-continue train-finetune train-post phase2-open phase2-closed stats clean

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

compile-example:
	PYTHONPATH=src python3 -m lattice compile \
		--input examples/materials/raw \
		--output outputs/materials \
		--domain materials \
		--dataset-name Lattice-Materials-v0.1

demo:
	PYTHONPATH=src python3 -m lattice demo \
		--raw-output data/demo_raw/solid_state \
		--compiled-output data/demo_compiled/solid_state \
		--domain materials \
		--dataset-name Lattice-Materials-RealDemo \
		--query "solid state battery electrolyte" \
		--compound "lithium iron phosphate" \
		--compound "lithium cobalt oxide"

fetch-p0:
	PYTHONPATH=src python3 -m lattice fetch-sources \
		--output data/p0_materials/li_o \
		--registry configs/source_registry.json \
		--domain materials \
		--source oqmd \
		--source nomad \
		--source materials_project \
		--element Li \
		--element O \
		--limit 2

phase1-release:
	PYTHONPATH=src python3 -m lattice phase1-run \
		--data-root ~/lattice-data \
		--registry configs/source_registry.json \
		--domain materials \
		--release-name lattice-materials-demo \
		--query "solid state battery electrolyte" \
		--compound "lithium iron phosphate" \
		--compound "lithium cobalt oxide" \
		--limit 2

engine-check:
	PYTHONPATH=src python3 -m lattice engine-check

engine-local:
	PYTHONPATH=src python3 -m lattice engine-compile \
		--engine local \
		--input examples/runtime/raw \
		--output outputs/runtime-local \
		--domain materials \
		--dataset-name Lattice-Runtime-Local

engine-pandas:
	PYTHONPATH=src python3 -m lattice engine-compile \
		--engine pandas \
		--input examples/runtime/raw \
		--output outputs/runtime-pandas \
		--domain materials \
		--dataset-name Lattice-Runtime-Pandas

engine-spark:
	PYTHONPATH=src python3 -m lattice engine-compile \
		--engine spark \
		--input examples/runtime/raw \
		--output outputs/runtime-spark \
		--domain materials \
		--dataset-name Lattice-Runtime-Spark

engine-flink:
	PYTHONPATH=src python3 -m lattice engine-compile \
		--engine flink \
		--input examples/runtime/raw \
		--output outputs/runtime-flink \
		--domain materials \
		--dataset-name Lattice-Runtime-Flink

train-pretrain:
	PYTHONPATH=src python3 -m lattice train-pretrain \
		--input examples/training/demo_dataset \
		--output training-runs/pretrain-demo \
		--run-name pretrain-demo

train-continue:
	PYTHONPATH=src python3 -m lattice train-continue \
		--input examples/training/demo_dataset \
		--output training-runs/continue-demo \
		--run-name continue-demo \
		--checkpoint-dir training-runs/pretrain-demo

train-finetune:
	PYTHONPATH=src python3 -m lattice train-finetune \
		--input examples/training/demo_dataset \
		--output training-runs/finetune-demo \
		--run-name finetune-demo \
		--checkpoint-dir training-runs/continue-demo

train-post:
	PYTHONPATH=src python3 -m lattice train-post \
		--input examples/training/demo_dataset \
		--output training-runs/post-demo \
		--run-name post-demo \
		--checkpoint-dir training-runs/finetune-demo

phase2-open:
	PYTHONPATH=src python3 -m lattice phase2-run \
		--workflow finetune \
		--engine pandas \
		--input examples/training/demo_dataset \
		--output training-runs/phase2-open \
		--run-name phase2-open \
		--model-backend local_tiny \
		--model-name tiny-local \
		--compiled-input

phase2-closed:
	PYTHONPATH=src python3 -m lattice phase2-run \
		--workflow posttrain \
		--engine pandas \
		--input examples/training/demo_dataset \
		--output training-runs/phase2-closed \
		--run-name phase2-closed \
		--model-backend external_connector \
		--model-name closed-provider-model \
		--provider openai_compatible \
		--model-family closed \
		--compiled-input

stats:
	PYTHONPATH=src python3 -m lattice stats --path outputs/materials

clean:
	rm -rf outputs
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
