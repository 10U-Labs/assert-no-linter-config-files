"""Integration tests for the CLI on a Python that has no tomllib."""

from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest


@pytest.mark.integration
def test_pyproject_section_found_without_tomllib_exits_1(
    tmp_path: Path, cli_without_tomllib: ModuleType
) -> None:
    """Exit 1 when the regex fallback finds [tool.mypy] in pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n")
    argv = ["prog", "--linters", "mypy", "--quiet", str(tmp_path)]
    with patch("sys.argv", argv):
        with pytest.raises(SystemExit, match="1"):
            cli_without_tomllib.main()


@pytest.mark.integration
def test_cargo_section_found_without_tomllib_exits_1(
    tmp_path: Path, cli_without_tomllib: ModuleType
) -> None:
    """Exit 1 when the regex fallback finds [lints.clippy] in Cargo.toml."""
    (tmp_path / "Cargo.toml").write_text("[lints.clippy]\npedantic = \"allow\"\n")
    argv = ["prog", "--linters", "clippy", "--quiet", str(tmp_path)]
    with patch("sys.argv", argv):
        with pytest.raises(SystemExit, match="1"):
            cli_without_tomllib.main()
