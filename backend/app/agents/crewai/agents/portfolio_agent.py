"""Portfolio agent: tracks holdings, suggests rebalances, flags concentration."""

ROLE = "Portfolio Manager"
GOAL = "Optimize a user's portfolio for risk-adjusted returns."
BACKSTORY = "You monitor holdings, watch concentrations, and propose rebalances."


def build_agent():
    return {"role": ROLE, "goal": GOAL, "backstory": BACKSTORY}
