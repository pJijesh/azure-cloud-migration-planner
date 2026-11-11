"""Error types. Input problems are collected so the user sees all of them at once."""

from __future__ import annotations


class PlannerError(Exception):
    """Base class for problems the user can fix. The CLI exits with status 2."""

    def __init__(self, problems):
        if isinstance(problems, str):
            problems = [problems]
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


class ValidationError(PlannerError):
    """The inventory, rules, overrides or assumptions file is not usable."""
