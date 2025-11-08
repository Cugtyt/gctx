"""Tests for MCP server tools."""

import asyncio
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from gctx.config import GctxConfig
from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager
from gctx.mcp import setup_mcp


def test_mcp_setup(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server setup and read_context tool."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    initial_content = "Initial test content"
    with GitContextManager("test") as manager:
        manager.write_context(initial_content, "Initial commit")

    mcp = setup_mcp("test")

    assert mcp is not None
    assert mcp.name == "gctx"

    result = asyncio.run(mcp._tool_manager._tools["read_context"].fn())
    assert result.success is True
    assert result.content == initial_content
    assert result.token_count > 0
    assert result.error == ""


@pytest.mark.asyncio
async def test_mcp_read_context_tool(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test read_context tool actually works."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    test_content = "Test context content"
    with GitContextManager("test") as manager:
        manager.write_context(test_content, "Initial")

    mcp = setup_mcp("test")
    read_context_tool = mcp._tool_manager._tools["read_context"]
    result = await read_context_tool.fn()

    assert result.success is True
    assert result.content == test_content
    assert result.token_count > 0
    assert result.error == ""


@pytest.mark.asyncio
async def test_mcp_update_context_tool(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test update_context tool actually works."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Initial content", "Initial")

    mcp = setup_mcp("test")
    update_context_tool = mcp._tool_manager._tools["update_context"]

    new_content = "Updated content"
    result = await update_context_tool.fn(new_content, "Update test")

    assert result.success is True
    assert result.new_token_count > 0
    assert result.error == ""

    read_context_tool = mcp._tool_manager._tools["read_context"]
    read_result = await read_context_tool.fn()
    assert read_result.content == new_content


@pytest.mark.asyncio
async def test_mcp_append_to_context_tool(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test append_to_context tool actually works."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    initial_content = "Initial content"
    with GitContextManager("test") as manager:
        manager.write_context(initial_content, "Initial")

    mcp = setup_mcp("test")
    append_context_tool = mcp._tool_manager._tools["append_to_context"]

    append_text = "\nAppended text"
    result = await append_context_tool.fn(append_text, "Append test")

    assert result.success is True
    assert result.token_delta > 0
    assert result.error == ""

    read_context_tool = mcp._tool_manager._tools["read_context"]
    read_result = await read_context_tool.fn()
    assert initial_content in read_result.content
    assert append_text in read_result.content


@pytest.mark.asyncio
async def test_mcp_history_tool(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test get_context_history tool actually works."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Content 1", "First commit")
        manager.write_context("Content 2", "Second commit")
        manager.write_context("Content 3", "Third commit")

    mcp = setup_mcp("test")
    history_tool = mcp._tool_manager._tools["get_context_history"]
    result = await history_tool.fn(limit=10)

    assert result.success is True
    assert len(result.commits) == 4
    assert result.total_commits == 4
    assert result.commits[0].message == "Third commit"
    assert result.commits[1].message == "Second commit"
    assert result.commits[2].message == "First commit"
    assert result.error == ""


@pytest.mark.asyncio
async def test_mcp_search_tool(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test search_context_history tool actually works."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Python code here", "Add Python")
        manager.write_context("JavaScript code here", "Add JavaScript")
        manager.write_context("More Python code", "More Python")

    mcp = setup_mcp("test")
    search_tool = mcp._tool_manager._tools["search_context_history"]
    result = await search_tool.fn(keywords=["Python"], limit=100)

    assert result.success is True
    assert result.total_matches == 2
    assert len(result.commits) == 2
    assert result.error == ""


def test_mcp_setup_with_config_override(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server setup with config override."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Initial content", "Initial")

    custom_config = GctxConfig(token_limit=15000)
    mcp = setup_mcp("test", config_override=custom_config)

    assert mcp is not None
    assert mcp.name == "gctx"

    tool_names = set(mcp._tool_manager._tools.keys())
    expected_tools = {
        "read_context",
        "update_context",
        "append_to_context",
        "get_context_history",
        "get_snapshot",
        "search_context_history",
    }
    assert expected_tools.issubset(tool_names)


def test_mcp_with_different_branches(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server works with different branches."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Master content", "Initial")

    with GitContextManager("develop") as manager:
        manager.write_context("Develop content", "Initial")

    mcp_master = setup_mcp("master")
    assert mcp_master is not None
    assert mcp_master.name == "gctx"

    mcp_develop = setup_mcp("develop")
    assert mcp_develop is not None
    assert mcp_develop.name == "gctx"

    tool_names_master = set(mcp_master._tool_manager._tools.keys())
    tool_names_develop = set(mcp_develop._tool_manager._tools.keys())
    assert tool_names_master == tool_names_develop


def test_mcp_context_manager_cleanup(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that MCP tools properly use context managers."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Test content", "Initial")
        manager.write_context("Update 1", "Update 1")
        manager.write_context("Update 2", "Update 2")

    mcp = setup_mcp("test")

    assert mcp is not None
    assert mcp.name == "gctx"

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "read_context" in tool_names
    assert "get_context_history" in tool_names


def test_mcp_setup_with_guidance_tool_enabled(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test MCP server setup with guidance tool enabled."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Initial content", "Initial")

    mcp = setup_mcp("test", enable_guidance_tool=True)

    assert mcp is not None
    assert mcp.name == "gctx"

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "guidance" in tool_names


def test_mcp_setup_with_guidance_tool_disabled(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test MCP server setup with guidance tool disabled (default)."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Initial content", "Initial")

    mcp = setup_mcp("test", enable_guidance_tool=False)

    assert mcp is not None
    assert mcp.name == "gctx"

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "guidance" not in tool_names
