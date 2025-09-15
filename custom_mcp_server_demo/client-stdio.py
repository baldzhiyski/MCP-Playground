import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Resolve server.py next to this file, avoiding issues with spaces in paths
SERVER = Path(__file__).with_name("server.py")

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,           # use the SAME interpreter as PyCharm/venv
        args=[str(SERVER)],               # absolute path to server.py
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            result = await session.call_tool("add", arguments={"a": 2, "b": 3})
            print(f"2 + 3 = {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
