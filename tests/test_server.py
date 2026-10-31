# SPDX-License-Identifier: MIT
import json
import threading
import unittest
import urllib.request

from heros_cloud.server import start_server


def request(url, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server(port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_health_pricing_and_execution(self):
        self.assertTrue(request(f"{self.base}/health")["ok"])
        pricing = request(f"{self.base}/v1/pricing")
        self.assertEqual([tier["price"] for tier in pricing["tiers"]], [0, 299, 999])
        execution = request(f"{self.base}/v1/workflows/execute", "POST", {"id": "wf-049"})
        self.assertIn("success", execution)
        self.assertEqual(execution["receipt_coverage"], 1.0)

    def test_policy_lifecycle(self):
        drafts = request(f"{self.base}/v1/pllb/distill", "POST", {})["drafts"]
        self.assertGreater(len(drafts), 0)
        approved = request(f"{self.base}/v1/policies/approve", "POST", {"id": drafts[0]["id"]})
        self.assertTrue(approved["ok"])
        policies = request(f"{self.base}/v1/policies")["policies"]
        self.assertTrue(any(policy["status"] == "approved" for policy in policies))


if __name__ == "__main__":
    unittest.main()
