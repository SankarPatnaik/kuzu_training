"""Validate all datasets before loading them into Kuzu."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .domains import DOMAINS, DomainSpec
from .loader import DEFAULT_DATA_ROOT, load_dataset


@dataclass(frozen=True)
class ValidationIssue:
    domain: str
    message: str


def validate_domain(spec: DomainSpec, data_root: Path = DEFAULT_DATA_ROOT) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    dataset = load_dataset(spec.name, data_root)
    nodes = dataset.get("nodes", {})
    relationships = dataset.get("relationships", {})

    key_sets: dict[str, set[object]] = {}
    for node_spec in spec.nodes:
        rows = nodes.get(node_spec.name)
        if rows is None:
            issues.append(ValidationIssue(spec.name, f"Missing node dataset: {node_spec.name}"))
            continue
        keys: set[object] = set()
        required_columns = {name for name, _kind in node_spec.columns}
        for index, row in enumerate(rows, start=1):
            missing = required_columns - set(row)
            if missing:
                issues.append(ValidationIssue(spec.name, f"{node_spec.name} row {index} missing {sorted(missing)}"))
            key = row.get(node_spec.primary_key)
            if key in keys:
                issues.append(ValidationIssue(spec.name, f"Duplicate {node_spec.name} key: {key}"))
            keys.add(key)
        key_sets[node_spec.name] = keys

    for rel_spec in spec.relationships:
        rows = relationships.get(rel_spec.name)
        if rows is None:
            issues.append(ValidationIssue(spec.name, f"Missing relationship dataset: {rel_spec.name}"))
            continue
        expected_properties = {name for name, _kind in rel_spec.columns}
        for index, row in enumerate(rows, start=1):
            if row.get("from") not in key_sets.get(rel_spec.from_node, set()):
                issues.append(ValidationIssue(spec.name, f"{rel_spec.name} row {index} has unknown source {row.get('from')}"))
            if row.get("to") not in key_sets.get(rel_spec.to_node, set()):
                issues.append(ValidationIssue(spec.name, f"{rel_spec.name} row {index} has unknown target {row.get('to')}"))
            properties = row.get("properties", {})
            missing = expected_properties - set(properties)
            if missing:
                issues.append(ValidationIssue(spec.name, f"{rel_spec.name} row {index} missing properties {sorted(missing)}"))
    return issues


def validate_all(data_root: Path = DEFAULT_DATA_ROOT) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for spec in DOMAINS.values():
        issues.extend(validate_domain(spec, data_root))
    return issues
