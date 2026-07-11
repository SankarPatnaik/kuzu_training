"""Schemas and progressive Cypher queries for all training domains."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class NodeSpec:
    name: str
    primary_key: str
    columns: tuple[tuple[str, str], ...]

    def create_statement(self) -> str:
        fields = ", ".join(f"{name} {kind}" for name, kind in self.columns)
        return f"CREATE NODE TABLE {self.name}({fields}, PRIMARY KEY({self.primary_key}))"


@dataclass(frozen