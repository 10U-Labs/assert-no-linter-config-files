"""Integration tests for the CLI module."""

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

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

    def test_linters_empty_exits_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters with empty string exits 2."""
        code, _, stderr = run_main_with_args([
            "--linters", "", str(tmp_path)
        ])
        assert code == 2
        assert "At least one linter" in stderr


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


@pytest.mark.integration
class TestVerboseFlag:
    """Tests for the --verbose flag."""

    def test_verbose_shows_linters(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows which linters are being checked."""
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert code == 0
        assert "Checking for:" in stdout
        assert "mypy" in stdout
        assert "pylint" in stdout

    def test_verbose_shows_config_files_per_linter(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows config files for each linter."""
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert code == 0
        # Check pylint config files are listed
        assert ".pylintrc" in stdout
        assert "[tool.pylint.*] in pyproject.toml" in stdout
        # Check mypy config files are listed
        assert "mypy.ini" in stdout
        assert "[tool.mypy] in pyproject.toml" in stdout

    def test_verbose_shows_scanning(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows directories being scanned."""
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 0
        assert "Scanning:" in stdout
        assert str(tmp_path) in stdout

    def test_verbose_shows_findings(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows findings as they are found."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "config file" in stdout

    def test_verbose_shows_summary(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows summary at end."""
        (tmp_path / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 1
        assert "Scanned 1 directory(ies)" in stdout
        assert "found 1 finding(s)" in stdout

    def test_verbose_no_findings_summary(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows zero findings in summary."""
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 0
        assert "found 0 finding(s)" in stdout

    def test_verbose_with_fail_fast(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose with --fail-fast shows summary with 1 finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", "--fail-fast", str(tmp_path)
        ])
        assert code == 1
        assert "found 1 finding" in stdout

    def test_verbose_multiple_directories(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows scanning for each directory."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(first), str(second)
        ])
        assert code == 0
        assert stdout.count("Scanning:") == 2
        assert "Scanned 2 directory(ies)" in stdout


@pytest.mark.integration
class TestPyprojectTomlSections:
    """Tests for pyproject.toml section detection through CLI."""

    def test_tool_pylint_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [tool.pylint] section in pyproject.toml."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout
        assert "tool.pylint" in stdout

    def test_tool_pytest_ini_options(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Detect [tool.pytest.ini_options] section."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1
        assert "pytest" in stdout
        assert "tool.pytest.ini_options" in stdout

    def test_tool_jscpd_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [tool.jscpd] section."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert code == 1
        assert "jscpd" in stdout
        assert "tool.jscpd" in stdout

    def test_tool_yamllint_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [tool.yamllint] section."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1
        assert "yamllint" in stdout
        assert "tool.yamllint" in stdout

    def test_invalid_toml_falls_back_to_regex_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid TOML falls back to regex detection for mypy."""
        content = "[tool.mypy]\nstrict = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1
        assert "mypy" in stdout

    def test_invalid_toml_falls_back_to_regex_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid TOML falls back to regex detection for pylint."""
        content = "[tool.pylint]\nmax-line = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout

    def test_invalid_toml_falls_back_to_regex_pytest(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid TOML falls back to regex detection for pytest."""
        content = "[tool.pytest.ini_options]\naddopts = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1
        assert "pytest" in stdout

    def test_invalid_toml_falls_back_to_regex_jscpd(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid TOML falls back to regex detection for jscpd."""
        content = "[tool.jscpd]\nthreshold = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert code == 1
        assert "jscpd" in stdout

    def test_invalid_toml_falls_back_to_regex_yamllint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid TOML falls back to regex detection for yamllint."""
        content = "[tool.yamllint]\nrules = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1
        assert "yamllint" in stdout


@pytest.mark.integration
class TestSetupCfgSections:
    """Tests for setup.cfg section detection through CLI."""

    def test_mypy_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [mypy] section in setup.cfg."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1
        assert "mypy" in stdout
        assert "mypy section" in stdout

    def test_tool_pytest_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [tool:pytest] section in setup.cfg."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1
        assert "pytest" in stdout
        assert "tool:pytest" in stdout

    def test_pylint_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect section containing 'pylint' in setup.cfg."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout


@pytest.mark.integration
class TestToxIniSections:
    """Tests for tox.ini section detection through CLI."""

    def test_pytest_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [pytest] section in tox.ini."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1
        assert "pytest" in stdout

    def test_tool_pytest_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [tool:pytest] section in tox.ini."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1
        assert "pytest" in stdout

    def test_mypy_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect [mypy] section in tox.ini."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "tox.ini").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1
        assert "mypy" in stdout

    def test_pylint_section(self, tmp_path: Path, run_main_with_args) -> None:
        """Detect section containing 'pylint' in tox.ini."""
        content = "[pylint]\ndisable = C0114\n"
        (tmp_path / "tox.ini").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1
        assert "pylint" in stdout


@pytest.mark.integration
class TestGitDirectorySkipping:
    """Tests for .git directory skipping."""

    def test_git_directory_is_skipped(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Config files inside .git directory are ignored."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 0
        assert stdout == ""

    def test_nested_git_directory_is_skipped(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Config files in nested .git directories are ignored."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        git_dir = subdir / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 0
        assert stdout == ""


@pytest.mark.integration
class TestOSErrorHandling:
    """Tests for OS-level error handling."""

    def test_oserror_on_file_read_failure(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """OSError when file cannot be read triggers error handling."""
        # Create a pyproject.toml that will cause read_text to fail
        bad_file = tmp_path / "pyproject.toml"
        bad_file.symlink_to("/dev/null/nonexistent")
        code, _, stderr = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 2
        assert "Error reading" in stderr


@pytest.mark.integration
class TestInvalidConfigFiles:
    """Tests for invalid config file handling."""

    def test_invalid_setup_cfg_is_ignored(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid setup.cfg syntax is gracefully ignored."""
        # Content that will cause configparser to fail
        content = "[section\nmissing closing bracket"
        (tmp_path / "setup.cfg").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 0
        assert stdout == ""

    def test_invalid_tox_ini_is_ignored(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Invalid tox.ini syntax is gracefully ignored."""
        # Content that will cause configparser to fail
        content = "[section\nmissing closing bracket"
        (tmp_path / "tox.ini").write_text(content)
        code, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 0
        assert stdout == ""


@pytest.mark.integration
class TestModuleEntryPoint:
    """Tests for python -m entry point."""

    def test_module_entry_point(self, tmp_path: Path) -> None:
        """Can run as python -m assert_no_linter_config_files."""
        result = subprocess.run(
            [sys.executable, "-m", "assert_no_linter_config_files",
             "--linters", "pylint", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    def test_module_entry_point_with_findings(self, tmp_path: Path) -> None:
        """Module entry point exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        result = subprocess.run(
            [sys.executable, "-m", "assert_no_linter_config_files",
             "--linters", "pylint", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "pylint" in result.stdout

    def test_main_module_runpy(self, tmp_path: Path) -> None:
        """Test __main__ module via runpy (in-process execution)."""
        with patch.object(sys, "argv", [
            "assert_no_linter_config_files",
            "--linters", "pylint", str(tmp_path)
        ]):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_module(
                    "assert_no_linter_config_files",
                    run_name="__main__",
                    alter_sys=True
                )
            assert exc_info.value.code == 0
