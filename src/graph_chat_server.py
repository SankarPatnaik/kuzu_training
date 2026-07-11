"""Serve the knowledge graph with a local chat/refinement panel."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from kg_chat import answer_question
from kg_chat import rebuild_outputs
from kg_chat import refine_graph_from_question
from visualize_graph import DEFAULT_OUTPUT as GRAPH_OUTPUT

ROOT = Path(__file__).resolve().parents[1]


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KYC Knowledge Graph Chat</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --text: #202124;
      --muted: #5f6368;
      --border: #d9dadd;
      --accent: #155EEF;
      --accent-text: #ffffff;
      --soft: #eef2ff;
      --ok: #137333;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }
    .app {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 430px;
      min-height: 100vh;
    }
    .graph {
      border: 0;
      width: 100%;
      height: 100vh;
      background: var(--panel);
    }
    aside {
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-width: 0;
      height: 100vh;
      border-left: 1px solid var(--border);
      background: var(--panel);
      padding: 16px;
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
    .subtle {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .messages {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding-right: 4px;
    }
    .message {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      white-space: pre-wrap;
      line-height: 1.4;
      font-size: 14px;
    }
    .user {
      background: var(--soft);
    }
    .assistant {
      background: #fff;
    }
    .status {
      color: var(--ok);
      font-size: 13px;
    }
    textarea {
      width: 100%;
      min-height: 92px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      font: inherit;
    }
    .row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
    }
    label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
    }
    button {
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: var(--accent-text);
      padding: 9px 13px;
      font-weight: 600;
      cursor: pointer;
    }
    button:disabled {
      cursor: not-allowed;
      opacity: 0.55;
    }
    code {
      background: #f1f3f4;
      padding: 2px 4px;
      border-radius: 4px;
    }
    @media (max-width: 980px) {
      .app {
        grid-template-columns: 1fr;
      }
      .graph {
        height: 56vh;
      }
      aside {
        height: auto;
        min-height: 44vh;
        border-left: 0;
        border-top: 1px solid var(--border);
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <iframe class="graph" src="/graph" title="Knowledge graph"></iframe>
    <aside>
      <div>
        <h1>Graph chat</h1>
        <p class="subtle">Ask about policies, requirements, evidence, controls, or systems. When saved, the question, retrieved evidence, and answer trail are added back into the graph.</p>
      </div>
      <div class="messages" id="messages">
        <div class="message assistant">Try: What evidence blocks Atlas Robotics approval?</div>
      </div>
      <form id="chat-form">
        <textarea id="question" placeholder="Ask the knowledge graph..."></textarea>
        <div class="row">
          <label><input type="checkbox" id="apply" checked> save evidence trail</label>
          <button id="send" type="submit">Ask</button>
        </div>
      </form>
      <p class="subtle">For Vertex/Gemini through ADK, run <code>adk run kg_adk_agent</code> after configuring Google Cloud env vars.</p>
      <div class="status" id="status"></div>
    </aside>
  </main>
  <script>
    const form = document.getElementById("chat-form");
    const question = document.getElementById("question");
    const apply = document.getElementById("apply");
    const send = document.getElementById("send");
    const messages = document.getElementById("messages");
    const status = document.getElementById("status");

    function addMessage(text, cls) {
      const div = document.createElement("div");
      div.className = `message ${cls}`;
      div.textContent = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = question.value.trim();
      if (!text) return;
      addMessage(text, "user");
      question.value = "";
      send.disabled = true;
      status.textContent = apply.checked ? "Answering and refining graph..." : "Answering...";
      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({question: text, apply_refinement: apply.checked})
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Request failed");
        let reply = payload.answer;
        if (payload.refinement) {
          reply += `\\n\\nSaved to graph: ${payload.refinement.query_id} -> ${payload.refinement.context_id} -> ${payload.refinement.answer_id}`;
          document.querySelector(".graph").contentWindow.location.reload();
        }
        addMessage(reply, "assistant");
        status.textContent = payload.refinement ? "Graph refined and regenerated." : "";
      } catch (error) {
        addMessage(`Error: ${error.message}`, "assistant");
        status.textContent = "";
      } finally {
        send.disabled = false;
        question.focus();
      }
    });
  </script>
</body>
</html>
"""


class GraphChatHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/":
            self.send_html(HTML)
            return
        if route == "/graph":
            self.send_file(GRAPH_OUTPUT, "text/html; charset=utf-8")
            return
        if route == "/api/health":
            self.send_json({"status": "ok"})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        if route != "/api/chat":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("question is required")

            result = answer_question(question)
            response = {"answer": result["answer"], "matches": result["matches"]}
            if payload.get("apply_refinement"):
                refinement = refine_graph_from_question(question, result["answer"])
                outputs = rebuild_outputs()
                response["refinement"] = refinement
                response["outputs"] = outputs
            self.send_json(response)
        except Exception as exc:  # pragma: no cover - visible in browser response
            self.send_json({"error": str(exc)}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_html(self, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            rebuild_outputs()
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), GraphChatHandler)
    print(f"Graph chat available at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
