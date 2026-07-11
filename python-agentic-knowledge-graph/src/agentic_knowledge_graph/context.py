"""GraphRAG retrieval and context formatting."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .db import QueryTable, connect, execute
from .domains import DomainSpec, QuerySpec, get_domain


@dataclass(frozen=True)
class RetrievalContext:
    domain: str
    question: str
    query_number: int
    query_title: str
    cypher: str
    table: QueryTable

    def as_prompt_context(self) -> str:
        evidence = self.table.to_text(max_rows=30)
        return (
            f"DOMAIN: {self.domain}\n"
            f"QUESTION: {self.question}\n"
            f"RETRIEVAL QUERY: {self.query_title}\n"
            f"CYPHER: {self.cypher}\n"
            f"GRAPH EVIDENCE:\n{evidence}\n"
            "INSTRUCTION: Answer only from the graph evidence. State when evidence is insufficient."
        )


def select_query(spec: DomainSpec, question: str) -> tuple[int, QuerySpec]:
    text = question.lower()
    rules: dict[str, tuple[tuple[str, ...], int]] = {
        "yoga": (("beginner", "easy"), 9),
        "fraud": (("high confidence", "confidence"), 5),
        "cycle": (("high risk", "risk"), 10),
        "migration": (("efficiency", "fast"), 10),
        "professional": (("achievement", "award"), 6),
    }
    domain_rules = rules.get(spec.name)
    if domain_rules and any(keyword in text for keyword in domain_rules[0]):
        number = domain_rules[1]
        return number, spec.queries[number - 1]

    keyword_to_query = {
        "benefit": 2,
        "flexibility": 2,
        "balance": 2,
        "strength": 2,
        "body": 3,
        "advanced": 4,
        "instructor": 6,
        "studio": 7,
        "indicator": 2,
        "source": 4,
        "coverage": 10,
        "two-step": 3,
        "three-step": 4,
        "four-step": 5,
        "route": 8,
        "season": 7,
        "environment": 6,
        "related": 3,
        "organization": 4,
        "location": 5,
        "skill": 10,
        "expert": 10,
    }
    for keyword, number in keyword_to_query.items():
        if keyword in text and number <= len(spec.queries):
            return number, spec.queries[number - 1]
    number = spec.default_query
    return number, spec.queries[number - 1]


def retrieve_context(question: str, domain: str, database_path: Path) -> RetrievalContext:
    spec = get_domain(domain)
    query_number, query = select_query(spec, question)
    _database, connection = connect(database_path)
    table = execute(connection, query.cypher)
    return RetrievalContext(domain, question, query_number, query.title, query.cypher, table)
