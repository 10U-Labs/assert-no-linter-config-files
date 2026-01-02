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
        code, stdout, _ = run_main_with_args([str(tmp_path)])
        assert code == 0
        assert stdout == ""

    def test_config_found_exits_1(self, tmp_path: Path) -> None:
        """Exit 1 when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([str(tmp_path)])
        assert code == 1
        assert "pylint" in stdout
        assert "config file" in stdout

    def test_invalid_directory_exits_2(self) -> None:
        """Exit 2 when directory does not exist."""
        code, _, _ = run_main_with_args(["/nonexistent/path"])
        assert code == 2

    def test_default_directory_is_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Default directory is current working directory."""
        (tmp_path / "pytest.ini").touch()
        monkeypatch.chdir(tmp_path)
        code, stdout, _ = run_main_with_args([])
        assert code == 1
        assert "pytest" in stdout

    def test_multiple_directories(self, tmp_path: Path) -> None:
        """Multiple directories can be scanned."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([str(first_dir), str(second_dir)])
        assert code == 1
        assert "pylint" in stdout
        assert "mypy" in stdout

    def test_help_exits_0(self) -> None:
        """--help exits with code 0."""
        code, _, _ = run_main_with_args(["--help"])
        assert code == 0

    def test_output_format(self, tmp_path: Path) -> None:
        """Output format is path:tool:reason."""
        (tmp_path / "pytest.ini").touch()
        code, stdout, _ = run_main_with_args([str(tmp_path)])
        assert code == 1
        lines = stdout.strip().split("\n")
        assert len(lines) == 1
        parts = lines[0].split(":")
        assert len(parts) == 3
        assert "pytest.ini" in parts[0]
        assert parts[1] == "pytest"
        assert parts[2] == "config file"

    def test_pyproject_toml_section(self, tmp_path: Path) -> None:
        """Embedded config in pyproject.toml is detected."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([str(tmp_path)])
        assert code == 1
        assert "mypy" in stdout
        assert "tool.mypy" in stdout

    def test_file_instead_of_directory_exits_2(self, tmp_path: Path) -> None:
        """Exit 2 when a file is provided instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        code, _, _ = run_main_with_args([str(file_path)])
        assert code == 2
