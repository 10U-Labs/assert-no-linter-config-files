"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.cli import main


PYPROJECT_MYPY_PYLINT_TOML = """
[tool.mypy]
strict = true

[tool.pylint]
max-line-length = 100
"""

PYPROJECT_MYPY_PYLINT_WITH_PROJECT_TOML = """
[project]
name = "myproject"

[tool.mypy]
strict = true

[tool.pylint]
max-line-length = 100
"""


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


def _run_main(args: list[str]) -> tuple[int, str, str]:
    """Run main() with patched sys.argv and return exit code, stdout, stderr."""
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def mock_print(*print_args: object, **kwargs: object) -> None:
        text = " ".join(str(a) for a in print_args)
        if kwargs.get("file") is sys.stderr:
            stderr_lines.append(text)
        elif kwargs.get("file") is None:
            stdout_lines.append(text)

    with patch("sys.argv", ["prog"] + args):
        with patch("builtins.print", side_effect=mock_print):
            with pytest.raises(SystemExit) as exc_info:
                main()
            code = int(exc_info.value.code or 0)
            return code, "\n".join(stdout_lines), "\n".join(stderr_lines)


@pytest.fixture
def run_main_with_args():
    """Fixture that returns a function to run main() with args."""
    return _run_main


@pytest.fixture
def pyproject_mypy_pylint_content() -> str:
    """TOML content with [tool.mypy] and [tool.pylint] sections."""
    return PYPROJECT_MYPY_PYLINT_TOML


@pytest.fixture
def pyproject_mypy_pylint_with_project_content() -> str:
    """TOML content with [project], [tool.mypy], and [tool.pylint] sections."""
    return PYPROJECT_MYPY_PYLINT_WITH_PROJECT_TOML


@pytest.fixture
def verbose_pylint_mypy_result(
    tmp_path: Path,
) -> tuple[int, str, str]:
    """Run main() with --linters pylint,mypy --verbose on an empty tmp_path."""
    return _run_main([
        "--linters", "pylint,mypy", "--verbose", str(tmp_path)
    ])


@pytest.fixture
def verbose_pylint_result(
    tmp_path: Path,
) -> tuple[int, str, str]:
    """Run main() with --linters pylint --verbose on an empty tmp_path."""
    return _run_main([
        "--linters", "pylint", "--verbose", str(tmp_path)
    ])


@pytest.fixture
def file_instead_of_directory_result(
    tmp_path: Path,
) -> tuple[int, str, str]:
    """Run main() with a file path instead of a directory."""
    file_path = tmp_path / "file.txt"
    file_path.touch()
    return _run_main([
        "--linters", "pylint", str(file_path)
    ])
