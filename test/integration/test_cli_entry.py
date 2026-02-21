"""Integration tests for module entry point."""

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestModuleEntryPoint:
    """Tests for python -m entry point."""

    def test_module_entry_point(self, tmp_path: Path) -> None:
        """Can run as python -m assert_no_linter_config_files."""
        result = subprocess.run(
            [
                sys.executable, "-m",
                "assert_no_linter_config_files",
                "--linters", "pylint", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    def test_module_entry_point_with_findings_exits_1(
        self, tmp_path: Path
    ) -> None:
        """Module entry point exits 1 when findings exist."""
        (tmp_path / ".pylintrc").touch()
        result = subprocess.run(
            [
                sys.executable, "-m",
                "assert_no_linter_config_files",
                "--linters", "pylint", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1

    def test_module_entry_point_with_findings_outputs_pylint(
        self, tmp_path: Path
    ) -> None:
        """Module entry point outputs pylint when findings exist."""
        (tmp_path / ".pylintrc").touch()
        result = subprocess.run(
            [
                sys.executable, "-m",
                "assert_no_linter_config_files",
                "--linters", "pylint", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "pylint" in result.stdout

    def test_main_module_runpy(self, tmp_path: Path) -> None:
        """Test __main__ module via runpy (in-process execution)."""
        with patch.object(sys, "argv", [
            "assert_no_linter_config_files",
            "--linters", "pylint", str(tmp_path)
        ]):
            with pytest.raises(SystemExit, match="0"):
                runpy.run_module(
                    "assert_no_linter_config_files",
                    run_name="__main__",
                    alter_sys=True
                )
