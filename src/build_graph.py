"""Build the KuzuDB policy knowledge graph and context graph from CSV files.

Usage:
    python src/build_graph.py --reset
    python src/build_graph.py --db ./policy_context_graph
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

try:
    import kuzu
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Kuzu Python package is not installed. Run: pip install -r requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA_FILE = ROOT / "schema" / "schema.cypher"
DEFAULT_DB = ROOT / "output" / "policy_context_graph"

NODE_LOADS = {
    "PolicyDocument": "policy_documents.csv",
    "Chunk": "chunks.csv",
    "Country": "countries.csv",
    "ClientType": "client_types.csv",
    "RiskLevel": "risk_levels.csv",
    "Topic": "topics.csv",
    "Requirement": "requirements.csv",
    "Control": "controls.csv",
    "System": "systems.csv",
    "UseCase": "use_cases.csv",
    "UserQuery": "user_queries.csv",
    "RetrievalContext": "retrieval_contexts.csv",
    "Answer": "answers.csv",
}

REL_LOADS = {
    "HAS_CHUNK": "document_has_chunk.csv",
    "APPLIES_TO_COUNTRY": "doc_applies_country.csv",
    "APPLIES_TO_CLIENT_TYPE": "doc_applies_client_type.csv",
    "APPLIES_TO_RISK": "doc_applies_risk.csv",
    "MENTIONS_TOPIC": "chunk_mentions_topic.csv",
    "GENERATES_REQUIREMENT": "doc_generates_requirement.csv",
    "REQUIREMENT_FROM_CHUNK": "requirement_from_chunk.csv",
    "MAPPED_TO_CONTROL": "requirement_mapped_control.csv",
    "IMPLEMENTED_IN": "requirement_implemented_in_system.csv",
    "DEPENDS_ON": "requirement_depends_on.csv",
    "USE_CASE_USES_DOCUMENT": "use_case_uses_document.csv",
    "USE_CASE_USES_SYSTEM": "use_case_uses_system.csv",
    "QUERY_RETRIEVES_CONTEXT": "query_retrieves_context.csv",
    "CONTEXT_USES_CHUNK": "context_uses_chunk.csv",
    "CONTEXT_SUPPORTS_REQUIREMENT": "context_supports_requirement.csv",
    "ANSWER_USES_CONTEXT": "answer_uses_context.csv",
}


def split_cypher_file(text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current))
    return statements


def execute_file(conn: "kuzu.Connection", path: Path) -> None:
    for statement in split_cypher_file(path.read_text()):
        conn.execute(statement)


def copy_table(conn: "kuzu.Connection", table: str, csv_name: str) -> None:
    csv_path = (DATA_DIR / csv_name).as_posix()
    conn.execute(f'COPY {table} FROM "{csv_path}"')


def build(db_path: Path, reset: bool) -> None:
    if reset and db_path.exists():
        shutil.rmtree(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)

    print(f"Creating schema in {db_path} ...")
    execute_file(conn, SCHEMA_FILE)

    print("Loading node tables ...")
    for table, csv_name in NODE_LOADS.items():
        print(f"  COPY {table} <- {csv_name}")
        copy_table(conn, table, csv_name)

    print("Loading relationship tables ...")
    for table, csv_name in REL_LOADS.items():
        print(f"  COPY {table} <- {csv_name}")
        copy_table(conn, table, csv_name)

    print("Graph build complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="KuzuDB output directory")
    parser.add_argument("--reset", action="store_true", help="Delete existing DB directory before build")
    args = parser.parse_args()
    build(args.db, args.reset)
