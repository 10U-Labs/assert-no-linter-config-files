"""Unit tests for the __main__ module."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestMainModule:
    """Tests for the __main__.py entry point."""

    def test_module_runs_main(self, tmp_path: Path) -> None:
        """python -m assert_no_linter_config_files runs main()."""
        env = os.environ.copy()
        src_path = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(src_path.resolve())
        cmd = [sys.executable, "-m", "assert_no_linter_config_files"]
        cmd.extend(["--linters", "mypy", str(tmp_path)])
        result = subprocess.run(cmd, capture_output=True, text=True, env=env,
                                check=False)
        assert result.returncode == 0

    def test_module_imports_and_calls_main(self):
        """The __main__ module imports and calls main."""
        import importlib

        with patch(
            "assert_no_linter_config_files.cli.main",
            side_effect=SystemExit(0)
        ) as mock_main:
            with pytest.raises(SystemExit):
                import assert_no_linter_config_files.__main__
                importlib.reload(assert_no_linter_config_files.__main__)
            mock_main.assert_called()
