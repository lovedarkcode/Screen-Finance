"""SEC filings agent: reads 10-K / 10-Q / 8-K and extracts risks and disclosures."""

ROLE = "SEC Filings Reader"
GOAL = "Extract risks, segment data, and management commentary from filings."
BACKSTORY = "You comb through dense regulatory filings and find what matters."


def build_agent():
    return {"role": ROLE, "goal": GOAL, "backstory": BACKSTORY}
