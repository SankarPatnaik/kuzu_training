"""Invoke the KYC knowledge graph ADK agent once from the command line.

Requires google-adk and Google Cloud/Gemini authentication environment variables.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def require_adk():
    try:
        from google.adk.runners import Runner
        from google.genai import types
    except ImportError as exc:  # pragma: no cover - depends on optional package.
        raise SystemExit(
            "google-adk is not installed. Run: pip install google-adk"
        ) from exc

    try:
        from google.adk.sessions import InMemorySessionService
    except ImportError:
        from google.adk.sessions.in_memory_session_service import InMemorySessionService

    return Runner, InMemorySessionService, types


def extract_text(event) -> str:
    content = getattr(event, "content", None)
    if not content or not getattr(content, "parts", None):
        return ""
    return "\n".join(part.text for part in content.parts if getattr(part, "text", None))


async def invoke(question: str, session_id: str) -> str:
    Runner, InMemorySessionService, types = require_adk()
    from kg_adk_agent.agent import root_agent

    if root_agent is None:
        raise SystemExit("ADK Agent could not be constructed. Is google-adk installed?")

    app_name = "kg_adk_agent"
    user_id = "local-user"
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(app_name=app_name, agent=root_agent, session_service=session_service)
    message = types.Content(role="user", parts=[types.Part(text=question)])

    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        if event.is_final_response():
            text = extract_text(event)
            if text:
                final_text = text
    return final_text or "No final text response was returned by the ADK agent."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Question to ask the ADK agent")
    parser.add_argument("--session-id", default="local-session")
    args = parser.parse_args()
    print(asyncio.run(invoke(args.question, args.session_id)))


if __name__ == "__main__":
    main()
