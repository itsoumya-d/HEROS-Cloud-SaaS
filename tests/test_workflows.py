# SPDX-License-Identifier: MIT
import unittest

from heros_cloud.engine import WorkflowEngine
from heros_cloud.policies import PolicyStore
from heros_cloud.workflows import FAMILIES, generate_workflows


class WorkflowTests(unittest.TestCase):
    def test_50_workflows_cover_four_families(self):
        workflows = generate_workflows(50)
        self.assertEqual(len(workflows), 50)
        self.assertEqual({workflow.family for workflow in workflows}, set(FAMILIES))
        self.assertTrue(all(workflow.risk_action for workflow in workflows))

    def test_baseline_has_failures_and_full_receipt_coverage(self):
        engine = WorkflowEngine(PolicyStore())
        executions = [engine.execute(workflow) for workflow in generate_workflows(50)]
        self.assertLess(sum(1 for item in executions if item.success), len(executions))
        self.assertTrue(all(item.receipt_coverage == 1.0 for item in executions))
        self.assertTrue(all(len(item.merkle_root) == 64 for item in executions))


if __name__ == "__main__":
    unittest.main()
