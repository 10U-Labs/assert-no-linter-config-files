"""Integration tests for the CLI on a Python that has no tomllib."""

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

from assert_no_linter_config_files import cli, scanner


@pytest.fixture
def cli_without_tomllib() -> Iterator[ModuleType]:
    """Reload the scanner and the CLI with tomllib unimportable."""
    with patch.dict(sys.modules, {"tomllib": None}):
        importlib.reload(scanner)
        yield importlib.reload(cli)
    importlib.reload(scanner)
    importlib.reload(cli)


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
