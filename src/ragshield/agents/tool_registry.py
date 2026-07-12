"""Tool registry for controlled agent execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ragshield.agents import sandbox_tools


TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "search_docs": sandbox_tools.search_docs,
    "update_ticket": sandbox_tools.update_ticket,
    "send_email": sandbox_tools.send_email,
    "read_secret_store": sandbox_tools.read_secret_store,
}


def get_tool(name: str) -> Callable[..., dict[str, Any]]:
    try:
        return TOOL_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown tool: {name}") from exc
