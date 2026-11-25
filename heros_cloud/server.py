# SPDX-License-Identifier: MIT
"""Minimal HEROS Cloud API: execution, PLLB policies, receipts, pricing."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .agent_orchestrator import AgentOrchestrator
from .engine import WorkflowEngine
from .eval import run_evaluation
from .policies import PolicyStore
from .pllb import PolicyLearner
from .workflows import generate_workflows

WORKFLOWS = {workflow.id: workflow for workflow in generate_workflows(50)}
STORE = PolicyStore()
ENGINE = WorkflowEngine(STORE)
AGENT_SERVICE = AgentOrchestrator()
EXECUTIONS = []
PRICING = [
    {"name": "Free", "price": 0, "features": ["MIT CLI", "Local workflows", "No hosted receipts"]},
    {"name": "Pro", "price": 299, "features": ["Hosted receipts", "PLLB policy studio", "Voice/text commands"]},
    {"name": "Enterprise", "price": 999, "features": ["SSO", "Compliance exports", "Dedicated support"]},
]


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self) -> bool:
        expected = os.environ.get("HEROS_API_KEY", "")
        if not expected:
            return True
        return self.headers.get("authorization") == f"Bearer {expected}"

    def do_GET(self):
        if not self._auth():
            return self._send(401, {"error": "unauthorized"})
        if self.path == "/health":
            return self._send(200, {"ok": True, "service": "heros-cloud", "version": "0.1.0"})
        if self.path == "/v1/pricing":
            return self._send(200, {"tiers": PRICING})
        if self.path == "/v1/policies":
            return self._send(200, {"policies": [rule.__dict__ for rule in STORE.rules]})
        if self.path == "/v1/receipts":
            return self._send(200, {"receipts": [asdict(execution) for execution in EXECUTIONS]})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return self._send(401, {"error": "unauthorized"})
        length = int(self.headers.get("content-length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON"})
        if self.path == "/v1/workflows/execute":
            workflow = WORKFLOWS.get(body.get("id"))
            if not workflow:
                return self._send(404, {"error": "workflow not found"})
            execution = ENGINE.execute(workflow)
            EXECUTIONS.append(execution)
            return self._send(200, asdict(execution))
        if self.path == "/v1/pllb/distill":
            train = list(WORKFLOWS.values())[:30]
            executions = [ENGINE.execute(workflow) for workflow in train]
            drafts = PolicyLearner(STORE).distill(train, executions)
            return self._send(200, {"drafts": [rule.__dict__ for rule in drafts]})
        if self.path == "/v1/policies/approve":
            if STORE.approve(body.get("id", "")):
                return self._send(200, {"ok": True})
            return self._send(404, {"error": "policy not found"})
        if self.path == "/v1/evaluate":
            return self._send(200, run_evaluation())
        if self.path == "/v1/agent/orchestrate":
            prompt = body.get("prompt", "")
            schema = body.get("schema", {})
            context = AGENT_SERVICE.build_context(
                prompt=prompt,
                context_vars=body.get("context_vars", {}),
                contract_schema=schema,
                max_tokens=body.get("max_tokens", 1024),
            )
            return self._send(200, AGENT_SERVICE.orchestrate(context))
        if self.path == "/v1/agent/stream":
            prompt = body.get("prompt", "")
            chunks = body.get("chunks", ["analyzing context", "synthesizing output", "completed"])
            context = AGENT_SERVICE.build_context(prompt=prompt)
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("cache-control", "no-cache")
            self.end_headers()
            for sse, _ in AGENT_SERVICE.stream_orchestration(context, chunks):
                self.wfile.write(sse.encode())
            return
        return self._send(404, {"error": "not found"})

    def log_message(self, *_args):
        pass


def start_server(host: str = "127.0.0.1", port: int = 8790):
    server = ThreadingHTTPServer((host, port), Handler)
    return server


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()
    server = start_server(port=args.port)
    print(f"HEROS Cloud listening on http://127.0.0.1:{args.port}")
    server.serve_forever()
