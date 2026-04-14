from __future__ import annotations

import argparse
import json
from pathlib import Path

from lattice.compiler import CompilerConfig, compile_dataset
from lattice.utils import read_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lattice", description="Lattice data compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile raw sources into dataset views.")
    compile_parser.add_argument("--input", required=True, help="Input directory containing raw sources.")
    compile_parser.add_argument("--output", required=True, help="Output directory for compiled artifacts.")
    compile_parser.add_argument("--domain", required=True, help="Target domain label.")
    compile_parser.add_argument("--dataset-name", required=True, help="Dataset release name.")
    compile_parser.add_argument("--chunk-size", type=int, default=1200, help="Maximum characters per pretrain chunk.")

    stats_parser = subparsers.add_parser("stats", help="Print summary stats from a compiled output.")
    stats_parser.add_argument("--path", required=True, help="Compiled output directory or manifest path.")
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
    if args.command == "stats":
        return _handle_stats(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
