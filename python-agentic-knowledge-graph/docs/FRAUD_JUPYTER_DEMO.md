# Fraud Jupyter Demo Guide

Use this guide when teaching beginners from:

- `notebooks/fraud_kuzu_tables_relationships_demo.ipynb`
- `notebooks/fraud_knowledge_graph_demo.ipynb`

## Goal

Students should leave with a clear mental model:

```text
Fraud JSON data
    -> schema in domains.py
    -> validation
    -> Kuzu node and relationship tables
    -> Cypher graph retrieval
    -> graph evidence
    -> simple agent answer
```

The demo uses a fraud operations scenario: a team wants to understand which detection methods use which indicators, which data sources support them, and which fraud types they detect with high confidence.

## Setup

Run from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-demo.txt
python -m jupyter lab notebooks/fraud_kuzu_tables_relationships_demo.ipynb
python -m jupyter lab notebooks/fraud_knowledge_graph_demo.ipynb
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-demo.txt
python -m jupyter lab notebooks/fraud_kuzu_tables_relationships_demo.ipynb
python -m jupyter lab notebooks/fraud_knowledge_graph_demo.ipynb
```

## Live demo flow

1. Open `fraud_kuzu_tables_relationships_demo.ipynb`.
2. Explain the node tables and relationship tables.
3. Execute the manual `CREATE NODE TABLE` statements.
4. Execute the manual `CREATE REL TABLE` statements.
5. Insert fraud nodes from `data/fraud.json`.
6. Create relationships by matching source and target primary keys.
7. Query and visualize the manually built graph.
8. Open `fraud_knowledge_graph_demo.ipynb`.
9. Validate the JSON dataset and build `output/fraud.kuzu`.
10. Run queries 1, 5, and 8.
11. Run the outcome query and discuss the analyst-review recommendation.
12. Run the graph agent examples and optional mini chatbot cell.
13. Save `output/fraud_knowledge_graph.html` as a standalone backup visualization.

## Schema explanation

The fraud schema is defined in `src/agentic_knowledge_graph/domains.py`.

Node tables:

| Node | Primary key | Why it exists |
|---|---|---|
| `FraudType` | `name` | The risk or fraud outcome being detected |
| `DetectionMethod` | `name` | The model, rule, graph method, or analytics technique |
| `Indicator` | `name` | The observable signal used by a method |
| `DataSource` | `name` | The system or dataset analyzed by a method |

Relationship tables:

| Relationship | Direction | Teaching point |
|---|---|---|
| `Detects` | `DetectionMethod -> FraudType` | Confidence belongs to one method detecting one fraud type |
| `Uses` | `DetectionMethod -> Indicator` | Weight belongs to one method using one indicator |
| `Analyzes` | `DetectionMethod -> DataSource` | Priority belongs to one method analyzing one source |

Key beginner explanation: the graph is not just storing lists. It stores connected evidence. That lets the class ask questions such as:

- Which method detects Transaction Fraud?
- Which indicators support Device Intelligence?
- Which data sources support each method?
- Which fraud type should analysts review first?

## Backup script

If Jupyter fails during class, run:

```bash
python scripts/fraud_demo.py
```

The script validates the fraud data, rebuilds the graph, runs teaching queries, writes `output/fraud_knowledge_graph.html`, and prints a sample graph-agent answer.

## Suggested classroom timing

| Section | Time |
|---|---:|
| Fraud scenario and graph vocabulary | 10 min |
| Schema and JSON data walkthrough | 15 min |
| Validation and Kuzu build | 10 min |
| Visualization and Cypher queries | 20 min |
| GraphRAG agent flow | 15 min |
| Student exercise | 20 min |

## Student exercise

Ask students to add `Impossible Travel` as a new `Indicator`, connect it to `Device Intelligence`, validate the dataset, rebuild the graph, and rerun the visualization.

Expected learning outcome: students see that adding one node and one relationship changes the graph evidence available to retrieval and agent answers.
