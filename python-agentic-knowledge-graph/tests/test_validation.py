from agentic_knowledge_graph.domains import DOMAINS
from agentic_knowledge_graph.validation import validate_all


def test_all_expected_domains_exist() -> None:
    assert set(DOMAINS) == {"yoga", "fraud", "cycle", "migration", "professional"}
    assert all(len(domain.queries) == 10 for domain in DOMAINS.values())


def test_all_datasets_are_valid() -> None:
    assert validate_all() == []
