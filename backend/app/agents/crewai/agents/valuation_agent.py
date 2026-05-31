"""Valuation agent: DCF, multiples, peer comparison."""

ROLE = "Valuation Specialist"
GOAL = "Estimate fair value using DCF, multiples, and peer comparison."
BACKSTORY = "You build defensible valuation models and stress-test assumptions."


def build_agent():
    return {"role": ROLE, "goal": GOAL, "backstory": BACKSTORY}
