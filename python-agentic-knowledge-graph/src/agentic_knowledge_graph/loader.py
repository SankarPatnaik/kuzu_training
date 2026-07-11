"""Create Kuzu schemas and load the synthetic JSON datasets."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .db import connect
from .domains import DomainSpec, get_domain

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PACKAGE_ROOT / "data"


def cypher_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def property_map(properties: dict[str, Any]) -> str:
    return "{" + ", ".join(f"{key}: {cypher_literal(value)}" for key, value in properties.items()) + "}"


def load_dataset(domain: str, data_root: Path = DEFAULT_DATA_ROOT) -> dict[str, Any]:
    path = data_root / f"{domain}.json"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def create_schema(connection: Any, spec: DomainSpec) -> None:
    for node in spec.nodes:
        connection.execute(node.create_statement())
    for relationship in spec.relationships:
        connection.execute(relationship.create_statement())


def insert_nodes(connection: Any, spec: DomainSpec, dataset: dict[str, Any]) -> int:
    inserted = 0
    for label, rows in dataset["nodes"].items():
        if label not in spec.node_map:
            raise ValueError(f"Dataset contains unknown node label: {label}")
        for row in rows:
            connection.execute(f"CREATE (n:{label} {property_map(row)})")
            inserted += 1
    return inserted


def insert_relationships(connection: Any, spec: DomainSpec, dataset: dict[str, Any]) -> int:
    inserted = 0
    for rel_name, rows in dataset["relationships"].items():
        rel_spec = spec.relationship_map.get(rel_name)
        if rel_spec is None:
            raise ValueError(f"Dataset contains unknown relationship type: {rel_name}")
        from_spec = spec.node_map[rel_spec.from_node]
        to_spec = spec.node_map[rel_spec.to_node]
        for row in rows:
            props = row.get("properties", {})
            rel_props = f" {property_map(props)}" if props else ""
            query = (
                f"MATCH (source:{rel_spec.from_node} "
                f"{{{from_spec.primary_key}: {cypher_literal(row['from'])}}}), "
                f"(target:{rel_spec.to_node} "
                f"{{{to_spec.primary_key}: {cypher_literal(row['to'])}}}) "
                f"CREATE (source)-[:{rel_name}{rel_props}]->(target)"
            )
            connection.execute(query)
            inserted += 1
    return inserted


def build_domain(
    domain: str,
    database_path: Path,
    *,
    reset: bool = False,
    data_root: Path = DEFAULT_DATA_ROOT,
) -> tuple[int, int]:
    spec = get_domain(domain)
    dataset = load_dataset(spec.name, data_root)
    if database_path.exists():
        if not reset:
            raise FileExistsError(
                f"Database already exists: {database_path}. Use reset=True or '--reset'."
            )
        if database_path.is_dir():
            shutil.rmtree(database_path)
        else:
            database_path.unlink()
    _database, connection = connect(database_path)
    create_schema(connection, spec)
    node_count = insert_nodes(connection, spec, dataset)
    relationship_count = insert_relationships(connection, spec, dataset)
    return node_count, relationship_count
