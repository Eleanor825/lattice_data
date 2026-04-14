.PHONY: test compile-example stats clean

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

compile-example:
	PYTHONPATH=src python3 -m lattice compile \
		--input examples/materials/raw \
		--output outputs/materials \
		--domain materials \
		--dataset-name Lattice-Materials-v0.1

stats:
	PYTHONPATH=src python3 -m lattice stats --path outputs/materials

clean:
	rm -rf outputs
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

