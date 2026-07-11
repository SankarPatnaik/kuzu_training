"""Create an interactive schema-level knowledge graph.

This view shows node tables as nodes and relationship tables as labeled edges.

Run after building the DB:
    python src/build_graph.py --reset
    python src/visualize_schema.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import kuzu
import networkx as nx
from pyvis.network import Network

from visualize_graph import GROUP_COLORS, NODE_SPECS, REL_SPECS, RelSpec, tooltip

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "output" / "policy_context_graph"
DEFAULT_OUTPUT = ROOT / "output" / "knowledge_graph_schema.html"


def count_query(conn: "kuzu.Connection", query: str) -> int:
    df = conn.execute(query).get_as_df()
    return int(df.iloc[0]["count"])


def node_count(conn: "kuzu.Connection", table: str) -> int:
    return count_query(conn, f"MATCH (n:{table}) RETURN count(n) AS count")


def relationship_count(conn: "kuzu.Connection", spec: RelSpec) -> int:
    query = f"""
    MATCH (source:{spec.source_table})-[rel:{spec.table}]->(target:{spec.target_table})
    RETURN count(rel) AS count
    """
    return count_query(conn, query)


def build_schema_graph(conn: "kuzu.Connection") -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    for spec in NODE_SPECS:
        count = node_count(conn, spec.table)
        fields = (spec.key, spec.label, *spec.title_fields)
        graph.add_node(
            spec.table,
            label=f"{spec.table}\n{count} rows",
            title=tooltip(
                spec.table,
                {
                    "primary_key": spec.key,
                    "display_label": spec.label,
                    "properties": ", ".join(dict.fromkeys(fields)),
                    "row_count": count,
                },
            ),
            group=spec.table,
            count=count,
        )

    for spec in REL_SPECS:
        count = relationship_count(conn, spec)
        graph.add_edge(
            spec.source_table,
            spec.target_table,
            label=f"{spec.table}\n{count}",
            title=tooltip(
                spec.table,
                {
                    "from": spec.source_table,
                    "to": spec.target_table,
                    "source_key": spec.source_key,
                    "target_key": spec.target_key,
                    "properties": ", ".join(spec.title_fields),
                    "row_count": count,
                },
            ),
            arrows="to",
            count=count,
        )

    return graph


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
    network.force_atlas_2based(gravity=-90, central_gravity=0.01, spring_length=170, spring_strength=0.08)

    for node, data in graph.nodes(data=True):
        group = data["group"]
        count = data["count"]
        network.add_node(
            node,
            label=data["label"],
            title=data["title"],
            group=group,
            color=GROUP_COLORS.get(group, "#9CA3AF"),
            shape="box",
            margin=12,
            size=18 + min(count, 10),
            font={"size": 18, "face": "arial"},
        )

    for source, target, data in graph.edges(data=True):
        network.add_edge(
            source,
            target,
            label=data["label"],
            title=data["title"],
            arrows=data["arrows"],
            width=1 + min(data["count"], 8) * 0.35,
            font={"size": 10, "align": "middle"},
            color={"color": "#6B7280", "highlight": "#111827"},
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
              "iterations": 350
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

    conn = kuzu.Connection(kuzu.Database(str(db_path), read_only=True))
    graph = build_schema_graph(conn)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    network = build_network(graph, height)
    network.write_html(str(output_path), notebook=False, open_browser=False)
    return graph.number_of_nodes(), graph.number_of_edges()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to the built Kuzu database")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="HTML file to create")
    parser.add_argument("--height", default="760px", help="Viewer height, for example 700px or 100vh")
    args = parser.parse_args()

    nodes, edges = write_visualization(args.db, args.output, args.height)
    print(f"Wrote {args.output} with {nodes} node types and {edges} relationship types.")


if __name__ == "__main__":
    main()
