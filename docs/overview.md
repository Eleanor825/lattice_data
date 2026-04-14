# Lattice Overview

## Goal

Lattice treats raw domain sources as input programs and compiles them into multiple training-ready dataset views.

## Phase 1 Pipeline

1. Ingest heterogeneous files from a source directory.
2. Normalize them into a minimal schema family.
3. Score and filter low-value records.
4. Export reusable dataset views.
5. Write manifests for reproducibility and auditing.

## Phase 2 Placeholder

Phase 2 will consume Phase 1 artifacts and add:

- value vectors
- proxy experiments
- mixture selection
- feeding schedule optimization

