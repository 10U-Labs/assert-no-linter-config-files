"""Integration tests for the main() function."""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestMainBasic:
    """Tests for the main() function basic behavior."""

    def test_no_config_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 0 when no linter config is found."""
        (tmp_path / "main.py").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 0

    def test_no_config_produces_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """No output when no linter config is found."""
        (tmp_path / "main.py").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert stdout == ""

    def test_config_found_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_config_found_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when pylint config is found."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_config_found_outputs_config_file(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'config file' when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "config file" in stdout

    def test_invalid_directory_exits_2(
        self, run_main_with_args
    ) -> None:
        """Exit 2 when directory does not exist."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "/nonexistent/path"
        ])
        assert code == 2

    def test_scans_current_directory_exits_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        run_main_with_args,
    ) -> None:
        """Can scan current directory with '.' and exit 1."""
        (tmp_path / ".yamllint").touch()
        monkeypatch.chdir(tmp_path)
        code, _, _ = run_main_with_args(["--linters", "yamllint", "."])
        assert code == 1

    def test_scans_current_directory_outputs_yamllint(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        run_main_with_args,
    ) -> None:
        """Can scan current directory with '.' and output yamllint."""
        (tmp_path / ".yamllint").touch()
        monkeypatch.chdir(tmp_path)
        _, stdout, _ = run_main_with_args(["--linters", "yamllint", "."])
        assert "yamllint" in stdout

    def test_multiple_directories_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when configs found across multiple directories."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            str(first_dir), str(second_dir)
        ])
        assert code == 1

    def test_multiple_directories_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when scanning multiple directories."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            str(first_dir), str(second_dir)
        ])
        assert "pylint" in stdout

    def test_multiple_directories_outputs_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains mypy when scanning multiple directories."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            str(first_dir), str(second_dir)
        ])
        assert "mypy" in stdout

    def test_help_exits_0(self, run_main_with_args) -> None:
        """--help exits with code 0."""
        code, _, _ = run_main_with_args(["--help"])
        assert code == 0

    def test_missing_linters_exits_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Missing --linters flag exits 2."""
        code, _, _ = run_main_with_args([str(tmp_path)])
        assert code == 2

    def test_file_instead_of_directory_exits_2(
        self, file_instead_of_directory_result: tuple[int, str, str]
    ) -> None:
        """Exit 2 when a file is provided instead of directory."""
        code, _, _ = file_instead_of_directory_result
        assert code == 2


@pytest.mark.integration
class TestMainOutputFormat:
    """Tests for the main() function output format."""

    def test_output_format_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when config file is found for output format test."""
        (tmp_path / ".yamllint").touch()
        code, _, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1

    def test_output_format_single_line(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output is a single line when one config file is found."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert len(stdout.strip().split("\n")) == 1

    def test_output_format_has_three_parts(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output line has three colon-separated parts."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert len(stdout.strip().split("\n")[0].split(":")) == 3

    def test_output_format_path_contains_filename(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """First part of output contains the config filename."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert ".yamllint" in stdout.strip().split("\n")[0].split(":")[0]

    def test_output_format_tool_is_yamllint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Second part of output is the tool name."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert stdout.strip().split("\n")[0].split(":")[1] == "yamllint"

    def test_output_format_reason_is_config_file(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Third part of output is 'config file'."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert stdout.strip().split("\n")[0].split(":")[2] == "config file"

    def test_pyproject_toml_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when embedded config in pyproject.toml is detected."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_pyproject_toml_section_outputs_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains mypy when pyproject.toml has mypy section."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_pyproject_toml_section_outputs_tool_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'tool.mypy' when pyproject.toml has section."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "tool.mypy" in stdout
