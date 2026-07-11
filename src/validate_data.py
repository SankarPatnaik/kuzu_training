"""Validate CSV primary keys and relationship references before loading Kuzu."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

NODE_TABLES = {
    "PolicyDocument": ("policy_documents.csv", "document_id"),
    "Chunk": ("chunks.csv", "chunk_id"),
    "Country": ("countries.csv", "code"),
    "ClientType": ("client_types.csv", "client_type_id"),
    "RiskLevel": ("risk_levels.csv", "risk_id"),
    "Topic": ("topics.csv", "topic_id"),
    "Requirement": ("requirements.csv", "requirement_id"),
    "Control": ("controls.csv", "control_id"),
    "System": ("systems.csv", "system_id"),
    "UseCase": ("use_cases.csv", "use_case_id"),
    "UserQuery": ("user_queries.csv", "query_id"),
    "RetrievalContext": ("retrieval_contexts.csv", "context_id"),
    "Answer": ("answers.csv", "answer_id"),
}

RELATIONSHIPS = (
    ("document_has_chunk.csv", "document_id", "PolicyDocument", "chunk_id", "Chunk"),
    ("doc_applies_country.csv", "document_id", "PolicyDocument", "code", "Country"),
    ("doc_applies_client_type.csv", "document_id", "PolicyDocument", "client_type_id", "ClientType"),
    ("doc_applies_risk.csv", "document_id", "PolicyDocument", "risk_id", "RiskLevel"),
    ("chunk_mentions_topic.csv", "chunk_id", "Chunk", "topic_id", "Topic"),
    ("doc_generates_requirement.csv", "document_id", "PolicyDocument", "requirement_id", "Requirement"),
    ("requirement_from_chunk.csv", "requirement_id", "Requirement", "chunk_id", "Chunk"),
    ("requirement_mapped_control.csv", "requirement_id", "Requirement", "control_id", "Control"),
    ("requirement_implemented_in_system.csv", "requirement_id", "Requirement", "system_id", "System"),
    ("requirement_depends_on.csv", "from_requirement_id", "Requirement", "to_requirement_id", "Requirement"),
    ("use_case_uses_document.csv", "use_case_id", "UseCase", "document_id", "PolicyDocument"),
    ("use_case_uses_system.csv", "use_case_id", "UseCase", "system_id", "System"),
    ("query_retrieves_context.csv", "query_id", "UserQuery", "context_id", "RetrievalContext"),
    ("context_uses_chunk.csv", "context_id", "RetrievalContext", "chunk_id", "Chunk"),
    ("context_supports_requirement.csv", "context_id", "RetrievalContext", "requirement_id", "Requirement"),
    ("answer_uses_context.csv", "answer_id", "Answer", "context_id", "RetrievalContext"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValueError(f"Missing file: {path}")
    with path.open(newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def load_keys() -> tuple[dict[str, set[str]], int]:
    keys: dict[str, set[str]] = {}
    node_count = 0
    for table, (csv_name, key_column) in NODE_TABLES.items():
        rows = read_csv(DATA_DIR / csv_name)
        values = [row[key_column] for row in rows]
        duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
        if duplicates:
            raise ValueError(f"{csv_name} has duplicate {key_column} values: {duplicates}")
        keys[table] = set(values)
        node_count += len(values)
    return keys, node_count


def validate_relationships(keys: dict[str, set[str]]) -> int:
    edge_count = 0
    for csv_name, from_column, from_table, to_column, to_table in RELATIONSHIPS:
        rows = read_csv(DATA_DIR / csv_name)
        for line_number, row in enumerate(rows, start=2):
            from_value = row[from_column]
            to_value = row[to_column]
            if from_value not in keys[from_table]:
                raise ValueError(f"{csv_name}:{line_number} references missing {from_table} key {from_value}")
            if to_value not in keys[to_table]:
                raise ValueError(f"{csv_name}:{line_number} references missing {to_table} key {to_value}")
        edge_count += len(rows)
    return edge_count


def main() -> None:
    keys, node_count = load_keys()
    edge_count = validate_relationships(keys)
    csv_count = len(NODE_TABLES) + len(RELATIONSHIPS)
    print(f"Validated {node_count} nodes and {edge_count} relationships across {csv_count} CSV files.")


if __name__ == "__main__":
    main()
