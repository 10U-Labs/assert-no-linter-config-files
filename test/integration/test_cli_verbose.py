"""Integration tests for the --verbose flag."""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestVerboseDisplay:
    """Tests for --verbose flag display output."""

    def test_verbose_exits_0(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose exits 0 when no config found."""
        code, _, _ = verbose_pylint_mypy_result
        assert code == 0

    def test_verbose_shows_checking_for(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows 'Checking for:' header."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "Checking for:" in stdout

    def test_verbose_shows_mypy(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows mypy in linter list."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "mypy" in stdout

    def test_verbose_shows_pylint(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows pylint in linter list."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "pylint" in stdout

    def test_verbose_shows_pylintrc_config_file(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows .pylintrc in config files list."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert ".pylintrc" in stdout

    def test_verbose_shows_pylint_pyproject_config(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows pylint pyproject.toml config pattern."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "[tool.pylint.*] in pyproject.toml" in stdout

    def test_verbose_shows_mypy_ini_config_file(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows mypy.ini in config files list."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "mypy.ini" in stdout

    def test_verbose_shows_mypy_pyproject_config(
        self, verbose_pylint_mypy_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows mypy pyproject.toml config pattern."""
        _, stdout, _ = verbose_pylint_mypy_result
        assert "[tool.mypy] in pyproject.toml" in stdout

    def test_verbose_shows_scanning_exits_0(
        self, verbose_pylint_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows directories being scanned and exits 0."""
        code, _, _ = verbose_pylint_result
        assert code == 0

    def test_verbose_shows_scanning_label(
        self, verbose_pylint_result: tuple[int, str, str]
    ) -> None:
        """--verbose shows 'Scanning:' label."""
        _, stdout, _ = verbose_pylint_result
        assert "Scanning:" in stdout

    def test_verbose_shows_scanning_path(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows the directory path being scanned."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert str(tmp_path) in stdout

    def test_verbose_findings_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 1

    def test_verbose_findings_shows_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows pylint in findings output."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_verbose_findings_shows_config_file(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows 'config file' in findings output."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "config file" in stdout


@pytest.mark.integration
class TestVerboseSummary:
    """Tests for --verbose flag summary and multi-directory output."""

    def test_verbose_summary_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose exits 1 when findings exist for summary test."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 1

    def test_verbose_summary_shows_scanned_count(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows 'Scanned 1 directory(ies)' in summary."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "Scanned 1 directory(ies)" in stdout

    def test_verbose_summary_shows_findings_count(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows 'found 1 finding(s)' in summary."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "found 1 finding(s)" in stdout

    def test_verbose_no_findings_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose exits 0 when no findings."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 0

    def test_verbose_no_findings_summary(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows zero findings in summary."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "found 0 finding(s)" in stdout

    def test_verbose_with_fail_fast_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose with --fail-fast exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--verbose", "--fail-fast", str(tmp_path)
        ])
        assert code == 1

    def test_verbose_with_fail_fast_shows_1_finding(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose with --fail-fast shows summary with 1 finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--verbose", "--fail-fast", str(tmp_path)
        ])
        assert "found 1 finding" in stdout

    def test_verbose_multiple_directories_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose with multiple directories exits 0."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose",
            str(first), str(second)
        ])
        assert code == 0

    def test_verbose_multiple_directories_shows_two_scanning(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows scanning for each of the two directories."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose",
            str(first), str(second)
        ])
        assert stdout.count("Scanning:") == 2

    def test_verbose_multiple_directories_shows_scanned_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows 'Scanned 2 directory(ies)' in summary."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose",
            str(first), str(second)
        ])
        assert "Scanned 2 directory(ies)" in stdout
