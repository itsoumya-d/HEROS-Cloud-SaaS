# SPDX-License-Identifier: MIT
import json
import threading
import unittest
import urllib.request

from heros_cloud.agent_orchestrator import AgentOrchestrator
from heros_cloud.server import start_server


class TestAgentOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AgentOrchestrator()

    def test_context_assembly_and_variable_substitution(self):
        ctx = self.orchestrator.build_context(
            prompt="Plan travel itinerary for {user} to {destination}",
            context_vars={"user": "Alex", "destination": "Wellington"},
            contract_schema={"itinerary": "list", "total_days": "int"},
            max_tokens=2048,
        )
        self.assertEqual(ctx.prompt, "Plan travel itinerary for Alex to Wellington")
        self.assertEqual(ctx.max_tokens, 2048)
        self.assertEqual(ctx.contract_schema["total_days"], "int")

    def test_contract_verification_pass(self):
        raw_output = {
            "title": "Corporate Flight Optimization",
            "score": 9.5,
            "segments": ["AKL-WLG"],
        }
        schema = {"title": "str", "score": "float", "segments": "list"}
        res = self.orchestrator.verify_contract(raw_output, schema, auto_repair=False)
        self.assertTrue(res.passed)
        self.assertFalse(res.repaired)
        self.assertEqual(res.validated_output["title"], "Corporate Flight Optimization")

    def test_contract_verification_auto_repair(self):
        # Non-deterministic LLM output with missing field and string int
        raw_output = {
            "title": "Marketplace Booking",
            "score": "8",
        }
        schema = {"title": "str", "score": "int", "items": "list", "notes": "str"}
        res = self.orchestrator.verify_contract(raw_output, schema, auto_repair=True)
        self.assertTrue(res.passed)
        self.assertTrue(res.repaired)
        self.assertEqual(res.validated_output["score"], 8)
        self.assertEqual(res.validated_output["items"], [])
        self.assertEqual(res.validated_output["notes"], "")

    def test_orchestrate_end_to_end(self):
        ctx = self.orchestrator.build_context(
            prompt="Generate travel policy compliance summary",
            contract_schema={"action": "str", "confidence": "float"},
        )
        result = self.orchestrator.orchestrate(ctx)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["verification"]["passed"])
        self.assertIn("latency_ms", result["telemetry"])

    def test_streaming_orchestration_ttft_and_sse(self):
        ctx = self.orchestrator.build_context(prompt="Stream analysis")
        chunks = ["Connecting to travel GDS...", "Resolving pricing...", "Itinerary confirmed."]
        events = list(self.orchestrator.stream_orchestration(ctx, chunks))
        self.assertEqual(len(events), 3)

        first_sse, first_telemetry = events[0]
        self.assertTrue(first_sse.startswith("data: "))
        self.assertEqual(first_telemetry.chunks_sent, 1)
        self.assertFalse(first_telemetry.verified)

        last_sse, last_telemetry = events[-1]
        self.assertEqual(last_telemetry.chunks_sent, 3)
        self.assertTrue(last_telemetry.verified)


class TestServerAgentEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server(port=8794)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_orchestrate_http_endpoint(self):
        req_data = json.dumps({
            "prompt": "Orchestrate agent flow for {role}",
            "context_vars": {"role": "travel-manager"},
            "schema": {"summary": "str", "confidence": "float"},
        }).encode()

        req = urllib.request.Request(
            "http://127.0.0.1:8794/v1/agent/orchestrate",
            data=req_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode())
            self.assertEqual(payload["status"], "success")
            self.assertTrue(payload["verification"]["passed"])

    def test_stream_http_endpoint(self):
        req_data = json.dumps({
            "prompt": "Stream test",
            "chunks": ["chunk A", "chunk B"],
        }).encode()

        req = urllib.request.Request(
            "http://127.0.0.1:8794/v1/agent/stream",
            data=req_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            raw = resp.read().decode()
            self.assertIn("chunk A", raw)
            self.assertIn("chunk B", raw)


if __name__ == "__main__":
    unittest.main()
