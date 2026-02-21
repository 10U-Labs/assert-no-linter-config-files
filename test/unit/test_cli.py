"""Unit tests for the cli module."""

import argparse
import json
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
    output_findings,
)
from assert_no_linter_config_files.scanner import Finding


@pytest.mark.unit
class TestDetermineExitCode:
    """Tests for _determine_exit_code helper."""

    def test_warn_only_returns_success(self) -> None:
        """--warn-only always returns EXIT_SUCCESS."""
        findings = [Finding("path", "pylint", "config file")]
        assert _determine_exit_code(findings, False, True) == EXIT_SUCCESS

    def test_findings_returns_findings(self) -> None:
        """Returns EXIT_FINDINGS when findings exist."""
        findings = [Finding("path", "pylint", "config file")]
        assert _determine_exit_code(findings, False, False) == EXIT_FINDINGS

    def test_error_returns_error(self) -> None:
        """Returns EXIT_ERROR when had_error is True."""
        assert _determine_exit_code([], True, False) == EXIT_ERROR

    def test_success_returns_success(self) -> None:
        """Returns EXIT_SUCCESS when no issues."""
        assert _determine_exit_code([], False, False) == EXIT_SUCCESS


@pytest.mark.unit
def test_print_verbose_summary_shows_directory_count(capsys: pytest.CaptureFixture[str]) -> None:
    """Prints directory count in summary."""
    _print_verbose_summary(3, 5)
    captured = capsys.readouterr()
    assert "Scanned 3 directory(ies)" in captured.out


@pytest.mark.unit
def test_print_verbose_summary_shows_finding_count(capsys: pytest.CaptureFixture[str]) -> None:
    """Prints finding count in summary."""
    _print_verbose_summary(3, 5)
    captured = capsys.readouterr()
    assert "found 5 finding(s)" in captured.out


@pytest.mark.unit
@pytest.mark.parametrize("verbose,quiet", [
    (True, False),
    (False, True),
    (False, False),
])
def test_handle_fail_fast_exits_with_findings_code(
    verbose: bool, quiet: bool
) -> None:
    """Test fail-fast exits with EXIT_FINDINGS code."""
    args = argparse.Namespace(
        verbose=verbose, quiet=quiet, json=False, count=False
    )
    finding = Finding("test.py", "pylint", "config file")
    with patch("builtins.print"):
        with pytest.raises(SystemExit, match=str(EXIT_FINDINGS)):
            _handle_fail_fast(finding, 1, args)


def _run_fail_fast_with_mock_print(
    verbose: bool, quiet: bool
) -> int:
    """Run _handle_fail_fast and return mock_print call count."""
    args = argparse.Namespace(
        verbose=verbose, quiet=quiet, json=False, count=False
    )
    finding = Finding("test.py", "pylint", "config file")
    with patch("builtins.print") as mock_print:
        try:
            _handle_fail_fast(finding, 1, args)
        except SystemExit:
            pass
    return mock_print.call_count


@pytest.mark.unit
def test_handle_fail_fast_verbose_prints_twice() -> None:
    """Test fail-fast in verbose mode prints finding and summary."""
    assert _run_fail_fast_with_mock_print(verbose=True, quiet=False) >= 2


@pytest.mark.unit
def test_handle_fail_fast_normal_prints_once() -> None:
    """Test fail-fast in normal mode prints finding."""
    assert _run_fail_fast_with_mock_print(verbose=False, quiet=False) >= 1


@pytest.mark.unit
def test_handle_fail_fast_quiet_no_output() -> None:
    """Test fail-fast in quiet mode produces no output."""
    args = argparse.Namespace(
        verbose=False, quiet=True, json=False, count=False
    )
    finding = Finding("test.py", "pylint", "config file")
    with patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit):
            _handle_fail_fast(finding, 1, args)
    mock_print.assert_not_called()


@pytest.mark.unit
class TestProcessDirectory:
    """Tests for _process_directory helper."""

    def test_verbose_returns_dirs_scanned_1(self, tmp_path: Path) -> None:
        """In verbose mode, returns dirs_scanned == 1."""
        args = argparse.Namespace(
            verbose=True, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch("builtins.print"):
            dirs_scanned, _ = _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            assert dirs_scanned == 1

    def test_verbose_returns_no_error(self, tmp_path: Path) -> None:
        """In verbose mode, returns had_error == False."""
        args = argparse.Namespace(
            verbose=True, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch("builtins.print"):
            _, had_error = _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            assert had_error is False

    @staticmethod
    def _run_verbose_process_directory(
        tmp_path: Path, create_pylintrc: bool = False,
    ) -> list[str]:
        """Run _process_directory in verbose mode, return str of calls."""
        if create_pylintrc:
            (tmp_path / ".pylintrc").touch()
        args = argparse.Namespace(
            verbose=True, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch("builtins.print") as mock_print:
            _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
        return [str(call) for call in mock_print.call_args_list]

    def test_verbose_prints_scanning(self, tmp_path: Path) -> None:
        """In verbose mode, prints scanning message."""
        calls = self._run_verbose_process_directory(tmp_path)
        assert any("Scanning:" in call for call in calls)

    def test_oserror_returns_zero_dirs_scanned(self, tmp_path: Path) -> None:
        """OSError during scan returns dirs_scanned == 0."""
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Permission denied"),
        ):
            dirs_scanned, _ = _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            assert dirs_scanned == 0

    def test_oserror_returns_had_error_true(self, tmp_path: Path) -> None:
        """OSError during scan returns had_error=True."""
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Permission denied"),
        ):
            _, had_error = _process_directory(
                tmp_path, args, frozenset(["pylint"]), 0, all_findings
            )
            assert had_error is True

    def test_findings_increments_dirs_scanned(self, tmp_path: Path) -> None:
        """Successful scan increments dirs_scanned."""
        (tmp_path / ".pylintrc").touch()
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        dirs_scanned, _ = _process_directory(
            tmp_path, args, frozenset(["pylint"]), 0, all_findings
        )
        assert dirs_scanned == 1

    def test_findings_returns_no_error(self, tmp_path: Path) -> None:
        """Successful scan returns had_error == False."""
        (tmp_path / ".pylintrc").touch()
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        _, had_error = _process_directory(
            tmp_path, args, frozenset(["pylint"]), 0, all_findings
        )
        assert had_error is False

    def test_findings_added_to_list(self, tmp_path: Path) -> None:
        """Findings are added to all_findings list."""
        (tmp_path / ".pylintrc").touch()
        args = argparse.Namespace(
            verbose=False, exclude=[], fail_fast=False
        )
        all_findings: list[Finding] = []
        _process_directory(
            tmp_path, args, frozenset(["pylint"]), 0, all_findings
        )
        assert len(all_findings) == 1

    def test_verbose_prints_findings(self, tmp_path: Path) -> None:
        """In verbose mode, prints each finding."""
        calls = self._run_verbose_process_directory(
            tmp_path, create_pylintrc=True
        )
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
            code, _, _ = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert code == 2

    def test_oserror_stderr_contains_error_reading(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """OSError stderr contains 'Error reading'."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Permission denied"),
        ):
            _, _, stderr = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert "Error reading" in stderr

    def test_oserror_stderr_contains_error_message(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """OSError stderr contains the original error message."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Permission denied"),
        ):
            _, _, stderr = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert "Permission denied" in stderr

    def test_oserror_exits_with_code_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """OSError exits with code 2."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Cannot read file"),
        ):
            code, _, _ = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert code == 2

    def test_oserror_produces_no_stdout(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """OSError produces no stdout output."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Cannot read file"),
        ):
            _, stdout, _ = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert stdout == ""

    def test_oserror_reports_message_to_stderr(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """OSError message is printed to stderr."""
        with patch(
            "assert_no_linter_config_files.cli.scan_directory",
            side_effect=OSError("Cannot read file"),
        ):
            _, _, stderr = run_main_with_args([
                "--linters", "pylint", str(tmp_path)
            ])
            assert "Cannot read file" in stderr


@pytest.mark.unit
def test_quiet_and_fail_fast_exits_1(
    tmp_path_with_pylintrc_and_mypy: Path, run_main_with_args
) -> None:
    """--quiet with --fail-fast exits with code 1."""
    code, _, _ = run_main_with_args([
        "--linters", "pylint,mypy",
        "--quiet", "--fail-fast",
        str(tmp_path_with_pylintrc_and_mypy)
    ])
    assert code == 1


@pytest.mark.unit
def test_quiet_and_fail_fast_no_output(
    tmp_path_with_pylintrc_and_mypy: Path, run_main_with_args
) -> None:
    """--quiet with --fail-fast produces no stdout output."""
    _, stdout, _ = run_main_with_args([
        "--linters", "pylint,mypy",
        "--quiet", "--fail-fast",
        str(tmp_path_with_pylintrc_and_mypy)
    ])
    assert stdout == ""


@pytest.mark.unit
class TestOutputFindings:
    """Tests for output_findings helper."""

    @pytest.fixture
    def json_output_parsed(self, capsys: pytest.CaptureFixture[str]) -> list[dict[str, str]]:
        """Parse JSON output from output_findings with two findings."""
        findings = [
            Finding("./test.py", "pylint", "config file"),
            Finding("./mypy.ini", "mypy", "config file"),
        ]
        output_findings(findings, use_json=True, use_count=False)
        captured = capsys.readouterr()
        return json.loads(captured.out)

    def test_json_output_has_two_items(self, json_output_parsed: list[dict[str, str]]) -> None:
        """--json outputs findings as JSON array with correct length."""
        assert len(json_output_parsed) == 2

    def test_json_output_first_tool_is_pylint(self, json_output_parsed: list[dict[str, str]]) -> None:
        """--json first finding has tool == pylint."""
        assert json_output_parsed[0]["tool"] == "pylint"

    def test_json_output_second_tool_is_mypy(self, json_output_parsed: list[dict[str, str]]) -> None:
        """--json second finding has tool == mypy."""
        assert json_output_parsed[1]["tool"] == "mypy"

    def test_count_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--count outputs finding count only."""
        findings = [
            Finding("./test.py", "pylint", "config file"),
            Finding("./mypy.ini", "mypy", "config file"),
        ]
        output_findings(findings, use_json=False, use_count=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "2"

    def test_default_output_includes_tool_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Default output includes the tool name."""
        findings = [Finding("./test.py", "pylint", "config file")]
        output_findings(findings, use_json=False, use_count=False)
        captured = capsys.readouterr()
        assert "pylint" in captured.out

    def test_default_output_includes_description(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Default output includes the finding description."""
        findings = [Finding("./test.py", "pylint", "config file")]
        output_findings(findings, use_json=False, use_count=False)
        captured = capsys.readouterr()
        assert "config file" in captured.out


@pytest.mark.unit
def test_invalid_linter_exits_2(tmp_path: Path, run_main_with_args) -> None:
    """Invalid linter name exits with code 2."""
    code, _, _ = run_main_with_args([
        "--linters", "invalid_linter", str(tmp_path)
    ])
    assert code == 2


@pytest.mark.unit
def test_invalid_linter_prints_error(tmp_path: Path, run_main_with_args) -> None:
    """Invalid linter name prints error to stderr."""
    _, _, stderr = run_main_with_args([
        "--linters", "invalid_linter", str(tmp_path)
    ])
    assert "Invalid linter" in stderr


@pytest.mark.unit
class TestMainVerbose:
    """Tests for verbose output in main()."""

    def test_verbose_prints_checking_for(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose prints 'Checking for:' header."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "Checking for:" in stdout

    def test_verbose_prints_pylint(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose prints pylint in linter list."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "pylint" in stdout

    def test_verbose_prints_mypy(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose prints mypy in linter list."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "mypy" in stdout

    def test_verbose_exits_0(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose with no findings exits with code 0."""
        code, _, _ = verbose_pylint_mypy_result
        assert code == 0

    def test_verbose_prints_scanned(
        self, verbose_pylint_result: tuple[int, str, str]
    ) -> None:
        """--verbose prints 'Scanned' in summary."""
        _, stdout, _ = verbose_pylint_result
        assert "Scanned" in stdout

    def test_verbose_prints_findings_count(
        self, verbose_pylint_result: tuple[int, str, str]
    ) -> None:
        """--verbose prints 'finding(s)' in summary."""
        _, stdout, _ = verbose_pylint_result
        assert "finding(s)" in stdout

    def test_verbose_summary_exits_0(
        self, verbose_pylint_result: tuple[int, str, str]
    ) -> None:
        """--verbose with no findings exits with code 0."""
        code, _, _ = verbose_pylint_result
        assert code == 0


@pytest.mark.unit
def test_file_instead_of_directory_exits_2(
    file_instead_of_directory_result: tuple[int, str, str],
) -> None:
    """Providing a file instead of directory exits with code 2."""
    code, _, _ = file_instead_of_directory_result
    assert code == 2


@pytest.mark.unit
def test_file_instead_of_directory_prints_error(
    file_instead_of_directory_result: tuple[int, str, str],
) -> None:
    """Providing a file instead of directory prints error to stderr."""
    _, _, stderr = file_instead_of_directory_result
    assert "is not a directory" in stderr
