from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from lattice.compiler import CompilerConfig, compile_dataset
from lattice.engines import EngineConfig, engine_check, run_engine_compile
from lattice.phase2 import Phase2Config, run_phase2_pipeline
from lattice.platform.server import create_app
from lattice.platform.sync import sync_phase1_manifest, sync_phase2_manifest
from lattice.sources import DemoFetchConfig, SourceFetchConfig, run_demo_fetch, run_source_fetch
from lattice.training import TrainingConfig, run_training_workflow
from lattice.utils import read_json
from lattice.workflows import Phase1Config, run_phase1_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lattice", description="Lattice data compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile raw sources into dataset views.")
    compile_parser.add_argument("--input", required=True, help="Input directory containing raw sources.")
    compile_parser.add_argument("--output", required=True, help="Output directory for compiled artifacts.")
    compile_parser.add_argument("--domain", required=True, help="Target domain label.")
    compile_parser.add_argument("--dataset-name", required=True, help="Dataset release name.")
    compile_parser.add_argument("--chunk-size", type=int, default=1200, help="Maximum characters per pretrain chunk.")

    engine_compile_parser = subparsers.add_parser(
        "engine-compile", help="Compile normalized JSONL records with local, Spark, or Flink."
    )
    engine_compile_parser.add_argument("--engine", required=True, choices=["local", "pandas", "spark", "flink"])
    engine_compile_parser.add_argument("--input", required=True, help="Input directory containing JSONL source records.")
    engine_compile_parser.add_argument("--output", required=True, help="Output directory for compiled artifacts.")
    engine_compile_parser.add_argument("--domain", required=True, help="Target domain label.")
    engine_compile_parser.add_argument("--dataset-name", required=True, help="Dataset release name.")
    engine_compile_parser.add_argument("--chunk-size", type=int, default=1200, help="Maximum characters per pretrain chunk.")

    engine_check_parser = subparsers.add_parser(
        "engine-check", help="Run local runtime checks for local, Spark, and Flink engines."
    )

    fetch_parser = subparsers.add_parser("fetch-demo", help="Fetch a small real-source demo dataset.")
    fetch_parser.add_argument("--output", required=True, help="Directory for fetched raw source files.")
    fetch_parser.add_argument("--domain", default="materials", help="Target domain label.")
    fetch_parser.add_argument("--query", default="solid state battery electrolyte", help="Topic query.")
    fetch_parser.add_argument("--openalex-limit", type=int, default=3, help="Number of OpenAlex works to fetch.")
    fetch_parser.add_argument("--arxiv-limit", type=int, default=3, help="Number of arXiv entries to fetch.")
    fetch_parser.add_argument(
        "--compound",
        action="append",
        default=[],
        help="Compound name for PubChem lookup. Can be repeated.",
    )

    demo_parser = subparsers.add_parser("demo", help="Fetch a real-source demo and compile it.")
    demo_parser.add_argument("--raw-output", required=True, help="Directory for fetched raw source files.")
    demo_parser.add_argument("--compiled-output", required=True, help="Directory for compiled outputs.")
    demo_parser.add_argument("--domain", default="materials", help="Target domain label.")
    demo_parser.add_argument("--dataset-name", default="Lattice-Materials-RealDemo", help="Compiled dataset name.")
    demo_parser.add_argument("--query", default="solid state battery electrolyte", help="Topic query.")
    demo_parser.add_argument("--openalex-limit", type=int, default=3, help="Number of OpenAlex works to fetch.")
    demo_parser.add_argument("--arxiv-limit", type=int, default=3, help="Number of arXiv entries to fetch.")
    demo_parser.add_argument(
        "--compound",
        action="append",
        default=[],
        help="Compound name for PubChem lookup. Can be repeated.",
    )

    fetch_sources_parser = subparsers.add_parser(
        "fetch-sources", help="Fetch selected real sources from the source registry."
    )
    fetch_sources_parser.add_argument("--output", required=True, help="Directory for fetched raw source files.")
    fetch_sources_parser.add_argument("--domain", default="materials", help="Target domain label.")
    fetch_sources_parser.add_argument(
        "--registry",
        default="configs/source_registry.json",
        help="Path to the source registry JSON file.",
    )
    fetch_sources_parser.add_argument(
        "--source",
        action="append",
        required=True,
        help="Source name from the registry. Can be repeated.",
    )
    fetch_sources_parser.add_argument("--query", default="solid state battery electrolyte", help="Topic query.")
    fetch_sources_parser.add_argument(
        "--element",
        action="append",
        default=[],
        help="Element symbol for materials queries. Can be repeated.",
    )
    fetch_sources_parser.add_argument(
        "--compound",
        action="append",
        default=[],
        help="Compound name for PubChem lookup. Can be repeated.",
    )
    fetch_sources_parser.add_argument("--limit", type=int, default=3, help="Maximum rows per source.")

    phase1_parser = subparsers.add_parser(
        "phase1-run", help="Run an end-to-end Phase 1 pipeline into raw / bronze / gold / manifests."
    )
    phase1_parser.add_argument(
        "--data-root",
        required=True,
        help="Root directory for Phase 1 outputs. Example: ~/lattice-data",
    )
    phase1_parser.add_argument(
        "--registry",
        default="configs/source_registry.json",
        help="Path to the source registry JSON file.",
    )
    phase1_parser.add_argument("--domain", default="materials", help="Target domain label.")
    phase1_parser.add_argument("--release-name", required=True, help="Release identifier.")
    phase1_parser.add_argument("--query", default="solid state battery electrolyte", help="Topic query.")
    phase1_parser.add_argument(
        "--element",
        action="append",
        default=[],
        help="Element symbol for materials queries. Can be repeated.",
    )
    phase1_parser.add_argument(
        "--compound",
        action="append",
        default=[],
        help="Compound name for chemistry lookups. Can be repeated.",
    )
    phase1_parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source name from the registry. When omitted, fetch all implemented open sources.",
    )
    phase1_parser.add_argument("--limit", type=int, default=3, help="Maximum rows per source.")
    phase1_parser.add_argument(
        "--include-optional-sources",
        action="store_true",
        help="Also include optional sources when selecting from the registry automatically.",
    )
    phase1_parser.add_argument("--registry-db", default="", help="Optional SQLite registry DB path.")

    for workflow_name in ("train-pretrain", "train-continue", "train-finetune", "train-post"):
        train_parser = subparsers.add_parser(workflow_name, help=f"Run the {workflow_name.replace('train-', '')} workflow.")
        train_parser.add_argument("--input", required=True, help="Input compiled dataset directory.")
        train_parser.add_argument("--output", required=True, help="Output training run directory.")
        train_parser.add_argument("--run-name", required=True, help="Training run name.")
        train_parser.add_argument("--checkpoint-dir", default="", help="Optional checkpoint directory for continue/fine-tune/post-train.")
        train_parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs.")
        train_parser.add_argument("--batch-size", type=int, default=2, help="Training batch size.")
        train_parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate.")
        train_parser.add_argument("--max-length", type=int, default=192, help="Maximum sequence length.")
        train_parser.add_argument("--hidden-size", type=int, default=96, help="Hidden size for the tiny local model.")

    phase2_parser = subparsers.add_parser(
        "phase2-run",
        help="Run a Phase 2 workflow using pandas/spark/flink preparation and open/closed model backends.",
    )
    phase2_parser.add_argument("--workflow", required=True, choices=["pretrain", "continue", "finetune", "posttrain"])
    phase2_parser.add_argument("--engine", required=True, choices=["pandas", "spark", "flink"])
    phase2_parser.add_argument("--input", required=True, help="Input directory. Raw normalized JSONL or compiled dataset.")
    phase2_parser.add_argument("--output", required=True, help="Output directory for the phase2 run.")
    phase2_parser.add_argument("--run-name", required=True, help="Run name.")
    phase2_parser.add_argument("--model-backend", required=True, choices=["local_tiny", "hf_causal_lm", "external_connector"])
    phase2_parser.add_argument("--model-name", required=True, help="Model name or model identifier.")
    phase2_parser.add_argument("--provider", default="local", help="Provider name. Example: huggingface, openai_compatible.")
    phase2_parser.add_argument("--model-family", default="open", choices=["open", "closed"], help="Model family.")
    phase2_parser.add_argument("--api-base", default="", help="Optional API base for external connector runs.")
    phase2_parser.add_argument("--api-key-env", default="", help="Optional API key env var name for external connector runs.")
    phase2_parser.add_argument("--domain", default="materials", help="Target domain.")
    phase2_parser.add_argument("--checkpoint-dir", default="", help="Optional checkpoint dir for continue/fine-tune/post-train.")
    phase2_parser.add_argument("--compiled-input", action="store_true", help="Treat input as an already-compiled dataset.")
    phase2_parser.add_argument("--registry-db", default="", help="Optional SQLite registry DB path.")
    phase2_parser.add_argument("--epochs", type=int, default=1, help="Training epochs.")
    phase2_parser.add_argument("--batch-size", type=int, default=2, help="Training batch size.")
    phase2_parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate.")
    phase2_parser.add_argument("--max-length", type=int, default=192, help="Maximum sequence length.")
    phase2_parser.add_argument("--hidden-size", type=int, default=96, help="Hidden size for local tiny backend.")

    stats_parser = subparsers.add_parser("stats", help="Print summary stats from a compiled output.")
    stats_parser.add_argument("--path", required=True, help="Compiled output directory or manifest path.")

    registry_parser = subparsers.add_parser("registry-sync", help="Sync a phase1/phase2 manifest into the platform registry.")
    registry_parser.add_argument("--db", required=True, help="SQLite registry DB path.")
    registry_parser.add_argument("--phase", required=True, choices=["phase1", "phase2"])
    registry_parser.add_argument("--manifest", required=True, help="Manifest JSON path.")

    registry_list_parser = subparsers.add_parser("registry-list", help="List runs, datasets, or backends from the platform registry.")
    registry_list_parser.add_argument("--db", required=True, help="SQLite registry DB path.")
    registry_list_parser.add_argument("--kind", required=True, choices=["runs", "datasets", "backends"])

    serve_parser = subparsers.add_parser("serve-platform", help="Serve the platform registry API with FastAPI.")
    serve_parser.add_argument("--db", required=True, help="SQLite registry DB path.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8787)
    return parser


def _handle_compile(args: argparse.Namespace) -> int:
    config = CompilerConfig(
        input_dir=args.input,
        output_dir=args.output,
        domain=args.domain,
        dataset_name=args.dataset_name,
        chunk_size=args.chunk_size,
    )
    manifest = compile_dataset(config)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _handle_engine_compile(args: argparse.Namespace) -> int:
    config = EngineConfig(
        input_dir=args.input,
        output_dir=args.output,
        domain=args.domain,
        dataset_name=args.dataset_name,
        engine=args.engine,
        chunk_size=args.chunk_size,
    )
    manifest = run_engine_compile(config)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _handle_engine_check(_: argparse.Namespace) -> int:
    payload = engine_check()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _compounds_or_default(compounds: list[str]) -> list[str]:
    if compounds:
        return compounds
    return ["lithium iron phosphate", "lithium cobalt oxide"]


def _elements_or_default(elements: list[str]) -> list[str]:
    if elements:
        return elements
    return ["Li", "O"]


def _handle_fetch_demo(args: argparse.Namespace) -> int:
    config = DemoFetchConfig(
        output_dir=args.output,
        domain=args.domain,
        query=args.query,
        openalex_limit=args.openalex_limit,
        arxiv_limit=args.arxiv_limit,
        compounds=_compounds_or_default(args.compound),
    )
    manifest = run_demo_fetch(config)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _handle_fetch_sources(args: argparse.Namespace) -> int:
    config = SourceFetchConfig(
        output_dir=args.output,
        domain=args.domain,
        registry_path=args.registry,
        sources=args.source,
        query=args.query,
        elements=_elements_or_default(args.element),
        compounds=_compounds_or_default(args.compound),
        limit=args.limit,
    )
    manifest = run_source_fetch(config)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _handle_phase1_run(args: argparse.Namespace) -> int:
    config = Phase1Config(
        data_root=args.data_root,
        registry_path=args.registry,
        domain=args.domain,
        release_name=args.release_name,
        query=args.query,
        elements=_elements_or_default(args.element),
        compounds=_compounds_or_default(args.compound),
        sources=args.source,
        limit=args.limit,
        include_optional_sources=args.include_optional_sources,
        registry_db=args.registry_db,
    )
    manifest = run_phase1_pipeline(config)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _handle_training_workflow(args: argparse.Namespace, workflow: str) -> int:
    result = run_training_workflow(
        TrainingConfig(
            workflow=workflow,
            input_dir=args.input,
            output_dir=args.output,
            run_name=args.run_name,
            checkpoint_dir=args.checkpoint_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
            hidden_size=args.hidden_size,
        )
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


def _handle_phase2_run(args: argparse.Namespace) -> int:
    manifest = run_phase2_pipeline(
        Phase2Config(
            workflow=args.workflow,
            engine=args.engine,
            input_dir=args.input,
            output_dir=args.output,
            run_name=args.run_name,
            model_backend=args.model_backend,
            model_name=args.model_name,
            compiled_input=args.compiled_input,
            provider=args.provider,
            model_family=args.model_family,
            api_base=args.api_base,
            api_key_env=args.api_key_env,
            domain=args.domain,
            checkpoint_dir=args.checkpoint_dir,
            registry_db=args.registry_db,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
            hidden_size=args.hidden_size,
        )
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _handle_registry_sync(args: argparse.Namespace) -> int:
    if args.phase == "phase1":
        payload = sync_phase1_manifest(args.db, args.manifest)
    else:
        payload = sync_phase2_manifest(args.db, args.manifest)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _handle_registry_list(args: argparse.Namespace) -> int:
    from lattice.platform.registry import PlatformRegistry

    registry = PlatformRegistry(args.db)
    try:
        if args.kind == "runs":
            payload = registry.list_runs()
        elif args.kind == "datasets":
            payload = registry.list_datasets()
        else:
            payload = registry.list_backends()
    finally:
        registry.close()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _handle_serve_platform(args: argparse.Namespace) -> int:
    import uvicorn

    app = create_app(args.db)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def _handle_demo(args: argparse.Namespace) -> int:
    fetch_config = DemoFetchConfig(
        output_dir=args.raw_output,
        domain=args.domain,
        query=args.query,
        openalex_limit=args.openalex_limit,
        arxiv_limit=args.arxiv_limit,
        compounds=_compounds_or_default(args.compound),
    )
    fetch_manifest = run_demo_fetch(fetch_config)
    compile_manifest = compile_dataset(
        CompilerConfig(
            input_dir=args.raw_output,
            output_dir=args.compiled_output,
            domain=args.domain,
            dataset_name=args.dataset_name,
        )
    )
    payload = {
        "fetch": fetch_manifest,
        "compile": compile_manifest,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _handle_stats(args: argparse.Namespace) -> int:
    path = Path(args.path)
    manifest_path = path if path.name.endswith(".json") else path / "reports" / "manifest.json"
    manifest = read_json(manifest_path)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "compile":
        return _handle_compile(args)
    if args.command == "engine-compile":
        return _handle_engine_compile(args)
    if args.command == "engine-check":
        return _handle_engine_check(args)
    if args.command == "fetch-demo":
        return _handle_fetch_demo(args)
    if args.command == "fetch-sources":
        return _handle_fetch_sources(args)
    if args.command == "phase1-run":
        return _handle_phase1_run(args)
    if args.command == "train-pretrain":
        return _handle_training_workflow(args, "pretrain")
    if args.command == "train-continue":
        return _handle_training_workflow(args, "continue")
    if args.command == "train-finetune":
        return _handle_training_workflow(args, "finetune")
    if args.command == "train-post":
        return _handle_training_workflow(args, "posttrain")
    if args.command == "phase2-run":
        return _handle_phase2_run(args)
    if args.command == "registry-sync":
        return _handle_registry_sync(args)
    if args.command == "registry-list":
        return _handle_registry_list(args)
    if args.command == "serve-platform":
        return _handle_serve_platform(args)
    if args.command == "demo":
        return _handle_demo(args)
    if args.command == "stats":
        return _handle_stats(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
