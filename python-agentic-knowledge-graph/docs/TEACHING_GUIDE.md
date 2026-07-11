# Beginner Teaching Guide: Agentic Knowledge Graphs and GraphRAG with KuzuDB

This guide is for a live beginner demonstration and a student hands-on lab. It explains what every major file does, how the schema is defined, how JSON data becomes a graph, how Cypher retrieves connected evidence, and how the small agent creates a GraphRAG context pack.

The repository follows the same high-level learning pattern described in the Medium reference article:

1. Define the graph schema.
2. Insert knowledge into the graph.
3. Retrieve connected knowledge.
4. Use the retrieved evidence to support an answer or action.

In this repository, those four steps map to:

| Learning step | Repository file |
|---|---|
| Define the schema and queries | `src/agentic_knowledge_graph/domains.py` |
| Store example knowledge | `data/<domain>.json` |
| Validate the input data | `src/agentic_knowledge_graph/validation.py` |
| Create KuzuDB and load data | `src/agentic_knowledge_graph/loader.py` |
| Run Cypher and format results | `src/agentic_knowledge_graph/db.py` |
| Select retrieval and build context | `src/agentic_knowledge_graph/context.py` |
| Choose a domain and answer | `src/agentic_knowledge_graph/agent.py` |
| Expose commands to students | `src/agentic_knowledge_graph/cli.py` |

---

## 1. Learning objectives

By the end of the lab, a student should be able to:

- Explain nodes, relationships, properties and paths.
- Explain the difference between a knowledge graph and a context graph.
- Read a KuzuDB node-table and relationship-table definition.
- Understand how the JSON datasets represent nodes and edges.
- Build a graph database from the repository.
- Run one-hop, multi-hop, filtered and aggregated Cypher queries.
- Explain how graph query results become GraphRAG evidence.
- Trace a user question through the CLI, router, database and answer generator.
- Explain why the current agent is deterministic and easy to inspect.
- Extend one example by adding a node, relationship and query.

Recommended audience: Python developers, data engineers, AI engineers and application engineers who are new to graph databases.

Recommended duration:

- 30 minutes: graph concepts.
- 30 minutes: repository walkthrough.
- 45 minutes: live build and queries.
- 30 minutes: GraphRAG and agent flow.
- 45 minutes: student exercise.

---

## 2. Start with a simple mental model

A normal table stores rows. A graph stores things and their connections.

```text
(Pose)-[:TARGETS_BENEFIT {intensity: 8}]->(Benefit)
```

Here:

- `Pose` is a node type.
- `Benefit` is another node type.
- `TARGETS_BENEFIT` is a directed relationship.
- `intensity` is a property of the relationship.

Why is `intensity` on the relationship rather than on the Benefit node?

Because the strength belongs to one specific connection. Tree Pose may target Balance with intensity 8, while another pose may target Balance with intensity 5. The benefit itself does not have one universal intensity.

### Knowledge graph versus context graph

A knowledge graph stores durable facts:

```text
(Person)-[:HAS_SKILL]->(Python)
```

A context graph adds facts needed for the current decision:

```text
(Person)-[:HAS_SKILL {proficiency: 92, last_used_year: 2026}]->(Python)
(Person)-[:AVAILABLE_FOR {from: '2026-07'}]->(Project)
(Project)-[:REQUIRES]->(Python)
```

Typical context includes time, confidence, risk, source, role, permissions, current task and recent activity.

---

## 3. Repository structure

```text
python-agentic-knowledge-graph/
├── data/
│   ├── yoga.json
│   ├── fraud.json
│   ├── cycle.json
│   ├── migration.json
│   └── professional.json
├── docs/
│   └── TEACHING_GUIDE.md
├── src/agentic_knowledge_graph/
│   ├── __init__.py
│   ├── __main__.py
│   ├── agent.py
│   ├── cli.py
│   ├── context.py
│   ├── cycle_detection.py
│   ├── db.py
│   ├── domains.py
│   ├── loader.py
│   └── validation.py
├── tests/
├── pyproject.toml
└── README.md
```

Tell students to think of the project in four layers:

```text
Data layer       data/*.json
Model layer      domains.py
Database layer   validation.py + loader.py + db.py
AI layer         context.py + agent.py + cli.py
```

---

## 4. Install and verify the project

### macOS or Linux

```bash
cd python-agentic-knowledge-graph
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

### Windows PowerShell

```powershell
cd python-agentic-knowledge-graph
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

`pip install -e .` performs an editable installation. The source code remains in the repository, and changes are available immediately without reinstalling.

The command `akg` is created by this entry in `pyproject.toml`:

```toml
[project.scripts]
akg = "agentic_knowledge_graph.cli:main"
```

Therefore:

```bash
akg list-domains
```

is equivalent to calling `main()` in `cli.py`.

Verify the installation:

```bash
akg list-domains
akg validate
pytest
```

Expected validation message:

```text
All five datasets are valid.
```

---

## 5. The five teaching domains

| Domain | Main learning topic |
|---|---|
| `yoga` | Basic nodes, edges, edge properties and multi-hop traversal |
| `fraud` | Confidence, indicators, source coverage and aggregation |
| `cycle` | Directed transaction paths and cycle detection |
| `migration` | Time, routes and environmental context |
| `professional` | Skills, proficiency, organizations and GraphRAG context |

For a beginner demo, start with `yoga`. It is visually intuitive and has several relationship types.

---

## 6. Understand `domains.py`: the schema definition

`domains.py` is the central modelling file. It contains four dataclasses.

### `NodeSpec`

```python
@dataclass(frozen=True)
class NodeSpec:
    name: str
    primary_key: str
    columns: tuple[tuple[str, str], ...]
```

It describes one Kuzu node table.

Example:

```python
N(
    "Pose",
    "name",
    ("name", "STRING"),
    ("sanskrit_name", "STRING"),
    ("difficulty", "INT64"),
    ("description", "STRING"),
    ("target_time", "STRING"),
)
```

This means:

- Node label: `Pose`
- Primary key: `name`
- Other properties: Sanskrit name, difficulty, description and target time

`create_statement()` converts the Python definition into Cypher similar to:

```cypher
CREATE NODE TABLE Pose(
    name STRING,
    sanskrit_name STRING,
    difficulty INT64,
    description STRING,
    target_time STRING,
    PRIMARY KEY(name)
)
```

The primary key uniquely identifies each node. The loader later uses it to locate the source and target node when it creates a relationship.

### `RelationshipSpec`

```python
@dataclass(frozen=True)
class RelationshipSpec:
    name: str
    from_node: str
    to_node: str
    columns: tuple[tuple[str, str], ...] = ()
```

Example:

```python
R("TargetsBenefit", "Pose", "Benefit", ("intensity", "INT64"))
```

It becomes:

```cypher
CREATE REL TABLE TargetsBenefit(
    FROM Pose TO Benefit,
    intensity INT64
)
```

This definition controls:

- Relationship direction: `Pose` to `Benefit`
- Allowed source label: `Pose`
- Allowed target label: `Benefit`
- Relationship property: `intensity`

### `QuerySpec`

```python
@dataclass(frozen=True)
class QuerySpec:
    title: str
    cypher: str
    teaching_point: str
```

Each domain contains ten progressive queries. Every query has a title, Cypher statement and teaching objective.

### `DomainSpec`

```python
@dataclass(frozen=True)
class DomainSpec:
    name: str
    description: str
    nodes: tuple[NodeSpec, ...]
    relationships: tuple[RelationshipSpec, ...]
    queries: tuple[QuerySpec, ...]
    keywords: tuple[str, ...]
    default_query: int = 1
```

A `DomainSpec` packages the complete graph model for one business domain.

The `keywords` field is used by the simple agent to choose a domain. The `default_query` field is used when no query-selection rule matches the question.

---

## 7. Read the Yoga schema as a graph

The Yoga domain contains these node types:

```text
YogaStyle
Pose
Benefit
BodyPart
Instructor
Studio
PoseType
```

It contains these relationship types:

```text
(Pose)-[:BelongsToStyle]->(YogaStyle)
(Pose)-[:TargetsBenefit {intensity}]->(Benefit)
(Pose)-[:EngagesBodyPart {engagement_level}]->(BodyPart)
(Instructor)-[:Teaches {years_teaching}]->(YogaStyle)
(Instructor)-[:WorksAt {start_year}]->(Studio)
(YogaStyle)-[:RecommendsFor]->(Benefit)
(Pose)-[:HasType]->(PoseType)
```

Ask students to read each relationship as a sentence:

- Tree Pose belongs to Hatha.
- Tree Pose targets Balance with intensity 8.
- Tree Pose engages Legs with level 8.
- Priya teaches Hatha and has taught it for 10 years.
- Priya works at Prana Centre and started in 2016.

That sentence test is a simple way to check whether relationship direction is meaningful.

---

## 8. Understand the JSON dataset

Open `data/yoga.json`.

The file has two top-level objects:

```json
{
  "nodes": {},
  "relationships": {}
}
```

### Node data

```json
"Pose": [
  {
    "name": "Tree Pose",
    "sanskrit_name": "Vrikshasana",
    "difficulty": 3,
    "description": "Single-leg balance pose",
    "target_time": "30 seconds each side"
  }
]
```

The object keys must match the columns declared in `NodeSpec`.

### Relationship data

```json
"TargetsBenefit": [
  {
    "from": "Tree Pose",
    "to": "Balance",
    "properties": {
      "intensity": 8
    }
  }
]
```

`from` and `to` contain primary-key values, not full node objects.

The loader uses the relationship schema to determine that:

- `from` must identify a `Pose`.
- `to` must identify a `Benefit`.
- `intensity` is required.

This keeps the training data simple while still representing a property graph.

---

## 9. Validate before building

Run:

```bash
akg validate
```

Execution path:

```text
cli.py command_validate()
        ↓
validation.py validate_all()
        ↓
validate_domain() for every DomainSpec
        ↓
loader.py load_dataset()
```

`validate_domain()` checks:

1. Every node type defined by the schema has a dataset.
2. Every node row contains all required columns.
3. Primary keys are not duplicated.
4. Every relationship type has a dataset.
5. Every relationship source exists.
6. Every relationship target exists.
7. Every required relationship property is present.

Example error:

```text
ERROR [yoga] TargetsBenefit row 3 has unknown target Flexiblity
```

This catches spelling and reference errors before KuzuDB is created.

Important teaching point: schema validation is not the same as business validation. The current code confirms structural correctness. Production systems should also check ranges, dates, allowed values, source lineage and business rules.

---

## 10. Build the Yoga graph

Run:

```bash
akg build yoga --reset
```

Execution path:

```text
cli.py command_build()
        ↓
loader.py build_domain()
        ↓
get_domain("yoga")
        ↓
load_dataset("yoga")
        ↓
connect(output/yoga.kuzu)
        ↓
create_schema()
        ↓
insert_nodes()
        ↓
insert_relationships()
```

### Step 1: Resolve the database path

`cli.py` creates:

```text
output/yoga.kuzu
```

### Step 2: Handle `--reset`

If the database already exists, `build_domain()` deletes it only when `reset=True`. This protects students from silently duplicating data.

### Step 3: Connect to embedded KuzuDB

`db.py` runs:

```python
database = kuzu.Database(str(database_path))
connection = kuzu.Connection(database)
```

Kuzu is embedded inside the Python process. There is no separate database server in this lab.

### Step 4: Create node tables

`create_schema()` loops through `spec.nodes` and executes every generated `CREATE NODE TABLE` statement.

### Step 5: Create relationship tables

It then loops through `spec.relationships` and executes every generated `CREATE REL TABLE` statement.

Nodes must be created before relationships because relationship tables refer to node tables.

### Step 6: Insert nodes

For each JSON node row, `insert_nodes()` creates Cypher such as:

```cypher
CREATE (n:Pose {
    name: 'Tree Pose',
    sanskrit_name: 'Vrikshasana',
    difficulty: 3,
    description: 'Single-leg balance pose',
    target_time: '30 seconds each side'
})
```

`cypher_literal()` converts Python values safely into Cypher literals:

- `None` to `NULL`
- Boolean to `true` or `false`
- Numbers without quotes
- Strings with quotes and escaping

### Step 7: Insert relationships

For each relationship row, the loader first locates both nodes by primary key and then creates the edge:

```cypher
MATCH
  (source:Pose {name: 'Tree Pose'}),
  (target:Benefit {name: 'Balance'})
CREATE
  (source)-[:TargetsBenefit {intensity: 8}]->(target)
```

This is why stable primary keys matter.

---

## 11. Run progressive Cypher queries

Start with:

```bash
akg query yoga --number 1
```

The CLI looks up `spec.queries[0]`, prints the title and teaching point, runs the Cypher through `db.execute()`, and formats the result as a table.

### Query 1: one-hop traversal

```cypher
MATCH (p:Pose)-[:BelongsToStyle]->(s:YogaStyle)
RETURN s.name, p.name, p.sanskrit_name, p.difficulty
ORDER BY s.name, p.difficulty
```

Read it in four parts:

- `MATCH`: describe the graph pattern.
- `(p:Pose)`: find Pose nodes and call each one `p`.
- `-[:BelongsToStyle]->`: follow the directed relationship.
- `(s:YogaStyle)`: reach YogaStyle nodes and call each one `s`.
- `RETURN`: select output properties.
- `ORDER BY`: sort the output.

### Query 2: relationship properties

```bash
akg query yoga --number 2
```

```cypher
MATCH (p:Pose)-[r:TargetsBenefit]->(b:Benefit)
RETURN p.name, b.name, b.category, r.intensity
ORDER BY r.intensity DESC
```

`r` names the relationship so its `intensity` property can be returned.

### Query 4: filtering

```bash
akg query yoga --number 4
```

```cypher
MATCH (p:Pose)
WHERE p.difficulty >= 7
RETURN p.name, p.sanskrit_name, p.difficulty
ORDER BY p.difficulty DESC
```

This query does not traverse an edge. Graph databases also support ordinary property filtering.

### Query 5: multi-path matching

```bash
akg query yoga --number 5
```

```cypher
MATCH
  (p:Pose)-[:BelongsToStyle]->(s:YogaStyle),
  (p)-[:TargetsBenefit]->(b:Benefit),
  (p)-[:HasType]->(t:PoseType)
RETURN p.name, s.name, b.name, t.name
```

All three patterns share the same `p`. The result combines style, benefit and type for each pose.

### Query 10: aggregation

```bash
akg query yoga --number 10
```

```cypher
MATCH (p:Pose)-[r:EngagesBodyPart]->(b:BodyPart)
WITH b, COUNT(p) AS poses, AVG(r.engagement_level) AS avg
RETURN b.name, poses, avg
ORDER BY poses DESC
```

`WITH` creates an intermediate result. `COUNT` and `AVG` summarize graph connections.

Run all ten:

```bash
akg query yoga --all
```

---

## 12. How query results are formatted

`db.execute()` does three jobs:

1. Sends Cypher to KuzuDB.
2. Reads column names.
3. Iterates through every result row.

It returns a `QueryTable`:

```python
QueryTable(
    columns=("p.name", "b.name", "r.intensity"),
    rows=(("Tree Pose", "Balance", 8), ...),
)
```

`QueryTable.to_text()` calculates column widths and prints a readable terminal table. Keeping results in a structured object is important because the same rows are later reused for GraphRAG context.

---

## 13. GraphRAG in this repository

Traditional RAG often retrieves text chunks by semantic similarity.

```text
Question → vector search → similar text chunks → LLM
```

GraphRAG retrieves facts by following graph structure.

```text
Question → choose graph query → traverse relationships → evidence rows → answer
```

This repository deliberately uses known Cypher queries rather than dynamically generating Cypher with an LLM. That makes the retrieval step safe, repeatable and explainable for beginners.

Build the professional graph:

```bash
akg build professional --reset
```

Ask:

```bash
akg ask "Which skills are expert level?" --domain professional --show-context
```

Execution path:

```text
cli.py command_ask()
        ↓
GraphAgent.ask()
        ↓
context.py retrieve_context()
        ↓
select_query()
        ↓
db.connect() and db.execute()
        ↓
RetrievalContext
        ↓
GraphAgent._grounded_summary()
```

---

## 14. How domain routing works

When `--domain` is supplied, the agent uses that domain directly.

When it is omitted, `GraphAgent.choose_domain()`:

1. Converts the question to lowercase.
2. Checks each domain's keyword list.
3. Counts keyword matches.
4. Selects the domain with the highest score.
5. Falls back to `professional` when no keyword matches.

Example:

```text
"Find circular account transfers for AML"
```

matches keywords such as `account`, `transfer` and `aml`, so the cycle domain is selected.

This is a rule-based router, not machine learning. It is intentionally simple so students can inspect and modify it.

---

## 15. How query routing works

After a domain is selected, `context.select_query()` chooses one of that domain's ten stored queries.

Examples:

- `beginner` or `easy` in Yoga selects the beginner-pose query.
- `confidence` in Fraud selects high-confidence detection.
- `four-step` in Cycle selects the four-step cycle query.
- `route` in Migration selects the complete-route query.
- `skill` or `expert` in Professional selects expertise classification.

If no rule matches, the domain's `default_query` is used.

This is important for the demo: the user question is not converted into arbitrary Cypher. It selects a reviewed query from `domains.py`.

---

## 16. How the GraphRAG context pack is created

`retrieve_context()` returns a `RetrievalContext` containing:

```text
domain
question
query number
query title
Cypher statement
structured result table
```

`as_prompt_context()` converts it into:

```text
DOMAIN: professional
QUESTION: Which skills are expert level?
RETRIEVAL QUERY: Expertise classification
CYPHER: MATCH ...
GRAPH EVIDENCE:
...
INSTRUCTION: Answer only from the graph evidence. State when evidence is insufficient.
```

This is the core GraphRAG teaching point. The model should receive:

- the original question,
- the exact retrieval strategy,
- graph evidence,
- and a grounding instruction.

The context also provides provenance because the selected Cypher is visible.

---

## 17. What makes the agent “agentic”

The current agent performs a small decision loop:

```text
Observe the question
        ↓
Choose a domain
        ↓
Choose a retrieval strategy
        ↓
Use KuzuDB as a tool
        ↓
Inspect evidence
        ↓
Generate a grounded response
```

The default answer generator is not an external LLM. `_grounded_summary()` displays up to five retrieved rows and explicitly states that the answer is based only on graph evidence.

This design has three advantages for training:

- No API key is required.
- Every decision is visible.
- Retrieval can be tested independently from generation.

Later, students can inject an external answer generator through the `answer_generator` constructor parameter, while keeping the retrieval process unchanged.

---

## 18. Cycle detection demonstration

Build the graph:

```bash
akg build cycle --reset
```

Show a known four-step Cypher pattern:

```bash
akg query cycle --number 5
```

Then run Python DFS:

```bash
akg cycles
```

`graph_cycles()` first asks KuzuDB for all directed account edges:

```cypher
MATCH (a:Account)-[:Transfers]->(b:Account)
RETURN a.account_id, b.account_id
```

It creates an adjacency list:

```python
{
    "A": ["B"],
    "B": ["C"],
    "C": ["D"],
    "D": ["A"],
}
```

`find_cycles()` then uses depth-first search:

1. Start at one account.
2. Follow each outgoing edge.
3. Track the current path.
4. Stop when the maximum length is exceeded.
5. Record a cycle when the path returns to the start.
6. Canonicalize rotations so `A-B-C-A` and `B-C-A-B` are not counted separately.

Compare the approaches:

- Fixed-length Cypher is excellent for a known typology.
- DFS can discover cycles of different lengths.

Production systems must also consider timestamps, transaction direction, amounts, repeated nodes, false positives and investigation thresholds.

---

## 19. Recommended live demo script

### Part A: concepts

Draw:

```text
(Tree Pose)-[:TargetsBenefit {intensity: 8}]->(Balance)
```

Ask students to identify node, edge and property.

### Part B: inspect the model

Open:

```text
src/agentic_knowledge_graph/domains.py
data/yoga.json
```

Compare `NodeSpec` with one JSON row, and `RelationshipSpec` with one relationship row.

### Part C: validate and build

```bash
akg validate
akg build yoga --reset
```

Explain each internal function in the execution path.

### Part D: grow query complexity

```bash
akg query yoga --number 1
akg query yoga --number 2
akg query yoga --number 4
akg query yoga --number 5
akg query yoga --number 10
```

### Part E: GraphRAG

```bash
akg ask "Which poses improve flexibility?" --domain yoga --show-context
akg build professional --reset
akg ask "Which skills are expert level?" --domain professional --show-context
```

Point out the domain, query number, evidence rows, Cypher and final grounding instruction.

### Part F: agent routing

```bash
akg ask "Show high-confidence fraud detection methods" --show-context
akg build cycle --reset
akg ask "Show the four-step account cycle" --show-context
```

Ask students to predict the selected domain and query before running each command.

---

## 20. Student hands-on exercise

### Exercise 1: add a new pose

Add a `Bridge Pose` row to the `Pose` array in `data/yoga.json`.

Add relationships:

```text
Bridge Pose → BelongsToStyle → Hatha
Bridge Pose → TargetsBenefit → Flexibility
Bridge Pose → EngagesBodyPart → Spine
Bridge Pose → HasType → suitable existing type
```

Then run:

```bash
akg validate
akg build yoga --reset
akg query yoga --all
```

### Exercise 2: create a query

Add an eleventh query in a local experimental branch that finds poses targeting both Strength and Flexibility.

Questions to answer:

- Which node is shared between the two paths?
- Should intensity be part of the filter?
- How will the CLI query-number range need to change?

### Exercise 3: improve routing

Add words such as `flexibility`, `balance` and `strength` to the Yoga query-selection rules. Add tests proving the correct query is selected.

### Exercise 4: extend context

Add source and last-updated properties to the professional skill relationship. Explain how these properties improve trust in the answer.

---

## 21. Common errors and fixes

### `akg: command not found`

Activate the virtual environment and run:

```bash
pip install -e .
```

Alternative:

```bash
python -m agentic_knowledge_graph list-domains
```

### `Kuzu is not installed`

```bash
pip install kuzu==0.11.3
```

### `Database already exists`

```bash
akg build yoga --reset
```

### `Build the graph first`

The query and ask commands do not automatically create a database.

```bash
akg build <domain> --reset
```

### Validation reports an unknown source or target

Check that `from` and `to` exactly match primary-key values in the node data. Matching is case-sensitive.

### A question selects the wrong query

Read `select_query()` in `context.py`. The system is rule-based, so add or adjust a keyword and write a regression test.

---

## 22. Production discussion

The repository is intentionally small and educational. A production GraphRAG platform would usually add:

- Bulk and incremental loading instead of one `CREATE` per row.
- Source document, chunk, version and timestamp nodes.
- Access control and sensitive-data filtering.
- Embedding or full-text candidate retrieval.
- Entity resolution and duplicate management.
- Query allow-lists or generated-Cypher validation.
- Observability for latency, selected query and result count.
- Evaluation for retrieval relevance, answer groundedness and completeness.
- Human review before agent write-back becomes trusted knowledge.
- Data-quality rules and graph schema migrations.
- Limits for path depth and result size.

Do not confuse a graph path with proof. The graph is only as reliable as its sources, modelling and update process.

---

## 23. Review questions

1. Why is proficiency stored on `HasSkill` rather than on `Skill`?
2. Why must node tables be created before relationship tables?
3. How does validation detect a dangling relationship?
4. What does `--reset` protect against?
5. What is the difference between one-hop and multi-hop retrieval?
6. What information is included in `RetrievalContext`?
7. Why does the beginner agent use reviewed queries instead of generating arbitrary Cypher?
8. What happens when no domain keyword matches?
9. How does DFS avoid counting rotated versions of the same cycle?
10. What provenance should be added before using this pattern in production?

---

## 24. Final summary

The complete repository flow is:

```text
Student command
      ↓
cli.py parses arguments
      ↓
validation.py checks JSON integrity
      ↓
domains.py supplies schema and reviewed queries
      ↓
loader.py creates Kuzu tables and inserts nodes/relationships
      ↓
db.py executes Cypher and returns structured rows
      ↓
context.py selects retrieval and builds an evidence pack
      ↓
agent.py selects a domain and produces a grounded response
```

The most important lesson is not merely how to create a graph. It is how to keep the full AI answer path explainable:

```text
Question → selected domain → selected Cypher → graph rows → context → answer
```

A beginner who can trace that path understands the foundation required for larger GraphRAG and agentic knowledge-graph systems.
