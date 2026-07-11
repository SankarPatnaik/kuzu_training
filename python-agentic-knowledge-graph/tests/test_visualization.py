from agentic_knowledge_graph.db import QueryTable
from agentic_knowledge_graph.visualization import dataset_graph, fraud_graph_svg, table_to_html


def test_fraud_dataset_graph_contains_expected_counts() -> None:
    nodes, edges = dataset_graph("fraud")
    assert len(nodes) == 21
    assert len(edges) == 28
    assert {"DataSource", "DetectionMethod", "Indicator", "FraudType"} <= {node.kind for node in nodes}


def test_fraud_svg_contains_core_labels() -> None:
    svg = fraud_graph_svg()
    assert "Fraud Detection Knowledge Graph" in svg
    assert "Machine Learning" in svg
    assert "Account Takeover" in svg
    assert "Detects" in svg


def test_table_to_html_escapes_values() -> None:
    table = QueryTable(("name",), (("<script>",),))
    html = table_to_html(table)
    assert "&lt;script&gt;" in html
    assert "<script>" not in html
