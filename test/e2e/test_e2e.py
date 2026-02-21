"""End-to-end tests for assert-no-linter-config-files."""

from pathlib import Path
from test.e2e.conftest import run_cli

import pytest


@pytest.mark.e2e
class TestEndToEndBasic:
    """End-to-end tests for basic CLI functionality."""

    def test_clean_directory_exits_0(self, tmp_path: Path) -> None:
        """Clean directory exits 0."""
        (tmp_path / "main.py").touch()
        (tmp_path / "README.md").write_text("# Hello")
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 0

    def test_clean_directory_no_output(
        self, tmp_path: Path
    ) -> None:
        """Clean directory produces no output."""
        (tmp_path / "main.py").touch()
        (tmp_path / "README.md").write_text("# Hello")
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.stdout == ""

    def test_single_config_file_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Single config file exits 1."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 1

    def test_single_config_file_reports_filename(
        self, tmp_path: Path
    ) -> None:
        """Single config file output includes filename."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert ".pylintrc" in result.stdout

    def test_single_config_file_reports_linter(
        self, tmp_path: Path
    ) -> None:
        """Single config file output includes linter name."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "pylint" in result.stdout

    def test_single_config_file_reports_reason(
        self, tmp_path: Path
    ) -> None:
        """Single config file output includes reason."""
        (tmp_path / ".pylintrc").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert "config file" in result.stdout

    def test_multiple_config_files_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Multiple config files exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,yamllint,mypy", str(tmp_path)
        )
        assert result.returncode == 1

    def test_multiple_config_files_reports_one_line_each(
        self, tmp_path: Path
    ) -> None:
        """Multiple config files produce one output line each."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,yamllint,mypy", str(tmp_path)
        )
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_multiple_config_files_reports_all_linters(
        self, tmp_path: Path
    ) -> None:
        """Multiple config files report all relevant linters."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / ".yamllint").touch()
        (tmp_path / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,yamllint,mypy", str(tmp_path)
        )
        lines = result.stdout.strip().split("\n")
        linters = {line.split(":")[1] for line in lines}
        assert linters == {"pylint", "yamllint", "mypy"}

    def test_nested_directory_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Files in nested directories cause exit 1."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert result.returncode == 1

    def test_nested_directory_reports_filename(
        self, tmp_path: Path
    ) -> None:
        """Files in nested directories report filename."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert ".yamllint" in result.stdout

    def test_nested_directory_reports_linter(
        self, tmp_path: Path
    ) -> None:
        """Files in nested directories report linter name."""
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)
        (subdir / ".yamllint").touch()
        result = run_cli("--linters", "yamllint", str(tmp_path))
        assert "yamllint" in result.stdout

    def test_git_directory_skipped_exits_0(
        self, tmp_path: Path
    ) -> None:
        """Files inside .git are skipped and exit is 0."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.returncode == 0

    def test_git_directory_skipped_no_output(
        self, tmp_path: Path
    ) -> None:
        """Files inside .git are skipped and produce no output."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        (tmp_path / "main.py").touch()
        result = run_cli("--linters", "pylint", str(tmp_path))
        assert result.stdout == ""

    def test_nonexistent_directory_exits_2(self) -> None:
        """Nonexistent directory exits 2."""
        result = run_cli(
            "--linters", "pylint",
            "/nonexistent/path/that/does/not/exist",
        )
        assert result.returncode == 2

    def test_nonexistent_directory_has_stderr(self) -> None:
        """Nonexistent directory produces stderr output."""
        result = run_cli(
            "--linters", "pylint",
            "/nonexistent/path/that/does/not/exist",
        )
        assert result.stderr != ""

    def test_missing_linters_flag_exits_2(
        self, tmp_path: Path
    ) -> None:
        """Missing --linters flag exits 2."""
        result = run_cli(str(tmp_path))
        assert result.returncode == 2


@pytest.mark.e2e
class TestEndToEndConfigDetection:
    """End-to-end tests for config file detection in shared files."""

    def test_pyproject_toml_exits_1(
        self,
        tmp_path: Path,
        pyproject_mypy_pylint_with_project_content: str,
    ) -> None:
        """pyproject.toml with tool sections exits 1."""
        (tmp_path / "pyproject.toml").write_text(
            pyproject_mypy_pylint_with_project_content
        )
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        assert result.returncode == 1

    def test_pyproject_toml_reports_two_lines(
        self,
        tmp_path: Path,
        pyproject_mypy_pylint_with_project_content: str,
    ) -> None:
        """pyproject.toml with two tool sections produces two lines."""
        (tmp_path / "pyproject.toml").write_text(
            pyproject_mypy_pylint_with_project_content
        )
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_pyproject_toml_reports_mypy(
        self,
        tmp_path: Path,
        pyproject_mypy_pylint_with_project_content: str,
    ) -> None:
        """pyproject.toml with tool.mypy section reports mypy."""
        (tmp_path / "pyproject.toml").write_text(
            pyproject_mypy_pylint_with_project_content
        )
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        assert "mypy" in result.stdout

    def test_pyproject_toml_reports_pylint(
        self,
        tmp_path: Path,
        pyproject_mypy_pylint_with_project_content: str,
    ) -> None:
        """pyproject.toml with tool.pylint section reports pylint."""
        (tmp_path / "pyproject.toml").write_text(
            pyproject_mypy_pylint_with_project_content
        )
        result = run_cli("--linters", "mypy,pylint", str(tmp_path))
        assert "pylint" in result.stdout

    def test_pyproject_toml_without_tool_exits_0(
        self, tmp_path: Path
    ) -> None:
        """pyproject.toml without relevant tool sections exits 0."""
        content = (
            "[project]\n"
            'name = "myproject"\n\n'
            "[tool.black]\n"
            "line-length = 88\n"
        )
        (tmp_path / "pyproject.toml").write_text(content)
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.returncode == 0

    def test_pyproject_toml_without_tool_no_output(
        self, tmp_path: Path
    ) -> None:
        """pyproject.toml without relevant sections produces none."""
        content = (
            "[project]\n"
            'name = "myproject"\n\n'
            "[tool.black]\n"
            "line-length = 88\n"
        )
        (tmp_path / "pyproject.toml").write_text(content)
        result = run_cli("--linters", "pylint,mypy", str(tmp_path))
        assert result.stdout == ""

    def test_setup_cfg_exits_1(self, tmp_path: Path) -> None:
        """setup.cfg with tool sections exits 1."""
        content = (
            "[metadata]\nname = myproject\n\n"
            "[mypy]\nstrict = True\n\n"
            "[tool:pytest]\naddopts = -v\n"
        )
        (tmp_path / "setup.cfg").write_text(content)
        result = run_cli("--linters", "mypy,pytest", str(tmp_path))
        assert result.returncode == 1

    def test_setup_cfg_reports_mypy(self, tmp_path: Path) -> None:
        """setup.cfg with mypy section reports mypy."""
        content = (
            "[metadata]\nname = myproject\n\n"
            "[mypy]\nstrict = True\n\n"
            "[tool:pytest]\naddopts = -v\n"
        )
        (tmp_path / "setup.cfg").write_text(content)
        result = run_cli("--linters", "mypy,pytest", str(tmp_path))
        assert "mypy" in result.stdout

    def test_setup_cfg_reports_pytest(
        self, tmp_path: Path
    ) -> None:
        """setup.cfg with tool:pytest section reports pytest."""
        content = (
            "[metadata]\nname = myproject\n\n"
            "[mypy]\nstrict = True\n\n"
            "[tool:pytest]\naddopts = -v\n"
        )
        (tmp_path / "setup.cfg").write_text(content)
        result = run_cli("--linters", "mypy,pytest", str(tmp_path))
        assert "pytest" in result.stdout

    def test_tox_ini_exits_1(self, tmp_path: Path) -> None:
        """tox.ini with tool sections exits 1."""
        content = (
            "[tox]\nenvlist = py310\n\n"
            "[pytest]\naddopts = -v\n"
        )
        (tmp_path / "tox.ini").write_text(content)
        result = run_cli("--linters", "pytest", str(tmp_path))
        assert result.returncode == 1

    def test_tox_ini_reports_pytest(self, tmp_path: Path) -> None:
        """tox.ini with pytest section reports pytest."""
        content = (
            "[tox]\nenvlist = py310\n\n"
            "[pytest]\naddopts = -v\n"
        )
        (tmp_path / "tox.ini").write_text(content)
        result = run_cli("--linters", "pytest", str(tmp_path))
        assert "pytest" in result.stdout

    def test_all_jscpd_config_files_exits_1(
        self, tmp_path: Path
    ) -> None:
        """All jscpd config file variants cause exit 1."""
        jscpd_files = [
            ".jscpd.json", ".jscpd.yml", ".jscpd.yaml",
            ".jscpd.toml", ".jscpdrc", ".jscpdrc.json",
            ".jscpdrc.yml", ".jscpdrc.yaml",
        ]
        for i, filename in enumerate(jscpd_files):
            subdir = tmp_path / f"dir{i}"
            subdir.mkdir()
            (subdir / filename).touch()
        result = run_cli("--linters", "jscpd", str(tmp_path))
        assert result.returncode == 1

    def test_all_jscpd_config_files_reports_eight(
        self, tmp_path: Path
    ) -> None:
        """All jscpd config file variants produce eight lines."""
        jscpd_files = [
            ".jscpd.json", ".jscpd.yml", ".jscpd.yaml",
            ".jscpd.toml", ".jscpdrc", ".jscpdrc.json",
            ".jscpdrc.yml", ".jscpdrc.yaml",
        ]
        for i, filename in enumerate(jscpd_files):
            subdir = tmp_path / f"dir{i}"
            subdir.mkdir()
            (subdir / filename).touch()
        result = run_cli("--linters", "jscpd", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 8

    def test_all_jscpd_config_files_all_reference_jscpd(
        self, tmp_path: Path
    ) -> None:
        """All jscpd config file output lines reference jscpd."""
        jscpd_files = [
            ".jscpd.json", ".jscpd.yml", ".jscpd.yaml",
            ".jscpd.toml", ".jscpdrc", ".jscpdrc.json",
            ".jscpdrc.yml", ".jscpdrc.yaml",
        ]
        for i, filename in enumerate(jscpd_files):
            subdir = tmp_path / f"dir{i}"
            subdir.mkdir()
            (subdir / filename).touch()
        result = run_cli("--linters", "jscpd", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert all("jscpd" in line for line in lines)


@pytest.mark.e2e
class TestEndToEndDirectories:
    """End-to-end tests for directory scanning scenarios."""

    def test_scans_current_directory_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Scanning current directory with '.' exits 1."""
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "yamllint", ".", cwd=tmp_path
        )
        assert result.returncode == 1

    def test_scans_current_directory_reports_filename(
        self, tmp_path: Path
    ) -> None:
        """Scanning current directory reports config filename."""
        (tmp_path / ".yamllint").touch()
        result = run_cli(
            "--linters", "yamllint", ".", cwd=tmp_path
        )
        assert ".yamllint" in result.stdout

    def test_multiple_directories_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Multiple directories with config files exits 1."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            str(project_a), str(project_b),
        )
        assert result.returncode == 1

    def test_multiple_directories_reports_pylint(
        self, tmp_path: Path
    ) -> None:
        """Multiple directories report pylint finding."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            str(project_a), str(project_b),
        )
        assert "pylint" in result.stdout

    def test_multiple_directories_reports_mypy(
        self, tmp_path: Path
    ) -> None:
        """Multiple directories report mypy finding."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()
        (project_a / ".pylintrc").touch()
        (project_b / "mypy.ini").touch()
        result = run_cli(
            "--linters", "pylint,mypy",
            str(project_a), str(project_b),
        )
        assert "mypy" in result.stdout

    def test_mixed_clean_and_dirty_dirs_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Findings from dirty dir cause exit 1."""
        clean_dir = tmp_path / "clean"
        dirty_dir = tmp_path / "dirty"
        clean_dir.mkdir()
        dirty_dir.mkdir()
        (clean_dir / "main.py").touch()
        (dirty_dir / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint",
            str(clean_dir), str(dirty_dir),
        )
        assert result.returncode == 1

    def test_mixed_clean_and_dirty_dirs_reports_linter(
        self, tmp_path: Path
    ) -> None:
        """Findings from dirty dir are reported."""
        clean_dir = tmp_path / "clean"
        dirty_dir = tmp_path / "dirty"
        clean_dir.mkdir()
        dirty_dir.mkdir()
        (clean_dir / "main.py").touch()
        (dirty_dir / ".pylintrc").touch()
        result = run_cli(
            "--linters", "pylint",
            str(clean_dir), str(dirty_dir),
        )
        assert "pylint" in result.stdout

    def test_complex_project_structure_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Complex project with mypy config exits 1."""
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        docs = tmp_path / "docs"
        src.mkdir()
        tests.mkdir()
        docs.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'name = "myproject"\n\n'
            "[tool.mypy]\n"
            "strict = true\n"
        )
        (tmp_path / "setup.cfg").write_text(
            "[metadata]\nname = myproject\n"
        )
        (src / "main.py").touch()
        (tests / "test_main.py").touch()
        (docs / "README.md").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert result.returncode == 1

    def test_complex_project_structure_reports_mypy(
        self, tmp_path: Path
    ) -> None:
        """Complex project with mypy config reports mypy."""
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        docs = tmp_path / "docs"
        src.mkdir()
        tests.mkdir()
        docs.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'name = "myproject"\n\n'
            "[tool.mypy]\n"
            "strict = true\n"
        )
        (tmp_path / "setup.cfg").write_text(
            "[metadata]\nname = myproject\n"
        )
        (src / "main.py").touch()
        (tests / "test_main.py").touch()
        (docs / "README.md").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        assert "mypy" in result.stdout

    def test_complex_project_structure_reports_one(
        self, tmp_path: Path
    ) -> None:
        """Complex project reports exactly one finding."""
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        docs = tmp_path / "docs"
        src.mkdir()
        tests.mkdir()
        docs.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'name = "myproject"\n\n'
            "[tool.mypy]\n"
            "strict = true\n"
        )
        (tmp_path / "setup.cfg").write_text(
            "[metadata]\nname = myproject\n"
        )
        (src / "main.py").touch()
        (tests / "test_main.py").touch()
        (docs / "README.md").touch()
        result = run_cli("--linters", "mypy", str(tmp_path))
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_output_paths_are_relative(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
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
