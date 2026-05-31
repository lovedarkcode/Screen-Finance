"""Task: deep-dive analysis of a single stock."""

DESCRIPTION = (
    "Analyze the company {symbol}. Cover business model, financial health, "
    "competitive position, risks, and a 1-year outlook."
)
EXPECTED_OUTPUT = "A structured Markdown report with sections: Summary, Financials, Risks, Outlook."


def build_task(symbol: str) -> dict:
    return {
        "description": DESCRIPTION.format(symbol=symbol),
        "expected_output": EXPECTED_OUTPUT,
    }
