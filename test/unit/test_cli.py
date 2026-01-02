"""Unit tests for the cli module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.cli import main


def run_main_with_args(args: list[str]) -> tuple[int, str, str]:
    """Run main() with patched sys.argv and return exit code, stdout, stderr."""
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def mock_print(*print_args: object, **kwargs: object) -> None:
        text = " ".join(str(a) for a in print_args)
        if kwargs.get("file") is sys.stderr:
            stderr_lines.append(text)
        elif kwargs.get("file") is None:
            stdout_lines.append(text)

    with patch("sys.argv", ["prog"] + args):
        with patch("builtins.print", side_effect=mock_print):
            with pytest.raises(SystemExit) as exc_info:
                main()
            code = int(exc_info.value.code or 0)
            return code, "\n".join(stdout_lines), "\n".join(stderr_lines)


@pytest.mark.unit
class TestOSErrorHandling:
    """Tests for OSError handling in main()."""

    def test_oserror_during_scan_exits_2(self, tmp_path: Path) -> None:
        """OSError during directory scan exits with code 2."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Permission denied"),
        ):
            code, _, stderr = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert code == 2
            assert "Error reading" in stderr
            assert "Permission denied" in stderr

    def test_oserror_reports_to_stderr(self, tmp_path: Path) -> None:
        """OSError message is printed to stderr."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Cannot read file"),
        ):
            code, stdout, stderr = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert code == 2
            assert stdout == ""
            assert "Cannot read file" in stderr


@pytest.mark.unit
class TestQuietWithFailFast:
    """Tests for --quiet combined with --fail-fast."""

    def test_quiet_and_fail_fast_no_output(self, tmp_path: Path) -> None:
        """--quiet with --fail-fast produces no output."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--quiet",
            "--fail-fast",
            str(tmp_path)
        ])
        assert code == 1
        assert stdout == ""
