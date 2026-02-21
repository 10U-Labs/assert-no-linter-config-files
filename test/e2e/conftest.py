"""Shared fixtures and helpers for end-to-end tests."""

import os
import subprocess
import sys
from pathlib import Path


def run_cli(
    *args: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the CLI via subprocess."""
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent.parent / "src"
    current_pythonpath = env.get("PYTHONPATH", "")
    if current_pythonpath:
        env["PYTHONPATH"] = (
            f"{src_path.resolve()}:{current_pythonpath}"
        )
    else:
        env["PYTHONPATH"] = str(src_path.resolve())
    return subprocess.run(
        [
            sys.executable, "-m",
            "assert_no_linter_config_files", *args,
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=False,
    )
