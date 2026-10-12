"""
Manual check of the stdio MCP server (mcp_app/run_server.py).

The stdio server is intentionally LOCKED: a direct MCP client has no trusted
login identity, so every tool call must be refused. Real tool execution goes
through the web API (api/chat.py -> llm/agent.py -> mcp_app/router.py), where
the identity comes from the login session.

Run:  python test_mcp_client.py
Expected: it lists the tools, then prints that get_doctors was REFUSED.
"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> bool:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_app.run_server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"Tools discovered: {len(tools.tools)}")

            result = await session.call_tool("get_doctors", arguments={})
            refused = bool(result.isError)
            print("get_doctors refused (expected):", refused)
            return refused


if __name__ == "__main__":
    sys.exit(0 if asyncio.run(main()) else 1)
