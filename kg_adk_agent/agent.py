"""Google ADK agent that can query and refine the KYC knowledge graph."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kg_chat import answer_question
from kg_chat import rebuild_outputs
from kg_chat import refine_graph_from_question

try:
    from google.adk import Agent
except ImportError:  # pragma: no cover - google-adk is optional until installed.
    Agent = None  # type: ignore[assignment]


def query_knowledge_graph(question: str) -> dict:
    """Answer a KYC onboarding question from the local knowledge graph."""
    return answer_question(question)


def refine_knowledge_graph(question: str) -> dict:
    """Persist a question, answer, and evidence links into the graph, then rebuild outputs."""
    result = answer_question(question)
    refinement = refine_graph_from_question(question, result["answer"])
    outputs = rebuild_outputs()
    return {"answer": result["answer"], "refinement": refinement, "outputs": outputs}


if Agent is None:
    root_agent = None
else:
    root_agent = Agent(
        name="kyc_knowledge_graph_agent",
        model=os.environ.get("KG_ADK_MODEL", "gemini-flash-latest"),
        instruction=(
            "You help KYC operations users inspect and refine a local Kuzu knowledge graph. "
            "Use query_knowledge_graph for ordinary questions. Use refine_knowledge_graph only "
            "when the user explicitly asks to save, refine, update, or add the question trail "
            "back into the graph. Keep answers concise and cite requirement IDs, policies, "
            "sections, controls, and systems returned by the tools."
        ),
        tools=[query_knowledge_graph, refine_knowledge_graph],
    )
