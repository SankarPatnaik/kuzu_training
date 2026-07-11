# Instructor guide: Agentic Knowledge Graphs with KuzuDB

## Audience

Experienced software, data, AI and platform engineers who are new to graph modelling or GraphRAG.

## Recommended duration

- 60 minutes: concepts and live walkthrough
- 90 minutes: guided coding
- 60 minutes: team challenge and review

## Module 1 — Graph thinking

Explain three words:

- **Node:** a thing, such as a person, account, pose or policy.
- **Relationship:** a meaningful connection between two things.
- **Property:** context stored on a node or relationship.

Use this visual:

```text
(Person)-[:HAS_SKILL {proficiency: 94}]->(Skill)
```

Ask learners why proficiency belongs on the relationship rather than the Skill node. Answer: the value is specific to one person’s connection to that skill.

## Module 2 — From knowledge graph to context graph

A knowledge graph stores durable facts. A context graph adds the current situation:

```text
Person --HAS_SKILL--> Python
Person --AVAILABLE_FOR {from: July 2026}--> Project
Project --REQUIRES--> Python
```

Context may include time, source, user role, confidence, risk, access permission and current task.

## Module 3 — Kuzu schema

Open `domains.py` and examine one `NodeSpec` and one `RelationshipSpec`.

Live commands:

```bash
akg validate
akg build yoga --reset
akg query yoga --number 1
akg query yoga --number 5
akg query yoga --number 10
```

Teaching progression:

1. One node label.
2. One relationship.
3. Relationship property.
4. Filter.
5. Multi-hop path.
6. Aggregation.

## Module 4 — GraphRAG

GraphRAG is not merely “put a graph next to an LLM.” The important engineering flow is:

1. Understand the question.
2. Select a graph retrieval strategy.
3. Run an explainable traversal.
4. Format the returned rows as evidence.
5. Instruct the model to answer only from that evidence.
6. Return provenance: query, domain and evidence rows.

Demo:

```bash
akg build professional --reset
akg ask "Which skills are expert level?" --domain professional --show-context
```

Point out that the default agent is deterministic. This makes retrieval behaviour visible before an external LLM is introduced.

## Module 5 — Agentic behaviour

The repository’s agent uses a small, inspectable loop:

```text
Observe question
   ↓
Choose domain
   ↓
Choose retrieval query
   ↓
Execute graph traversal
   ↓
Build context
   ↓
Generate grounded answer
```

Production extensions can add planning, tool approval, retries, human review and write-back. Do not begin training with a complex multi-agent framework; first make the retrieval logic observable.

## Module 6 — Cycle detection

Build the cycle domain:

```bash
akg build cycle --reset
akg query cycle --number 5
akg cycles
```

Compare two methods:

- Fixed-length Cypher patterns: explainable and useful for known typologies.
- DFS in Python: discovers cycles of varying lengths.

Discuss deduplication, maximum path length and false positives.

## Team challenge

Each team chooses one task:

1. Add a new yoga pose and connect it to a style, benefit and body part.
2. Add a fraud indicator used by two detection methods.
3. Add a non-circular transfer and verify that DFS does not create a false cycle.
4. Add a new migration stopover and seasonal relationship.
5. Add a new engineer and rank skill coverage for a project.

## Production review checklist

- Is every important answer traceable to a graph path?
- Are source, version and timestamps represented?
- Are relationship directions meaningful?
- Are primary keys stable?
- Can the system distinguish absence of evidence from negative evidence?
- Are sensitive properties access-controlled or excluded?
- Are model answers evaluated for groundedness?
- Is graph write-back reviewed before becoming trusted knowledge?
