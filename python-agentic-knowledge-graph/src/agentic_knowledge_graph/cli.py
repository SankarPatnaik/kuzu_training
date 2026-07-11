"""Command-line interface for the training repository."""
from __future__ import annotations

import argparse
from pathlib import Path

from .agent import GraphAgent
from .cycle_detection import graph_cycles
from .db import connect, execute
from .domains import DOMAINS, get_domain
from .loader import build_domain
from .validation import validate_all


def database_path(root: Path, domain: str) -> Path:
    return root / f"{domain}.kuzu"


def command_list_domains(_args: argparse.Namespace) -> int:
    for name, spec in DOMAINS.items():
        print(f"{name:12} {spec.description}")
    return 0


def command_validate(_args: argparse.Namespace) -> int:
    issues = validate_all()
    if issues:
        for issue in issues:
            print(f"ERROR [{issue.domain}] {issue.message}")
        return 1
    print("All five datasets are valid.")
    return 0


def command_build(args: argparse.Namespace) -> int:
    path = database_path(args.output, args.domain)
    nodes, relationships = build_domain(args.domain, path, reset=args.reset)
    print(f"Built {args.domain} at {path}")
    print(f"Nodes: {nodes}; relationships: {relationships}")
    return 0


def command_query(args: argparse.Namespace) -> int:
    spec = get_domain(args.domain)
    path = database_path(args.output, args.domain)
    if not path.exists():
        raise FileNotFoundError(f"Build the graph first: akg build {args.domain} --reset")
    _database, connection = connect(path)
    query_numbers = range(1, len(spec.queries) + 1) if args.all else (args.number,)
    for number in query_numbers:
        query = spec.queries[number - 1]
        print(f"\n=== {number}. {query.title} ===")
        print(f"Teaching point: {query.teaching_point}")
        print(execute(connection, query.cypher).to_text())
    return 0


def command_ask(args: argparse.Namespace) -> int:
    response = GraphAgent(database_root=args.output).ask(args.question, domain=args.domain)
    print(f"Domain: {response.domain}")
    print(f"Query: {response.query_number}")
    print(f"Evidence rows: {response.evidence_rows}\n")
    print(response.answer)
    if args.show_context:
        print("\n--- GraphRAG context ---")
        print(response.context)
    return 0


def command_cycles(args: argparse.Namespace) -> int:
    path = database_path(args.output, "cycle")
    if not path.exists():
        raise FileNotFoundError("Build the cycle graph first: akg build cycle --reset")
    cycles = graph_cycles(path)
    if not cycles:
        print("No directed cycles found.")
        return 0
    for index, cycle in enumerate(cycles, start=1):
        print(f"Cycle {index}: {' -> '.join(cycle)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="akg", description="Agentic knowledge graph training CLI")
    parser.set_defaults(handler=lambda _args: parser.print_help() or 0)
    subparsers = parser.add_subparsers(dest="command")
    list_parser = subparsers.add_parser("list-domains")
    list_parser.set_defaults(handler=command_list_domains)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.set_defaults(handler=command_validate)
    build = subparsers.add_parser("build")
    build.add_argument("domain", choices=sorted(DOMAINS))
    build.add_argument("--output", type=Path, default=Path("output"))
    build.add_argument("--reset", action="store_true")
    build.set_defaults(handler=command_build)
    query = subparsers.add_parser("query")
    query.add_argument("domain", choices=sorted(DOMAINS))
    query.add_argument("--output", type=Path, default=Path("output"))
    group = query.add_mutually_exclusive_group(required=True)
    group.add_argument("--number", type=int, choices=range(1, 11))
    group.add_argument("--all", action="store_true")
    query.set_defaults(handler=command_query)
    ask = subparsers.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--domain", choices=sorted(DOMAINS))
    ask.add_argument("--output", type=Path, default=Path("output"))
    ask.add_argument("--show-context", action="store_true")
    ask.set_defaults(handler=command_ask)
    cycles = subparsers.add_parser("cycles")
    cycles.add_argument("--output", type=Path, default=Path("output"))
    cycles.set_defaults(handler=command_cycles)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        status = args.handler(args)
    except (FileExistsError, FileNotFoundError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
        return
    raise SystemExit(status)
