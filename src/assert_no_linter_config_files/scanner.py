"""Scanner for detecting linter configuration files and sections."""

import configparser
import os
import re
from pathlib import Path
from typing import NamedTuple

try:
    import tomllib
    HAS_TOMLLIB = True
except ImportError:
    HAS_TOMLLIB = False

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


class Finding(NamedTuple):
    """Represents a detected linter configuration."""

    path: str
    tool: str
    reason: str

    def __str__(self) -> str:
        """Format the finding as path:tool:reason."""
        return f"{self.path}:{self.tool}:{self.reason}"


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
        except Exception:  # pylint: disable=broad-except
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
    if filename == "tox.ini":
        return check_tox_ini(file_path, content)
    return []


def scan_directory(directory: Path) -> list[Finding]:
    """Scan a directory recursively for linter configuration files."""
    findings: list[Finding] = []
    shared_config_files = {"pyproject.toml", "setup.cfg", "tox.ini"}

    for root, dirs, files in os.walk(directory):
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            file_path = Path(root) / filename

            if filename in DEDICATED_CONFIG_FILES:
                tool = DEDICATED_CONFIG_FILES[filename]
                findings.append(Finding(str(file_path), tool, "config file"))
            elif filename in shared_config_files:
                findings.extend(_process_shared_config_file(file_path, filename))

    return findings


def make_path_relative(path: str) -> str:
    """Convert an absolute path to a relative path from cwd."""
    try:
        return str(Path(path).relative_to(Path.cwd()))
    except ValueError:
        return path
