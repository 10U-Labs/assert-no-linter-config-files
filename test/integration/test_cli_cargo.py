"""Integration tests for Rust tools and Cargo.toml through the CLI."""

from pathlib import Path

import pytest

RUST_LINTERS = "clippy,rustc,rustdoc,rustfmt"

WORKSPACE_CARGO_TOML = """\
[workspace]
members = ["crate"]

[workspace.lints.rust]
dead_code = "allow"

[workspace.lints.clippy]
too_many_arguments = "allow"
"""

CRATE_CARGO_TOML = """\
[package]
name = "sample"
version = "0.1.0"
edition = "2024"

[lints.rust]
unused_variables = "allow"

[lints.clippy]
pedantic = "allow"
"""

DEDICATED_FINDINGS = {
    ("clippy.toml", "clippy", "config file"),
    ("crate/.clippy.toml", "clippy", "config file"),
    ("crate/.rustfmt.toml", "rustfmt", "config file"),
    ("rustfmt.toml", "rustfmt", "config file"),
}

CARGO_FINDINGS = {
    ("Cargo.toml", "clippy", "workspace.lints.clippy section"),
    ("Cargo.toml", "rustc", "workspace.lints.rust section"),
    ("crate/Cargo.toml", "clippy", "lints.clippy section"),
    ("crate/Cargo.toml", "rustc", "lints.rust section"),
}


def _write_rust_tree(root: Path) -> None:
    """Write the six-file Rust workspace of issue #8 under root."""
    crate = root / "crate"
    crate.mkdir()
    for path in (root / "rustfmt.toml", crate / ".rustfmt.toml"):
        path.write_text("max_width = 120\n")
    for path in (root / "clippy.toml", crate / ".clippy.toml"):
        path.write_text("too-many-arguments-threshold = 12\n")
    (root / "Cargo.toml").write_text(WORKSPACE_CARGO_TOML)
    (crate / "Cargo.toml").write_text(CRATE_CARGO_TOML)


def _parse_findings(root: Path, stdout: str) -> set[tuple[str, str, str]]:
    """Parse path:tool:reason lines into tuples relative to root."""
    findings = set()
    for line in stdout.splitlines():
        path, tool, reason = line.split(":")
        relative = Path(path).relative_to(root).as_posix()
        findings.add((relative, tool, reason))
    return findings


@pytest.mark.integration
class TestRustTree:
    """Tests for the Rust workspace of issue #8 through the CLI."""

    @pytest.fixture
    def rust_tree_result(
        self, tmp_path: Path, run_main_with_args
    ) -> tuple[int, str, str]:
        """Run the CLI over the Rust tree with every Rust linter."""
        _write_rust_tree(tmp_path)
        return run_main_with_args([
            "--linters", RUST_LINTERS, str(tmp_path)
        ])

    @pytest.fixture
    def rust_tree_excluded_result(
        self, tmp_path: Path, run_main_with_args
    ) -> tuple[int, str, str]:
        """Run the CLI over the Rust tree, excluding every Cargo.toml."""
        _write_rust_tree(tmp_path)
        return run_main_with_args([
            "--linters", RUST_LINTERS,
            "--exclude", "*/Cargo.toml", str(tmp_path)
        ])

    def test_rust_tree_exits_1(
        self, rust_tree_result: tuple[int, str, str]
    ) -> None:
        """Exit 1 when Rust tools are configured."""
        assert rust_tree_result[0] == 1

    def test_rust_tree_reports_eight_findings(
        self, tmp_path: Path, rust_tree_result: tuple[int, str, str]
    ) -> None:
        """The four files and four lint tables are reported."""
        assert _parse_findings(tmp_path, rust_tree_result[1]) == (
            DEDICATED_FINDINGS | CARGO_FINDINGS
        )

    def test_excluding_cargo_toml_reports_four_files(
        self,
        tmp_path: Path,
        rust_tree_excluded_result: tuple[int, str, str],
    ) -> None:
        """Excluding */Cargo.toml leaves only the four dedicated files."""
        assert _parse_findings(
            tmp_path, rust_tree_excluded_result[1]
        ) == DEDICATED_FINDINGS


@pytest.mark.integration
def test_invalid_cargo_toml_falls_back_to_regex(
    tmp_path: Path, run_main_with_args
) -> None:
    """A Cargo.toml that does not parse is read by the regex fallback."""
    (tmp_path / "Cargo.toml").write_text(
        "[package\n\n[lints.rustdoc]\nbroken_intra_doc_links = \"allow\"\n"
    )
    _, stdout, _ = run_main_with_args([
        "--linters", RUST_LINTERS, str(tmp_path)
    ])
    assert _parse_findings(tmp_path, stdout) == {
        ("Cargo.toml", "rustdoc", "lints.rustdoc section")
    }


@pytest.mark.integration
def test_workspace_opt_in_reports_clean(
    tmp_path: Path, run_main_with_args
) -> None:
    """A [lints] table holding only workspace = true exits 0."""
    (tmp_path / "Cargo.toml").write_text(
        "[package]\nname = \"sample\"\n\n[lints]\nworkspace = true\n"
    )
    code, _, _ = run_main_with_args([
        "--linters", RUST_LINTERS, str(tmp_path)
    ])
    assert code == 0


@pytest.mark.integration
def test_verbose_lists_cargo_tables(
    tmp_path: Path, run_main_with_args
) -> None:
    """--verbose lists the Cargo.toml tables of clippy."""
    _, stdout, _ = run_main_with_args([
        "--linters", "clippy", "--verbose", str(tmp_path)
    ])
    assert (
        "[lints.clippy] or [workspace.lints.clippy] in Cargo.toml" in stdout
    )
