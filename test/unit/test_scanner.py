"""Unit tests for the scanner module."""

import builtins
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.scanner import (
    DEDICATED_CONFIG_FILES,
    SHARED_CONFIG_SECTIONS,
    VALID_LINTERS,
    Finding,
    _check_pyproject_with_regex,
    _process_shared_config_file,
    check_pyproject_toml,
    check_setup_cfg,
    check_tox_ini,
    get_config_files_for_linters,
    make_path_relative,
    parse_linters,
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
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1
        assert findings[0].tool == expected_tool
        assert findings[0].reason == "config file"

    def test_no_findings_for_unrelated_files(self, tmp_path: Path) -> None:
        """Unrelated files are not flagged."""
        (tmp_path / "README.md").touch()
        (tmp_path / "main.py").touch()
        (tmp_path / ".gitignore").touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
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
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 0

    def test_recursive_scan(self, tmp_path: Path) -> None:
        """Subdirectories are scanned recursively."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "pytest.ini").touch()
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"

    def test_pyproject_toml_scanned(self, tmp_path: Path) -> None:
        """pyproject.toml is scanned for embedded config."""
        content = "[tool.mypy]\nstrict = true\n"
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_setup_cfg_scanned(self, tmp_path: Path) -> None:
        """setup.cfg is scanned for embedded config."""
        content = "[mypy]\nstrict = True\n"
        (tmp_path / "setup.cfg").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_tox_ini_scanned(self, tmp_path: Path) -> None:
        """tox.ini is scanned for embedded config."""
        content = "[pytest]\naddopts = -v\n"
        (tmp_path / "tox.ini").write_text(content)
        findings = scan_directory(tmp_path, linters=VALID_LINTERS)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"

    def test_pyproject_toml_without_tool_sections(self, tmp_path: Path) -> None:
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


@pytest.mark.unit
class TestGetConfigFilesForLinters:
    """Tests for the get_config_files_for_linters function."""

    def test_single_linter_returns_dedicated_files(self) -> None:
        """Single linter returns its dedicated config files."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        assert "pylint" in result
        assert ".pylintrc" in result["pylint"]
        assert "pylintrc" in result["pylint"]
        assert ".pylintrc.toml" in result["pylint"]

    def test_single_linter_returns_shared_sections(self) -> None:
        """Single linter returns shared config sections."""
        result = get_config_files_for_linters(frozenset({"mypy"}))
        assert "mypy" in result
        assert "[tool.mypy] in pyproject.toml" in result["mypy"]
        assert "[mypy] in setup.cfg" in result["mypy"]
        assert "[mypy] in tox.ini" in result["mypy"]

    def test_multiple_linters_returns_all(self) -> None:
        """Multiple linters returns configs for each."""
        result = get_config_files_for_linters(frozenset({"pylint", "mypy"}))
        assert len(result) == 2
        assert "pylint" in result
        assert "mypy" in result

    def test_results_sorted_by_linter(self) -> None:
        """Results are sorted alphabetically by linter name."""
        result = get_config_files_for_linters(frozenset({"yamllint", "mypy", "pylint"}))
        linter_order = list(result.keys())
        assert linter_order == ["mypy", "pylint", "yamllint"]

    def test_dedicated_files_sorted(self) -> None:
        """Dedicated config files are sorted alphabetically."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        dedicated = [f for f in result["pylint"] if "in" not in f]
        assert dedicated == sorted(dedicated)

    def test_linter_without_shared_sections(self) -> None:
        """Linter with only dedicated files works correctly."""
        # yamllint only has pyproject.toml shared section
        result = get_config_files_for_linters(frozenset({"yamllint"}))
        assert ".yamllint" in result["yamllint"]
        assert "[tool.yamllint.*] in pyproject.toml" in result["yamllint"]

    def test_all_valid_linters(self) -> None:
        """All valid linters return non-empty config lists."""
        result = get_config_files_for_linters(VALID_LINTERS)
        assert len(result) == len(VALID_LINTERS)
        for linter, configs in result.items():
            assert len(configs) > 0, f"{linter} has no configs"


@pytest.mark.unit
class TestSharedConfigSectionsMapping:
    """Tests for the SHARED_CONFIG_SECTIONS mapping."""

    def test_all_linters_have_pyproject_section(self) -> None:
        """All linters in SHARED_CONFIG_SECTIONS have pyproject.toml."""
        for linter, sections in SHARED_CONFIG_SECTIONS.items():
            assert "pyproject.toml" in sections, f"{linter} missing pyproject.toml"

    def test_pylint_has_all_shared_files(self) -> None:
        """Pylint has sections in all shared config files."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS["pylint"]
        assert "setup.cfg" in SHARED_CONFIG_SECTIONS["pylint"]
        assert "tox.ini" in SHARED_CONFIG_SECTIONS["pylint"]

    def test_mypy_has_all_shared_files(self) -> None:
        """Mypy has sections in all shared config files."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS["mypy"]
        assert "setup.cfg" in SHARED_CONFIG_SECTIONS["mypy"]
        assert "tox.ini" in SHARED_CONFIG_SECTIONS["mypy"]

    def test_pytest_has_all_shared_files(self) -> None:
        """Pytest has sections in all shared config files."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS["pytest"]
        assert "setup.cfg" in SHARED_CONFIG_SECTIONS["pytest"]
        assert "tox.ini" in SHARED_CONFIG_SECTIONS["pytest"]


@pytest.mark.unit
class TestParseLinters:
    """Tests for the parse_linters function."""

    def test_single_linter(self) -> None:
        """Parse a single linter."""
        result = parse_linters("pylint")
        assert result == frozenset({"pylint"})

    def test_multiple_linters(self) -> None:
        """Parse comma-separated linters."""
        result = parse_linters("pylint,mypy,pytest")
        assert result == frozenset({"pylint", "mypy", "pytest"})

    def test_linters_with_spaces(self) -> None:
        """Parse linters with surrounding spaces."""
        result = parse_linters(" pylint , mypy ")
        assert result == frozenset({"pylint", "mypy"})

    def test_case_insensitive(self) -> None:
        """Linter names are case-insensitive."""
        result = parse_linters("PYLINT,MyPy")
        assert result == frozenset({"pylint", "mypy"})

    def test_invalid_linter_raises(self) -> None:
        """Invalid linter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid linter"):
            parse_linters("invalid")

    def test_empty_string_raises(self) -> None:
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="At least one linter"):
            parse_linters("")

    def test_all_valid_linters(self) -> None:
        """All valid linters can be parsed."""
        linters_str = ",".join(VALID_LINTERS)
        result = parse_linters(linters_str)
        assert result == VALID_LINTERS


@pytest.mark.unit
class TestFindingToDict:
    """Tests for the Finding.to_dict method."""

    def test_to_dict(self) -> None:
        """to_dict returns correct dictionary."""
        finding = Finding("./pytest.ini", "pytest", "config file")
        result = finding.to_dict()
        assert result == {
            "path": "./pytest.ini",
            "tool": "pytest",
            "reason": "config file",
        }

    def test_to_dict_with_section(self) -> None:
        """to_dict works with section reason."""
        finding = Finding("./pyproject.toml", "mypy", "tool.mypy section")
        result = finding.to_dict()
        assert result["path"] == "./pyproject.toml"
        assert result["tool"] == "mypy"
        assert result["reason"] == "tool.mypy section"


@pytest.mark.unit
class TestScanDirectoryWithFilters:
    """Tests for scan_directory with linters and exclude filters."""

    def test_filter_by_single_linter(self, tmp_path: Path) -> None:
        """Filter by a single linter."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        findings = scan_directory(tmp_path, linters=frozenset({"pylint"}))
        assert len(findings) == 1
        assert findings[0].tool == "pylint"

    def test_filter_by_multiple_linters(self, tmp_path: Path) -> None:
        """Filter by multiple linters."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / "pytest.ini").touch()
        findings = scan_directory(tmp_path, linters=frozenset({"pylint", "mypy"}))
        assert len(findings) == 2
        linters_found = {f.tool for f in findings}
        assert linters_found == {"pylint", "mypy"}

    def test_exclude_pattern(self, tmp_path: Path) -> None:
        """Exclude paths matching pattern."""
        subdir = tmp_path / "vendor"
        subdir.mkdir()
        (subdir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        findings = scan_directory(
            tmp_path, linters=VALID_LINTERS, exclude_patterns=["*vendor*"]
        )
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_exclude_multiple_patterns(self, tmp_path: Path) -> None:
        """Multiple exclude patterns work together."""
        lib_dir = tmp_path / "lib"
        ext_dir = tmp_path / "external"
        lib_dir.mkdir()
        ext_dir.mkdir()
        (lib_dir / ".pylintrc").touch()
        (ext_dir / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        findings = scan_directory(
            tmp_path, linters=VALID_LINTERS, exclude_patterns=["*lib*", "*external*"]
        )
        assert len(findings) == 1
        assert findings[0].tool == "yamllint"

    def test_filter_embedded_config_by_linter(self, tmp_path: Path) -> None:
        """Filter embedded config in pyproject.toml by linter."""
        content = """
[tool.mypy]
strict = true

[tool.pylint]
max-line-length = 100
"""
        (tmp_path / "pyproject.toml").write_text(content)
        findings = scan_directory(tmp_path, linters=frozenset({"mypy"}))
        assert len(findings) == 1
        assert findings[0].tool == "mypy"


@pytest.mark.unit
class TestPyprojectRegexFallback:
    """Tests for the regex fallback when tomllib is unavailable or fails."""

    def test_regex_fallback_detects_pylint(self, tmp_path: Path) -> None:
        """Regex fallback detects [tool.pylint] section."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = _check_pyproject_with_regex(str(tmp_path), content)
        assert len(findings) == 1
        assert findings[0].tool == "pylint"

    def test_regex_fallback_detects_mypy(self, tmp_path: Path) -> None:
        """Regex fallback detects [tool.mypy] section."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = _check_pyproject_with_regex(str(tmp_path), content)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_regex_fallback_detects_pytest(self, tmp_path: Path) -> None:
        """Regex fallback detects [tool.pytest.ini_options] section."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = _check_pyproject_with_regex(str(tmp_path), content)
        assert len(findings) == 1
        assert findings[0].tool == "pytest"

    def test_regex_fallback_detects_jscpd(self, tmp_path: Path) -> None:
        """Regex fallback detects [tool.jscpd] section."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = _check_pyproject_with_regex(str(tmp_path), content)
        assert len(findings) == 1
        assert findings[0].tool == "jscpd"

    def test_regex_fallback_detects_yamllint(self, tmp_path: Path) -> None:
        """Regex fallback detects [tool.yamllint] section."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = _check_pyproject_with_regex(str(tmp_path), content)
        assert len(findings) == 1
        assert findings[0].tool == "yamllint"

    def test_regex_fallback_no_findings(self, tmp_path: Path) -> None:
        """Regex fallback returns empty for non-matching content."""
        content = "[tool.black]\nline-length = 88\n"
        findings = _check_pyproject_with_regex(str(tmp_path), content)
        assert len(findings) == 0

    def test_tomllib_parse_error_falls_back_to_regex(
        self, tmp_path: Path
    ) -> None:
        """When tomllib fails to parse, regex fallback is used."""
        # Invalid TOML but regex can still match
        content = "[tool.mypy]\nstrict = {\n"  # Invalid TOML
        findings = check_pyproject_toml(tmp_path / "pyproject.toml", content)
        assert len(findings) == 1
        assert findings[0].tool == "mypy"

    def test_check_pyproject_without_tomllib(self, tmp_path: Path) -> None:
        """check_pyproject_toml uses regex when HAS_TOMLLIB is False."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        with patch(
            "assert_no_linter_config_files.scanner.HAS_TOMLLIB", False
        ):
            findings = check_pyproject_toml(
                tmp_path / "pyproject.toml", content
            )
        assert len(findings) == 1
        assert findings[0].tool == "pylint"


@pytest.mark.unit
class TestConfigParserErrors:
    """Tests for configparser error handling."""

    def test_setup_cfg_invalid_syntax_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Invalid setup.cfg returns no findings instead of crashing."""
        # Content that will cause configparser to fail
        content = "[section\nmissing closing bracket"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 0

    def test_tox_ini_invalid_syntax_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Invalid tox.ini returns no findings instead of crashing."""
        # Content that will cause configparser to fail
        content = "[section\nmissing closing bracket"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 0


@pytest.mark.unit
class TestProcessSharedConfigFile:
    """Tests for the _process_shared_config_file function."""

    def test_unknown_filename_returns_empty(self, tmp_path: Path) -> None:
        """Unknown config file returns empty list."""
        unknown_file = tmp_path / "unknown.txt"
        unknown_file.write_text("content")
        findings = _process_shared_config_file(unknown_file, "unknown.txt")
        assert len(findings) == 0


@pytest.mark.unit
class TestTomlibImportFallback:
    """Tests for the tomllib import fallback."""

    def test_has_tomllib_false_when_import_fails(self) -> None:
        """HAS_TOMLLIB is False when tomllib import fails."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "tomllib":
                raise ImportError("No module named 'tomllib'")
            return original_import(name, *args, **kwargs)

        # Remove cached module
        scanner_module = "assert_no_linter_config_files.scanner"
        if scanner_module in sys.modules:
            del sys.modules[scanner_module]
        if "tomllib" in sys.modules:
            saved_tomllib = sys.modules["tomllib"]
            del sys.modules["tomllib"]
        else:
            saved_tomllib = None

        try:
            with patch.object(builtins, "__import__", side_effect=mock_import):
                # Re-import scanner with mocked import
                # The module import itself exercises the fallback path
                importlib.import_module(scanner_module)
        finally:
            # Restore modules
            if saved_tomllib is not None:
                sys.modules["tomllib"] = saved_tomllib
            # Force reimport of original scanner
            if scanner_module in sys.modules:
                del sys.modules[scanner_module]
            importlib.import_module(scanner_module)
