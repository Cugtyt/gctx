"""Pytest configuration and fixtures."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from pytest import MonkeyPatch


@pytest.fixture
def temp_gnote_home(monkeypatch: MonkeyPatch) -> Generator[Path]:
    """Create a temporary .gnote directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gnote_home = Path(tmpdir) / ".gnote"
        gnote_home.mkdir()
        monkeypatch.setenv("HOME", tmpdir)
        monkeypatch.setenv("USERPROFILE", tmpdir)
        yield gnote_home
        if gnote_home.exists():
            shutil.rmtree(gnote_home, ignore_errors=True)
