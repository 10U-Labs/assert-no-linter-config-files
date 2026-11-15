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

    @pytest.fixture
    def module_entry_point_with_findings_result(
        self, tmp_path: Path
    ) -> subprocess.CompletedProcess[str]:
        """Run python -m on a directory holding a .pylintrc."""
        (tmp_path / ".pylintrc").touch()
        return subprocess.run(
            [
                sys.executable, "-m",
                "assert_no_linter_config_files",
                "--linters", "pylint", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_module_entry_point_with_findings_exits_1(
        self,
        module_entry_point_with_findings_result: (
            subprocess.CompletedProcess[str]
        ),
    ) -> None:
        """Module entry point exits 1 when findings exist."""
        assert module_entry_point_with_findings_result.returncode == 1

    def test_module_entry_point_with_findings_outputs_pylint(
        self,
        module_entry_point_with_findings_result: (
            subprocess.CompletedProcess[str]
        ),
    ) -> None:
        """Module entry point outputs pylint when findings exist."""
        assert "pylint" in module_entry_point_with_findings_result.stdout

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
