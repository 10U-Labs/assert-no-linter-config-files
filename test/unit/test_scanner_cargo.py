"""Unit tests for the scanner module - Rust tools and Cargo.toml."""

from pathlib import Path
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.scanner import (
    SHARED_CONFIG_SECTIONS,
    Finding,
    check_cargo_toml,
    get_config_files_for_linters,
    parse_linters,
    scan_directory,
)

RUST_LINTERS: list[str] = ["clippy", "rustc", "rustdoc", "rustfmt"]

RUST_DEDICATED_FILES: list[tuple[str, str]] = [
    ("rustfmt.toml", "rustfmt"),
    (".rustfmt.toml", "rustfmt"),
    ("clippy.toml", "clippy"),
    (".clippy.toml", "clippy"),
]

CARGO_LINT_TABLES: list[tuple[str, str, str]] = [
    ("[lints.clippy]\npedantic = \"allow\"\n",
     "clippy", "lints.clippy section"),
    ("[lints.rust]\ndead_code = \"allow\"\n",
     "rustc", "lints.rust section"),
    ("[lints.rustdoc]\nbroken_intra_doc_links = \"allow\"\n",
     "rustdoc", "lints.rustdoc section"),
    ("[workspace.lints.clippy]\npedantic = \"allow\"\n",
     "clippy", "workspace.lints.clippy section"),
    ("[workspace.lints.rust]\ndead_code = \"allow\"\n",
     "rustc", "workspace.lints.rust section"),
    ("[workspace.lints.rustdoc]\nbroken_intra_doc_links = \"allow\"\n",
     "rustdoc", "workspace.lints.rustdoc section"),
]

CARGO_WITHOUT_LINT_LEVELS: list[str] = [
    "[package]\nname = \"sample\"\nversion = \"0.1.0\"\n",
    "[package]\nname = \"sample\"\n\n[lints]\nworkspace = true\n",
    "[workspace]\nmembers = [\"crate\"]\n",
    "workspace = 1\n",
]


@pytest.mark.unit
@pytest.mark.parametrize("linter", RUST_LINTERS)
def test_parse_linters_accepts_rust_linter(linter: str) -> None:
    """parse_linters accepts each Rust linter."""
    assert parse_linters(linter) == frozenset({linter})


@pytest.mark.unit
@pytest.mark.parametrize("subdir", ["", "crate"])
@pytest.mark.parametrize("filename,tool", RUST_DEDICATED_FILES)
def test_rust_dedicated_file_reports_its_tool(
    tmp_path: Path, subdir: str, filename: str, tool: str
) -> None:
    """A Rust tool's file is reported, at the top or in a subdirectory."""
    directory = tmp_path / subdir
    directory.mkdir(exist_ok=True)
    (directory / filename).touch()
    findings = scan_directory(tmp_path, linters=frozenset(RUST_LINTERS))
    assert findings == [
        Finding(str(directory / filename), tool, "config file")
    ]


@pytest.mark.unit
def test_unrequested_rust_linter_is_not_reported(tmp_path: Path) -> None:
    """A clippy.toml reports clean when only rustfmt is asked for."""
    (tmp_path / "clippy.toml").touch()
    assert not scan_directory(tmp_path, linters=frozenset({"rustfmt"}))


@pytest.mark.unit
@pytest.mark.parametrize("content,tool,reason", CARGO_LINT_TABLES)
def test_cargo_lint_table_reports_its_tool(
    tmp_path: Path, content: str, tool: str, reason: str
) -> None:
    """Each [lints] and [workspace.lints] sub-table gives one finding."""
    path = tmp_path / "Cargo.toml"
    assert check_cargo_toml(path, content) == [
        Finding(str(path), tool, reason)
    ]


@pytest.mark.unit
@pytest.mark.parametrize("content,tool,reason", CARGO_LINT_TABLES)
def test_cargo_lint_table_without_tomllib_reports_its_tool(
    tmp_path: Path, content: str, tool: str, reason: str
) -> None:
    """The regex fallback finds each sub-table when tomllib is missing."""
    path = tmp_path / "Cargo.toml"
    with patch(
        "assert_no_linter_config_files.scanner.HAS_TOMLLIB", False
    ):
        findings = check_cargo_toml(path, content)
    assert findings == [Finding(str(path), tool, reason)]


@pytest.mark.unit
@pytest.mark.parametrize("content", CARGO_WITHOUT_LINT_LEVELS)
def test_cargo_without_lint_levels_reports_nothing(
    tmp_path: Path, content: str
) -> None:
    """No finding without a sub-table, or for [lints] workspace = true."""
    assert not check_cargo_toml(tmp_path / "Cargo.toml", content)


@pytest.mark.unit
def test_invalid_cargo_toml_falls_back_to_regex(tmp_path: Path) -> None:
    """A Cargo.toml that does not parse is read by the regex fallback."""
    path = tmp_path / "Cargo.toml"
    content = "[package\n\n[lints.clippy]\npedantic = \"allow\"\n"
    assert check_cargo_toml(path, content) == [
        Finding(str(path), "clippy", "lints.clippy section")
    ]


@pytest.mark.unit
def test_scan_directory_reads_cargo_toml(tmp_path: Path) -> None:
    """scan_directory opens Cargo.toml as a shared config file."""
    path = tmp_path / "Cargo.toml"
    path.write_text("[lints.rust]\ndead_code = \"allow\"\n")
    findings = scan_directory(tmp_path, linters=frozenset({"rustc"}))
    assert findings == [Finding(str(path), "rustc", "lints.rust section")]


@pytest.mark.unit
@pytest.mark.parametrize(
    "linter,expected",
    [
        ("clippy", [
            ".clippy.toml",
            "clippy.toml",
            "[lints.clippy] or [workspace.lints.clippy] in Cargo.toml",
        ]),
        ("rustc", [
            "[lints.rust] or [workspace.lints.rust] in Cargo.toml",
        ]),
        ("rustdoc", [
            "[lints.rustdoc] or [workspace.lints.rustdoc] in Cargo.toml",
        ]),
        ("rustfmt", [".rustfmt.toml", "rustfmt.toml"]),
    ],
)
def test_get_config_files_lists_rust_configs(
    linter: str, expected: list[str]
) -> None:
    """get_config_files_for_linters lists each Rust tool's configs."""
    result = get_config_files_for_linters(frozenset({linter}))
    assert result == {linter: expected}


@pytest.mark.unit
@pytest.mark.parametrize("linter", ["clippy", "rustc", "rustdoc"])
def test_rust_linter_has_cargo_section(linter: str) -> None:
    """Rust linters configurable in Cargo.toml have a shared section."""
    assert "Cargo.toml" in SHARED_CONFIG_SECTIONS[linter]
