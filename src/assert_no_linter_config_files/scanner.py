"""Scanner for detecting linter configuration files and sections."""

import configparser
import fnmatch
import os
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
    HAS_TOMLLIB = True
except ImportError:  # pragma: no cover (Python < 3.11)
    HAS_TOMLLIB = False

VALID_LINTERS: frozenset[str] = frozenset({
    "pylint", "pytest", "mypy", "yamllint", "jscpd"
})

DEDICATED_CONFIG_FILES: dict[str, str] = {
    ".pylintrc": "pylint",
    "pylintrc": "pylint",
    ".pylintrc.toml": "pylint",
    "pytest.ini": "pytest",
    "mypy.ini": "mypy",
    ".mypy.ini": "mypy",
    ".yamllint": "yamllint",
    ".yamllint.yml": "yamllint",
    ".yamllint.yaml": "yamllint",
    ".jscpd.json": "jscpd",
    ".jscpd.yml": "jscpd",
    ".jscpd.yaml": "jscpd",
    ".jscpd.toml": "jscpd",
    ".jscpdrc": "jscpd",
    ".jscpdrc.json": "jscpd",
    ".jscpdrc.yml": "jscpd",
    ".jscpdrc.yaml": "jscpd",
}

SHARED_CONFIG_SECTIONS: dict[str, dict[str, str]] = {
    "pylint": {
        "pyproject.toml": "[tool.pylint.*]",
        "setup.cfg": "[pylint.*]",
        "tox.ini": "[pylint.*]",
    },
    "pytest": {
        "pyproject.toml": "[tool.pytest.ini_options]",
        "setup.cfg": "[tool:pytest]",
        "tox.ini": "[pytest] or [tool:pytest]",
    },
    "mypy": {
        "pyproject.toml": "[tool.mypy]",
        "setup.cfg": "[mypy]",
        "tox.ini": "[mypy]",
    },
    "yamllint": {
        "pyproject.toml": "[tool.yamllint.*]",
    },
    "jscpd": {
        "pyproject.toml": "[tool.jscpd.*]",
    },
}


def get_config_files_for_linters(linters: frozenset[str]) -> dict[str, list[str]]:
    """Get the config files that will be checked for each linter.

    Args:
        linters: Set of linter names to get config files for.

    Returns:
        Dictionary mapping each linter to its list of config file descriptions.
    """
    result: dict[str, list[str]] = {}

    for linter in sorted(linters):
        configs: list[str] = []

        # Add dedicated config files
        dedicated = sorted(
            filename for filename, tool in DEDICATED_CONFIG_FILES.items()
            if tool == linter
        )
        configs.extend(dedicated)

        # Add shared config sections
        if linter in SHARED_CONFIG_SECTIONS:
            for shared_file, section in SHARED_CONFIG_SECTIONS[linter].items():
                configs.append(f"{section} in {shared_file}")

        result[linter] = configs

    return result


def make_path_relative(path: str) -> str:
    """Convert an absolute path to a relative path from cwd."""
    try:
        return str(Path(path).relative_to(Path.cwd()))
    except ValueError:
        return path


@dataclass(frozen=True)
class Finding:
    """Represents a detected linter configuration."""

    path: str
    tool: str
    reason: str

    def __str__(self) -> str:
        """Format the finding as path:tool:reason."""
        relative_path = make_path_relative(self.path)
        return f"{relative_path}:{self.tool}:{self.reason}"

    def to_dict(self) -> dict[str, str]:
        """Convert finding to dictionary for JSON output."""
        return {
            "path": self.path,
            "tool": self.tool,
            "reason": self.reason,
        }


def parse_linters(linters_str: str) -> frozenset[str]:
    """Parse comma-separated linters string and validate.

    Args:
        linters_str: Comma-separated list of linter names.

    Returns:
        Frozenset of valid linter names.

    Raises:
        ValueError: If any linter name is invalid.
    """
    linters = frozenset(
        t.strip().lower() for t in linters_str.split(",") if t.strip()
    )

    invalid = linters - VALID_LINTERS
    if invalid:
        valid_list = ", ".join(sorted(VALID_LINTERS))
        invalid_list = ", ".join(sorted(invalid))
        raise ValueError(
            f"Invalid linter(s): {invalid_list}. Valid options: {valid_list}"
        )

    if not linters:
        raise ValueError("At least one linter must be specified")

    return linters


def _check_pyproject_with_tomllib(
    path_str: str, tool_section: dict[str, object]
) -> list[Finding]:
    """Check tool section using parsed TOML data."""
    findings: list[Finding] = []
    if "pylint" in tool_section:
        findings.append(Finding(path_str, "pylint", "tool.pylint section"))
    if "mypy" in tool_section:
        findings.append(Finding(path_str, "mypy", "tool.mypy section"))
    if "pytest" in tool_section:
        pytest_section = tool_section["pytest"]
        if isinstance(pytest_section, dict) and "ini_options" in pytest_section:
            findings.append(
                Finding(path_str, "pytest", "tool.pytest.ini_options section")
            )
    if "jscpd" in tool_section:
        findings.append(Finding(path_str, "jscpd", "tool.jscpd section"))
    if "yamllint" in tool_section:
        findings.append(Finding(path_str, "yamllint", "tool.yamllint section"))
    return findings


def _check_pyproject_with_regex(path_str: str, content: str) -> list[Finding]:
    """Check pyproject.toml content using regex fallback."""
    findings: list[Finding] = []
    if re.search(r"^\[tool\.pylint", content, re.MULTILINE):
        findings.append(Finding(path_str, "pylint", "tool.pylint section"))
    if re.search(r"^\[tool\.mypy\]", content, re.MULTILINE):
        findings.append(Finding(path_str, "mypy", "tool.mypy section"))
    if re.search(r"^\[tool\.pytest\.ini_options\]", content, re.MULTILINE):
        findings.append(
            Finding(path_str, "pytest", "tool.pytest.ini_options section")
        )
    if re.search(r"^\[tool\.jscpd", content, re.MULTILINE):
        findings.append(Finding(path_str, "jscpd", "tool.jscpd section"))
    if re.search(r"^\[tool\.yamllint", content, re.MULTILINE):
        findings.append(Finding(path_str, "yamllint", "tool.yamllint section"))
    return findings


def check_pyproject_toml(path: Path, content: str) -> list[Finding]:
    """Check pyproject.toml for tool-specific sections."""
    path_str = str(path)

    if HAS_TOMLLIB:
        try:
            data = tomllib.loads(content)
            tool_section = data.get("tool", {})
            return _check_pyproject_with_tomllib(path_str, tool_section)
        except (tomllib.TOMLDecodeError, ValueError, KeyError, TypeError):
            pass

    return _check_pyproject_with_regex(path_str, content)


def check_setup_cfg(path: Path, content: str) -> list[Finding]:
    """Check setup.cfg for tool-specific sections."""
    findings: list[Finding] = []
    path_str = str(path)

    parser = configparser.ConfigParser()
    try:
        parser.read_string(content)
    except configparser.Error:
        return findings

    for section in parser.sections():
        if section == "mypy":
            findings.append(Finding(path_str, "mypy", "mypy section"))
        elif section == "tool:pytest":
            findings.append(Finding(path_str, "pytest", "tool:pytest section"))
        elif "pylint" in section.lower():
            findings.append(Finding(path_str, "pylint", f"{section} section"))

    return findings


def check_tox_ini(path: Path, content: str) -> list[Finding]:
    """Check tox.ini for tool-specific sections."""
    findings: list[Finding] = []
    path_str = str(path)

    parser = configparser.ConfigParser()
    try:
        parser.read_string(content)
    except configparser.Error:
        return findings

    for section in parser.sections():
        if section in ("pytest", "tool:pytest"):
            findings.append(Finding(path_str, "pytest", f"{section} section"))
        elif section == "mypy":
            findings.append(Finding(path_str, "mypy", "mypy section"))
        elif "pylint" in section.lower():
            findings.append(Finding(path_str, "pylint", f"{section} section"))

    return findings


def _process_shared_config_file(
    file_path: Path, filename: str
) -> list[Finding]:
    """Process shared config files (pyproject.toml, setup.cfg, tox.ini)."""
    content = file_path.read_text(encoding="utf-8")
    if filename == "pyproject.toml":
        return check_pyproject_toml(file_path, content)
    if filename == "setup.cfg":
        return check_setup_cfg(file_path, content)
    # filename == "tox.ini"
    return check_tox_ini(file_path, content)


def _matches_exclude_pattern(
    path: str, exclude_patterns: list[str]
) -> bool:
    """Check if path matches any exclude pattern."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def scan_directory(
    directory: Path,
    linters: frozenset[str],
    exclude_patterns: list[str] | None = None,
) -> list[Finding]:
    """Scan a directory recursively for linter configuration files.

    Args:
        directory: The directory to scan.
        linters: Set of linters to check.
        exclude_patterns: List of glob patterns to exclude paths.

    Returns:
        A list of Finding objects for each config found.
    """
    if exclude_patterns is None:
        exclude_patterns = []

    findings: list[Finding] = []
    shared_config_files = {"pyproject.toml", "setup.cfg", "tox.ini"}

    for root, dirs, files in os.walk(directory):
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            file_path = Path(root) / filename
            path_str = str(file_path)

            # Check exclude patterns
            if _matches_exclude_pattern(path_str, exclude_patterns):
                continue

            if filename in DEDICATED_CONFIG_FILES:
                tool = DEDICATED_CONFIG_FILES[filename]
                if tool in linters:
                    findings.append(Finding(path_str, tool, "config file"))
            elif filename in shared_config_files:
                file_findings = _process_shared_config_file(file_path, filename)
                # Filter by requested linters
                findings.extend(f for f in file_findings if f.tool in linters)

    return findings
