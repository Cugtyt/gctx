"""Tests for git_manager module."""

from pathlib import Path

from gnote.config_manager import ConfigManager
from gnote.git_manager import GitContextManager
from pytest import MonkeyPatch


def test_git_manager_initialization(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test GitContextManager initialization."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitContextManager("test") as manager:
        assert manager.branch == "test"
        assert (temp_gnote_home / "repo" / ".git").exists()


def test_git_manager_write_and_read(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test writing and reading context."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitContextManager("test") as manager:
        content = "Test context content"
        commit_sha = manager.write_context(content, "Test commit")

        assert len(commit_sha) > 0

        read_content = manager.read_context()
        assert read_content == content


def test_git_manager_append(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test appending to context."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitContextManager("test") as manager:
        initial_content = "Initial content"
        manager.write_context(initial_content, "Initial commit")

        append_text = "Appended text"
        manager.append_context(append_text, "Append commit")

        read_content = manager.read_context()
        expected = "Initial content\nAppended text"
        assert read_content.replace("\r\n", "\n") == expected


def test_git_manager_history(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test getting commit history."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Content 1", "Commit 1")
        manager.write_context("Content 2", "Commit 2")
        manager.write_context("Content 3", "Commit 3")

        history = manager.get_history(10, None)

        assert len(history.commits) >= 3
        assert history.commits[0].message == "Commit 3"
        assert history.commits[1].message == "Commit 2"
        assert history.commits[2].message == "Commit 1"


def test_git_manager_snapshot(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test getting snapshot from commit."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitContextManager("test") as manager:
        content1 = "Content 1"
        sha1 = manager.write_context(content1, "Commit 1")

        manager.write_context("Content 2", "Commit 2")

        snapshot = manager.get_snapshot(sha1)
        assert snapshot.content == content1
        assert snapshot.commit_message == "Commit 1"


def test_git_manager_search_history(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test searching commit history by keywords."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitContextManager("test") as manager:
        # Create commits with different content and messages
        manager.write_context("Python code here", "Add python implementation")
        manager.write_context("JavaScript code here", "Add javascript feature")
        manager.write_context("Rust code here", "Add rust module")
        manager.write_context("More python examples", "Update documentation")

        # Search for "python" - should match commit message and content
        result = manager.search_history(["python"])
        assert result.total_matches == 2
        assert any("python" in c.message.lower() for c in result.commits)

        # Search for "javascript"
        result = manager.search_history(["javascript"])
        assert result.total_matches == 1
        assert "javascript" in result.commits[0].message.lower()

        # Search for multiple keywords
        result = manager.search_history(["python", "rust"])
        assert result.total_matches == 3

        # Search with no keywords
        result = manager.search_history([])
        assert result.total_matches == 0

        # Search with limit
        result = manager.search_history(["code"], limit=2)
        assert len(result.commits) <= 2
