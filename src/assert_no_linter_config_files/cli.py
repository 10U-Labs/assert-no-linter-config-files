"""Command-line interface for assert-no-linter-config-files."""

import argparse
import sys
from pathlib import Path

from .scanner import Finding, make_path_relative, scan_directory


def main() -> None:
    """Run the assert-no-linter-config-files CLI."""
    parser = argparse.ArgumentParser(
        description="Assert that no linter config files exist in directories"
    )
    parser.add_argument(
        "directories",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="Directories to scan (default: current directory)",
    )

    try:
        args = parser.parse_args()
    except SystemExit as e:
        sys.exit(2 if e.code != 0 else 0)

    all_findings: list[Finding] = []

    for directory in args.directories:
        if not directory.is_dir():
            print(f"Error: '{directory}' is not a directory", file=sys.stderr)
            sys.exit(2)

        try:
            findings = scan_directory(directory)
            all_findings.extend(findings)
        except OSError as e:
            print(f"Error reading: {e}", file=sys.stderr)
            sys.exit(2)

    if all_findings:
        for finding in all_findings:
            relative_path = make_path_relative(finding.path)
            print(f"{relative_path}:{finding.tool}:{finding.reason}")
        sys.exit(1)

    sys.exit(0)
