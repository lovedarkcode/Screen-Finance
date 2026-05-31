"""Task: summarize a long report (10-K, transcript, presentation)."""

DESCRIPTION = (
    "Summarize the report at {url} for {symbol}. Extract key financials, "
    "guidance, risks, and management commentary. Keep it under 500 words."
)
EXPECTED_OUTPUT = "A concise Markdown summary with bullet-pointed highlights."


def build_task(symbol: str, url: str) -> dict:
    return {
        "description": DESCRIPTION.format(symbol=symbol, url=url),
        "expected_output": EXPECTED_OUTPUT,
    }
