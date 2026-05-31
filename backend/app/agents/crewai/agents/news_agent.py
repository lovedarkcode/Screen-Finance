"""News agent: aggregates and summarizes recent company / sector news."""

ROLE = "News Researcher"
GOAL = "Surface recent news that materially affects a stock's thesis."
BACKSTORY = "You scan reputable sources and distill what matters for investors."


def build_agent():
    return {"role": ROLE, "goal": GOAL, "backstory": BACKSTORY}
