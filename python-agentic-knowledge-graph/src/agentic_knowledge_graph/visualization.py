"""Small HTML/SVG helpers for notebook-friendly graph demos."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

from .db import QueryTable
from .domains import get_domain
from .loader import DEFAULT_DATA_ROOT, load_dataset


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    label: str
    kind: str
    x: float
    y: float


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    kind: str
    properties: Mapping[str, Any]


FRAUD_COLUMN_ORDER = ("DataSource", "DetectionMethod", "Indicator", "FraudType")

NODE_COLORS = {
    "DataSource": ("#e0f2fe", "#075985"),
    "DetectionMethod": ("#ecfdf3", "#067647"),
    "Indicator": ("#fff7ed", "#b54708"),
    "FraudType": ("#fee4e2", "#b42318"),
}

EDGE_COLORS = {
    "Analyzes": "#175cd3",
    "Uses": "#b54708",
    "Detects": "#d92d20",
}


def records_to_html(records: Sequence[Mapping[str, Any]], columns: Sequence[str] | None = None) -> str:
    """Render a small list of dictionaries as a notebook-safe HTML table."""
    if not records:
        return "<p><em>No rows.</em></p>"
    visible_columns = tuple(columns or records[0].keys())
    header = "".join(f"<th>{escape(str(column))}</th>" for column in visible_columns)
    body_rows = []
    for record in records:
        cells = "".join(f"<td>{escape(str(record.get(column, '')))}</td>" for column in visible_columns)
        body_rows.append(f"<tr>{cells}</tr>")
    return _table_html(header, "".join(body_rows))


def table_to_html(table: QueryTable, max_rows: int = 50) -> str:
    """Render a QueryTable as HTML for Jupyter display."""
    if not table.rows:
        return "<p><em>No graph rows returned.</em></p>"
    header = "".join(f"<th>{escape(str(column))}</th>" for column in table.columns)
    body_rows = []
    for row in table.rows[:max_rows]:
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    if len(table.rows) > max_rows:
        body_rows.append(
            f'<tr><td colspan="{len(table.columns)}">'
            f"... {len(table.rows) - max_rows} more row(s)</td></tr>"
        )
    return _table_html(header, "".join(body_rows))


def _table_html(header: str, body: str) -> str:
    return (
        "<style>"
        ".akg-table{border-collapse:collapse;font-family:system-ui,-apple-system,Segoe UI,sans-serif;"
        "font-size:14px;margin:12px 0;width:100%;}"
        ".akg-table th{background:#f2f4f7;text-align:left;color:#344054;}"
        ".akg-table th,.akg-table td{border:1px solid #d0d5dd;padding:8px 10px;vertical-align:top;}"
        ".akg-table tr:nth-child(even) td{background:#fcfcfd;}"
        "</style>"
        f'<table class="akg-table"><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>'
    )


def dataset_graph(
    domain: str = "fraud",
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    width: int = 1120,
    height: int = 760,
) -> tuple[tuple[GraphNode, ...], tuple[GraphEdge, ...]]:
    """Convert a JSON graph dataset into positioned nodes and edges."""
    spec = get_domain(domain)
    dataset = load_dataset(spec.name, data_root)
    labels = tuple(node.name for node in spec.nodes)
    column_order = FRAUD_COLUMN_ORDER if spec.name == "fraud" else labels
    column_order = tuple(label for label in column_order if label in labels)

    left_margin = 115
    top_margin = 105
    bottom_margin = 92
    usable_width = width - (2 * left_margin)
    usable_height = height - top_margin - bottom_margin

    x_by_label: dict[str, float] = {}
    for index, label in enumerate(column_order):
        step = usable_width / max(len(column_order) - 1, 1)
        x_by_label[label] = left_margin + (index * step)

    nodes: list[GraphNode] = []
    node_ids: dict[tuple[str, Any], str] = {}
    for label in column_order:
        rows = dataset["nodes"].get(label, [])
        key_name = spec.node_map[label].primary_key
        for index, row in enumerate(rows):
            key = row[key_name]
            gap = usable_height / max(len(rows) - 1, 1)
            y = top_margin + (index * gap if len(rows) > 1 else usable_height / 2)
            node_id = f"{label}:{key}"
            node_ids[(label, key)] = node_id
            nodes.append(GraphNode(node_id=node_id, label=str(key), kind=label, x=x_by_label[label], y=y))

    edges: list[GraphEdge] = []
    for rel_name, rows in dataset["relationships"].items():
        rel_spec = spec.relationship_map[rel_name]
        for row in rows:
            source_id = node_ids[(rel_spec.from_node, row["from"])]
            target_id = node_ids[(rel_spec.to_node, row["to"])]
            edges.append(
                GraphEdge(
                    source_id=source_id,
                    target_id=target_id,
                    kind=rel_name,
                    properties=dict(row.get("properties", {})),
                )
            )
    return tuple(nodes), tuple(edges)


def fraud_graph_svg(*, data_root: Path = DEFAULT_DATA_ROOT, width: int = 1120, height: int = 760) -> str:
    """Build a self-contained SVG visualization of the fraud graph dataset."""
    nodes, edges = dataset_graph("fraud", data_root=data_root, width=width, height=height)
    node_by_id = {node.node_id: node for node in nodes}
    column_labels = _column_labels(nodes)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="Fraud knowledge graph">',
        "<defs>",
        _arrow_marker("marker-Analyzes", EDGE_COLORS["Analyzes"]),
        _arrow_marker("marker-Uses", EDGE_COLORS["Uses"]),
        _arrow_marker("marker-Detects", EDGE_COLORS["Detects"]),
        "</defs>",
        "<style>",
        ".title{font:700 24px system-ui,-apple-system,Segoe UI,sans-serif;fill:#101828;}",
        ".subtitle{font:400 14px system-ui,-apple-system,Segoe UI,sans-serif;fill:#475467;}",
        ".column{font:700 13px system-ui,-apple-system,Segoe UI,sans-serif;fill:#344054;text-anchor:middle;}",
        ".node-label{font:700 12px system-ui,-apple-system,Segoe UI,sans-serif;fill:#101828;text-anchor:middle;}",
        ".node-kind{font:500 10px system-ui,-apple-system,Segoe UI,sans-serif;fill:#667085;text-anchor:middle;}",
        ".edge-label{font:600 9px system-ui,-apple-system,Segoe UI,sans-serif;fill:#344054;text-anchor:middle;}",
        ".legend{font:600 11px system-ui,-apple-system,Segoe UI,sans-serif;fill:#344054;}",
        "</style>",
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        '<text class="title" x="40" y="38">Fraud Detection Knowledge Graph</text>',
        '<text class="subtitle" x="40" y="62">Data sources feed methods; methods use indicators and detect fraud types.</text>',
    ]

    for label, x in column_labels:
        parts.append(f'<text class="column" x="{x:.1f}" y="88">{escape(label)}</text>')

    for edge_index, edge in enumerate(edges):
        source = node_by_id[edge.source_id]
        target = node_by_id[edge.target_id]
        color = EDGE_COLORS.get(edge.kind, "#667085")
        start_x, start_y, end_x, end_y = _edge_points(source, target)
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        curve_offset = ((edge_index % 3) - 1) * 22
        control_x = (start_x + end_x) / 2
        path = (
            f"M {start_x:.1f} {start_y:.1f} "
            f"C {control_x:.1f} {start_y + curve_offset:.1f}, "
            f"{control_x:.1f} {end_y - curve_offset:.1f}, "
            f"{end_x:.1f} {end_y:.1f}"
        )
        parts.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.7" '
            f'stroke-opacity="0.68" marker-end="url(#marker-{escape(edge.kind)})">'
            f"<title>{escape(_edge_title(edge))}</title></path>"
        )
        if edge.kind in {"Detects", "Uses"}:
            parts.append(
                f'<text class="edge-label" x="{mid_x:.1f}" y="{mid_y - 7 + curve_offset / 6:.1f}">'
                f"{escape(_edge_caption(edge))}</text>"
            )

    for node in nodes:
        parts.append(_node_svg(node))

    parts.extend(_legend_svg(height))
    parts.append("</svg>")
    return "".join(parts)


def fraud_graph_html(*, data_root: Path = DEFAULT_DATA_ROOT) -> str:
    svg = fraud_graph_svg(data_root=data_root)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>Fraud Knowledge Graph</title>"
        "<style>body{margin:0;padding:24px;background:#f8fafc;font-family:system-ui,-apple-system,Segoe UI,sans-serif;}"
        ".frame{max-width:1180px;margin:auto;background:white;border:1px solid #d0d5dd;padding:16px;}"
        "</style></head><body><div class=\"frame\">"
        f"{svg}"
        "</div></body></html>"
    )


def write_fraud_graph_html(path: Path, *, data_root: Path = DEFAULT_DATA_ROOT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fraud_graph_html(data_root=data_root), encoding="utf-8")
    return path


def _arrow_marker(marker_id: str, color: str) -> str:
    return (
        f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
    )


def _column_labels(nodes: Sequence[GraphNode]) -> tuple[tuple[str, float], ...]:
    seen: dict[str, float] = {}
    for node in nodes:
        seen.setdefault(node.kind, node.x)
    return tuple((kind, seen[kind]) for kind in FRAUD_COLUMN_ORDER if kind in seen)


def _edge_points(source: GraphNode, target: GraphNode) -> tuple[float, float, float, float]:
    dx = target.x - source.x
    dy = target.y - source.y
    distance = max((dx * dx + dy * dy) ** 0.5, 1)
    unit_x = dx / distance
    unit_y = dy / distance
    node_padding = 72
    return (
        source.x + (unit_x * node_padding),
        source.y + (unit_y * 28),
        target.x - (unit_x * node_padding),
        target.y - (unit_y * 28),
    )


def _node_svg(node: GraphNode) -> str:
    fill, border = NODE_COLORS.get(node.kind, ("#f2f4f7", "#667085"))
    width = 158
    height = 58
    x = node.x - width / 2
    y = node.y - height / 2
    lines = _wrap_label(node.label)
    text_y = node.y - (5 if len(lines) == 1 else 12)
    label_parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height}" rx="8" fill="{fill}" '
        f'stroke="{border}" stroke-width="1.4"/>',
        f"<title>{escape(node.kind)}: {escape(node.label)}</title>",
    ]
    for index, line in enumerate(lines):
        label_parts.append(
            f'<text class="node-label" x="{node.x:.1f}" y="{text_y + (index * 14):.1f}">{escape(line)}</text>'
        )
    label_parts.append(
        f'<text class="node-kind" x="{node.x:.1f}" y="{node.y + 22:.1f}">{escape(node.kind)}</text>'
    )
    return f"<g>{''.join(label_parts)}</g>"


def _wrap_label(label: str, max_chars: int = 18) -> tuple[str, ...]:
    words = label.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) <= 2:
        return tuple(lines)
    return (lines[0], f"{lines[1][: max_chars - 3]}...")


def _edge_caption(edge: GraphEdge) -> str:
    if not edge.properties:
        return edge.kind
    name, value = next(iter(edge.properties.items()))
    if isinstance(value, float):
        value_text = f"{value:.2f}"
    else:
        value_text = str(value)
    short_name = {"confidence": "conf", "weight": "w", "priority": "p"}.get(name, name)
    return f"{edge.kind} {short_name}={value_text}"


def _edge_title(edge: GraphEdge) -> str:
    if not edge.properties:
        return edge.kind
    details = ", ".join(f"{key}={value}" for key, value in edge.properties.items())
    return f"{edge.kind}: {details}"


def _legend_svg(height: int) -> list[str]:
    start_x = 40
    y = height - 35
    items = (("Analyzes data source", "Analyzes"), ("Uses indicator", "Uses"), ("Detects fraud type", "Detects"))
    parts = []
    offset = 0
    for label, edge_kind in items:
        color = EDGE_COLORS[edge_kind]
        parts.append(f'<line x1="{start_x + offset}" y1="{y}" x2="{start_x + offset + 28}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text class="legend" x="{start_x + offset + 36}" y="{y + 4}">{escape(label)}</text>')
        offset += 190
    return parts
