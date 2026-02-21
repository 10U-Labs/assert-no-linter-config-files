"""Integration tests for setup.cfg, tox.ini, .git skipping, and error handling."""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestSetupCfgSections:
    """Tests for setup.cfg section detection through CLI."""

    def test_mypy_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [mypy] section found in setup.cfg."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_mypy_section_outputs_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains mypy when [mypy] found in setup.cfg."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_mypy_section_outputs_section_name(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains 'mypy section' when [mypy] found."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy section" in stdout

    @pytest.fixture
    def setup_cfg_tool_pytest_result(
        self, tmp_path: Path, run_main_with_args
    ) -> tuple[int, str, str]:
        """Run CLI after writing [tool:pytest] to setup.cfg."""
        (tmp_path / "setup.cfg").write_text(
            "[tool:pytest]\naddopts = -v\n"
        )
        return run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])

    def test_tool_pytest_section_exits_1(
        self, setup_cfg_tool_pytest_result: tuple[int, str, str]
    ) -> None:
        """Exit 1 when [tool:pytest] section found in setup.cfg."""
        assert setup_cfg_tool_pytest_result[0] == 1

    def test_tool_pytest_section_outputs_pytest(
        self, setup_cfg_tool_pytest_result: tuple[int, str, str]
    ) -> None:
        """Output contains pytest when [tool:pytest] found."""
        assert "pytest" in setup_cfg_tool_pytest_result[1]

    def test_tool_pytest_section_outputs_section_name(
        self, setup_cfg_tool_pytest_result: tuple[int, str, str]
    ) -> None:
        """Output contains 'tool:pytest' when section found."""
        assert "tool:pytest" in setup_cfg_tool_pytest_result[1]

    def test_pylint_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when pylint section found in setup.cfg."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        (tmp_path / "setup.cfg").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_pylint_section_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when pylint section found."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        (tmp_path / "setup.cfg").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert "pylint" in stdout


@pytest.mark.integration
class TestToxIniSections:
    """Tests for tox.ini section detection through CLI."""

    def test_pytest_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [pytest] section found in tox.ini."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert code == 1

    def test_pytest_section_outputs_pytest(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pytest when [pytest] found in tox.ini."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])
        assert "pytest" in stdout

    @pytest.fixture
    def tox_ini_tool_pytest_result(
        self, tmp_path: Path, run_main_with_args
    ) -> tuple[int, str, str]:
        """Run CLI after writing [tool:pytest] to tox.ini."""
        (tmp_path / "tox.ini").write_text(
            "[tool:pytest]\naddopts = -v\n"
        )
        return run_main_with_args([
            "--linters", "pytest", str(tmp_path)
        ])

    def test_tool_pytest_section_exits_1(
        self, tox_ini_tool_pytest_result: tuple[int, str, str]
    ) -> None:
        """Exit 1 when [tool:pytest] section found in tox.ini."""
        assert tox_ini_tool_pytest_result[0] == 1

    def test_tool_pytest_section_outputs_pytest(
        self, tox_ini_tool_pytest_result: tuple[int, str, str]
    ) -> None:
        """Output contains pytest when [tool:pytest] found."""
        assert "pytest" in tox_ini_tool_pytest_result[1]

    def test_mypy_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when [mypy] section found in tox.ini."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert code == 1

    def test_mypy_section_outputs_mypy(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains mypy when [mypy] found in tox.ini."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "tox.ini").write_text(content)
        _, stdout, _ = run_main_with_args([
            "--linters", "mypy", str(tmp_path)
        ])
        assert "mypy" in stdout

    def test_pylint_section_exits_1(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Exit 1 when pylint section found in tox.ini."""
        content = "[pylint]\ndisable = C0114\n"
        (tmp_path / "tox.ini").write_text(content)
        code, _, _ = run_main_with_args([
            "--linters", "pylint", str(tmp_path)
        ])
        assert code == 1

    def test_pylint_section_outputs_pylint(
        self, tmp_path: Path, run_main_with_args
    ) -> None:
        """Output contains pylint when pylint section found."""
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
        """No output when config files are only inside .git."""
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
        """No output when config files are in nested .git dirs."""
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
