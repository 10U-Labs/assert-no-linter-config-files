"""Unit tests for the scanner module - mappings, filters, and fallbacks."""

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
    parse_linters,
    scan_directory,
)


@pytest.mark.unit
class TestDedicatedConfigFilesMapping:
    """Tests for the DEDICATED_CONFIG_FILES mapping."""

    @pytest.mark.parametrize(
        "filename",
        [".pylintrc", "pylintrc", ".pylintrc.toml"],
    )
    def test_pylint_file_maps_to_pylint(self, filename: str) -> None:
        """Pylint config file maps to pylint."""
        assert DEDICATED_CONFIG_FILES[filename] == "pylint"

    @pytest.mark.parametrize(
        "filename",
        ["pytest.ini"],
    )
    def test_pytest_file_maps_to_pytest(self, filename: str) -> None:
        """Pytest config file maps to pytest."""
        assert DEDICATED_CONFIG_FILES[filename] == "pytest"

    @pytest.mark.parametrize(
        "filename",
        ["mypy.ini", ".mypy.ini"],
    )
    def test_mypy_file_maps_to_mypy(self, filename: str) -> None:
        """Mypy config file maps to mypy."""
        assert DEDICATED_CONFIG_FILES[filename] == "mypy"

    @pytest.mark.parametrize(
        "filename",
        [".yamllint", ".yamllint.yml", ".yamllint.yaml"],
    )
    def test_yamllint_file_maps_to_yamllint(
        self, filename: str
    ) -> None:
        """Yamllint config file maps to yamllint."""
        assert DEDICATED_CONFIG_FILES[filename] == "yamllint"

    def test_markdownlint_has_five_dedicated_files(self) -> None:
        """There are exactly five markdownlint dedicated config files."""
        markdownlint_count = sum(
            1 for tool in DEDICATED_CONFIG_FILES.values()
            if tool == "markdownlint"
        )
        assert markdownlint_count == 5

    @pytest.mark.parametrize(
        "filename",
        [
            f
            for f in DEDICATED_CONFIG_FILES
            if "markdownlint" in f
        ],
    )
    def test_markdownlint_filename_maps_to_markdownlint(
        self, filename: str
    ) -> None:
        """Markdownlint config file maps to markdownlint."""
        assert DEDICATED_CONFIG_FILES[filename] == "markdownlint"

    def test_jscpd_has_eight_dedicated_files(self) -> None:
        """There are exactly eight jscpd dedicated config files."""
        jscpd_count = sum(
            1 for tool in DEDICATED_CONFIG_FILES.values()
            if tool == "jscpd"
        )
        assert jscpd_count == 8

    @pytest.mark.parametrize(
        "filename",
        [
            f
            for f in DEDICATED_CONFIG_FILES
            if "jscpd" in f
        ],
    )
    def test_jscpd_filename_maps_to_jscpd(
        self, filename: str
    ) -> None:
        """Jscpd config file maps to jscpd."""
        assert DEDICATED_CONFIG_FILES[filename] == "jscpd"


@pytest.mark.unit
class TestGetConfigFilesForLinters:
    """Tests for the get_config_files_for_linters function."""

    def test_single_linter_contains_pylint_key(self) -> None:
        """Single linter result contains pylint key."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        assert "pylint" in result

    def test_single_linter_contains_pylintrc(self) -> None:
        """Single linter result contains .pylintrc."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        assert ".pylintrc" in result["pylint"]

    def test_single_linter_contains_pylintrc_no_dot(self) -> None:
        """Single linter result contains pylintrc."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        assert "pylintrc" in result["pylint"]

    def test_single_linter_contains_pylintrc_toml(self) -> None:
        """Single linter result contains .pylintrc.toml."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        assert ".pylintrc.toml" in result["pylint"]

    def test_single_linter_shared_contains_mypy_key(self) -> None:
        """Single linter result contains mypy key."""
        result = get_config_files_for_linters(frozenset({"mypy"}))
        assert "mypy" in result

    def test_single_linter_shared_contains_pyproject(self) -> None:
        """Single linter contains pyproject.toml shared section."""
        result = get_config_files_for_linters(frozenset({"mypy"}))
        assert "[tool.mypy] in pyproject.toml" in result["mypy"]

    def test_single_linter_shared_contains_setup_cfg(self) -> None:
        """Single linter contains setup.cfg shared section."""
        result = get_config_files_for_linters(frozenset({"mypy"}))
        assert "[mypy] in setup.cfg" in result["mypy"]

    def test_single_linter_shared_contains_tox_ini(self) -> None:
        """Single linter contains tox.ini shared section."""
        result = get_config_files_for_linters(frozenset({"mypy"}))
        assert "[mypy] in tox.ini" in result["mypy"]

    def test_multiple_linters_returns_correct_count(self) -> None:
        """Multiple linters returns correct count."""
        result = get_config_files_for_linters(
            frozenset({"pylint", "mypy"})
        )
        assert len(result) == 2

    def test_multiple_linters_contains_pylint(self) -> None:
        """Multiple linters result contains pylint."""
        result = get_config_files_for_linters(
            frozenset({"pylint", "mypy"})
        )
        assert "pylint" in result

    def test_multiple_linters_contains_mypy(self) -> None:
        """Multiple linters result contains mypy."""
        result = get_config_files_for_linters(
            frozenset({"pylint", "mypy"})
        )
        assert "mypy" in result

    def test_results_sorted_by_linter(self) -> None:
        """Results are sorted alphabetically by linter name."""
        result = get_config_files_for_linters(
            frozenset({"yamllint", "mypy", "pylint"})
        )
        linter_order = list(result.keys())
        assert linter_order == ["mypy", "pylint", "yamllint"]

    def test_dedicated_files_sorted(self) -> None:
        """Dedicated config files are sorted alphabetically."""
        result = get_config_files_for_linters(frozenset({"pylint"}))
        dedicated = [f for f in result["pylint"] if "in" not in f]
        assert dedicated == sorted(dedicated)

    def test_linter_without_shared_has_dedicated(self) -> None:
        """Linter with only dedicated files includes them."""
        result = get_config_files_for_linters(
            frozenset({"yamllint"})
        )
        assert ".yamllint" in result["yamllint"]

    def test_linter_without_shared_has_pyproject(self) -> None:
        """Linter with pyproject.toml shared section includes it."""
        result = get_config_files_for_linters(
            frozenset({"yamllint"})
        )
        assert (
            "[tool.yamllint.*] in pyproject.toml"
            in result["yamllint"]
        )

    def test_all_valid_linters_returns_correct_count(self) -> None:
        """All valid linters return correct number of results."""
        result = get_config_files_for_linters(VALID_LINTERS)
        assert len(result) == len(VALID_LINTERS)

    @pytest.mark.parametrize(
        "linter",
        sorted(VALID_LINTERS),
    )
    def test_each_valid_linter_has_configs(
        self, linter: str
    ) -> None:
        """Each valid linter returns non-empty config list."""
        result = get_config_files_for_linters(VALID_LINTERS)
        assert len(result[linter]) > 0


@pytest.mark.unit
class TestGetConfigFilesForMarkdownlint:
    """Tests for get_config_files_for_linters with markdownlint."""

    def test_markdownlint_contains_key(self) -> None:
        """Markdownlint result contains markdownlint key."""
        result = get_config_files_for_linters(
            frozenset({"markdownlint"})
        )
        assert "markdownlint" in result

    def test_markdownlint_contains_json(self) -> None:
        """Markdownlint result contains .markdownlint.json."""
        result = get_config_files_for_linters(
            frozenset({"markdownlint"})
        )
        assert ".markdownlint.json" in result["markdownlint"]

    def test_markdownlint_contains_jsonc(self) -> None:
        """Markdownlint result contains .markdownlint.jsonc."""
        result = get_config_files_for_linters(
            frozenset({"markdownlint"})
        )
        assert ".markdownlint.jsonc" in result["markdownlint"]

    def test_markdownlint_contains_yml(self) -> None:
        """Markdownlint result contains .markdownlint.yml."""
        result = get_config_files_for_linters(
            frozenset({"markdownlint"})
        )
        assert ".markdownlint.yml" in result["markdownlint"]

    def test_markdownlint_contains_yaml(self) -> None:
        """Markdownlint result contains .markdownlint.yaml."""
        result = get_config_files_for_linters(
            frozenset({"markdownlint"})
        )
        assert ".markdownlint.yaml" in result["markdownlint"]

    def test_markdownlint_contains_rc(self) -> None:
        """Markdownlint result contains .markdownlintrc."""
        result = get_config_files_for_linters(
            frozenset({"markdownlint"})
        )
        assert ".markdownlintrc" in result["markdownlint"]


@pytest.mark.unit
class TestSharedConfigSectionsMapping:
    """Tests for the SHARED_CONFIG_SECTIONS mapping."""

    @pytest.mark.parametrize(
        "linter",
        list(SHARED_CONFIG_SECTIONS.keys()),
    )
    def test_linter_has_pyproject_section(self, linter: str) -> None:
        """Linter in SHARED_CONFIG_SECTIONS has pyproject.toml."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS[linter]

    def test_pylint_has_pyproject(self) -> None:
        """Pylint has pyproject.toml shared section."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS["pylint"]

    def test_pylint_has_setup_cfg(self) -> None:
        """Pylint has setup.cfg shared section."""
        assert "setup.cfg" in SHARED_CONFIG_SECTIONS["pylint"]

    def test_pylint_has_tox_ini(self) -> None:
        """Pylint has tox.ini shared section."""
        assert "tox.ini" in SHARED_CONFIG_SECTIONS["pylint"]

    def test_mypy_has_pyproject(self) -> None:
        """Mypy has pyproject.toml shared section."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS["mypy"]

    def test_mypy_has_setup_cfg(self) -> None:
        """Mypy has setup.cfg shared section."""
        assert "setup.cfg" in SHARED_CONFIG_SECTIONS["mypy"]

    def test_mypy_has_tox_ini(self) -> None:
        """Mypy has tox.ini shared section."""
        assert "tox.ini" in SHARED_CONFIG_SECTIONS["mypy"]

    def test_pytest_has_pyproject(self) -> None:
        """Pytest has pyproject.toml shared section."""
        assert "pyproject.toml" in SHARED_CONFIG_SECTIONS["pytest"]

    def test_pytest_has_setup_cfg(self) -> None:
        """Pytest has setup.cfg shared section."""
        assert "setup.cfg" in SHARED_CONFIG_SECTIONS["pytest"]

    def test_pytest_has_tox_ini(self) -> None:
        """Pytest has tox.ini shared section."""
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

    def test_to_dict_with_section_has_correct_path(self) -> None:
        """to_dict with section reason has correct path."""
        finding = Finding(
            "./pyproject.toml", "mypy", "tool.mypy section"
        )
        result = finding.to_dict()
        assert result["path"] == "./pyproject.toml"

    def test_to_dict_with_section_has_correct_tool(self) -> None:
        """to_dict with section reason has correct tool."""
        finding = Finding(
            "./pyproject.toml", "mypy", "tool.mypy section"
        )
        result = finding.to_dict()
        assert result["tool"] == "mypy"

    def test_to_dict_with_section_has_correct_reason(self) -> None:
        """to_dict with section reason has correct reason."""
        finding = Finding(
            "./pyproject.toml", "mypy", "tool.mypy section"
        )
        result = finding.to_dict()
        assert result["reason"] == "tool.mypy section"


@pytest.mark.unit
class TestScanDirectoryWithFilters:
    """Tests for scan_directory with linters and exclude filters."""

    def test_filter_by_single_linter_returns_one(
        self, tmp_path: Path
    ) -> None:
        """Filter by a single linter returns one finding."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        findings = scan_directory(
            tmp_path, linters=frozenset({"pylint"})
        )
        assert len(findings) == 1

    def test_filter_by_single_linter_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Filter by a single linter reports the correct tool."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        findings = scan_directory(
            tmp_path, linters=frozenset({"pylint"})
        )
        assert findings[0].tool == "pylint"

    def test_filter_by_multiple_linters_returns_correct(
        self, tmp_path: Path
    ) -> None:
        """Filter by multiple linters returns correct count."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / "pytest.ini").touch()
        findings = scan_directory(
            tmp_path, linters=frozenset({"pylint", "mypy"})
        )
        assert len(findings) == 2

    def test_filter_by_multiple_linters_has_correct_tools(
        self, tmp_path: Path
    ) -> None:
        """Filter by multiple linters reports the correct tools."""
        (tmp_path / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        (tmp_path / "pytest.ini").touch()
        findings = scan_directory(
            tmp_path, linters=frozenset({"pylint", "mypy"})
        )
        linters_found = {f.tool for f in findings}
        assert linters_found == {"pylint", "mypy"}

    def test_exclude_pattern_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        """Exclude paths matching pattern returns one finding."""
        subdir = tmp_path / "vendor"
        subdir.mkdir()
        (subdir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        findings = scan_directory(
            tmp_path,
            linters=VALID_LINTERS,
            exclude_patterns=["*vendor*"],
        )
        assert len(findings) == 1

    def test_exclude_pattern_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Exclude paths matching pattern reports correct tool."""
        subdir = tmp_path / "vendor"
        subdir.mkdir()
        (subdir / ".pylintrc").touch()
        (tmp_path / "mypy.ini").touch()
        findings = scan_directory(
            tmp_path,
            linters=VALID_LINTERS,
            exclude_patterns=["*vendor*"],
        )
        assert findings[0].tool == "mypy"

    @pytest.fixture
    def exclude_multiple_findings(
        self, tmp_path: Path
    ) -> list[Finding]:
        """Scan with multiple exclude patterns on lib and external."""
        lib_dir = tmp_path / "lib"
        ext_dir = tmp_path / "external"
        lib_dir.mkdir()
        ext_dir.mkdir()
        (lib_dir / ".pylintrc").touch()
        (ext_dir / "mypy.ini").touch()
        (tmp_path / ".yamllint").touch()
        return scan_directory(
            tmp_path,
            linters=VALID_LINTERS,
            exclude_patterns=["*lib*", "*external*"],
        )

    def test_exclude_multiple_patterns_returns_one(
        self, exclude_multiple_findings: list[Finding]
    ) -> None:
        """Multiple exclude patterns return one finding."""
        assert len(exclude_multiple_findings) == 1

    def test_exclude_multiple_patterns_has_correct_tool(
        self, exclude_multiple_findings: list[Finding]
    ) -> None:
        """Multiple exclude patterns report the correct tool."""
        assert exclude_multiple_findings[0].tool == "yamllint"

    def test_filter_embedded_config_returns_one(
        self, tmp_path: Path, pyproject_mypy_pylint_content: str
    ) -> None:
        """Filter embedded config returns one finding."""
        (tmp_path / "pyproject.toml").write_text(
            pyproject_mypy_pylint_content
        )
        findings = scan_directory(
            tmp_path, linters=frozenset({"mypy"})
        )
        assert len(findings) == 1

    def test_filter_embedded_config_has_correct_tool(
        self, tmp_path: Path, pyproject_mypy_pylint_content: str
    ) -> None:
        """Filter embedded config reports the correct tool."""
        (tmp_path / "pyproject.toml").write_text(
            pyproject_mypy_pylint_content
        )
        findings = scan_directory(
            tmp_path, linters=frozenset({"mypy"})
        )
        assert findings[0].tool == "mypy"


@pytest.mark.unit
class TestPyprojectRegexFallbackDetection:
    """Tests for the regex fallback detection of tool sections."""

    def test_regex_detects_pylint_returns_one(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.pylint] returns one."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert len(findings) == 1

    def test_regex_detects_pylint_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.pylint] reports pylint."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert findings[0].tool == "pylint"

    def test_regex_detects_mypy_returns_one(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.mypy] returns one."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert len(findings) == 1

    def test_regex_detects_mypy_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.mypy] reports mypy."""
        content = "[tool.mypy]\nstrict = true\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert findings[0].tool == "mypy"

    def test_regex_detects_pytest_returns_one(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.pytest.ini_options]."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert len(findings) == 1

    def test_regex_detects_pytest_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects pytest reports pytest."""
        content = "[tool.pytest.ini_options]\naddopts = '-v'\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert findings[0].tool == "pytest"

    def test_regex_detects_jscpd_returns_one(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.jscpd] returns one."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert len(findings) == 1

    def test_regex_detects_jscpd_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.jscpd] reports jscpd."""
        content = "[tool.jscpd]\nthreshold = 0\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert findings[0].tool == "jscpd"

    def test_regex_detects_yamllint_returns_one(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.yamllint] returns one."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert len(findings) == 1

    def test_regex_detects_yamllint_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """Regex fallback detects [tool.yamllint] reports yamllint."""
        content = "[tool.yamllint]\nrules = {}\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert findings[0].tool == "yamllint"

    def test_regex_no_findings(self, tmp_path: Path) -> None:
        """Regex fallback returns empty for non-matching content."""
        content = "[tool.black]\nline-length = 88\n"
        findings = _check_pyproject_with_regex(
            str(tmp_path), content
        )
        assert len(findings) == 0


@pytest.mark.unit
class TestPyprojectRegexFallbackIntegration:
    """Tests for tomllib failure fallback to regex."""

    def test_tomllib_parse_error_returns_one(
        self, tmp_path: Path
    ) -> None:
        """When tomllib fails, regex fallback returns one finding."""
        content = "[tool.mypy]\nstrict = {\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert len(findings) == 1

    def test_tomllib_parse_error_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """When tomllib fails, regex fallback reports mypy."""
        content = "[tool.mypy]\nstrict = {\n"
        findings = check_pyproject_toml(
            tmp_path / "pyproject.toml", content
        )
        assert findings[0].tool == "mypy"

    def test_without_tomllib_returns_one(
        self, tmp_path: Path
    ) -> None:
        """HAS_TOMLLIB=False returns one finding."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        with patch(
            "assert_no_linter_config_files.scanner.HAS_TOMLLIB",
            False,
        ):
            findings = check_pyproject_toml(
                tmp_path / "pyproject.toml", content
            )
        assert len(findings) == 1

    def test_without_tomllib_has_correct_tool(
        self, tmp_path: Path
    ) -> None:
        """HAS_TOMLLIB=False reports pylint tool."""
        content = "[tool.pylint]\nmax-line-length = 100\n"
        with patch(
            "assert_no_linter_config_files.scanner.HAS_TOMLLIB",
            False,
        ):
            findings = check_pyproject_toml(
                tmp_path / "pyproject.toml", content
            )
        assert findings[0].tool == "pylint"


@pytest.mark.unit
class TestConfigParserErrors:
    """Tests for configparser error handling."""

    def test_setup_cfg_invalid_syntax_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Invalid setup.cfg returns no findings."""
        content = "[section\nmissing closing bracket"
        findings = check_setup_cfg(tmp_path / "setup.cfg", content)
        assert len(findings) == 0

    def test_tox_ini_invalid_syntax_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Invalid tox.ini returns no findings."""
        content = "[section\nmissing closing bracket"
        findings = check_tox_ini(tmp_path / "tox.ini", content)
        assert len(findings) == 0


@pytest.mark.unit
def test_unknown_filename_returns_empty(tmp_path: Path) -> None:
    """Unknown config file returns empty list."""
    unknown_file = tmp_path / "unknown.txt"
    unknown_file.write_text("content")
    findings = _process_shared_config_file(
        unknown_file, "unknown.txt"
    )
    assert len(findings) == 0


@pytest.mark.unit
def test_has_tomllib_false_when_import_fails() -> None:
    """HAS_TOMLLIB is False when tomllib import fails."""
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "tomllib":
            raise ImportError("No module named 'tomllib'")
        return original_import(name, *args, **kwargs)

    scanner_module = "assert_no_linter_config_files.scanner"
    if scanner_module in sys.modules:
        del sys.modules[scanner_module]
    if "tomllib" in sys.modules:
        saved_tomllib = sys.modules["tomllib"]
        del sys.modules["tomllib"]
    else:
        saved_tomllib = None

    try:
        with patch.object(
            builtins, "__import__", side_effect=mock_import
        ):
            mod = importlib.import_module(scanner_module)
        assert mod.HAS_TOMLLIB is False
    finally:
        if saved_tomllib is not None:
            sys.modules["tomllib"] = saved_tomllib
        if scanner_module in sys.modules:
            del sys.modules[scanner_module]
        importlib.import_module(scanner_module)
