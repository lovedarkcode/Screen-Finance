"""Task: head-to-head comparison of multiple stocks."""

DESCRIPTION = (
    "Compare the companies {symbols} side-by-side on growth, profitability, "
    "valuation, and risk. Recommend which is most attractive and why."
)
EXPECTED_OUTPUT = "A Markdown comparison table plus a verdict paragraph."


def build_task(symbols: list[str]) -> dict:
    return {
        "description": DESCRIPTION.format(symbols=", ".join(symbols)),
        "expected_output": EXPECTED_OUTPUT,
    }
