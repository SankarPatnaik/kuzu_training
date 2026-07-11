# Beginner Student Lab

Follow the full explanation in `TEACHING_GUIDE.md`. Use this page to complete the hands-on exercise.

## Part 1: Build and query

```bash
akg validate
akg build yoga --reset
akg query yoga --number 1
akg query yoga --number 2
akg query yoga --number 5
akg query yoga --number 10
```

For each query, write down:

- The starting node.
- The relationship followed.
- The target node.
- Any filter or aggregation.
- What business question the query answers.

## Part 2: Trace GraphRAG

```bash
akg ask "Which poses improve flexibility?" --domain yoga --show-context
```

Identify:

1. The selected domain.
2. The selected query number.
3. The Cypher statement.
4. The returned evidence rows.
5. The grounding instruction.

## Part 3: Extend the graph

Add `Bridge Pose` to `data/yoga.json` and connect it to a style, benefit, body part and pose type.

Then run:

```bash
akg validate
akg build yoga --reset
akg query yoga --all
```

## Part 4: Reflection

Answer these questions:

- Why should `from` and `to` reference primary keys?
- What error occurs when a relationship target does not exist?
- What is the difference between graph retrieval and answer generation?
- Which source and timestamp properties would you add for production use?
