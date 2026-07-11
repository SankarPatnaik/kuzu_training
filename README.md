# KuzuDB Knowledge Graph + Context Graph Training Lab

This package accompanies the PowerPoint deck. It teaches engineers how to build a domain knowledge graph and a runtime context graph using KuzuDB.

## Scenario

A Policy AI system reads global and regional KYC policy documents, converts them into normalized requirement questions, maps those questions to controls and systems, and retrieves grounded context for LLM answers.

## Why KuzuDB

Kuzu is an embedded property graph database with Cypher support. It is useful for local-first graph analytics, GraphRAG experiments, policy lineage, impact analysis, and engineering labs where you do not want to manage a separate graph database server.

## Folder structure

```text
data/                 CSV node and relationship tables
schema/schema.cypher  Kuzu node and relationship table definitions
queries/              Reusable Cypher examples
src/build_graph.py    Create schema and load CSVs
src/run_queries.py    Run the 5 main training queries
src/context_retrieval.py  GraphRAG-style evidence pack builder
src/visualize_graph.py  Export an interactive HTML graph viewer
output/               Generated KuzuDB directory after running build
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/build_graph.py --reset
python src/run_queries.py
python src/context_retrieval.py
python src/visualize_graph.py
```

Open `output/policy_context_graph.html` in a browser to explore the graph.

## Learning outcomes

By the end of the lab, engineers should be able to:

1. Explain the difference between a knowledge graph and a context graph.
2. Design node and relationship tables for KuzuDB.
3. Load CSV data into Kuzu using `COPY`.
4. Write Cypher traversals for policy applicability, source traceability, impact analysis, and control coverage.
5. Assemble a grounded evidence pack for an LLM or agent using graph paths.
6. Add provenance, governance, and review checks to reduce hallucination risk.

## Hands-on tasks

1. Add a new country appendix and load it as a new PolicyDocument.
2. Add a new requirement and connect it to a source Chunk.
3. Write a query to find requirements without a mapped control.
4. Add a `ModelRun` node and connect it to UserQuery, RetrievalContext, and Answer.
5. Create a small UI or API endpoint that returns the evidence pack from `context_retrieval.py`.

## Notes

The sample data is intentionally small so the graph is easy to teach. In production, add versioned policy ingestion, incremental loads, access controls, audit logs, PII masking, embedding/FTS retrieval, and CI checks for schema and query quality.
