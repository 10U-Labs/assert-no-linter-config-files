"""End-to-end tests for CLI flags."""

import json
import subprocess
from pathlib import Path
from test.e2e.conftest import run_cli

import pytest


@pytest.mark.e2e
class TestLintersFlag:
    """E2E tests for the --linters flag."""

    def test_linters_filters_output_exits_1(
        self, tmp_path: Path
    ) -> None:
        """--linters with matching config exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 1

    def test_linters_filters_output_includes_pylint(
        self, tmp_path: Path
    ) -> None:
        """--linters filters to include specified linter."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "pylint" in result.stdout

    def test_linters_filters_output_excludes_mypy(
        self, tmp_path: Path
    ) -> None:
        """--linters filters out non-specified linters like mypy."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "mypy" not in result.stdout

    def test_linters_filters_output_excludes_yamllint(
        self, tmp_path: Path
    ) -> None:
        """--linters filters out yamllint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "yamllint" not in result.stdout

    def test_linters_comma_separated_exits_1(
        self, tmp_path: Path
    ) -> None:
        """--linters with comma-separated values exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 1

    def test_linters_comma_separated_includes_pylint(
        self, tmp_path: Path
    ) -> None:
        """--linters comma-separated includes pylint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert "pylint" in result.stdout

    def test_linters_comma_separated_includes_mypy(
        self, tmp_path: Path
    ) -> None:
        """--linters comma-separated includes mypy."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert "mypy" in result.stdout

    def test_linters_comma_separated_excludes_yamllint(
        self, tmp_path: Path
    ) -> None:
        """--linters comma-separated excludes yamllint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert "yamllint" not in result.stdout

    def test_linters_no_findings_exits_0(
        self, tmp_path: Path
    ) -> None:
        """No findings for specified linter exits 0."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert result.returncode == 0

    def test_linters_no_findings_no_output(
        self, tmp_path: Path
    ) -> None:
        """No findings for specified linter produces no output."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert result.stdout == ""

    def test_linters_invalid_exits_2(
        self, tmp_path: Path
    ) -> None:
        """Invalid linter exits 2."""
        result = run_cli("--linters", "invalid", str(tmp_path))
        assert result.returncode == 2


@pytest.mark.e2e
class TestExcludeFlag:
    """E2E tests for the --exclude flag."""

    def test_exclude_pattern_exits_1(
        self, tmp_path: Path
    ) -> None:
        """--exclude with remaining findings exits 1."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            "--exclude", "*cache*", str(tmp_path),
        )
        assert result.returncode == 1

    def test_exclude_pattern_includes_non_excluded(
        self, tmp_path: Path
    ) -> None:
        """--exclude still reports non-excluded findings."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            "--exclude", "*cache*", str(tmp_path),
        )
        assert "mypy" in result.stdout

    def test_exclude_pattern_skips_excluded(
        self, tmp_path: Path
    ) -> None:
        """--exclude skips matching paths."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            "--exclude", "*cache*", str(tmp_path),
        )
        assert "cache" not in result.stdout

    @pytest.fixture
    def exclude_repeated_result(
        self, tmp_path: Path
    ) -> subprocess.CompletedProcess[str]:
        """Run CLI with multiple --exclude on vendor/node_modules/venv."""
        for name in ["vendor", "node_modules", "venv"]:
            subdir = tmp_path / name
            subdir.mkdir()
            (subdir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        return run_cli(
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*",
            "--exclude", "*node_modules*",
            "--exclude", "*venv*",
            str(tmp_path),
        )

    def test_exclude_repeated_exits_1(
        self, exclude_repeated_result: subprocess.CompletedProcess[str]
    ) -> None:
        """--exclude used multiple times exits 1."""
        assert exclude_repeated_result.returncode == 1

    def test_exclude_repeated_reports_one_finding(
        self, exclude_repeated_result: subprocess.CompletedProcess[str]
    ) -> None:
        """--exclude used multiple times leaves one finding."""
        lines = exclude_repeated_result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_exclude_repeated_reports_mypy(
        self, exclude_repeated_result: subprocess.CompletedProcess[str]
    ) -> None:
        """--exclude used multiple times reports mypy."""
        assert "mypy" in exclude_repeated_result.stdout


@pytest.mark.e2e
class TestOutputModes:
    """E2E tests for output mode flags."""

    def test_quiet_exits_1(self, tmp_path: Path) -> None:
        """--quiet with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--quiet", str(tmp_path)
        )
        assert result.returncode == 1

    def test_quiet_no_stdout(self, tmp_path: Path) -> None:
        """--quiet produces no stdout."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--quiet", str(tmp_path)
        )
        assert result.stdout == ""

    def test_count_exits_1(self, tmp_path: Path) -> None:
        """--count with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint",
            "--count", str(tmp_path),
        )
        assert result.returncode == 1

    def test_count_outputs_number(self, tmp_path: Path) -> None:
        """--count outputs the number of findings."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint",
            "--count", str(tmp_path),
        )
        assert result.stdout.strip() == "3"

    def test_json_exits_1(self, tmp_path: Path) -> None:
        """--json with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--json", str(tmp_path)
        )
        assert result.returncode == 1

    def test_json_outputs_list(self, tmp_path: Path) -> None:
        """--json outputs a JSON list."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--json", str(tmp_path)
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_json_outputs_one_finding(
        self, tmp_path: Path
    ) -> None:
        """--json outputs exactly one finding."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--json", str(tmp_path)
        )
        data = json.loads(result.stdout)
        assert len(data) == 1

    def test_json_finding_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """--json finding has correct tool field."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--json", str(tmp_path)
        )
        data = json.loads(result.stdout)
        assert data[0]["tool"] == "pylint"

    def test_json_finding_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """--json finding has correct reason field."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--json", str(tmp_path)
        )
        data = json.loads(result.stdout)
        assert data[0]["reason"] == "config file"


@pytest.mark.e2e
class TestBehaviorModifiers:
    """E2E tests for behavior modifier flags."""

    def test_fail_fast_exits_1(self, tmp_path: Path) -> None:
        """--fail-fast with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint",
            "--fail-fast", str(tmp_path),
        )
        assert result.returncode == 1

    def test_fail_fast_single_output(
        self, tmp_path: Path
    ) -> None:
        """--fail-fast outputs only one finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint",
            "--fail-fast", str(tmp_path),
        )
        lines = [
            line for line in result.stdout.strip().split("\n")
            if line
        ]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """--warn-only always exits 0 even with findings."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--warn-only", str(tmp_path)
        )
        assert result.returncode == 0

    def test_warn_only_reports_linter(
        self, tmp_path: Path
    ) -> None:
        """--warn-only still reports findings in output."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint", "--warn-only", str(tmp_path)
        )
        assert "pylint" in result.stdout

    def test_warn_only_no_findings_exits_0(
        self, tmp_path: Path
    ) -> None:
        """--warn-only exits 0 with no findings."""
        (tmp_path / "main.py").touch()
        result = run_cli(
            "--linters", "pylint", "--warn-only", str(tmp_path)
        )
        assert result.returncode == 0
