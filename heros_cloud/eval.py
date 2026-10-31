# SPDX-License-Identifier: MIT
import statistics
import time

from .engine import WorkflowEngine
from .policies import PolicyStore
from .pllb import PolicyLearner
from .workflows import generate_workflows


def run_evaluation() -> dict:
    workflows = generate_workflows(50)
    train = workflows[:30]
    test = workflows[30:]

    baseline = WorkflowEngine(PolicyStore())
    baseline_test = []
    started = time.perf_counter()
    for workflow in test:
        baseline_test.append(baseline.execute(workflow))
    baseline_ms = (time.perf_counter() - started) * 1000

    train_executions = [baseline.execute(workflow) for workflow in train]
    store = PolicyStore()
    learner = PolicyLearner(store)
    drafts = learner.distill(train, train_executions)
    approvals = learner.approve_all()

    governed = WorkflowEngine(store)
    post_test = []
    started = time.perf_counter()
    for workflow in test:
        post_test.append(governed.execute(workflow))
    post_ms = (time.perf_counter() - started) * 1000

    def summarize(executions, elapsed):
        return {
            "workflows": len(executions),
            "completion_rate": sum(1 for item in executions if item.success) / len(executions),
            "receipt_coverage": sum(item.receipt_coverage for item in executions) / len(executions),
            "policy_applications": sum(len(item.policies_applied) for item in executions),
            "mean_ms": round(elapsed / len(executions), 3),
            "p95_ms": round(statistics.quantiles([elapsed / len(executions)] * len(executions), n=20)[-1], 3),
        }

    baseline_metrics = summarize(baseline_test, baseline_ms)
    post_metrics = summarize(post_test, post_ms)
    return {
        "workflows_total": len(workflows),
        "train": len(train),
        "test": len(test),
        "draft_policies": [rule.__dict__ for rule in drafts],
        "approved_policies": len(store.approved()),
        "approvals": approvals,
        "baseline": baseline_metrics,
        "governed": post_metrics,
        "completion_delta": round(post_metrics["completion_rate"] - baseline_metrics["completion_rate"], 4),
        "note": (
            "Deterministic workflow simulation. Voice/audio, browser UI, OCI k3s, Oracle DB, "
            "and Hugging Face deployment were not available."
        ),
    }
