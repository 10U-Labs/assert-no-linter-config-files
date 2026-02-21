"""Unit tests for the scanner module - config file detection."""

from pathlib import Path

import pytest

from assert_no_linter_config_files.scanner import (
    VALID_LINTERS,
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
        "filename",
        [
            ".pylintrc",
            "pylintrc",
            ".pylintrc.toml",
            "pytest.ini",
            "mypy.ini",
            ".mypy.ini",
            ".yamllint",
            ".yamllint.yml",
            ".yamllint.yaml",
            ".jscpd.json",
            ".jscpd.yml",
            ".jscpd.yaml",
            ".jscpd.toml",
            ".jscpdrc",
            ".jscpdrc.json",
            ".jscpdrc.yml",
            ".jscpdrc.yaml",
        ],
    )
    def test_dedicated_config_file_returns_one_finding(
        self, tmp_path: Path, filename: str
    ) -> None:
        """Dedicated config files produce exactly one finding."""
        (tmp_path / filename).touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1

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
    def test_dedicated_config_file_has_correct_tool(
        self, tmp_path: Path, filename: str, expected_tool: str
    ) -> None:
        """Dedicated config files report the correct tool."""
        (tmp_path / filename).touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert findings[0].tool == expected_tool

    @pytest.mark.parametrize(
        "filename",
        [
            ".pylintrc",
            "pylintrc",
            ".pylintrc.toml",
            "pytest.ini",
            "mypy.ini",
            ".mypy.ini",
            ".yamllint",
            ".yamllint.yml",
            ".yamllint.yaml",
            ".jscpd.json",
            ".jscpd.yml",
            ".jscpd.yaml",
            ".jscpd.toml",
            ".jscpdrc",
            ".jscpdrc.json",
            ".jscpdrc.yml",
            ".jscpdrc.yaml",
        ],
    )
    def test_dedicated_config_file_has_config_file_reason(
        self, tmp_path: Path, filename: str
    ) -> None:
        """Dedicated config files report 'config file' as reason."""
        (tmp_path / filename).touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert findings[0].reason == "config file"

    def test_no_findings_for_unrelated_files(self, tmp_path: Path) -> None:
        """Unrelated files are not flagged."""
        (tmp_path / "README.md").touch()
        (tmp_path / "main.py").touch()
        (tmp_path / ".gitignore").touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 0


@pytest.mark.unit
class TestPyprojectTomlPylintMypy:
    """Tests for pyproject.toml pylint and mypy section detection."""

    def test_tool_pylint_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pylint] section returns one finding."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tool_pylint_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pylint] section reports pylint tool."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "pylint"

    def test_tool_pylint_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pylint] section reports tool.pylint in reason."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert "tool.pylint" in findings[0].reason

    def test_tool_pylint_subsection_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pylint.messages_control] returns one finding."""
        content = "[tool.pylint.messages_control]\ndisable = ['C0114']\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tool_pylint_subsection_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pylint.messages_control] reports pylint."""
        content = "[tool.pylint.messages_control]\ndisable = ['C0114']\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "pylint"

    def test_tool_mypy_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.mypy] section returns one finding."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tool_mypy_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.mypy] section reports mypy tool."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "mypy"

    def test_tool_mypy_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.mypy] section reports tool.mypy in reason."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert "tool.mypy" in findings[0].reason

    def test_no_findings_for_other_tools(self, tmp_path: Path) -> None:
        """Other tool sections are not flagged."""
        content = "[tool.black]\nline-length = 88\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 0

    def test_multiple_sections_returns_two_findings(
        self, tmp_path: Path, pyproject_mypy_pylint_content: str
    ) -> None:
        """Multiple tool sections produce two findings."""
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml",
            pyproject_mypy_pylint_content,
        )
        assert len(findings) == 2

    def test_multiple_sections_has_correct_tools(
        self, tmp_path: Path, pyproject_mypy_pylint_content: str
    ) -> None:
        """Multiple tool sections report the correct tools."""
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml",
            pyproject_mypy_pylint_content,
        )
        tools = {f.tool for f in findings}
        assert tools == {"mypy", "pylint"}


@pytest.mark.unit
class TestPyprojectTomlOtherTools:
    """Tests for pyproject.toml pytest, jscpd, yamllint detection."""

    def test_tool_pytest_ini_options_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pytest.ini_options] returns one finding."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tool_pytest_ini_options_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pytest.ini_options] reports pytest tool."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "pytest"

    def test_tool_pytest_ini_options_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.pytest.ini_options] reports correct reason."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert "tool.pytest.ini_options" in findings[0].reason

    def test_tool_pytest_without_ini_options_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """[tool.pytest] without ini_options is not flagged."""
        content = "[tool.pytest]\nmarkers = ['slow']\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 0

    def test_tool_jscpd_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.jscpd] section returns one finding."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tool_jscpd_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.jscpd] section reports jscpd tool."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "jscpd"

    def test_tool_jscpd_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.jscpd] section reports tool.jscpd in reason."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert "tool.jscpd" in findings[0].reason

    def test_tool_yamllint_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.yamllint] section returns one finding."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tool_yamllint_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.yamllint] section reports yamllint tool."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "yamllint"

    def test_tool_yamllint_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool.yamllint] section reports reason."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert "tool.yamllint" in findings[0].reason


@pytest.mark.unit
class TestSetupCfg:
    """Tests for setup.cfg section detection."""

    def test_mypy_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [mypy] section returns one finding."""
        content = "[mypy]\nstrict = True\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1

    def test_mypy_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [mypy] section reports mypy tool."""
        content = "[mypy]\nstrict = True\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert findings[0].tool == "mypy"

    def test_mypy_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [mypy] section reports mypy section in reason."""
        content = "[mypy]\nstrict = True\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert "mypy section" in findings[0].reason

    def test_tool_pytest_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool:pytest] section returns one finding."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1

    def test_tool_pytest_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool:pytest] section reports pytest tool."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert findings[0].tool == "pytest"

    def test_tool_pytest_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool:pytest] section reports tool:pytest in reason."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert "tool:pytest" in findings[0].reason

    def test_pylint_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect section containing 'pylint' returns one finding."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1

    def test_pylint_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect section containing 'pylint' reports pylint tool."""
        content = "[pylint.messages_control]\ndisable = C0114\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert findings[0].tool == "pylint"

    def test_pylint_master_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [pylint.master] section returns one finding."""
        content = "[pylint.master]\njobs = 4\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 1

    def test_pylint_master_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [pylint.master] section reports pylint tool."""
        content = "[pylint.master]\njobs = 4\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert findings[0].tool == "pylint"

    def test_no_findings_for_other_sections(
        self, tmp_path: Path
    ) -> None:
        """Other sections are not flagged."""
        content = "[metadata]\nname = mypackage\n"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 0


@pytest.mark.unit
class TestToxIni:
    """Tests for tox.ini section detection."""

    def test_pytest_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [pytest] section returns one finding."""
        content = "[pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1

    def test_pytest_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [pytest] section reports pytest tool."""
        content = "[pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert findings[0].tool == "pytest"

    def test_pytest_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [pytest] section reports pytest section in reason."""
        content = "[pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert "pytest section" in findings[0].reason

    def test_tool_pytest_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool:pytest] section returns one finding."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1

    def test_tool_pytest_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [tool:pytest] section reports pytest tool."""
        content = "[tool:pytest]\naddopts = -v\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert findings[0].tool == "pytest"

    def test_mypy_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect [mypy] section returns one finding."""
        content = "[mypy]\nstrict = True\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1

    def test_mypy_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect [mypy] section reports mypy tool."""
        content = "[mypy]\nstrict = True\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert findings[0].tool == "mypy"

    def test_mypy_section_has_correct_reason(
        self, tmp_path: Path
    ) -> None:
        """Detect [mypy] section reports mypy section in reason."""
        content = "[mypy]\nstrict = True\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert "mypy section" in findings[0].reason

    def test_pylint_section_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Detect section containing 'pylint' returns one finding."""
        content = "[pylint]\ndisable = C0114\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 1

    def test_pylint_section_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Detect section containing 'pylint' reports pylint tool."""
        content = "[pylint]\ndisable = C0114\n"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert findings[0].tool == "pylint"

    def test_no_findings_for_tox_sections(
        self, tmp_path: Path
    ) -> None:
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
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 0

    def test_recursive_scan_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Subdirectories are scanned recursively."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "pytest.ini").touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1

    def test_recursive_scan_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Subdirectories report the correct tool."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "pytest.ini").touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert findings[0].tool == "pytest"

    def test_pyproject_toml_scanned_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """pyproject.toml is scanned and produces one finding."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1

    def test_pyproject_toml_scanned_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """pyproject.toml is scanned and reports the correct tool."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert findings[0].tool == "mypy"

    def test_setup_cfg_scanned_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """setup.cfg is scanned and produces one finding."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1

    def test_setup_cfg_scanned_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """setup.cfg is scanned and reports the correct tool."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert findings[0].tool == "mypy"

    def test_tox_ini_scanned_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """tox.ini is scanned and produces one finding."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1

    def test_tox_ini_scanned_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """tox.ini is scanned and reports the correct tool."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert findings[0].tool == "pytest"

    def test_pyproject_toml_without_tool_sections(
        self, tmp_path: Path
    ) -> None:
        """pyproject.toml without tool sections is not flagged."""
        content = "[project]\nname = 'myproject'\n"
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 0

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns no findings."""
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 0


@pytest.mark.unit
class TestFinding:
    """Tests for the Finding class."""

    def test_str_format(self) -> None:
        """Finding formats as path:tool:reason."""
        finding = Finding("./pytest.ini", "pytest", "config file")
        assert str(finding) == "./pytest.ini:pytest:config file"

    def test_namedtuple_has_correct_path(self) -> None:
        """Finding has correct path field."""
        finding = Finding("./mypy.ini", "mypy", "config file")
        assert finding.path == "./mypy.ini"

    def test_namedtuple_has_correct_tool(self) -> None:
        """Finding has correct tool field."""
        finding = Finding("./mypy.ini", "mypy", "config file")
        assert finding.tool == "mypy"

    def test_namedtuple_has_correct_reason(self) -> None:
        """Finding has correct reason field."""
        finding = Finding("./mypy.ini", "mypy", "config file")
        assert finding.reason == "config file"


@pytest.mark.unit
class TestMakePathRelative:
    """Tests for the make_path_relative function."""

    def test_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
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
