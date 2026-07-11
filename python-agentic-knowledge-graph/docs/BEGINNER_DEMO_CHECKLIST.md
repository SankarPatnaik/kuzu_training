# Beginner Demo Checklist

Use this one-page checklist while presenting the repository.

## Before the session

```bash
cd python-agentic-knowledge-graph
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-demo.txt
akg validate
pytest
```

## Fraud Jupyter demo

Use this flow when you want students to learn from a notebook:

```bash
python -m jupyter lab notebooks/fraud_knowledge_graph_demo.ipynb
```

Backup command if Jupyter is not available during class:

```bash
python scripts/fraud_demo.py
```

The notebook covers schema inspection, dataset validation, Kuzu loading, graph visualization, Cypher retrieval, a meaningful fraud-prioritization outcome, and a small graph-agent chatbot cell.

## Demo flow

1. Open `domains.py` and explain `NodeSpec`, `RelationshipSpec`, `QuerySpec` and `DomainSpec`.
2. Open `data/yoga.json` and match one node row and one relationship row to the schema.
3. Run `akg build yoga --reset`.
4. Explain the call chain: CLI → loader → KuzuDB.
5. Run queries 1, 2, 4, 5 and 10.
6. Run `akg ask "Which poses improve flexibility?" --domain yoga --show-context`.
7. Point out the selected query, Cypher, evidence table and grounding instruction.
8. Build the cycle graph and compare fixed-length Cypher with DFS:

```bash
akg build cycle --reset
akg query cycle --number 5
akg cycles
```

## Questions to ask students

- Why is `intensity` stored on the relationship?
- Why are nodes inserted before relationships?
- How does validation detect an unknown target?
- What makes the answer explainable?
- What should be added before this pattern is used in production?
