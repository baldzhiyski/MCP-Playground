import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables (API keys, etc.)
load_dotenv("../.env")


class MCPOpenAIClient:
    """Client for interacting with OpenAI models using MCP tools over Streamable HTTP."""

    def __init__(self, model: str = "gpt-4o"):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai_client = AsyncOpenAI()
        self.model = model

        # streamable-http specifics
        self._get_session_id = None  # callable returned by streamablehttp_client

    async def connect_to_server_http(self, base_url: str = "http://localhost:8050/mcp"):
        """
        Connect to an MCP server via Streamable HTTP.
        The server must already be running and exposing the /mcp endpoint.
        """
        # Establish transport; returns (read_stream, write_stream, get_session_id)
        read, write, get_session_id = await self.exit_stack.enter_async_context(
            streamablehttp_client(base_url)
        )
        self._get_session_id = get_session_id

        # Open MCP session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        # Initialize
        await self.session.initialize()

        # Optional: show session id (useful for resuming/diagnostics)
        try:
            sid = self._get_session_id()
            if sid:
                print(f"[mcp] Connected (session: {sid})")
        except Exception:
            pass

        # List tools for visibility
        tools_result = await self.session.list_tools()
        print("\nConnected to server with tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Return MCP tools in OpenAI function-tool format."""
        assert self.session, "Not connected"
        tools_result = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,  # JSON Schema from MCP
                },
            }
            for tool in tools_result.tools
        ]

    async def process_query(self, query: str) -> str:
        """Send a query to OpenAI with MCP tools available; execute tool calls and return final answer."""
        assert self.session, "Not connected"
        tools = await self.get_mcp_tools()

        # First pass: let the model decide which tool(s) to call
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message

        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": query},
            assistant_message,
        ]

        # Handle tool calls
        if getattr(assistant_message, "tool_calls", None):
            for call in assistant_message.tool_calls:
                result = await self.session.call_tool(
                    call.function.name,
                    arguments=json.loads(call.function.arguments or "{}"),
                )

                # Append tool result for the model to see
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": (result.content[0].text if result.content else ""),
                    }
                )

            # Second pass: produce the final answer without more tools
            final = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="none",
            )
            return final.choices[0].message.content or ""

        # No tool calls—return assistant’s direct reply
        return assistant_message.content or ""

    async def cleanup(self):
        await self.exit_stack.aclose()  # closes MCP session + transport (LIFO)
        await self.openai_client.close()  # close httpx async client


async def main():
    client = MCPOpenAIClient()
    try:
        await client.connect_to_server_http("http://localhost:8050/mcp")
        query = "What is our company's vacation policy?"
        print(f"\nQuery: {query}")
        answer = await client.process_query(query)
        print(f"\nResponse: {answer}")
    finally:
        # Ensures streamablehttp_client, ClientSession, and OpenAI client are closed
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
