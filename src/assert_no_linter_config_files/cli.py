"""Command-line interface for assert-no-linter-config-files."""

import argparse
import json
import sys
from pathlib import Path

from .scanner import (
    VALID_LINTERS,
    Finding,
    get_config_files_for_linters,
    parse_linters,
    scan_directory,
)

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    linters_list = ", ".join(sorted(VALID_LINTERS))

    parser = argparse.ArgumentParser(
        prog="assert-no-linter-config-files",
        description="Assert that no linter config files exist in directories.",
    )
    parser.add_argument(
        "directories",
        nargs="+",
        type=Path,
        metavar="DIRECTORY",
        help="One or more directories to scan.",
    )
    parser.add_argument(
        "--linters",
        required=True,
        metavar="LINTERS",
        help=f"Comma-separated linters to check. Options: {linters_list}",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="PATTERN",
        help="Glob pattern to exclude paths (repeatable).",
    )

    # Output mode group (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output, exit code only.",
    )
    output_group.add_argument(
        "--count",
        action="store_true",
        help="Print finding count only.",
    )
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON.",
    )
    output_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show linters, directories scanned, findings, and summary.",
    )

    # Behavior modifiers (mutually exclusive)
    behavior_group = parser.add_mutually_exclusive_group()
    behavior_group.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit on first finding.",
    )
    behavior_group.add_argument(
        "--warn-only",
        action="store_true",
        help="Always exit 0, report only.",
    )

    return parser


def output_findings(
    findings: list[Finding],
    use_json: bool,
    use_count: bool,
) -> None:
    """Output findings in the appropriate format."""
    if use_json:
        print(json.dumps([f.to_dict() for f in findings]))
    elif use_count:
        print(len(findings))
    else:
        for finding in findings:
            print(finding)


def _print_verbose_summary(dirs_scanned: int, finding_count: int) -> None:
    """Print verbose summary of scan results."""
    print(f"Scanned {dirs_scanned} directory(ies), found {finding_count} finding(s)")


def _handle_fail_fast(
    finding: Finding,
    dirs_scanned: int,
    args: argparse.Namespace,
) -> None:
    """Handle fail-fast output and exit."""
    if args.verbose:
        print(finding)
        _print_verbose_summary(dirs_scanned, 1)
    elif not args.quiet:
        output_findings([finding], args.json, args.count)
    sys.exit(EXIT_FINDINGS)


def _determine_exit_code(
    all_findings: list[Finding],
    had_error: bool,
    warn_only: bool,
) -> int:
    """Determine the exit code based on results."""
    if warn_only:
        return EXIT_SUCCESS
    if all_findings:
        return EXIT_FINDINGS
    if had_error:
        return EXIT_ERROR
    return EXIT_SUCCESS


def _process_directory(
    directory: Path,
    args: argparse.Namespace,
    linters: frozenset[str],
    dirs_scanned: int,
    all_findings: list[Finding],
) -> tuple[int, bool]:
    """Process a single directory. Returns (dirs_scanned, had_error)."""
    if args.verbose:
        print(f"Scanning: {directory}")

    try:
        findings = scan_directory(
            directory,
            linters=linters,
            exclude_patterns=args.exclude,
        )
        dirs_scanned += 1

        if findings and args.fail_fast:
            _handle_fail_fast(findings[0], dirs_scanned, args)

        if args.verbose:
            for finding in findings:
                print(finding)

        all_findings.extend(findings)
        return dirs_scanned, False
    except OSError as e:
        print(f"Error reading: {e}", file=sys.stderr)
        return dirs_scanned, True


def main() -> None:
    """Run the assert-no-linter-config-files CLI."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        linters = parse_linters(args.linters)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if args.verbose:
        print(f"Checking for: {', '.join(sorted(linters))}")
        config_files = get_config_files_for_linters(linters)
        for linter, configs in config_files.items():
            print(f"  {linter}: {', '.join(configs)}")

    all_findings: list[Finding] = []
    had_error = False
    dirs_scanned = 0

    for directory in args.directories:
        if not directory.is_dir():
            print(f"Error: '{directory}' is not a directory", file=sys.stderr)
            had_error = True
            continue

        dirs_scanned, dir_error = _process_directory(
            directory, args, linters, dirs_scanned, all_findings
        )
        had_error = had_error or dir_error

    if args.verbose:
        _print_verbose_summary(dirs_scanned, len(all_findings))
    elif not args.quiet:
        output_findings(all_findings, args.json, args.count)

    sys.exit(_determine_exit_code(all_findings, had_error, args.warn_only))
