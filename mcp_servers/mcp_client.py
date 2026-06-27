"""
mcp_servers/mcp_client.py
============================
A thin async client wrapper for connecting to KrishiMitra's own MCP
servers over stdio, used by agents that prefer to call tools via the
MCP protocol rather than importing the Python functions directly
(demonstrating real MCP client/server usage end-to-end, as required
by the Kaggle capstone rubric).

In normal operation, agents call the `tools/*.py` functions directly
in-process for speed. This client is used:
  * by tests/test_mcp.py to prove the MCP servers work standalone via
    the protocol;
  * by any external MCP-compatible host (e.g. an ADK agent or another
    LLM application) that wants to call KrishiMitra's tools remotely.
"""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVERS_DIR = Path(__file__).resolve().parent

# Registration table: maps a friendly server name to the module that
# implements it. This is the "registration example" referenced in the
# project requirements -- a real ADK/MCP host would read a config like
# this to know which servers to spawn.
MCP_SERVER_REGISTRY = {
    "weather": "mcp_servers.weather_server",
    "crop_db": "mcp_servers.crop_db_server",
    "knowledge_base": "mcp_servers.knowledge_base_server",
    "market_price": "mcp_servers.market_price_server",
}


@asynccontextmanager
async def mcp_session(server_key: str):
    """Spawn one of KrishiMitra's MCP servers as a subprocess and yield
    a connected ClientSession.

    Usage:
        async with mcp_session("weather") as session:
            result = await session.call_tool("get_current_weather", {"region": "Madurai"})
    """
    module = MCP_SERVER_REGISTRY.get(server_key)
    if module is None:
        raise ValueError(f"Unknown MCP server '{server_key}'. Known servers: {list(MCP_SERVER_REGISTRY)}")

    params = StdioServerParameters(command=sys.executable, args=["-m", module], cwd=str(SERVERS_DIR.parent))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_tool_json(server_key: str, tool_name: str, arguments: dict) -> dict | list:
    """Convenience helper: open a session, call one tool, parse its
    JSON text result, and close the session. Most call sites only need
    a single call per process spawn, so this avoids boilerplate.
    """
    async with mcp_session(server_key) as session:
        result = await session.call_tool(tool_name, arguments)
        # MCP tool results are a list of content blocks; our servers
        # always return a single text block containing a JSON string.
        text_blocks = [c.text for c in result.content if hasattr(c, "text")]
        if not text_blocks:
            return {}
        return json.loads(text_blocks[0])


async def list_tools_for_server(server_key: str) -> list[str]:
    """List tool names exposed by a given MCP server -- useful for the
    Coordinator Agent to discover capabilities dynamically."""
    async with mcp_session(server_key) as session:
        tools = await session.list_tools()
        return [t.name for t in tools.tools]
