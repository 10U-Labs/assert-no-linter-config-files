"""Fixtures shared by the integration tests."""

import importlib
import sys
from collections.abc import Iterator
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
