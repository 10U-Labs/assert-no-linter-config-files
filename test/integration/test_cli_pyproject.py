"""Integration tests for pyproject.toml section detection through CLI."""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestPyprojectValidToml:
    """Tests for valid pyproject.toml section detection."""

    def test_tool_pylint_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [tool.pylint] section found in pyproject.toml."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_tool_pylint_section_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when [tool.pylint] found."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_tool_pylint_section_outputs_section_name(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'tool.pylint' when section found."""
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
        """Output contains 'tool.pytest.ini_options' when found."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "tool.pytest.ini_options" in stdout

    def test_tool_jscpd_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [tool.jscpd] section found."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert code == 1

    def test_tool_jscpd_section_outputs_jscpd(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains jscpd when [tool.jscpd] found."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert "jscpd" in stdout

    def test_tool_jscpd_section_outputs_section_name(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'tool.jscpd' when section found."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert "tool.jscpd" in stdout

    def test_tool_yamllint_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [tool.yamllint] section found."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1

    def test_tool_yamllint_section_outputs_yamllint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains yamllint when [tool.yamllint] found."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert "yamllint" in stdout

    def test_tool_yamllint_section_outputs_section_name(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'tool.yamllint' when section found."""
        content = "[tool.yamllint]\nrules = {}\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert "tool.yamllint" in stdout


@pytest.mark.integration
class TestPyprojectInvalidToml:
    """Tests for invalid TOML regex fallback through CLI."""

    def test_invalid_toml_mypy_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex for mypy."""
        content = "[tool.mypy]\nstrict = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_mypy_outputs_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains mypy when invalid TOML falls back."""
        content = "[tool.mypy]\nstrict = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_invalid_toml_pylint_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex for pylint."""
        content = "[tool.pylint]\nmax-line = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_pylint_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when invalid TOML falls back."""
        content = "[tool.pylint]\nmax-line = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout

    def test_invalid_toml_pytest_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex for pytest."""
        content = "[tool.pytest.ini_options]\naddopts = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_pytest_outputs_pytest(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pytest when invalid TOML falls back."""
        content = "[tool.pytest.ini_options]\naddopts = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    def test_invalid_toml_jscpd_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex for jscpd."""
        content = "[tool.jscpd]\nthreshold = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_jscpd_outputs_jscpd(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains jscpd when invalid TOML falls back."""
        content = "[tool.jscpd]\nthreshold = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "jscpd", str(tmp_path)
        ])
        assert "jscpd" in stdout

    def test_invalid_toml_yamllint_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when invalid TOML falls back to regex for yamllint."""
        content = "[tool.yamllint]\nrules = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert code == 1

    def test_invalid_toml_yamllint_outputs_yamllint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains yamllint when invalid TOML falls back."""
        content = "[tool.yamllint]\nrules = {\n"
        (tmp_path / "pyproject.toml").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "yamllint", str(tmp_path)
        ])
        assert "yamllint" in stdout
