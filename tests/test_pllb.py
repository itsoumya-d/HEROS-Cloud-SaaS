# SPDX-License-Identifier: MIT
import unittest

from heros_cloud.engine import WorkflowEngine
from heros_cloud.eval import run_evaluation
from heros_cloud.policies import PolicyStore
from heros_cloud.pllb import PolicyLearner
from heros_cloud.workflows import generate_workflows


class PLLBTests(unittest.TestCase):
    def test_distills_approves_and_improves_completion(self):
        workflows = generate_workflows(50)
        train, test = workflows[:30], workflows[30:]
        baseline = WorkflowEngine(PolicyStore())
        train_executions = [baseline.execute(workflow) for workflow in train]
        baseline_test = [baseline.execute(workflow) for workflow in test]

        store = PolicyStore()
        learner = PolicyLearner(store)
        drafts = learner.distill(train, train_executions)
        self.assertEqual(len(drafts), 4)
        learner.approve_all()

        governed = WorkflowEngine(store)
        governed_test = [governed.execute(workflow) for workflow in test]
        baseline_rate = sum(1 for item in baseline_test if item.success) / len(baseline_test)
        governed_rate = sum(1 for item in governed_test if item.success) / len(governed_test)
        self.assertGreater(governed_rate, baseline_rate)
        self.assertEqual(governed_rate, 1.0)
        self.assertTrue(all(item.policies_applied for item in governed_test))

    def test_evaluation_shape(self):
        result = run_evaluation()
        self.assertEqual(result["workflows_total"], 50)
        self.assertEqual(result["approved_policies"], 4)
        self.assertGreater(result["completion_delta"], 0)


if __name__ == "__main__":
    unittest.main()
