# KuzuDB KYC Onboarding Knowledge Graph Lab

This package accompanies the PowerPoint deck. It teaches engineers how to build a KYC onboarding knowledge graph using KuzuDB.

## Scenario

A KYC operations team needs to decide whether synthetic client `Atlas Robotics Inc`, a high-risk US corporate, can proceed to onboarding approval. The graph connects policy sections, required evidence, controls, operational systems, and reviewer questions so the team can see missing evidence, approval blockers, and citations.

## Why KuzuDB

Kuzu is an embedded property graph database with Cypher support. It is useful for local-first graph analytics, policy lineage, impact analysis, and engineering labs where you do not want to manage a separate graph database server.

## Folder structure

```text
data/                 CSV node and relationship tables
schema/schema.cypher  Kuzu node and relationship table definitions
queries/              Reusable Cypher examples
src/build_graph.py    Create schema and load CSVs
src/validate_data.py  Validate CSV primary keys and relationship references
src/run_queries.py    Run the 5 main training queries
src/context_retrieval.py  Onboarding evidence pack builder
src/visualize_graph.py  Export an interactive HTML graph viewer
src/visualize_schema.py  Export a schema-level node and edge viewer
output/               Generated KuzuDB directory after running build
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/validate_data.py
python src/build_graph.py --reset
python src/run_queries.py
python src/context_retrieval.py
python src/visualize_graph.py
python src/visualize_schema.py
```

Open `output/policy_context_graph.html` in a browser to explore the record-level graph.
Open `output/knowledge_graph_schema.html` to see how node types connect through edge types.

## Learning outcomes

By the end of the lab, engineers should be able to:

1. Explain how a knowledge graph links policies, evidence, controls, systems, and reviewer questions.
2. Design node and relationship tables for KuzuDB.
3. Load CSV data into Kuzu using `COPY`.
4. Write Cypher traversals for policy applicability, source citations, impact analysis, and control coverage.
5. Assemble an evidence pack for a reviewer using graph paths.
6. Add provenance, governance, and review checks to reduce incorrect onboarding decisions.

## Hands-on tasks

1. Add a new country appendix and load it as a new PolicyDocument.
2. Add a new onboarding requirement and connect it to a source Chunk.
3. Write a query to find requirements without a mapped control.
4. Add a `ReviewDecision` node and connect it to UserQuery, RetrievalContext, and Answer.
5. Create a small UI or API endpoint that returns the evidence pack from `context_retrieval.py`.

## Notes

The sample data is intentionally small so the graph is easy to teach. In production, add versioned policy ingestion, incremental loads, access controls, audit logs, sensitive-data redaction, search, and CI checks for schema and query quality.
