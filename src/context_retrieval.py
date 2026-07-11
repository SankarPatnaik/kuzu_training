"""Tiny onboarding evidence retriever over KuzuDB.

This is deliberately simple and deterministic so engineers can understand the pattern:
1. Convert user intent into graph filters.
2. Retrieve requirements plus source chunks and controls.
3. Assemble an evidence pack for a reviewer or a rules-based answer.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import kuzu

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "output" / "policy_context_graph"


@dataclass(frozen=True)
class RetrievalFilter:
    country_code: str
    client_type_id: str
    risk_id: str


def get_df(result):
    try:
        return result.get_as_df()
    except Exception:
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        return rows


def retrieve_policy_context(conn: "kuzu.Connection", f: RetrievalFilter):
    query = f"""
    MATCH (d:PolicyDocument)-[:APPLIES_TO_COUNTRY]->(country:Country),
          (d)-[:APPLIES_TO_CLIENT_TYPE]->(ct:ClientType),
          (d)-[:APPLIES_TO_RISK]->(risk:RiskLevel),
          (d)-[:GENERATES_REQUIREMENT]->(r:Requirement)-[:REQUIREMENT_FROM_CHUNK]->(chunk:Chunk),
          (r)-[:MAPPED_TO_CONTROL]->(ctrl:Control)
    WHERE (country.code = 'GLOBAL' OR country.code = '{f.country_code}')
      AND (ct.client_type_id = 'ALL' OR ct.client_type_id = '{f.client_type_id}')
      AND (risk.risk_id = 'ALL' OR risk.risk_id = '{f.risk_id}')
    RETURN r.requirement_id AS requirement_id,
           r.normalized_question AS question,
           r.priority AS priority,
           d.title AS source_policy,
           d.version AS source_version,
           chunk.section AS evidence_section,
           chunk.text AS evidence_text,
           ctrl.name AS control
    ORDER BY priority, requirement_id;
    """
    return get_df(conn.execute(query))


def make_prompt(evidence_pack) -> str:
    lines = [
        "You are a KYC onboarding assistant. Answer only from the evidence below.",
        "Return: required evidence, approval blockers, controls, and citations.",
        "",
        "Evidence:",
    ]
    if hasattr(evidence_pack, "iterrows"):
        iterator: Iterable = (row for _, row in evidence_pack.iterrows())
    else:
        iterator = evidence_pack
    for row in iterator:
        lines.append(
            f"- [{row['requirement_id']}] {row['question']} | "
            f"Source={row['source_policy']} {row['source_version']} / {row['evidence_section']} | "
            f"Control={row['control']} | Evidence={row['evidence_text']}"
        )
    return "\n".join(lines)


def main(db_path: Path) -> None:
    conn = kuzu.Connection(kuzu.Database(str(db_path), read_only=True))
    filters = RetrievalFilter(country_code="US", client_type_id="CORP", risk_id="HIGH")
    evidence = retrieve_policy_context(conn, filters)
    print(evidence)
    print("\n--- Evidence brief assembled for reviewer ---\n")
    print(make_prompt(evidence))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    main(args.db)
