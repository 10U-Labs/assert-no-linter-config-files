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
        """Clean directory exits 0."""
        (tmp_path / "main.py").touch()
        (tmp_path / "README.md").write_text("# Hello")
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 0

    def test_clean_directory_no_output(self, tmp_path: Path) -> None:
        """Clean directory produces no output."""
        (tmp_path / "main.py").touch()
        (tmp_path / "README.md").write_text("# Hello")
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.stdout == ""

    def test_single_config_file_exits_1(self, tmp_path: Path) -> None:
        """Single config file exits 1."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 1

    def test_single_config_file_reports_filename(self, tmp_path: Path) -> None:
        """Single config file output includes filename."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert ".pylintrc" in result.stdout

    def test_single_config_file_reports_linter(self, tmp_path: Path) -> None:
        """Single config file output includes linter name."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "pylint" in result.stdout

    def test_single_config_file_reports_reason(self, tmp_path: Path) -> None:
        """Single config file output includes reason."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "config file" in result.stdout

    def test_multiple_config_files_exits_1(self, tmp_path: Path) -> None:
        """Multiple config files exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli("--linters", "pylint,yamllint,mypy", str(tmp_path))
        assert result.returncode == 1

    def test_multiple_config_files_reports_one_line_each(self, tmp_path: Path) -> None:
        """Multiple config files produce one output line each."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli("--linters", "pylint,yamllint,mypy", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_multiple_config_files_reports_all_linters(self, tmp_path: Path) -> None:
        """Multiple config files report all relevant linters."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli("--linters", "pylint,yamllint,mypy", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        linters = {line.split(":")[1] for line in lines}
        assert linters == {"pylint", "yamllint", "mypy"}

    def test_nested_directory_exits_1(self, tmp_path: Path) -> None:
        """Files in nested directories cause exit 1."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert result.returncode == 1

    def test_nested_directory_reports_filename(self, tmp_path: Path) -> None:
        """Files in nested directories report filename."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert ".yamllint" in result.stdout

    def test_nested_directory_reports_linter(self, tmp_path: Path) -> None:
        """Files in nested directories report linter name."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert "yamllint" in result.stdout

    def test_git_directory_skipped_exits_0(self, tmp_path: Path) -> None:
        """Files inside .git are skipped and exit is 0."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 0

    def test_git_directory_skipped_no_output(self, tmp_path: Path) -> None:
        """Files inside .git are skipped and produce no output."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.stdout == ""

    def test_pyproject_toml_with_tool_sections_exits_1(
        self, tmp_path: Path, pyproject_mypy_pylint_with_project_content: str
    ) -> None:
        """pyproject.toml with tool sections exits 1."""
        (tmp_path / "pyproject.toml").write_text(pyproject_mypy_pylint_with_project_content)
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        assert result.returncode == 1

    def test_pyproject_toml_with_tool_sections_reports_two_lines(
        self, tmp_path: Path, pyproject_mypy_pylint_with_project_content: str
    ) -> None:
        """pyproject.toml with two tool sections produces two output lines."""
        (tmp_path / "pyproject.toml").write_text(pyproject_mypy_pylint_with_project_content)
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_pyproject_toml_with_tool_sections_reports_mypy(
        self, tmp_path: Path, pyproject_mypy_pylint_with_project_content: str
    ) -> None:
        """pyproject.toml with tool.mypy section reports mypy."""
        (tmp_path / "pyproject.toml").write_text(pyproject_mypy_pylint_with_project_content)
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        assert "mypy" in result.stdout

    def test_pyproject_toml_with_tool_sections_reports_pylint(
        self, tmp_path: Path, pyproject_mypy_pylint_with_project_content: str
    ) -> None:
        """pyproject.toml with tool.pylint section reports pylint."""
        (tmp_path / "pyproject.toml").write_text(pyproject_mypy_pylint_with_project_content)
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        assert "pylint" in result.stdout

    def test_pyproject_toml_without_tool_sections_exits_0(self, tmp_path: Path) -> None:
        """pyproject.toml without relevant tool sections exits 0."""
        content = """
[project]
name = "myproject"

[tool.black]
line-length = 88
"""
        (tmp_path / "pyproject.toml").write_text(content)
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 0

    def test_pyproject_toml_without_tool_sections_no_output(self, tmp_path: Path) -> None:
        """pyproject.toml without relevant tool sections produces no output."""
        content = """
[project]
name = "myproject"

[tool.black]
line-length = 88
"""
        (tmp_path / "pyproject.toml").write_text(content)
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.stdout == ""

    def test_setup_cfg_with_tool_sections_exits_1(self, tmp_path: Path) -> None:
        """setup.cfg with tool sections exits 1."""
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

    def test_setup_cfg_with_tool_sections_reports_mypy(self, tmp_path: Path) -> None:
        """setup.cfg with mypy section reports mypy."""
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
        assert "mypy" in result.stdout

    def test_setup_cfg_with_tool_sections_reports_pytest(self, tmp_path: Path) -> None:
        """setup.cfg with tool:pytest section reports pytest."""
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
        assert "pytest" in result.stdout

    def test_tox_ini_with_tool_sections_exits_1(self, tmp_path: Path) -> None:
        """tox.ini with tool sections exits 1."""
        content = """
[tox]
envlist = py310

[pytest]
addopts = -v
"""
        (tmp_path / "tox.ini").write_text(content)
        result = run_cli("--linters", "pytest", str(tmp_path))
        assert result.returncode == 1

    def test_tox_ini_with_tool_sections_reports_pytest(self, tmp_path: Path) -> None:
        """tox.ini with pytest section reports pytest."""
        content = """
[tox]
envlist = py310

[pytest]
addopts = -v
"""
        (tmp_path / "tox.ini").write_text(content)
        result = run_cli("--linters", "pytest", str(tmp_path))
        assert "pytest" in result.stdout

    def test_all_jscpd_config_files_exits_1(self, tmp_path: Path) -> None:
        """All jscpd config file variants cause exit 1."""
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

    def test_all_jscpd_config_files_reports_eight_lines(self, tmp_path: Path) -> None:
        """All jscpd config file variants produce eight output lines."""
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
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 8

    def test_all_jscpd_config_files_all_reference_jscpd(self, tmp_path: Path) -> None:
        """All jscpd config file output lines reference jscpd."""
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
        lines = result.stdout.strip().split("\n")
        assert all("jscpd" in line for line in lines)

    def test_nonexistent_directory_exits_2(self) -> None:
        """Nonexistent directory exits 2."""
        result = run_cli(
            "--linters", "pylint", "/nonexistent/path/that/does/not/exist"
        )
        assert result.returncode == 2

    def test_nonexistent_directory_has_stderr(self) -> None:
        """Nonexistent directory produces stderr output."""
        result = run_cli(
            "--linters", "pylint", "/nonexistent/path/that/does/not/exist"
        )
        assert result.stderr != ""

    def test_missing_linters_flag_exits_2(self, tmp_path: Path) -> None:
        """Missing --linters flag exits 2."""
        result = run_cli(str(tmp_path))
        assert result.returncode == 2

    def test_scans_current_directory_exits_1(self, tmp_path: Path) -> None:
        """Scanning current directory with '.' exits 1 when config found."""
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", ".", cwd=tmp_path)
        assert result.returncode == 1

    def test_scans_current_directory_reports_filename(self, tmp_path: Path) -> None:
        """Scanning current directory with '.' reports config filename."""
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", ".", cwd=tmp_path)
        assert ".yamllint" in result.stdout

    def test_multiple_directories_exits_1(self, tmp_path: Path) -> None:
        """Multiple directories with config files exits 1."""
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

    def test_multiple_directories_reports_pylint(self, tmp_path: Path) -> None:
        """Multiple directories report pylint finding."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()

        result = run_cli(
            "--linters", "pylint,mypy", str(project_a), str(project_b)
        )
        assert "pylint" in result.stdout

    def test_multiple_directories_reports_mypy(self, tmp_path: Path) -> None:
        """Multiple directories report mypy finding."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()

        result = run_cli(
            "--linters", "pylint,mypy", str(project_a), str(project_b)
        )
        assert "mypy" in result.stdout

    def test_mixed_clean_and_dirty_dirs_exits_1(self, tmp_path: Path) -> None:
        """Findings from dirty dir cause exit 1 even with clean dirs."""
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

    def test_mixed_clean_and_dirty_dirs_reports_linter(self, tmp_path: Path) -> None:
        """Findings from dirty dir are reported even with clean dirs."""
        clean_dir = tmp_path / "clean"
        dirty_dir = tmp_path / "dirty"
        clean_dir.mkdir()
        dirty_dir.mkdir()
        (clean_dir / "main.py").touch()
        (dirty_dir / ".pylintrc").touch()

        result = run_cli(
            "--linters", "pylint", str(clean_dir), str(dirty_dir)
        )
        assert "pylint" in result.stdout

    def test_complex_project_structure_exits_1(self, tmp_path: Path) -> None:
        """Complex project with mypy config in pyproject.toml exits 1."""
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

    def test_complex_project_structure_reports_mypy(self, tmp_path: Path) -> None:
        """Complex project with mypy config in pyproject.toml reports mypy."""
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
        assert "mypy" in result.stdout

    def test_complex_project_structure_reports_one_finding(self, tmp_path: Path) -> None:
        """Complex project with only mypy config reports exactly one finding."""
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
        assert (
            "project/.pylintrc" in result.stdout
            or "project\\.pylintrc" in result.stdout
        )


@pytest.mark.e2e
class TestLintersFlag:
    """E2E tests for the --linters flag."""

    def test_linters_filters_output_exits_1(self, tmp_path: Path) -> None:
        """--linters with matching config exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 1

    def test_linters_filters_output_includes_pylint(self, tmp_path: Path) -> None:
        """--linters filters to include specified linter."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "pylint" in result.stdout

    def test_linters_filters_output_excludes_mypy(self, tmp_path: Path) -> None:
        """--linters filters out non-specified linters like mypy."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "mypy" not in result.stdout

    def test_linters_filters_output_excludes_yamllint(self, tmp_path: Path) -> None:
        """--linters filters out non-specified linters like yamllint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "yamllint" not in result.stdout

    def test_linters_comma_separated_exits_1(self, tmp_path: Path) -> None:
        """--linters with comma-separated values exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 1

    def test_linters_comma_separated_includes_pylint(self, tmp_path: Path) -> None:
        """--linters comma-separated includes pylint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert "pylint" in result.stdout

    def test_linters_comma_separated_includes_mypy(self, tmp_path: Path) -> None:
        """--linters comma-separated includes mypy."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert "mypy" in result.stdout

    def test_linters_comma_separated_excludes_yamllint(self, tmp_path: Path) -> None:
        """--linters comma-separated excludes non-specified yamllint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert "yamllint" not in result.stdout

    def test_linters_no_findings_exits_0(self, tmp_path: Path) -> None:
        """No findings for specified linter exits 0."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert result.returncode == 0

    def test_linters_no_findings_no_output(self, tmp_path: Path) -> None:
        """No findings for specified linter produces no output."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert result.stdout == ""

    def test_linters_invalid_exits_2(self, tmp_path: Path) -> None:
        """Invalid linter exits 2."""
        result = run_cli("--linters", "invalid", str(tmp_path))
        assert result.returncode == 2


@pytest.mark.e2e
class TestExcludeFlag:
    """E2E tests for the --exclude flag."""

    def test_exclude_pattern_exits_1(self, tmp_path: Path) -> None:
        """--exclude with remaining findings exits 1."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy", "--exclude", "*cache*", str(tmp_path)
        )
        assert result.returncode == 1

    def test_exclude_pattern_includes_non_excluded(self, tmp_path: Path) -> None:
        """--exclude still reports non-excluded findings."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy", "--exclude", "*cache*", str(tmp_path)
        )
        assert "mypy" in result.stdout

    def test_exclude_pattern_skips_excluded(self, tmp_path: Path) -> None:
        """--exclude skips matching paths."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy", "--exclude", "*cache*", str(tmp_path)
        )
        assert "cache" not in result.stdout

    def test_exclude_repeated_exits_1(self, tmp_path: Path) -> None:
        """--exclude used multiple times with remaining findings exits 1."""
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

    def test_exclude_repeated_reports_one_finding(self, tmp_path: Path) -> None:
        """--exclude used multiple times leaves only non-excluded findings."""
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
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_exclude_repeated_reports_mypy(self, tmp_path: Path) -> None:
        """--exclude used multiple times still reports non-excluded mypy finding."""
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
        assert "mypy" in result.stdout


@pytest.mark.e2e
class TestOutputModes:
    """E2E tests for output mode flags."""

    def test_quiet_exits_1(self, tmp_path: Path) -> None:
        """--quiet with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--quiet", str(tmp_path))
        assert result.returncode == 1

    def test_quiet_no_stdout(self, tmp_path: Path) -> None:
        """--quiet produces no stdout."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--quiet", str(tmp_path))
        assert result.stdout == ""

    def test_count_exits_1(self, tmp_path: Path) -> None:
        """--count with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint", "--count", str(tmp_path)
        )
        assert result.returncode == 1

    def test_count_outputs_number(self, tmp_path: Path) -> None:
        """--count outputs the number of findings."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint", "--count", str(tmp_path)
        )
        assert result.stdout.strip() == "3"

    def test_json_exits_1(self, tmp_path: Path) -> None:
        """--json with findings exits 1."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--json", str(tmp_path))
        assert result.returncode == 1

    def test_json_outputs_list(self, tmp_path: Path) -> None:
        """--json outputs a JSON list."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--json", str(tmp_path))
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_json_outputs_one_finding(self, tmp_path: Path) -> None:
        """--json outputs exactly one finding for single config file."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--json", str(tmp_path))
        data = json.loads(result.stdout)
        assert len(data) == 1

    def test_json_finding_has_correct_tool(self, tmp_path: Path) -> None:
        """--json finding has correct tool field."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--json", str(tmp_path))
        data = json.loads(result.stdout)
        assert data[0]["tool"] == "pylint"

    def test_json_finding_has_correct_reason(self, tmp_path: Path) -> None:
        """--json finding has correct reason field."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--json", str(tmp_path))
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
            "--linters", "pylint,mypy,yamllint", "--fail-fast", str(tmp_path)
        )
        assert result.returncode == 1

    def test_fail_fast_single_output(self, tmp_path: Path) -> None:
        """--fail-fast outputs only one finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "pylint,mypy,yamllint", "--fail-fast", str(tmp_path)
        )
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(self, tmp_path: Path) -> None:
        """--warn-only always exits 0 even with findings."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--warn-only", str(tmp_path))
        assert result.returncode == 0

    def test_warn_only_reports_linter(self, tmp_path: Path) -> None:
        """--warn-only still reports findings in output."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", "--warn-only", str(tmp_path))
        assert "pylint" in result.stdout

    def test_warn_only_no_findings_exits_0(self, tmp_path: Path) -> None:
        """--warn-only exits 0 with no findings."""
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", "--warn-only", str(tmp_path))
        assert result.returncode == 0
