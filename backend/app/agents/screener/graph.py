"""Bounded parse → validate → execute → format workflow. No autonomous loops."""
import logging
from time import perf_counter
from typing import Any, TypedDict
from langgraph.graph import END, START, StateGraph
from app.schemas.screener import ScreenResponse
from app.services.screener import indexes, parser, query_builder
from app.services.screener.validator import ScreenIssue, validate_screen

logger = logging.getLogger("screen-finance")


class ScreenState(TypedDict, total=False):
    query: str
    market: str | None
    original_query: str | None
    draft: Any
    screen: Any
    session: Any
    page: int
    warnings: list[str]
    result: dict


async def parse(state):
    if state.get("draft") is not None:
        return {}
    try:
        draft = await parser.parse_query(state["query"], market=state["market"]) if state.get("market") else await parser.parse_query(state["query"])
        return {"draft": draft}
    except ScreenIssue as issue:
        return {"result": ScreenResponse(status=issue.status, original_query=state.get("query") or state.get("original_query"), clarification=str(issue)).model_dump(mode="json")}


async def validate(state):
    try:
        draft = state["draft"]
        if state.get("market"):
            # The explicit selector is authoritative even when the model omits it.
            # Source validation below still rejects a conflicting prompt/exchange.
            draft = draft.model_copy(update={"market": state["market"]})
        screen, warnings = validate_screen(draft, state.get("query") or None, market=state.get("market"))
        return {"screen": screen, "warnings": warnings}
    except ScreenIssue as issue:
        return {"result": ScreenResponse(status=issue.status, original_query=state.get("query") or state.get("original_query"), clarification=str(issue)).model_dump(mode="json")}


async def execute(state):
    started = perf_counter()
    session, screen, page = state["session"], state["screen"], state["page"]
    try:
        index_symbols = await indexes.members(session) if screen.index else None
    except ScreenIssue as issue:
        return {"result": ScreenResponse(status=issue.status, original_query=state.get("query") or state.get("original_query"), clarification=str(issue)).model_dump(mode="json")}
    # Read results on every execution: count/max(updated_at) cannot detect all
    # in-place corrections. Parsed requests remain cached independently.
    updated = await query_builder.last_updated(session)
    statement, count, selections = query_builder.statements(screen, page, index_symbols)
    total = (await session.execute(count)).scalar_one()
    rows = (await session.execute(statement)).all()
    universe = await query_builder.universe_count(session, screen.market)
    eligible = await query_builder.eligible_count(session, screen, index_symbols)
    warnings = list(state["warnings"])
    reason, explanation = await query_builder.empty_explanation(session, screen, universe, total, index_symbols) if not rows else (None, None)
    if explanation:
        warnings.append(explanation)
    result = ScreenResponse(status="success", parsed_filters=screen, original_query=state.get("query") or state.get("original_query"), stocks=query_builder.format_rows(rows, screen, selections), total_count=total, page=page, page_size=screen.limit, data_as_of=updated.isoformat() if updated else None, universe_count=universe, eligible_count=eligible, warnings=warnings, empty_reason=reason, explanation=explanation, execution_ms=round((perf_counter() - started) * 1000, 2)).model_dump(mode="json")
    logger.info("Screen completed: market=%s matches=%s page=%s elapsed_ms=%s", screen.market, total, page, result["execution_ms"])
    return {"result": result}


async def format_result(state):
    return {"result": ScreenResponse.model_validate(state["result"]).model_dump(mode="json")}


def build_graph():
    graph = StateGraph(ScreenState)
    for name, node in [("parse", parse), ("validate", validate), ("execute", execute), ("format", format_result)]:
        graph.add_node(name, node)
    graph.add_edge(START, "parse")
    graph.add_conditional_edges("parse", lambda state: "format" if state.get("result") else "validate")
    graph.add_conditional_edges("validate", lambda state: "format" if state.get("result") else "execute")
    graph.add_edge("execute", "format")
    graph.add_edge("format", END)
    return graph.compile()


screener_graph = build_graph()
