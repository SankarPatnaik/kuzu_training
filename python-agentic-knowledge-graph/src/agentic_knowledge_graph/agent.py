"""A deliberately small, explainable graph agent."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .context import RetrievalContext, retrieve_context
from .domains import DOMAINS


@dataclass(frozen=True)
class AgentResponse:
    domain: str
    answer: str
    context: str
    query_number: int
    evidence_rows: int


class GraphAgent:
    """Observe → choose domain → retrieve graph evidence → answer."""

    def __init__(self, database_root: Path = Path("output"), answer_generator: Callable[[RetrievalContext], str] | None = None) -> None:
        self.database_root = database_root
        self.answer_generator = answer_generator or self._grounded_summary

    def choose_domain(self, question: str) -> str:
        text = question.lower()
        scored = {name: sum(1 for keyword in spec.keywords if keyword in text) for name, spec in DOMAINS.items()}
        best_name, best_score = max(scored.items(), key=lambda item: item[1])
        return "professional" if best_score == 0 else best_name

    def ask(self, question: str, domain: str | None = None) -> AgentResponse:
        selected_domain = domain or self.choose_domain(question)
        database_path = self.database_root / f"{selected_domain}.kuzu"
        if not database_path.exists():
            raise FileNotFoundError(
                f"Database does not exist: {database_path}. Build it first with 'akg build {selected_domain} --reset'."
            )
        context = retrieve_context(question, selected_domain, database_path)
        answer = self.answer_generator(context)
        return AgentResponse(selected_domain, answer, context.as_prompt_context(), context.query_number, len(context.table.rows))

    @staticmethod
    def _grounded_summary(context: RetrievalContext) -> str:
        if not context.table.rows:
            return "The graph returned no evidence for this question."
        sample = context.table.rows[:5]
        lines = [f"The agent used '{context.query_title}' and found {len(context.table.rows)} evidence row(s)."]
        lines.extend("- " + " | ".join(str(value) for value in row) for row in sample)
        if len(context.table.rows) > len(sample):
            lines.append(f"- {len(context.table.rows) - len(sample)} additional row(s) are available.")
        lines.append("This answer is grounded only in the retrieved graph rows shown above.")
        return "\n".join(lines)
