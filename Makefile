.PHONY: test compile-example demo fetch-p0 engine-check engine-local engine-spark engine-flink stats clean

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

engine-check:
	PYTHONPATH=src python3 -m lattice engine-check

engine-local:
	PYTHONPATH=src python3 -m lattice engine-compile \
		--engine local \
		--input examples/runtime/raw \
		--output outputs/runtime-local \
		--domain materials \
		--dataset-name Lattice-Runtime-Local

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

stats:
	PYTHONPATH=src python3 -m lattice stats --path outputs/materials

clean:
	rm -rf outputs
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
