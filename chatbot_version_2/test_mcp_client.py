import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_app.run_server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # result = await session.list_tools()

            # print(f"\nTotal tools discovered: {len(result.tools)}")

            # for tool in result.tools:
            #     print(f"- {tool.name}")
            result = await session.call_tool(
                "get_doctors",
                arguments={},
            )

            print("\nTool execution error:", result.isError)
            print("Tool result:")

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())