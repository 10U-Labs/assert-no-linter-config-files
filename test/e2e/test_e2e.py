"""End-to-end tests for assert-no-linter-config-files."""

import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CLI via subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "assert_no_linter_config_files", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests for the CLI."""

    def test_clean_directory_exits_0(self, tmp_path: Path) -> None:
        """Clean directory exits 0 with no output."""
        (tmp_path / "main.py").touch()
        (tmp_path / "README.md").write_text("# Hello")
        result = run_cli(str(tmp_path))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_single_config_file_exits_1(self, tmp_path: Path) -> None:
        """Single config file exits 1 with finding."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        assert ".pylintrc" in result.stdout
        assert "pylint" in result.stdout
        assert "config file" in result.stdout

    def test_multiple_config_files_all_reported(self, tmp_path: Path) -> None:
        """Multiple config files are all reported."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "pytest.ini").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3
        tools = {line.split(":")[1] for line in lines}
        assert tools == {"pylint", "pytest", "mypy"}

    def test_nested_directory_structure(self, tmp_path: Path) -> None:
        """Files in nested directories are found."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        assert ".yamllint" in result.stdout
        assert "yamllint" in result.stdout

    def test_git_directory_skipped(self, tmp_path: Path) -> None:
        """Files inside .git are skipped."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        (tmp_path / "main.py").touch()
        result = run_cli(str(tmp_path))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_pyproject_toml_with_tool_sections(self, tmp_path: Path) -> None:
        """pyproject.toml with tool sections is flagged."""
        content = """
[project]
name = "myproject"

[tool.mypy]
strict = true

[tool.pylint]
max-line-length = 100
"""
        (tmp_path / "pyproject.toml").write_text(content)
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2
        assert "mypy" in result.stdout
        assert "pylint" in result.stdout

    def test_pyproject_toml_without_tool_sections(self, tmp_path: Path) -> None:
        """pyproject.toml without relevant tool sections is clean."""
        content = """
[project]
name = "myproject"

[tool.black]
line-length = 88
"""
        (tmp_path / "pyproject.toml").write_text(content)
        result = run_cli(str(tmp_path))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_setup_cfg_with_tool_sections(self, tmp_path: Path) -> None:
        """setup.cfg with tool sections is flagged."""
        content = """
[metadata]
name = myproject

[mypy]
strict = True

[tool:pytest]
addopts = -v
"""
        (tmp_path / "setup.cfg").write_text(content)
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        assert "mypy" in result.stdout
        assert "pytest" in result.stdout

    def test_tox_ini_with_tool_sections(self, tmp_path: Path) -> None:
        """tox.ini with tool sections is flagged."""
        content = """
[tox]
envlist = py310

[pytest]
addopts = -v
"""
        (tmp_path / "tox.ini").write_text(content)
        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        assert "pytest" in result.stdout

    def test_all_jscpd_config_files(self, tmp_path: Path) -> None:
        """All jscpd config file variants are detected."""
        jscpd_files = [
            ".jscpd.json",
            ".jscpd.yml",
            ".jscpd.yaml",
            ".jscpd.toml",
            ".jscpdrc",
            ".jscpdrc.json",
            ".jscpdrc.yml",
            ".jscpdrc.yaml",
        ]
        for i, filename in enumerate(jscpd_files):
            subdir = tmp_path / f"dir{i}"
            subdir.mkdir()
            (subdir / filename).touch()

        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 8
        assert all("jscpd" in line for line in lines)

    def test_nonexistent_directory_exits_2(self) -> None:
        """Nonexistent directory exits 2."""
        result = run_cli("/nonexistent/path/that/does/not/exist")
        assert result.returncode == 2
        assert result.stderr != ""

    def test_default_directory_is_cwd(self, tmp_path: Path) -> None:
        """Running with no args scans current directory."""
        (tmp_path / "pytest.ini").touch()
        result = run_cli(cwd=tmp_path)
        assert result.returncode == 1
        assert "pytest.ini" in result.stdout

    def test_multiple_directories_argument(self, tmp_path: Path) -> None:
        """Multiple directories can be specified."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()

        result = run_cli(str(project_a), str(project_b))
        assert result.returncode == 1
        assert "pylint" in result.stdout
        assert "mypy" in result.stdout

    def test_mixed_clean_and_dirty_dirs(self, tmp_path: Path) -> None:
        """Findings from dirty dir reported even with clean dirs."""
        clean_dir = tmp_path / "clean"
        dirty_dir = tmp_path / "dirty"
        clean_dir.mkdir()
        dirty_dir.mkdir()
        (clean_dir / "main.py").touch()
        (dirty_dir / ".pylintrc").touch()

        result = run_cli(str(clean_dir), str(dirty_dir))
        assert result.returncode == 1
        assert "pylint" in result.stdout

    def test_complex_project_structure(self, tmp_path: Path) -> None:
        """Complex project with multiple levels and file types."""
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        docs = tmp_path / "docs"
        src.mkdir()
        tests.mkdir()
        docs.mkdir()

        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "myproject"

[tool.mypy]
strict = true
""")
        (tmp_path / "setup.cfg").write_text("""
[metadata]
name = myproject
""")
        (src / "main.py").touch()
        (tests / "test_main.py").touch()
        (docs / "README.md").touch()

        result = run_cli(str(tmp_path))
        assert result.returncode == 1
        assert "mypy" in result.stdout
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_output_paths_are_relative(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Output paths are relative to cwd."""
        subdir = tmp_path / "project"
        subdir.mkdir()
        (subdir / ".pylintrc").touch()
        monkeypatch.chdir(tmp_path)

        result = run_cli("project")
        assert result.returncode == 1
        assert "project/.pylintrc" in result.stdout or "project\\.pylintrc" in result.stdout
