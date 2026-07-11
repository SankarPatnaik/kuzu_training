from agentic_knowledge_graph.cycle_detection import find_cycles


def test_finds_four_node_cycle_once() -> None:
    adjacency = {"A": ["B", "E"], "B": ["C"], "C": ["D"], "D": ["A"], "E": []}
    assert find_cycles(adjacency) == [["A", "B", "C", "D", "A"]]


def test_acyclic_graph_returns_empty_list() -> None:
    assert find_cycles({"A": ["B"], "B": ["C"], "C": []}) == []
