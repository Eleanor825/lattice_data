from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


TEST_FILES = [
    "tests/test_target_build.py",
    "tests/test_rag_target.py",
    "tests/test_sft_target.py",
    "tests/test_eval_target.py",
    "tests/test_pretrain_target.py",
    "tests/test_preference_target.py",
    "tests/test_target_policy.py",
    "tests/test_entity_linking.py",
    "tests/test_target_scoring.py",
    "tests/test_source_governance.py",
    "tests/test_transform_extension.py",
    "tests/test_target_regression_suite.py",
]


def main() -> int:
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    outputs: list[dict[str, object]] = []
    failures = 0
    for relative_path in TEST_FILES:
        cmd = [sys.executable, relative_path]
        result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
        outputs.append(
            {
                "test_file": relative_path,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if result.returncode != 0:
            failures += 1
    stdout = f"Ran {len(TEST_FILES)} test files\n"
    if failures:
        stdout += f"failures={failures}\n"
    summary = {
        "command": [sys.executable, "scripts/benchmark_target_compiler.py"],
        "returncode": 0 if failures == 0 else 1,
        "stdout": stdout,
        "stderr": "",
        "test_files": TEST_FILES,
        "results": outputs,
    }
    results_dir = ROOT / "benchmarks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "target-compiler-benchmark.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(stdout, end="")
    return summary["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
