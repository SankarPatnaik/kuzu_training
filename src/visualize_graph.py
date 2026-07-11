"""Create an interactive HTML visualization of the built Kuzu graph.

Run after building the DB:
    python src/build_graph.py --reset
    python src/visualize_graph.py
"""
from __future__ import annotations

import argparse
import html
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import kuzu
import networkx as nx
from pyvis.network import Network

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "output" / "policy_context_graph"
DEFAULT_OUTPUT = ROOT / "output" / "policy_context_graph.html"


@dataclass(frozen=True)
class NodeSpec:
    table: str
    key: str
    label: str
    title_fields: tuple[str, ...]


@dataclass(frozen=True)
class RelSpec:
    table: str
    source_table: str
    source_key: str
    target_table: str
    target_key: str
    title_fields: tuple[str, ...] = ()


NODE_SPECS = (
    NodeSpec("PolicyDocument", "document_id", "title", ("source", "region", "client_type", "risk_rating", "version", "effective_date", "text_summary")),
    NodeSpec("Chunk", "chunk_id", "section", ("document_id", "sequence", "token_count", "text")),
    NodeSpec("Country", "code", "name", ("region",)),
    NodeSpec("ClientType", "client_type_id", "name", ("description",)),
    NodeSpec("RiskLevel", "risk_id", "name", ("score",)),
    NodeSpec("Topic", "topic_id", "name", ("description",)),
    NodeSpec("Requirement", "requirement_id", "requirement_id", ("priority", "region", "client_type", "risk_rating", "normalized_question", "description")),
    NodeSpec("Control", "control_id", "name", ("control_type", "severity", "description")),
    NodeSpec("System", "system_id", "name", ("system_type", "owner", "description")),
    NodeSpec("UseCase", "use_case_id", "name", ("business_goal", "owner", "maturity")),
    NodeSpec("UserQuery", "query_id", "query_id", ("user_role", "question", "timestamp")),
    NodeSpec("RetrievalContext", "context_id", "context_id", ("query_id", "strategy", "rank", "summary")),
    NodeSpec("Answer", "answer_id", "answer_id", ("query_id", "summary", "confidence")),
)

REL_SPECS = (
    RelSpec("HAS_CHUNK", "PolicyDocument", "document_id", "Chunk", "chunk_id", ("position",)),
    RelSpec("APPLIES_TO_COUNTRY", "PolicyDocument", "document_id", "Country", "code", ("rule",)),
    RelSpec("APPLIES_TO_CLIENT_TYPE", "PolicyDocument", "document_id", "ClientType", "client_type_id", ("rule",)),
    RelSpec("APPLIES_TO_RISK", "PolicyDocument", "document_id", "RiskLevel", "risk_id", ("rule",)),
    RelSpec("MENTIONS_TOPIC", "Chunk", "chunk_id", "Topic", "topic_id", ("weight",)),
    RelSpec("GENERATES_REQUIREMENT", "PolicyDocument", "document_id", "Requirement", "requirement_id", ("confidence",)),
    RelSpec("REQUIREMENT_FROM_CHUNK", "Requirement", "requirement_id", "Chunk", "chunk_id", ("evidence_score",)),
    RelSpec("MAPPED_TO_CONTROL", "Requirement", "requirement_id", "Control", "control_id", ("mapping_type",)),
    RelSpec("IMPLEMENTED_IN", "Requirement", "requirement_id", "System", "system_id", ("implementation_status",)),
    RelSpec("DEPENDS_ON", "Requirement", "requirement_id", "Requirement", "requirement_id", ("dependency_type",)),
    RelSpec("USE_CASE_USES_DOCUMENT", "UseCase", "use_case_id", "PolicyDocument", "document_id", ("usage_type",)),
    RelSpec("USE_CASE_USES_SYSTEM", "UseCase", "use_case_id", "System", "system_id", ("usage_type",)),
    RelSpec("QUERY_RETRIEVES_CONTEXT", "UserQuery", "query_id", "RetrievalContext", "context_id", ("latency_ms",)),
    RelSpec("CONTEXT_USES_CHUNK", "RetrievalContext", "context_id", "Chunk", "chunk_id", ("rank",)),
    RelSpec("CONTEXT_SUPPORTS_REQUIREMENT", "RetrievalContext", "context_id", "Requirement", "requirement_id", ("rank",)),
    RelSpec("ANSWER_USES_CONTEXT", "Answer", "answer_id", "RetrievalContext", "context_id", ("groundedness_score",)),
)


GROUP_COLORS = {
    "PolicyDocument": "#4C78A8",
    "Chunk": "#72B7B2",
    "Country": "#54A24B",
    "ClientType": "#B279A2",
    "RiskLevel": "#E45756",
    "Topic": "#F58518",
    "Requirement": "#EECA3B",
    "Control": "#9D755D",
    "System": "#59A14F",
    "UseCase": "#FF9DA6",
    "UserQuery": "#76B7B2",
    "RetrievalContext": "#AF7AA1",
    "Answer": "#BAB0AC",
}


def node_id(table: str, key: Any) -> str:
    return f"{table}:{key}"


def escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def result_rows(result: Any) -> list[dict[str, Any]]:
    return result.get_as_df().to_dict(orient="records")


def tooltip(title: str, properties: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><th>{escape(key)}</th><td>{escape(value)}</td></tr>"
        for key, value in properties.items()
        if value is not None and value != ""
    )
    return f"<strong>{escape(title)}</strong><table>{rows}</table>"


def load_nodes(conn: "kuzu.Connection", graph: nx.MultiDiGraph) -> None:
    for spec in NODE_SPECS:
        fields = list(dict.fromkeys([spec.key, spec.label, *spec.title_fields]))
        query = f"MATCH (n:{spec.table}) RETURN " + ", ".join(f"n.{field} AS {field}" for field in fields)
        for row in result_rows(conn.execute(query)):
            key = row[spec.key]
            label = row.get(spec.label) or key
            title_props = {spec.key: key, **{field: row.get(field) for field in spec.title_fields}}
            graph.add_node(
                node_id(spec.table, key),
                label=str(label),
                title=tooltip(spec.table, title_props),
                group=spec.table,
            )


def load_edges(conn: "kuzu.Connection", graph: nx.MultiDiGraph) -> None:
    for spec in REL_SPECS:
        rel_fields = ", ".join(f"rel.{field} AS {field}" for field in spec.title_fields)
        rel_projection = f", {rel_fields}" if rel_fields else ""
        query = f"""
        MATCH (source:{spec.source_table})-[rel:{spec.table}]->(target:{spec.target_table})
        RETURN source.{spec.source_key} AS source_key,
               target.{spec.target_key} AS target_key{rel_projection}
        """
        for row in result_rows(conn.execute(query)):
            properties = {field: row.get(field) for field in spec.title_fields}
            graph.add_edge(
                node_id(spec.source_table, row["source_key"]),
                node_id(spec.target_table, row["target_key"]),
                label=spec.table,
                title=tooltip(spec.table, properties),
                arrows="to",
            )


def build_network(graph: nx.MultiDiGraph, height: str) -> Network:
    network = Network(
        height=height,
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#1f2937",
        notebook=False,
        cdn_resources="in_line",
    )
    network.barnes_hut(gravity=-16000, central_gravity=0.25, spring_length=180, spring_strength=0.02)

    degrees = dict(graph.degree())
    for node, data in graph.nodes(data=True):
        group = data["group"]
        degree = degrees.get(node, 0)
        network.add_node(
            node,
            label=data["label"],
            title=data["title"],
            group=group,
            color=GROUP_COLORS.get(group, "#9CA3AF"),
            size=14 + min(degree, 8) * 3,
        )

    for source, target, data in graph.edges(data=True):
        network.add_edge(
            source,
            target,
            label=data["label"],
            title=data["title"],
            arrows=data["arrows"],
            font={"size": 9, "align": "middle"},
            color={"color": "#9CA3AF", "highlight": "#374151"},
        )

    network.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          },
          "physics": {
            "stabilization": {
              "enabled": true,
              "iterations": 250
            }
          },
          "edges": {
            "smooth": {
              "type": "dynamic"
            }
          }
        }
        """
    )
    return network


def write_visualization(db_path: Path, output_path: Path, height: str) -> tuple[int, int]:
    if not db_path.exists():
        raise SystemExit(f"Database not found at {db_path}. Run python src/build_graph.py --reset first.")

    conn = kuzu.Connection(kuzu.Database(str(db_path)))
    graph = nx.MultiDiGraph()
    load_nodes(conn, graph)
    load_edges(conn, graph)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    network = build_network(graph, height)
    network.write_html(str(output_path), notebook=False, open_browser=False)
    return graph.number_of_nodes(), graph.number_of_edges()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to the built Kuzu database")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="HTML file to create")
    parser.add_argument("--height", default="850px", help="Viewer height, for example 700px or 100vh")
    args = parser.parse_args()

    nodes, edges = write_visualization(args.db, args.output, args.height)
    print(f"Wrote {args.output} with {nodes} nodes and {edges} edges.")


if __name__ == "__main__":
    main()
