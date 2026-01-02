"""End-to-end tests for assert-no-linter-config-files."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CLI via subprocess."""
    # Preserve PYTHONPATH and ensure src path is absolute
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent.parent / "src"
    current_pythonpath = env.get("PYTHONPATH", "")
    if current_pythonpath:
        env["PYTHONPATH"] = f"{src_path.resolve()}:{current_pythonpath}"
    else:
        env["PYTHONPATH"] = str(src_path.resolve())
    return subprocess.run(
        [sys.executable, "-m", "assert_no_linter_config_files", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=False,
    )


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests for the CLI."""

    def test_clean_directory_exits_0(self, tmp_path: Path) -> None:
        """Clean directory exits 0 with no output."""
        (tmp_path / "main.py").touch()
        (tmp_path / "README.md").write_text("# Hello")
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_single_config_file_exits_1(self, tmp_path: Path) -> None:
        """Single config file exits 1 with finding."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 1
        assert ".pylintrc" in result.stdout
        assert "pylint" in result.stdout
        assert "config file" in result.stdout

    def test_multiple_config_files_all_reported(self, tmp_path: Path) -> None:
        """Multiple config files are all reported."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli("--linters", "pylint,yamllint,mypy", str(tmp_path))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3
        linters = {line.split(":")[1] for line in lines}
        assert linters == {"pylint", "yamllint", "mypy"}

    def test_nested_directory_structure(self, tmp_path: Path) -> None:
        """Files in nested directories are found."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert result.returncode == 1
        assert ".yamllint" in result.stdout
        assert "yamllint" in result.stdout

    def test_git_directory_skipped(self, tmp_path: Path) -> None:
        """Files inside .git are skipped."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
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
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
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
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
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
        result = run_cli("--linters", "mypy,pytest", str(tmp_path))
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
        result = run_cli("--linters", "pytest", str(tmp_path))
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

        result = run_cli("--linters", "jscpd", str(tmp_path))
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 8
        assert all("jscpd" in line for line in lines)

    def test_nonexistent_directory_exits_2(self) -> None:
        """Nonexistent directory exits 2."""
        result = run_cli(
            "--linters", "pylint", "/nonexistent/path/that/does/not/exist"
        )
        assert result.returncode == 2
        assert result.stderr != ""

    def test_missing_linters_flag_exits_2(self, tmp_path: Path) -> None:
        """Missing --linters flag exits 2."""
        result = run_cli(str(tmp_path))
        assert result.returncode == 2

    def test_scans_current_directory(self, tmp_path: Path) -> None:
        """Can scan current directory with '.'."""
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", ".", cwd=tmp_path)
        assert result.returncode == 1
        assert ".yamllint" in result.stdout

    def test_multiple_directories_argument(self, tmp_path: Path) -> None:
        """Multiple directories can be specified."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()

        result = run_cli(
            "--linters", "pylint,mypy", str(project_a), str(project_b)
        )
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

        result = run_cli(
            "--linters", "pylint", str(clean_dir), str(dirty_dir)
        )
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

        result = run_cli("--linters", "mypy", str(tmp_path))
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

        result = run_cli("--linters", "pylint", "project")
        assert result.returncode == 1
        assert (
            "project/.pylintrc" in result.stdout
            or "project\\.pylintrc" in result.stdout
        )


@pytest.mark.e2e
class TestLintersFlag:
    """E2E tests for the --linters flag."""

    def test_linters_filters_output(self, tmp_path: Path) -> None:
        """--linters filters to specified linters only."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 1
        assert "pylint" in result.stdout
        assert "mypy" not in result.stdout
        assert "yamllint" not in result.stdout

    def test_linters_comma_separated(self, tmp_path: Path) -> None:
        """--linters accepts comma-separated values."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 1
        assert "pylint" in result.stdout
        assert "mypy" in result.stdout
        assert "yamllint" not in result.stdout

    def test_linters_no_findings_exits_0(self, tmp_path: Path) -> None:
        """No findings for specified linter exits 0."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert result.returncode == 0
        assert result.stdout == ""

    def test_linters_invalid_exits_2(self, tmp_path: Path) -> None:
        """Invalid linter exits 2."""
        result = run_cli("--linters", "invalid", str(tmp_path))
        assert result.returncode == 2


@pytest.mark.e2e
class TestExcludeFlag:
    """E2E tests for the --exclude flag."""

    def test_exclude_pattern(self, tmp_path: Path) -> None:
        """--exclude skips matching paths."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy", "--exclude", "*cache*", str(tmp_path)
        )
        assert result.returncode == 1
        assert "mypy" in result.stdout
        assert "cache" not in result.stdout

    def test_exclude_repeated(self, tmp_path: Path) -> None:
        """--exclude can be used multiple times."""
        for name in ["vendor", "node_modules", "venv"]:
            subdir = tmp_path / name
            subdir.mkdir()
            (subdir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*",
            "--exclude", "*node_modules*",
            "--exclude", "*venv*",
            str(tmp_path)
        )
        assert result.returncode == 1
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1
        assert "mypy" in result.stdout


@pytest.mark.e2e
class TestOutputModes:
    """E2E tests for output mode flags."""

    def test_quiet_no_stdout(self, tmp_path: Path) -> None:
        """--quiet produces no stdout."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--quiet", str(tmp_path))
        assert result.returncode == 1
        assert result.stdout == ""

    def test_count_outputs_number(self, tmp_path: Path) -> None:
        """--count outputs the number of findings."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint", "--count", str(tmp_path)
        )
        assert result.returncode == 1
        assert result.stdout.strip() == "3"

    def test_json_valid_output(self, tmp_path: Path) -> None:
        """--json outputs valid JSON."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--json", str(tmp_path))
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["tool"] == "pylint"
        assert data[0]["reason"] == "config file"


@pytest.mark.e2e
class TestBehaviorModifiers:
    """E2E tests for behavior modifier flags."""

    def test_fail_fast_single_output(self, tmp_path: Path) -> None:
        """--fail-fast outputs only one finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint", "--fail-fast", str(tmp_path)
        )
        assert result.returncode == 1
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """--warn-only always exits 0 even with findings."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--warn-only", str(tmp_path))
        assert result.returncode == 0
        assert "pylint" in result.stdout

    def test_warn_only_no_findings_exits_0(self, tmp_path: Path) -> None:
        """--warn-only exits 0 with no findings."""
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", "--warn-only", str(tmp_path))
        assert result.returncode == 0
