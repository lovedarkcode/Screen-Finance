"""CrewAI crew orchestration entry point."""
from __future__ import annotations


class Crew:
    """Stub crew. Replace with crewai.Crew when wiring real agents."""

    def __init__(self, agents: list | None = None, tasks: list | None = None) -> None:
        self.agents = agents or []
        self.tasks = tasks or []

    def kickoff(self, inputs: dict | None = None) -> dict:
        return {"inputs": inputs or {}, "result": None}
