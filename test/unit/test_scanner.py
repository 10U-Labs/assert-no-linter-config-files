"""Unit tests for the scanner module."""

from pathlib import Path

import pytest

from assert_no_linter_config_files.scanner import (
    DEDICATED_CONFIG_FILES,
    Finding,
    check_pyproject_toml,
    check_setup_cfg,
    check_tox_ini,
    make_path_relative,
    scan_directory,
)


@pytest.mark.unit
class TestDedicatedConfigFiles:
    """Tests for detecting dedicated config files."""

    @pytest.mark.parametrize(
        "filename,expected_tool",
        [
            (".pylintrc", "pylint"),
            ("pylintrc", "pylint"),
            (".pylintrc.toml", "pylint"),
            ("pytest.ini", "pytest"),
            ("mypy.ini", "mypy"),
            (".mypy.ini", "mypy"),
            (".yamllint", "yamllint"),
            (".yamllint.yml", "yamllint"),
            (".yamllint.yaml", "yamllint"),
            (".jscpd.json", "jscpd"),
            (".jscpd.yml", "jscpd"),
            (".jscpd.yaml", "jscpd"),
            (".jscpd.toml", "jscpd"),
            (".jscpdrc", "jscpd"),
            (".jscpdrc.json", "jscpd"),
            (".jscpdrc.yml", "jscpd"),
            (".jscpdrc.yaml", "jscpd"),
        ],
    )
    def test_dedicated_config_file_detected(
        self, tmp_path: Path, filename: str, expected_tool: str
    ) -> None:
        """Dedicated config files are detected."""
        (tmp_path / filename).touch()
        findings = scan_directory(tmp_path)
        assert len(findings) == 1
        assert findings[0].tool == expected_tool
        assert findings[0].reason == "config file"

    def test_no_findings_for_unrelated_files(self, tmp_path: Path) -> None:
        """Unrelated files are not flagged."""
        (tmp_path / "README.md").touch()
        (tmp_path / "main.py").touch()
        (tmp_path / ".gitignore").touch()
        findings = scan_directory(tmp_path)
        assert len(findings) == 0


@pytest.mark.unit
class TestPyprojectToml:
    """Tests for pyproject.toml section detection."""

    def test_tool_pylint_section(self, tmp_path: Path) -> None:
        """Detect [tool.pylint] section."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "pylint"
        assert "tool.pylint" in findings[0].reason

    def test_tool_pylint_subsection(self, tmp_path: Path) -> None:
        """Detect [tool.pylint.messages_control] subsection."""
        content = "[tool.pylint.messages_control]\ndisable = ['C0114']\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "pylint"

    def test_tool_mypy_section(self, tmp_path: Path) -> None:
        """Detect [tool.mypy] section."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"
        assert "tool.mypy" in findings[0].reason

    def test_tool_pytest_ini_options(self, tmp_path: Path) -> None:
        """Detect [tool.pytest.ini_options] section."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"
        assert "tool.pytest.ini_options" in findings[0].reason

    def test_tool_pytest_without_ini_options_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """[tool.pytest] without ini_options is not flagged."""
        content = "[tool.pytest]\nmarkers = ['slow']\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 0

    def test_tool_jscpd_section(self, tmp_path: Path) -> None:
        """Detect [tool.jscpd] section."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "jscpd"
        assert "tool.jscpd" in findings[0].reason

    def test_tool_yamllint_section(self, tmp_path: Path) -> None:
        """Detect [tool.yamllint] section."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "yamllint"
        assert "tool.yamllint" in findings[0].reason

    def test_no_findings_for_other_tools(self, tmp_path: Path) -> None:
        """Other tool sections are not flagged."""
        content = "[tool.black]\nline-length = 88\n"
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 0

    def test_multiple_sections(self, tmp_path: Path) -> None:
        """Multiple tool sections are all detected."""
        content = """
[tool.mypy]
strict = true

[tool.pylint]
max-line-length = 100
"""
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 2
        tools = {f.tool for f in findings}
        assert tools == {"mypy", "pylint"}


@pytest.mark.unit
class TestSetupCfg:
    """Tests for setup.cfg section detection."""

    def test_mypy_section(self, tmp_path: Path) -> None:
        """Detect [mypy] section."""
        content = "[mypy]\nstrict = True\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"
        assert "mypy section" in findings[0].reason

    def test_tool_pytest_section(self, tmp_path: Path) -> None:
        """Detect [tool:pytest] section."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"
        assert "tool:pytest" in findings[0].reason

    def test_pylint_section(self, tmp_path: Path) -> None:
        """Detect section containing 'pylint'."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1
        assert findings[0].tool == "pylint"

    def test_pylint_master_section(self, tmp_path: Path) -> None:
        """Detect [pylint.master] section."""
        content = "[pylint.master]\njobs = 4\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1
        assert findings[0].tool == "pylint"

    def test_no_findings_for_other_sections(self, tmp_path: Path) -> None:
        """Other sections are not flagged."""
        content = "[metadata]\nname = mypackage\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 0


@pytest.mark.unit
class TestToxIni:
    """Tests for tox.ini section detection."""

    def test_pytest_section(self, tmp_path: Path) -> None:
        """Detect [pytest] section."""
        content = "[pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"
        assert "pytest section" in findings[0].reason

    def test_tool_pytest_section(self, tmp_path: Path) -> None:
        """Detect [tool:pytest] section."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"

    def test_mypy_section(self, tmp_path: Path) -> None:
        """Detect [mypy] section."""
        content = "[mypy]\nstrict = True\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"
        assert "mypy section" in findings[0].reason

    def test_pylint_section(self, tmp_path: Path) -> None:
        """Detect section containing 'pylint'."""
        content = "[pylint]\ndisable = C0114\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1
        assert findings[0].tool == "pylint"

    def test_no_findings_for_tox_sections(self, tmp_path: Path) -> None:
        """Tox-specific sections are not flagged."""
        content = "[tox]\nenvlist = py310,py311\n\n[testenv]\ndeps = pytest\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 0


@pytest.mark.unit
class TestScanDirectory:
    """Tests for the scan_directory function."""

    def test_skips_git_directory(self, tmp_path: Path) -> None:
        """The .git directory is skipped."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / ".pylintrc").touch()
        findings = scan_directory(tmp_path)
        assert len(findings) == 0

    def test_recursive_scan(self, tmp_path: Path) -> None:
        """Subdirectories are scanned recursively."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "pytest.ini").touch()
        findings = scan_directory(tmp_path)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"

    def test_pyproject_toml_scanned(self, tmp_path: Path) -> None:
        """pyproject.toml is scanned for embedded config."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_setup_cfg_scanned(self, tmp_path: Path) -> None:
        """setup.cfg is scanned for embedded config."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        findings = scan_directory(tmp_path)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_tox_ini_scanned(self, tmp_path: Path) -> None:
        """tox.ini is scanned for embedded config."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        findings = scan_directory(tmp_path)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"

    def test_pyproject_toml_without_tool_sections(self, tmp_path: Path) -> None:
        """pyproject.toml without tool sections is not flagged."""
        content = "[project]\nname = 'myproject'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path)
        assert len(findings) == 0

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns no findings."""
        findings = scan_directory(tmp_path)
        assert len(findings) == 0


@pytest.mark.unit
class TestFinding:
    """Tests for the Finding class."""

    def test_str_format(self) -> None:
        """Finding formats as path:tool:reason."""
        finding = Finding("./pytest.ini", "pytest", "config file")
        assert str(finding) == "./pytest.ini:pytest:config file"

    def test_namedtuple_fields(self) -> None:
        """Finding has path, tool, and reason fields."""
        finding = Finding("./mypy.ini", "mypy", "config file")
        assert finding.path == "./mypy.ini"
        assert finding.tool == "mypy"
        assert finding.reason == "config file"


@pytest.mark.unit
class TestMakePathRelative:
    """Tests for the make_path_relative function."""

    def test_relative_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Absolute paths are converted to relative."""
        monkeypatch.chdir(tmp_path)
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = make_path_relative(str(subdir / "file.txt"))
        assert result == "subdir/file.txt"

    def test_path_outside_cwd(self) -> None:
        """Paths outside cwd are returned unchanged."""
        result = make_path_relative("/some/absolute/path")
        assert result == "/some/absolute/path"


@pytest.mark.unit
class TestDedicatedConfigFilesMapping:
    """Tests for the DEDICATED_CONFIG_FILES mapping."""

    def test_all_pylint_files(self) -> None:
        """All pylint config files are mapped."""
        pylint_files = [".pylintrc", "pylintrc", ".pylintrc.toml"]
        for filename in pylint_files:
            assert filename in DEDICATED_CONFIG_FILES
            assert DEDICATED_CONFIG_FILES[filename] == "pylint"

    def test_all_pytest_files(self) -> None:
        """All pytest config files are mapped."""
        pytest_files = ["pytest.ini"]
        for filename in pytest_files:
            assert filename in DEDICATED_CONFIG_FILES
            assert DEDICATED_CONFIG_FILES[filename] == "pytest"

    def test_all_mypy_files(self) -> None:
        """All mypy config files are mapped."""
        mypy_files = ["mypy.ini", ".mypy.ini"]
        for filename in mypy_files:
            assert filename in DEDICATED_CONFIG_FILES
            assert DEDICATED_CONFIG_FILES[filename] == "mypy"

    def test_all_yamllint_files(self) -> None:
        """All yamllint config files are mapped."""
        yamllint_files = [".yamllint", ".yamllint.yml", ".yamllint.yaml"]
        for filename in yamllint_files:
            assert filename in DEDICATED_CONFIG_FILES
            assert DEDICATED_CONFIG_FILES[filename] == "yamllint"

    def test_all_jscpd_files(self) -> None:
        """All jscpd config files are mapped."""
        jscpd_count = sum(
            1 for tool in DEDICATED_CONFIG_FILES.values() if tool == "jscpd"
        )
        assert jscpd_count == 8
        for filename, tool in DEDICATED_CONFIG_FILES.items():
            if "jscpd" in filename:
                assert tool == "jscpd"
