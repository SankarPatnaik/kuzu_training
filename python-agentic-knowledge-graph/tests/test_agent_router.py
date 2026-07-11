from agentic_knowledge_graph.agent import GraphAgent
from agentic_knowledge_graph.context import select_query
from agentic_knowledge_graph.domains import get_domain


def test_domain_router() -> None:
    agent = GraphAgent()
    assert agent.choose_domain("Find circular account transfers for AML") == "cycle"
    assert agent.choose_domain("Which pose improves flexibility?") == "yoga"
    assert agent.choose_domain("Which engineer has Python skills?") == "professional"


def test_query_router() -> None:
    number, query = select_query(get_domain("cycle"), "Show the four-step cycle")
    assert number == 5
    assert query.title == "Four-step cycles"
