"""CLI entry point: chat with the Snowflake Text2SQL agent."""

from __future__ import annotations

import asyncio
import logging
import shutil
import sys
from pathlib import Path

import typer
from langchain_mcp_adapters.client import MultiServerMCPClient
from rich.console import Console
from rich.markdown import Markdown

from .agent import create_text2sql_agent
from .config import Settings, load_settings
from .tools import make_execute_sql_tool

app = typer.Typer(help="Snowflake Text2SQL agent for the neocarta workshop.")
console = Console()
logger = logging.getLogger(__name__)


def _mcp_command() -> str:
    """Locate neocarta-mcp next to the running interpreter, else on PATH."""
    local = Path(sys.executable).parent / "neocarta-mcp"
    if local.exists():
        return str(local)
    return shutil.which("neocarta-mcp") or "neocarta-mcp"


async def _chat(settings: Settings, question: str | None) -> None:
    client = MultiServerMCPClient(
        {
            "sql_metadata_graph": {
                "transport": "stdio",
                "command": _mcp_command(),
                "args": [],
                "env": settings.mcp_env,
            }
        }
    )
    tools = list(await client.get_tools(server_name="sql_metadata_graph"))
    tools.append(make_execute_sql_tool(settings.snowflake, settings.row_limit))
    console.print(f"🔍 Tools: {', '.join(t.name for t in tools)}")
    agent = create_text2sql_agent(tools, settings)
    config = {"configurable": {"thread_id": "workshop"}}

    async def ask(text: str) -> None:
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": text}]},
            stream_mode="values",
            config=config,
        ):
            msg = chunk["messages"][-1]
            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    console.print(f"🌿 [dim]{tc['name']}({tc['args']})[/dim]")
            elif msg.type == "ai" and msg.content:
                console.print(Markdown(str(msg.content)))

    if question:
        await ask(question)
        return
    console.print("✅ Ready. Ask a question (exit/quit/q to leave).")
    while True:
        text = await asyncio.to_thread(console.input, "[bold]> [/bold]")
        if text.strip().lower() in {"exit", "quit", "q"}:
            break
        if text.strip():
            await ask(text)


@app.command()
def chat(
    question: str = typer.Argument(None, help="One-shot question; omit for chat."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    """Chat with the agent (interactive, or one-shot when QUESTION is given)."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    if not debug:  # keep third-party chatter out of the workshop transcript
        for noisy in ("LiteLLM", "litellm", "snowflake", "httpx", "mcp"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
    settings = load_settings()
    asyncio.run(_chat(settings, question))


if __name__ == "__main__":
    app()
