"""Pytest configuration and shared fixtures."""

import sys
from unittest.mock import patch

import pytest

from assert_no_linter_config_files.cli import main


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


@pytest.fixture
def run_main_with_args():
    """Fixture that returns a function to run main() with args."""
    def _run(args: list[str]) -> tuple[int, str, str]:
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
    return _run
