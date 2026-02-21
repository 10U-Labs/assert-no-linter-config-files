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
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 0

    def test_no_config_produces_no_output(self, tmp_path: Path, run_main_with_args) -> None:
        """No output when no linter config is found."""
        (tmp_path / "main.py").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert stdout == ""

    def test_config_found_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_config_found_outputs_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pylint when pylint config is found."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_config_found_outputs_config_file(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'config file' when linter config is found."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "config file" in stdout

    def test_invalid_directory_exits_2(self, run_main_with_args) -> None:
        """Exit 2 when directory does not exist."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "/nonexistent/path"
        ])
        assert code == 2

    def test_scans_current_directory_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_main_with_args
    ) -> None:
        """Can scan current directory with '.' and exit 1 when config found."""
        (tmp_path / ".yamllint").touch()
        monkeypatch.chdir(tmp_path)
        code, _, _ = run_main_with_args(["--linters", "yamllint", "."])
        assert code == 1

    def test_scans_current_directory_outputs_yamllint(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_main_with_args
    ) -> None:
        """Can scan current directory with '.' and output yamllint."""
        (tmp_path / ".yamllint").touch()
        monkeypatch.chdir(tmp_path)
        _, stdout, _ = run_main_with_args(["--linters", "yamllint", "."])
        assert "yamllint" in stdout

    def test_multiple_directories_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when configs found across multiple directories."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(first_dir), str(second_dir)
        ])
        assert code == 1

    def test_multiple_directories_outputs_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pylint when scanning multiple directories."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(first_dir), str(second_dir)
        ])
        assert "pylint" in stdout

    def test_multiple_directories_outputs_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains mypy when scanning multiple directories."""
        first_dir = tmp_path / "first"
        second_dir = tmp_path / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / ".pylintrc").touch()
        (second_dir / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(first_dir), str(second_dir)
        ])
        assert "mypy" in stdout

    def test_help_exits_0(self, run_main_with_args) -> None:
        """--help exits with code 0."""
        code, _, _ = run_main_with_args(["--help"])
        assert code == 0

    def test_missing_linters_exits_2(self, tmp_path: Path, run_main_with_args) -> None:
        """Missing --linters flag exits 2."""
        code, _, _ = run_main_with_args([str(tmp_path)])
        assert code == 2

    def test_output_format_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when config file is found for output format test."""
        (tmp_path / ".yamllint").touch()
        code, _, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1

    def test_output_format_single_line(self, tmp_path: Path, run_main_with_args) -> None:
        """Output is a single line when one config file is found."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert len(stdout.strip().split("\n")) == 1

    def test_output_format_has_three_parts(self, tmp_path: Path, run_main_with_args) -> None:
        """Output line has three colon-separated parts."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert len(stdout.strip().split("\n")[0].split(":")) == 3

    def test_output_format_path_contains_filename(self, tmp_path: Path, run_main_with_args) -> None:
        """First part of output contains the config filename."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert ".yamllint" in stdout.strip().split("\n")[0].split(":")[0]

    def test_output_format_tool_is_yamllint(self, tmp_path: Path, run_main_with_args) -> None:
        """Second part of output is the tool name."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert stdout.strip().split("\n")[0].split(":")[1] == "yamllint"

    def test_output_format_reason_is_config_file(self, tmp_path: Path, run_main_with_args) -> None:
        """Third part of output is 'config file'."""
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert stdout.strip().split("\n")[0].split(":")[2] == "config file"

    def test_pyproject_toml_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when embedded config in pyproject.toml is detected."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_pyproject_toml_section_outputs_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains mypy when pyproject.toml has mypy section."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_pyproject_toml_section_outputs_tool_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'tool.mypy' when pyproject.toml has mypy section."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
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

    def test_linters_filters_findings_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters filters to only specified linters and exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_linters_filters_includes_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters includes specified linter in output."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_linters_filters_excludes_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters excludes non-specified linter from output."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "mypy" not in stdout

    def test_linters_multiple_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--linters with comma-separated values exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 1

    def test_linters_multiple_includes_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """--linters with comma-separated values includes pylint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_linters_multiple_includes_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """--linters with comma-separated values includes mypy."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_linters_multiple_excludes_yamllint(self, tmp_path: Path, run_main_with_args) -> None:
        """--linters with comma-separated values excludes yamllint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
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
        code, _, _ = run_main_with_args([
            "--linters", "", str(tmp_path)
        ])
        assert code == 2

    def test_linters_empty_outputs_error_message(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters with empty string outputs error about needing at least one linter."""
        _, _, stderr = run_main_with_args([
            "--linters", "", str(tmp_path)
        ])
        assert "At least one linter" in stderr


@pytest.mark.integration
class TestExcludeFlag:
    """Tests for the --exclude flag."""

    def test_exclude_pattern_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude skips matching paths but still exits 1 for other findings."""
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*", str(tmp_path)
        ])
        assert code == 1

    def test_exclude_pattern_includes_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude skips matching paths but includes non-excluded findings."""
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_exclude_pattern_excludes_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude skips matching paths so pylint in vendor is not reported."""
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*", str(tmp_path)
        ])
        assert "pylint" not in stdout

    def test_exclude_multiple_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude can be repeated and still exits 1 for remaining findings."""
        deps = tmp_path / "deps"
        third = tmp_path / "third_party"
        deps.mkdir()
        third.mkdir()
        (deps / ".pylintrc").touch()
        (third / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy,yamllint",
            "--exclude", "*deps*",
            "--exclude", "*third_party*",
            str(tmp_path)
        ])
        assert code == 1

    def test_exclude_multiple_includes_yamllint(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude can be repeated and non-excluded findings are reported."""
        deps = tmp_path / "deps"
        third = tmp_path / "third_party"
        deps.mkdir()
        third.mkdir()
        (deps / ".pylintrc").touch()
        (third / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy,yamllint",
            "--exclude", "*deps*",
            "--exclude", "*third_party*",
            str(tmp_path)
        ])
        assert "yamllint" in stdout

    def test_exclude_multiple_excludes_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude with *deps* excludes pylint config in deps directory."""
        deps = tmp_path / "deps"
        third = tmp_path / "third_party"
        deps.mkdir()
        third.mkdir()
        (deps / ".pylintrc").touch()
        (third / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy,yamllint",
            "--exclude", "*deps*",
            "--exclude", "*third_party*",
            str(tmp_path)
        ])
        assert "pylint" not in stdout

    def test_exclude_multiple_excludes_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """--exclude with *third_party* excludes mypy config in third_party directory."""
        deps = tmp_path / "deps"
        third = tmp_path / "third_party"
        deps.mkdir()
        third.mkdir()
        (deps / ".pylintrc").touch()
        (third / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy,yamllint",
            "--exclude", "*deps*",
            "--exclude", "*third_party*",
            str(tmp_path)
        ])
        assert "mypy" not in stdout


@pytest.mark.integration
class TestOutputModes:
    """Tests for output mode flags."""

    def test_quiet_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--quiet exits 1 when config found."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--quiet", str(tmp_path)
        ])
        assert code == 1

    def test_quiet_no_output(self, tmp_path: Path, run_main_with_args) -> None:
        """--quiet suppresses output."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--quiet", str(tmp_path)
        ])
        assert stdout == ""

    def test_count_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--count exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--count", str(tmp_path)
        ])
        assert code == 1

    def test_count_outputs_number(self, tmp_path: Path, run_main_with_args) -> None:
        """--count outputs finding count."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--count", str(tmp_path)
        ])
        assert stdout.strip() == "2"

    def test_json_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--json exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert code == 1

    def test_json_outputs_json_array(self, tmp_path: Path, run_main_with_args) -> None:
        """--json output starts with JSON array bracket."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert stdout.startswith("[")

    def test_json_outputs_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """--json output contains pylint."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert "pylint" in stdout


@pytest.mark.integration
class TestBehaviorModifiers:
    """Tests for behavior modifier flags."""

    def test_fail_fast_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--fail-fast exits 1 on first finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--fail-fast", str(tmp_path)
        ])
        assert code == 1

    def test_fail_fast_stops_early(self, tmp_path: Path, run_main_with_args) -> None:
        """--fail-fast outputs only one finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--fail-fast", str(tmp_path)
        ])
        assert len([line for line in stdout.strip().split("\n") if line]) == 1

    def test_warn_only_exits_0(self, tmp_path: Path, run_main_with_args) -> None:
        """--warn-only always exits 0."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--warn-only", str(tmp_path)
        ])
        assert code == 0

    def test_warn_only_still_outputs(self, tmp_path: Path, run_main_with_args) -> None:
        """--warn-only still outputs findings."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--warn-only", str(tmp_path)
        ])
        assert "pylint" in stdout


@pytest.mark.integration
class TestVerboseFlag:
    """Tests for the --verbose flag."""

    def test_verbose_exits_0(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose exits 0 when no config found."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert code == 0

    def test_verbose_shows_checking_for(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows 'Checking for:' header."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert "Checking for:" in stdout

    def test_verbose_shows_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows mypy in linter list."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_verbose_shows_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows pylint in linter list."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_verbose_shows_pylintrc_config_file(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows .pylintrc in config files list."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert ".pylintrc" in stdout

    def test_verbose_shows_pylint_pyproject_config(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows pylint pyproject.toml config pattern."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert "[tool.pylint.*] in pyproject.toml" in stdout

    def test_verbose_shows_mypy_ini_config_file(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows mypy.ini in config files list."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert "mypy.ini" in stdout

    def test_verbose_shows_mypy_pyproject_config(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows mypy pyproject.toml config pattern."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", str(tmp_path)
        ])
        assert "[tool.mypy] in pyproject.toml" in stdout

    def test_verbose_shows_scanning_exits_0(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows directories being scanned and exits 0."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 0

    def test_verbose_shows_scanning_label(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows 'Scanning:' label."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "Scanning:" in stdout

    def test_verbose_shows_scanning_path(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows the directory path being scanned."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert str(tmp_path) in stdout

    def test_verbose_findings_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 1

    def test_verbose_findings_shows_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows pylint in findings output."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_verbose_findings_shows_config_file(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows 'config file' in findings output."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "config file" in stdout

    def test_verbose_summary_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose exits 1 when findings exist for summary test."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 1

    def test_verbose_summary_shows_scanned_count(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows 'Scanned 1 directory(ies)' in summary."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "Scanned 1 directory(ies)" in stdout

    def test_verbose_summary_shows_findings_count(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose shows 'found 1 finding(s)' in summary."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "found 1 finding(s)" in stdout

    def test_verbose_no_findings_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose exits 0 when no findings."""
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert code == 0

    def test_verbose_no_findings_summary(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows zero findings in summary."""
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(tmp_path)
        ])
        assert "found 0 finding(s)" in stdout

    def test_verbose_with_fail_fast_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose with --fail-fast exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", "--fail-fast", str(tmp_path)
        ])
        assert code == 1

    def test_verbose_with_fail_fast_shows_1_finding(self, tmp_path: Path, run_main_with_args) -> None:
        """--verbose with --fail-fast shows summary with 1 finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--verbose", "--fail-fast", str(tmp_path)
        ])
        assert "found 1 finding" in stdout

    def test_verbose_multiple_directories_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose with multiple directories exits 0."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(first), str(second)
        ])
        assert code == 0

    def test_verbose_multiple_directories_shows_two_scanning(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows scanning for each of the two directories."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(first), str(second)
        ])
        assert stdout.count("Scanning:") == 2

    def test_verbose_multiple_directories_shows_scanned_2(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--verbose shows 'Scanned 2 directory(ies)' in summary."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--verbose", str(first), str(second)
        ])
        assert "Scanned 2 directory(ies)" in stdout


@pytest.mark.integration
class TestPyprojectTomlSections:
    """Tests for pyproject.toml section detection through CLI."""

    def test_tool_pylint_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [tool.pylint] section found in pyproject.toml."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_tool_pylint_section_outputs_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pylint when [tool.pylint] found in pyproject.toml."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_tool_pylint_section_outputs_section_name(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'tool.pylint' when [tool.pylint] found in pyproject.toml."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "tool.pylint" in stdout

    def test_tool_pytest_ini_options_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [tool.pytest.ini_options] section found."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_tool_pytest_ini_options_outputs_pytest(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pytest when [tool.pytest.ini_options] found."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    def test_tool_pytest_ini_options_outputs_section_name(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'tool.pytest.ini_options' when section found."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "tool.pytest.ini_options" in stdout

    def test_tool_jscpd_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [tool.jscpd] section found."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert code == 1

    def test_tool_jscpd_section_outputs_jscpd(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains jscpd when [tool.jscpd] found."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert "jscpd" in stdout

    def test_tool_jscpd_section_outputs_section_name(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'tool.jscpd' when [tool.jscpd] found."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert "tool.jscpd" in stdout

    def test_tool_yamllint_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [tool.yamllint] section found."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1

    def test_tool_yamllint_section_outputs_yamllint(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains yamllint when [tool.yamllint] found."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert "yamllint" in stdout

    def test_tool_yamllint_section_outputs_section_name(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'tool.yamllint' when [tool.yamllint] found."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert "tool.yamllint" in stdout

    def test_invalid_toml_falls_back_to_regex_mypy_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex detection for mypy."""
        content = "[tool.mypy]\nstrict = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_falls_back_to_regex_mypy_outputs_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains mypy when invalid TOML falls back to regex."""
        content = "[tool.mypy]\nstrict = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_invalid_toml_falls_back_to_regex_pylint_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex detection for pylint."""
        content = "[tool.pylint]\nmax-line = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_falls_back_to_regex_pylint_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when invalid TOML falls back to regex."""
        content = "[tool.pylint]\nmax-line = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_invalid_toml_falls_back_to_regex_pytest_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex detection for pytest."""
        content = "[tool.pytest.ini_options]\naddopts = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_falls_back_to_regex_pytest_outputs_pytest(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pytest when invalid TOML falls back to regex."""
        content = "[tool.pytest.ini_options]\naddopts = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    def test_invalid_toml_falls_back_to_regex_jscpd_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex detection for jscpd."""
        content = "[tool.jscpd]\nthreshold = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_falls_back_to_regex_jscpd_outputs_jscpd(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains jscpd when invalid TOML falls back to regex."""
        content = "[tool.jscpd]\nthreshold = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert "jscpd" in stdout

    def test_invalid_toml_falls_back_to_regex_yamllint_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex detection for yamllint."""
        content = "[tool.yamllint]\nrules = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_falls_back_to_regex_yamllint_outputs_yamllint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains yamllint when invalid TOML falls back to regex."""
        content = "[tool.yamllint]\nrules = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert "yamllint" in stdout


@pytest.mark.integration
class TestSetupCfgSections:
    """Tests for setup.cfg section detection through CLI."""

    def test_mypy_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [mypy] section found in setup.cfg."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_mypy_section_outputs_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains mypy when [mypy] found in setup.cfg."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_mypy_section_outputs_section_name(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'mypy section' when [mypy] found in setup.cfg."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy section" in stdout

    def test_tool_pytest_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [tool:pytest] section found in setup.cfg."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_tool_pytest_section_outputs_pytest(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pytest when [tool:pytest] found in setup.cfg."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    def test_tool_pytest_section_outputs_section_name(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains 'tool:pytest' when [tool:pytest] found in setup.cfg."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "tool:pytest" in stdout

    def test_pylint_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when section containing 'pylint' found in setup.cfg."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_pylint_section_outputs_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pylint when pylint section found in setup.cfg."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout


@pytest.mark.integration
class TestToxIniSections:
    """Tests for tox.ini section detection through CLI."""

    def test_pytest_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [pytest] section found in tox.ini."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_pytest_section_outputs_pytest(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pytest when [pytest] found in tox.ini."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    def test_tool_pytest_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [tool:pytest] section found in tox.ini."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_tool_pytest_section_outputs_pytest(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pytest when [tool:pytest] found in tox.ini."""
        content = "[tool:pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    def test_mypy_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when [mypy] section found in tox.ini."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_mypy_section_outputs_mypy(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains mypy when [mypy] found in tox.ini."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_pylint_section_exits_1(self, tmp_path: Path, run_main_with_args) -> None:
        """Exit 1 when section containing 'pylint' found in tox.ini."""
        content = "[pylint]\ndisable = C0114\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_pylint_section_outputs_pylint(self, tmp_path: Path, run_main_with_args) -> None:
        """Output contains pylint when pylint section found in tox.ini."""
        content = "[pylint]\ndisable = C0114\n"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout


@pytest.mark.integration
class TestGitDirectorySkipping:
    """Tests for .git directory skipping."""

    def test_git_directory_is_skipped_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 0 when config files are only inside .git directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 0

    def test_git_directory_is_skipped_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """No output when config files are only inside .git directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert stdout == ""

    def test_nested_git_directory_is_skipped_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 0 when config files are in nested .git directories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        git_dir = subdir / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 0

    def test_nested_git_directory_is_skipped_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """No output when config files are in nested .git directories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        git_dir = subdir / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert stdout == ""


@pytest.mark.integration
def test_oserror_on_file_read_failure_exits_2(
    tmp_path: Path, run_main_with_args
) -> None:
    """OSError when file cannot be read exits 2."""
    bad_file = tmp_path / "pyproject.toml"
    bad_file.symlink_to("/dev/null/nonexistent")
    code, _, _ = run_main_with_args([
        "--linters", "pylint", str(tmp_path)
    ])
    assert code == 2


@pytest.mark.integration
def test_oserror_on_file_read_failure_outputs_error(
    tmp_path: Path, run_main_with_args
) -> None:
    """OSError when file cannot be read outputs error message."""
    bad_file = tmp_path / "pyproject.toml"
    bad_file.symlink_to("/dev/null/nonexistent")
    _, _, stderr = run_main_with_args([
        "--linters", "pylint", str(tmp_path)
    ])
    assert "Error reading" in stderr


@pytest.mark.integration
class TestInvalidConfigFiles:
    """Tests for invalid config file handling."""

    def test_invalid_setup_cfg_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 0 when setup.cfg has invalid syntax."""
        content = "[section\nmissing closing bracket"
        (tmp_path / "setup.cfg").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 0

    def test_invalid_setup_cfg_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """No output when setup.cfg has invalid syntax."""
        content = "[section\nmissing closing bracket"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert stdout == ""

    def test_invalid_tox_ini_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 0 when tox.ini has invalid syntax."""
        content = "[section\nmissing closing bracket"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 0

    def test_invalid_tox_ini_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """No output when tox.ini has invalid syntax."""
        content = "[section\nmissing closing bracket"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
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

    def test_module_entry_point_with_findings_exits_1(self, tmp_path: Path) -> None:
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

    def test_module_entry_point_with_findings_outputs_pylint(self, tmp_path: Path) -> None:
        """Module entry point outputs pylint when findings exist."""
        (tmp_path / ".pylintrc").touch()
        result = subprocess.run(
            [sys.executable, "-m", "assert_no_linter_config_files",
             "--linters", "pylint", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "pylint" in result.stdout

    def test_main_module_runpy(self, tmp_path: Path) -> None:
        """Test __main__ module via runpy (in-process execution)."""
        exc_info = None
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
