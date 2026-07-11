"""Small compatibility layer around the Kuzu Python client."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class KuzuNotInstalledError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueryTable:
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]

    def to_text(self, max_rows: int = 100) -> str:
        visible = self.rows[:max_rows]
        widths = [len(str(column)) for column in self.columns]
        for row in visible:
            for index, value in enumerate(row):
                widths[index] = max(widths[index], len(str(value)))
        header = " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(self.columns))
        divider = "-+-".join("-" * width for width in widths)
        body = [" | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)) for row in visible]
        suffix = []
        if len(self.rows) > max_rows:
            suffix.append(f"... {len(self.rows) - max_rows} more row(s)")
        return "\n".join([header, divider, *body, *suffix])


def import_kuzu() -> Any:
    try:
        import kuzu  # type: ignore
    except ImportError as exc:
        raise KuzuNotInstalledError(
            "Kuzu is not installed. Run 'pip install -e .' or 'pip install kuzu==0.11.3'."
        ) from exc
    return kuzu


def connect(database_path: Path) -> tuple[Any, Any]:
    kuzu = import_kuzu()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database = kuzu.Database(str(database_path))
    connection = kuzu.Connection(database)
    return database, connection


def execute(connection: Any, cypher: str) -> QueryTable:
    result = connection.execute(cypher)
    columns: Iterable[str]
    if hasattr(result, "get_column_names"):
        columns = result.get_column_names()
    else:
        columns = ()
    rows: list[tuple[Any, ...]] = []
    while result.has_next():
        rows.append(tuple(result.get_next()))
    if not tuple(columns) and rows:
        columns = tuple(f"column_{index + 1}" for index in range(len(rows[0])))
    return QueryTable(tuple(columns), tuple(rows))
