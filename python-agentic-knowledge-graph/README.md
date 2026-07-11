# Agentic Knowledge Graphs with KuzuDB — Python Edition

A Python-first teaching repository for building knowledge graphs, context graphs, GraphRAG retrieval, and simple graph agents with KuzuDB.

This project recreates the **learning scope** of [`vishalmysore/agenticknowledgegraph`](https://github.com/vishalmysore/agenticknowledgegraph) in Python. It is an independent implementation: the architecture is reusable, the datasets are synthetic, and the examples are organized as one Python package rather than separate Java classes.

## What engineers learn

1. Model entities as nodes and business connections as relationships.
2. Create Kuzu node and relationship tables.
3. Load JSON datasets into an embedded graph database.
4. Write progressive Cypher queries from basic retrieval to multi-hop analytics.
5. Build a context pack for GraphRAG.
6. Use a small agent loop to select a domain, retrieve graph evidence, and produce a grounded response.
7. Detect circular transaction patterns with a pure-Python DFS algorithm.

## Included domains

| Domain | Main nodes | Main relationships | Teaching focus |
|---|---|---|---|
| Yoga | Pose, YogaStyle, Benefit, Instructor, Studio | BelongsToStyle, TargetsBenefit, Teaches, WorksAt | Basic modelling and multi-hop traversal |
| Fraud detection | FraudType, DetectionMethod, Indicator, DataSource | Detects, Uses, Analyzes | Confidence, coverage, aggregation |
| Transaction cycles | Account, Transaction, CyclePattern, Algorithm | Transfers, Involves, DetectsPattern | AML-style paths and DFS cycle detection |
| Bird migration | BirdSpecies, Location, Season, EnvironmentalFactor | MigratesFrom, MigratesTo, ActiveIn, InfluencedBy | Temporal and environmental context |
| Professional skills | Person, Skill, Organization, Location, Achievement | HasSkill, WorksFor, RelatedTo | Expertise discovery and GraphRAG context |

Each domain contains ten progressive Cypher queries.

## Requirements

- Python 3.10+
- Kuzu Python package `0.11.3`

> **Kuzu lifecycle note:** Kuzu 0.11.3 was released on 10 October 2025 and the project is archived. Existing releases remain usable, so this repository pins 0.11.3 for reproducible training. Treat it as an educational and prototyping platform unless your organization has completed its own support assessment.

## Quick start

```bash
cd python-agentic-knowledge-graph
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .

akg list-domains
akg validate
akg build yoga --reset
akg query yoga --number 1
akg query yoga --all
akg ask "Which poses improve flexibility?" --domain yoga

akg build cycle --reset
akg cycles
```

## Repository structure

```text
python-agentic-knowledge-graph/
├── data/                         # Five synthetic graph datasets
├── docs/TEACHING_GUIDE.md        # Instructor-ready lesson plan
├── src/agentic_knowledge_graph/
│   ├── agent.py                  # Observe → retrieve → reason → answer loop
│   ├── cli.py                    # Command-line interface
│   ├── context.py                # GraphRAG context construction
│   ├── cycle_detection.py        # Pure-Python DFS cycle detection
│   ├── db.py                     # Kuzu connection and result helpers
│   ├── domains.py                # Schemas and 50 progressive queries
│   ├── loader.py                 # Build and populate each graph
│   └── validation.py             # Dataset integrity checks
└── tests/                        # Unit tests independent of Kuzu runtime
```

## Core architecture

```text
User question
     │
     ▼
Question router ── selects domain and retrieval query
     │
     ▼
KuzuDB graph traversal
     │
     ▼
Structured evidence rows
     │
     ▼
Graph context pack with provenance
     │
     ▼
Grounded answer or optional external LLM
```

## Python example

```python
from pathlib import Path

from agentic_knowledge_graph.agent import GraphAgent
from agentic_knowledge_graph.loader import build_domain

build_domain("professional", Path("output/professional.kuzu"), reset=True)

agent = GraphAgent(database_root=Path("output"))
response = agent.ask("Which technical skills are strongest?", domain="professional")
print(response.answer)
print(response.context)
```

## Attribution

The domain selection and progressive-query teaching idea were inspired by the public repository `vishalmysore/agenticknowledgegraph`. This Python edition is a clean-room educational implementation with new package design, validation, agent workflow, tests, and synthetic data.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
