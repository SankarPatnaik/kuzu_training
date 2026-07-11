"""Run the fraud knowledge-graph demo without opening Jupyter.

This script is useful as a classroom backup: it validates the fraud dataset,
builds the Kuzu database, runs a few teaching queries, and writes an HTML graph
visualization to the output folder.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agentic_knowledge_graph.agent import GraphAgent
from agentic_knowledge_graph.db import connect, execute
from agentic_knowledge_graph.domains import get_domain
from agentic_knowledge_graph.loader import build_domain
from agentic_knowledge_graph.validation import validate_domain
from agentic_knowledge_graph.visualization import write_fraud_graph_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and inspect the fraud knowledge graph demo.")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "output", help="Folder for Kuzu DB and HTML output.")
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Reuse an existing output/fraud.kuzu database instead of rebuilding it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = get_domain("fraud")
    issues = validate_domain(spec)
    if issues:
        for issue in issues:
            print(f"ERROR [{issue.domain}] {issue.message}", file=sys.stderr)
        return 1

    db_path = args.output / "fraud.kuzu"
    if args.keep_existing and not db_path.exists():
        print(f"Cannot keep existing database because it does not exist: {db_path}", file=sys.stderr)
        return 1
    if not args.keep_existing:
        nodes, relationships = build_domain("fraud", db_path, reset=True)
        print(f"Built fraud graph at {db_path}")
        print(f"Loaded {nodes} nodes and {relationships} relationships.")
    else:
        print(f"Using existing fraud graph at {db_path}")

    graph_path = write_fraud_graph_html(args.output / "fraud_knowledge_graph.html")
    print(f"Wrote visualization: {graph_path}")

    _database, connection = connect(db_path)
    for number in (1, 5, 8, 9, 10):
        query = spec.queries[number - 1]
        print(f"\n=== Query {number}: {query.title} ===")
        print(f"Teaching point: {query.teaching_point}")
        print(execute(connection, query.cypher).to_text(max_rows=12))

    agent = GraphAgent(database_root=args.output)
    response = agent.ask("Which fraud detection methods have high confidence?", domain="fraud")
    print("\n=== Agent answer ===")
    print(response.answer)
    print("\nOpen the notebook with:")
    print("python -m jupyter lab notebooks/fraud_knowledge_graph_demo.ipynb")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
