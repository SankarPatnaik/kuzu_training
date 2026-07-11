"""Pure-Python DFS cycle detection for the transaction example."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .db import connect, execute


def canonical_cycle(cycle: list[str]) -> tuple[str, ...]:
    body = cycle[:-1]
    rotations = [tuple(body[index:] + body[:index]) for index in range(len(body))]
    best = min(rotations)
    return (*best, best[0])


def find_cycles(adjacency: dict[str, list[str]], max_length: int = 8) -> list[list[str]]:
    cycles: set[tuple[str, ...]] = set()

    def visit(start: str, current: str, path: list[str], seen: set[str]) -> None:
        if len(path) > max_length:
            return
        for neighbor in adjacency.get(current, []):
            if neighbor == start and len(path) >= 2:
                cycles.add(canonical_cycle([*path, start]))
            elif neighbor not in seen:
                visit(start, neighbor, [*path, neighbor], {*seen, neighbor})

    for node in adjacency:
        visit(node, node, [node], {node})
    return [list(cycle) for cycle in sorted(cycles)]


def graph_cycles(database_path: Path) -> list[list[str]]:
    _database, connection = connect(database_path)
    table = execute(connection, "MATCH (a:Account)-[:Transfers]->(b:Account) RETURN a.account_id, b.account_id")
    adjacency: dict[str, list[str]] = defaultdict(list)
    for source, target in table.rows:
        adjacency[str(source)].append(str(target))
    return find_cycles(dict(adjacency))


def total_cycle_amount(cycle: list[str], transfers: Iterable[tuple[str, str, float]]) -> float:
    amounts = {(source, target): amount for source, target, amount in transfers}
    return sum(amounts.get((cycle[index], cycle[index + 1]), 0.0) for index in range(len(cycle) - 1))
