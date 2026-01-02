"""Integration tests for the CLI module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.cli import main


def run_main_with_args(args: list[str]) -> tuple[int, str, str]:
    """Run main() with patched sys.argv and return exit code, stdout, stderr."""
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def mock_stdout_print(*print_args: object, **kwargs: object) -> None:
        if kwargs.get("file") is None:
            stdout_lines.append(" ".join(str(a) for a in print_args))

    def mock_stderr_print(*print_args: object, **kwargs: object) -> None:
        if kwargs.get("file") is sys.stderr:
            stderr_lines.append(" ".join(str(a) for a in print_args))

    with patch("sys.argv", ["prog"] + args):
        with patch("builtins.print", side_effect=lambda *a, **k: (
            mock_stderr_print(*a, **k) if k.get("file") else
            mock_stdout_print(*a, **k)
        )):
            with pytest.raises(SystemExit) as exc_info:
                main()
            code = int(exc_info.value.code or 0)
            return code, "\n".join(stdout_lines), "\n".join(stderr_lines)


@pytest.mark.integration
class TestMainFunction:
    """Tests for the main() function."""

    def test_no_config_exits_0(self, tmp_path: Path) -> None:
        """Exit 0 when no linter config is found."""
        (tmp_path / "main.py").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 0
        assert stdout == ""

    def test_config_found_exits_1(self, tmp_path: Path) -> None:
        """Exit 1 when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "config file" in stdout

    def test_invalid_directory_exits_2(self) -> None:
        """Exit 2 when directory does not exist."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "/nonexistent/path"
        ])
        assert code == 2

    def test_scans_current_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Can scan current directory with '.'."""
        (tmp_path / ".yamllint").touch()
        monkeypatch.chdir(tmp_path)
        code, stdout, _ = run_main_with_args(["--linters", "yamllint", "."])
        assert code == 1
        assert "yamllint" in stdout

    def test_multiple_directories(self, tmp_path: Path) -> None:
        """Multiple directories can be scanned."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(first_dir), str(second_dir)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "mypy" in stdout

    def test_help_exits_0(self) -> None:
        """--help exits with code 0."""
        code, _, _ = run_main_with_args(["--help"])
        assert code == 0

    def test_missing_linters_exits_2(self, tmp_path: Path) -> None:
        """Missing --linters flag exits 2."""
        code, _, _ = run_main_with_args([str(tmp_path)])
        assert code == 2

    def test_output_format(self, tmp_path: Path) -> None:
        """Output format is path:tool:reason."""
        (tmp_path / ".yamllint").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1
        lines = stdout.strip().split("\n")
        assert len(lines) == 1
        parts = lines[0].split(":")
        assert len(parts) == 3
        assert ".yamllint" in parts[0]
        assert parts[1] == "yamllint"
        assert parts[2] == "config file"

    def test_pyproject_toml_section(self, tmp_path: Path) -> None:
        """Embedded config in pyproject.toml is detected."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1
        assert "mypy" in stdout
        assert "tool.mypy" in stdout

    def test_file_instead_of_directory_exits_2(self, tmp_path: Path) -> None:
        """Exit 2 when a file is provided instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(file_path)
        ])
        assert code == 2


@pytest.mark.integration
class TestLintersFlag:
    """Tests for the --linters flag."""

    def test_linters_filters_findings(self, tmp_path: Path) -> None:
        """--linters filters to only specified linters."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "mypy" not in stdout

    def test_linters_multiple(self, tmp_path: Path) -> None:
        """--linters accepts comma-separated values."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "mypy" in stdout
        assert "yamllint" not in stdout

    def test_linters_invalid_exits_2(self, tmp_path: Path) -> None:
        """--linters with invalid linter exits 2."""
        code, _, _ = run_main_with_args([
            "--linters", "invalid", str(tmp_path)
        ])
        assert code == 2


@pytest.mark.integration
class TestExcludeFlag:
    """Tests for the --exclude flag."""

    def test_exclude_pattern(self, tmp_path: Path) -> None:
        """--exclude skips matching paths."""
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*", str(tmp_path)
        ])
        assert code == 1
        assert "mypy" in stdout
        assert "pylint" not in stdout

    def test_exclude_multiple(self, tmp_path: Path) -> None:
        """--exclude can be repeated."""
        deps = tmp_path / "deps"
        third = tmp_path / "third_party"
        deps.mkdir()
        third.mkdir()
        (deps / ".pylintrc").touch()
        (third / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy,yamllint",
            "--exclude", "*deps*",
            "--exclude", "*third_party*",
            str(tmp_path)
        ])
        assert code == 1
        assert "yamllint" in stdout
        assert "pylint" not in stdout
        assert "mypy" not in stdout


@pytest.mark.integration
class TestOutputModes:
    """Tests for output mode flags."""

    def test_quiet_no_output(self, tmp_path: Path) -> None:
        """--quiet suppresses output."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--quiet", str(tmp_path)
        ])
        assert code == 1
        assert stdout == ""

    def test_count_outputs_number(self, tmp_path: Path) -> None:
        """--count outputs finding count."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--count", str(tmp_path)
        ])
        assert code == 1
        assert stdout.strip() == "2"

    def test_json_outputs_json(self, tmp_path: Path) -> None:
        """--json outputs JSON format."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert code == 1
        assert stdout.startswith("[")
        assert "pylint" in stdout


@pytest.mark.integration
class TestBehaviorModifiers:
    """Tests for behavior modifier flags."""

    def test_fail_fast_stops_early(self, tmp_path: Path) -> None:
        """--fail-fast exits on first finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--fail-fast", str(tmp_path)
        ])
        assert code == 1
        lines = [line for line in stdout.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """--warn-only always exits 0."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--warn-only", str(tmp_path)
        ])
        assert code == 0
        assert "pylint" in stdout
