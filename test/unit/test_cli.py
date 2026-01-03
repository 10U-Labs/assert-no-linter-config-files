"""Unit tests for the cli module."""

import argparse
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.cli import (
    _determine_exit_code,
    _handle_fail_fast,
    _print_verbose_summary,
    _process_directory,
    EXIT_ERROR,
    EXIT_FINDINGS,
    EXIT_SUCCESS,
)
from assert_no_linter_config_files.scanner import Finding


@pytest.mark.unit
class TestDetermineExitCode:
    """Tests for _determine_exit_code helper."""

    def test_warn_only_returns_success(self) -> None:
        """--warn-only always returns EXIT_SUCCESS."""
        findings = [Finding("path", "pylint", "config file", None)]
        assert _determine_exit_code(findings, False, True) == EXIT_SUCCESS

    def test_findings_returns_findings(self) -> None:
        """Returns EXIT_FINDINGS when findings exist."""
        findings = [Finding("path", "pylint", "config file", None)]
        assert _determine_exit_code(findings, False, False) == EXIT_FINDINGS

    def test_error_returns_error(self) -> None:
        """Returns EXIT_ERROR when had_error is True."""
        assert _determine_exit_code([], True, False) == EXIT_ERROR

    def test_success_returns_success(self) -> None:
        """Returns EXIT_SUCCESS when no issues."""
        assert _determine_exit_code([], False, False) == EXIT_SUCCESS


@pytest.mark.unit
class TestPrintVerboseSummary:
    """Tests for _print_verbose_summary helper."""

    def test_prints_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Prints directory and finding counts."""
        _print_verbose_summary(3, 5)
        captured = capsys.readouterr()
        assert "Scanned 3 directory(ies)" in captured.out
        assert "found 5 finding(s)" in captured.out


@pytest.mark.unit
class TestHandleFailFast:
    """Tests for _handle_fail_fast helper."""

    def test_verbose_prints_finding_and_summary(self) -> None:
        """In verbose mode, prints finding and summary."""
        args = argparse.Namespace(verbose=True, quiet=False, json=False, count=False)
        finding = Finding("test.py", "pylint", "config file", None)
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                _handle_fail_fast(finding, 1, args)
            assert exc_info.value.code == EXIT_FINDINGS
            assert mock_print.call_count >= 2

    def test_quiet_no_output(self) -> None:
        """In quiet mode, no output."""
        args = argparse.Namespace(verbose=False, quiet=True, json=False, count=False)
        finding = Finding("test.py", "pylint", "config file", None)
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                _handle_fail_fast(finding, 1, args)
            assert exc_info.value.code == EXIT_FINDINGS
            mock_print.assert_not_called()

    def test_normal_outputs_finding(self) -> None:
        """In normal mode, outputs finding."""
        args = argparse.Namespace(verbose=False, quiet=False, json=False, count=False)
        finding = Finding("test.py", "pylint", "config file", None)
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                _handle_fail_fast(finding, 1, args)
            assert exc_info.value.code == EXIT_FINDINGS
            mock_print.assert_called_once()


@pytest.mark.unit
class TestProcessDirectory:
    """Tests for _process_directory helper."""

    def test_verbose_prints_scanning(self, tmp_path: Path) -> None:
        """In verbose mode, prints scanning message."""
        args = argparse.Namespace(
            verbose=True, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch("builtins.print") as mock_print:
            dirs_scanned, had_error = _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            assert dirs_scanned == 1
            assert had_error is False
            assert any("Scanning:" in str(call) for call in mock_print.call_args_list)

    def test_oserror_returns_error(self, tmp_path: Path) -> None:
        """OSError during scan returns had_error=True."""
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Permission denied"),
        ):
            dirs_scanned, had_error = _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            assert dirs_scanned == 0
            assert had_error is True

    def test_findings_added_to_list(self, tmp_path: Path) -> None:
        """Findings are added to all_findings list."""
        (tmp_path / ".pylintrc").touch()
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        dirs_scanned, had_error = _process_directory(
            tmp_path, args, frozenset(["pylint"]), 0, all_findings
        )
        assert dirs_scanned == 1
        assert had_error is False
        assert len(all_findings) == 1

    def test_verbose_prints_findings(self, tmp_path: Path) -> None:
        """In verbose mode, prints each finding."""
        (tmp_path / ".pylintrc").touch()
        args = argparse.Namespace(
            verbose=True, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch("builtins.print") as mock_print:
            _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("pylint" in call for call in calls)


@pytest.mark.unit
class TestOSErrorHandling:
    """Tests for OSError handling in main()."""

    def test_oserror_during_scan_exits_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
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

    def test_oserror_reports_to_stderr(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
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

    def test_quiet_and_fail_fast_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
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
