"""Integration tests for CLI flags (--linters, --exclude, output modes, behavior)."""

from pathlib import Path

import pytest


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

    def test_linters_multiple_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters with comma-separated values exits 1."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert code == 1

    def test_linters_multiple_includes_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters with comma-separated values includes pylint."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_linters_multiple_includes_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--linters with comma-separated values includes mypy."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_linters_multiple_excludes_yamllint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
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
        """--linters with empty string outputs error message."""
        _, _, stderr = run_main_with_args([
            "--linters", "", str(tmp_path)
        ])
        assert "At least one linter" in stderr


@pytest.mark.integration
class TestExcludeFlag:
    """Tests for the --exclude flag."""

    @pytest.fixture
    def exclude_vendor_result(
        self, tmp_path: Path, run_main_with_args
    ) -> tuple[int, str, str]:
        """Run CLI with --exclude *vendor* on vendor/.pylintrc + mypy.ini."""
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        return run_main_with_args([
            "--linters", "pylint,mypy",
            "--exclude", "*vendor*", str(tmp_path)
        ])

    def test_exclude_pattern_exits_1(
        self, exclude_vendor_result: tuple[int, str, str]
    ) -> None:
        """--exclude skips matching paths but still exits 1."""
        assert exclude_vendor_result[0] == 1

    def test_exclude_pattern_includes_mypy(
        self, exclude_vendor_result: tuple[int, str, str]
    ) -> None:
        """--exclude includes non-excluded findings."""
        assert "mypy" in exclude_vendor_result[1]

    def test_exclude_pattern_excludes_pylint(
        self, exclude_vendor_result: tuple[int, str, str]
    ) -> None:
        """--exclude skips matching paths so pylint is not reported."""
        assert "pylint" not in exclude_vendor_result[1]

    @pytest.fixture
    def exclude_multiple_result(
        self, tmp_path: Path, run_main_with_args
    ) -> tuple[int, str, str]:
        """Run CLI with multiple --exclude on deps/third_party dirs."""
        deps = tmp_path / "deps"
        third = tmp_path / "third_party"
        deps.mkdir()
        third.mkdir()
        (deps / ".pylintrc").touch()
        (third / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        return run_main_with_args([
            "--linters", "pylint,mypy,yamllint",
            "--exclude", "*deps*",
            "--exclude", "*third_party*",
            str(tmp_path)
        ])

    def test_exclude_multiple_exits_1(
        self, exclude_multiple_result: tuple[int, str, str]
    ) -> None:
        """--exclude can be repeated and still exits 1."""
        assert exclude_multiple_result[0] == 1

    def test_exclude_multiple_includes_yamllint(
        self, exclude_multiple_result: tuple[int, str, str]
    ) -> None:
        """--exclude can be repeated; non-excluded findings reported."""
        assert "yamllint" in exclude_multiple_result[1]

    def test_exclude_multiple_excludes_pylint(
        self, exclude_multiple_result: tuple[int, str, str]
    ) -> None:
        """--exclude with *deps* excludes pylint config in deps."""
        assert "pylint" not in exclude_multiple_result[1]

    def test_exclude_multiple_excludes_mypy(
        self, exclude_multiple_result: tuple[int, str, str]
    ) -> None:
        """--exclude with *third_party* excludes mypy config."""
        assert "mypy" not in exclude_multiple_result[1]


@pytest.mark.integration
class TestOutputModes:
    """Tests for output mode flags."""

    def test_quiet_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--quiet exits 1 when config found."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--quiet", str(tmp_path)
        ])
        assert code == 1

    def test_quiet_no_output(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--quiet suppresses output."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--quiet", str(tmp_path)
        ])
        assert stdout == ""

    def test_count_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--count exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--count", str(tmp_path)
        ])
        assert code == 1

    def test_count_outputs_number(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--count outputs finding count."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--count", str(tmp_path)
        ])
        assert stdout.strip() == "2"

    def test_json_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--json exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert code == 1

    def test_json_outputs_json_array(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--json output starts with JSON array bracket."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert stdout.startswith("[")

    def test_json_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--json output contains pylint."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--json", str(tmp_path)
        ])
        assert "pylint" in stdout


@pytest.mark.integration
class TestBehaviorModifiers:
    """Tests for behavior modifier flags."""

    def test_fail_fast_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--fail-fast exits 1 on first finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--fail-fast", str(tmp_path)
        ])
        assert code == 1

    def test_fail_fast_stops_early(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--fail-fast outputs only one finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint,mypy", "--fail-fast", str(tmp_path)
        ])
        lines = [line for line in stdout.strip().split("\n") if line]
        assert len(lines) == 1

    def test_warn_only_exits_0(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--warn-only always exits 0."""
        (tmp_path / ".pylintrc").touch()
        code, _, _ = run_main_with_args([
            "--linters", "pylint", "--warn-only", str(tmp_path)
        ])
        assert code == 0

    def test_warn_only_still_outputs(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """--warn-only still outputs findings."""
        (tmp_path / ".pylintrc").touch()
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", "--warn-only", str(tmp_path)
        ])
        assert "pylint" in stdout
