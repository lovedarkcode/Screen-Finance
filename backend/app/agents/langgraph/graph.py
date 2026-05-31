"""Top-level LangGraph state graph definition."""
from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    symbol: str
    question: str
    context: list[dict]
    answer: str


def build_graph():
    """Return a compiled LangGraph workflow.

    Stub: wire up StateGraph(AgentState) with nodes/edges from the
    sibling `nodes/` and `edges/` modules.
    """
    return None
