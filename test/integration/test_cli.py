"""Integration tests for the CLI module."""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestMainFunction:
    """Tests for the main() function."""

    def test_no_config_exits_0(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 0 when no linter config is found."""
        (tmp_path / "main.py").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 0
        assert stdout == ""

    def test_config_found_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "config file" in stdout

    def test_invalid_directory_exits_2(self, run_main_with_args) -> None:
        """Exit 2 when directory does not exist."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "/nonexistent/path"
        ])
        assert code == 2

    def test_scans_current_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_main_with_args
    ) -> None:
        """Can scan current directory with '.'."""
        (tmp_path / ".yamllint").touch()
        monkeypatch.chdir(tmp_path)
        code, stdout, _ = run_main_with_args(["--linters", "yamllint", "."])
        assert code == 1
        assert "yamllint" in stdout

    def test_multiple_directories(self, tmp_path: Path, run_main_with_args) -> None:
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

    def test_help_exits_0(self, run_main_with_args) -> None:
        """--help exits with code 0."""
        code, _, _ = run_main_with_args(["--help"])
        assert code == 0

    def test_missing_linters_exits_2(self, tmp_path: Path, run_main_with_args) -> None:
        """Missing --linters flag exits 2."""
        code, _, _ = run_main_with_args([str(tmp_path)])
        assert code == 2

    def test_output_format(self, tmp_path: Path, run_main_with_args) -> None:
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

    def test_pyproject_toml_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Embedded config in pyproject.toml is detected."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1
        assert "mypy" in stdout
        assert "tool.mypy" in stdout

    def test_file_instead_of_directory_exits_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
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

    def test_linters_filters_findings(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters filters to only specified linters."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "mypy" not in stdout

    def test_linters_multiple(self, tmp_path: Path, run_main_with_args) -> None:
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

    def test_linters_invalid_exits_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters with invalid linter exits 2."""
        code, _, _ = run_main_with_args([
            "--linters", "invalid", str(tmp_path)
        ])
        assert code == 2


@pytest.mark.integration
class TestExcludeFlag:
    """Tests for the --exclude flag."""

    def test_exclude_pattern(self, tmp_path: Path, run_main_with_args) -> None:
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

    def test_exclude_multiple(self, tmp_path: Path, run_main_with_args) -> None:
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

    def test_quiet_no_output(self, tmp_path: Path, run_main_with_args) -> None:
        """--quiet suppresses output."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--quiet", str(tmp_path)
        ])
        assert code == 1
        assert stdout == ""

    def test_count_outputs_number(self, tmp_path: Path, run_main_with_args) -> None:
        """--count outputs finding count."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--count", str(tmp_path)
        ])
        assert code == 1
        assert stdout.strip() == "2"

    def test_json_outputs_json(self, tmp_path: Path, run_main_with_args) -> None:
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

    def test_fail_fast_stops_early(self, tmp_path: Path, run_main_with_args) -> None:
        """--fail-fast exits on first finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--fail-fast", str(tmp_path)
        ])
        assert code == 1
        lines = [line for line in stdout.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path, run_main_with_args) -> None:
        """--warn-only always exits 0."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--warn-only", str(tmp_path)
        ])
        assert code == 0
        assert "pylint" in stdout
