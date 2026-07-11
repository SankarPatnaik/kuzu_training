"""Run practical Cypher examples over the KuzuDB knowledge graph.

Run after building the DB:
    python src/run_queries.py --db ./output/policy_context_graph
"""
from __future__ import annotations

import argparse
from pathlib import Path

import kuzu

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "output" / "policy_context_graph"


def print_result(result, title: str) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    try:
        print(result.get_as_df().to_string(index=False))
        return
    except Exception:
        pass
    while result.has_next():
        print(result.get_next())


def main(db_path: Path) -> None:
    conn = kuzu.Connection(kuzu.Database(str(db_path)))

    q1 = """
    MATCH (d:PolicyDocument)-[:APPLIES_TO_COUNTRY]->(country:Country),
          (d)-[:APPLIES_TO_CLIENT_TYPE]->(ct:ClientType),
          (d)-[:APPLIES_TO_RISK]->(risk:RiskLevel),
          (d)-[:GENERATES_REQUIREMENT]->(r:Requirement)
    WHERE (country.code = 'GLOBAL' OR country.code = 'US')
      AND (ct.client_type_id = 'ALL' OR ct.client_type_id = 'CORP')
      AND (risk.risk_id = 'ALL' OR risk.risk_id = 'HIGH')
    RETURN d.title AS policy, d.version AS version, r.requirement_id AS req_id,
           r.priority AS priority, r.normalized_question AS question
    ORDER BY priority, req_id;
    """
    print_result(conn.execute(q1), "Q1. Requirements for a high-risk US Corporate client")

    q2 = """
    MATCH (r:Requirement)-[ev:REQUIREMENT_FROM_CHUNK]->(c:Chunk)<-[:HAS_CHUNK]-(d:PolicyDocument)
    WHERE r.requirement_id = 'R004'
    RETURN r.requirement_id AS requirement, r.description AS requirement_text,
           d.title AS source_policy, d.version AS version, c.section AS section,
           c.text AS evidence_text, ev.evidence_score AS evidence_score;
    """
    print_result(conn.execute(q2), "Q2. Explainability path for requirement R004")

    q3 = """
    MATCH (r:Requirement)-[:MAPPED_TO_CONTROL]->(ctrl:Control)
    WHERE r.priority = 'Critical'
    RETURN r.requirement_id AS critical_req, r.description AS requirement,
           ctrl.name AS mapped_control, ctrl.control_type AS control_type, ctrl.severity AS severity
    ORDER BY critical_req;
    """
    print_result(conn.execute(q3), "Q3. Critical requirements mapped to controls")

    q4 = """
    MATCH (uc:UseCase)-[:USE_CASE_USES_DOCUMENT]->(d:PolicyDocument)-[:GENERATES_REQUIREMENT]->(r:Requirement)-[:IMPLEMENTED_IN]->(s:System)
    WHERE uc.use_case_id = 'UC001'
    RETURN uc.name AS use_case, d.title AS policy, r.requirement_id AS req_id,
           s.name AS system, s.owner AS system_owner
    ORDER BY policy, req_id;
    """
    print_result(conn.execute(q4), "Q4. Use case lineage: Policy AI -> documents -> requirements -> systems")

    q5 = """
    MATCH (q:UserQuery)-[:QUERY_RETRIEVES_CONTEXT]->(ctx:RetrievalContext)-[:CONTEXT_SUPPORTS_REQUIREMENT]->(r:Requirement),
          (ctx)-[:CONTEXT_USES_CHUNK]->(chunk:Chunk)<-[:HAS_CHUNK]-(doc:PolicyDocument)
    WHERE q.query_id = 'Q001'
    RETURN q.question AS user_question, ctx.strategy AS retrieval_strategy,
           r.requirement_id AS req_id, r.normalized_question AS generated_question,
           doc.title AS source_policy, chunk.section AS evidence_section
    ORDER BY req_id;
    """
    print_result(conn.execute(q5), "Q5. Context graph: retrieved evidence used to ground an answer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    main(args.db)
