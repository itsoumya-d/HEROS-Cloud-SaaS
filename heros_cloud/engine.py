# SPDX-License-Identifier: MIT
import hashlib
import json
from dataclasses import asdict

from .policies import PolicyStore
from .types import Execution, StepResult, Workflow


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _merkle(leaves: list[str]) -> str:
    if not leaves:
        return "0" * 64
    level = list(leaves)
    while len(level) > 1:
        level = [
            hashlib.sha256((level[i] + level[(i + 1) if i + 1 < len(level) else i]).encode()).hexdigest()
            for i in range(0, len(level), 2)
        ]
    return level[0]


class WorkflowEngine:
    def __init__(self, policies: PolicyStore | None = None):
        self.policies = policies or PolicyStore()

    def execute(self, workflow: Workflow) -> Execution:
        execution = Execution(workflow_id=workflow.id, family=workflow.family, success=True)
        for step in workflow.steps:
            action = step["action"]
            risk = bool(step.get("risk"))
            matching = [rule for rule in self.policies.approved() if rule.matches(workflow.family, action)]
            if risk and not matching:
                # Deterministic baseline failure: 35% of ungated risky steps fail.
                failed = int(hashlib.sha256(f"{workflow.id}:{action}".encode()).hexdigest(), 16) % 100 < 35
                if failed:
                    execution.success = False
                    detail = "ungated destructive action failed; no rollback plan"
                    status = "failed"
                else:
                    detail = "ungated destructive action happened to succeed"
                    status = "warning"
            elif risk and matching:
                execution.policies_applied.append(matching[0].id)
                detail = "human approval + rollback plan verified"
                status = "approved"
            else:
                detail = "completed"
                status = "ok"
            receipt = _hash({"workflow": workflow.id, "action": action, "status": status, "detail": detail})
            execution.steps.append(StepResult(action=action, status=status, detail=detail, receipt_hash=receipt))
        execution.merkle_root = _merkle([step.receipt_hash for step in execution.steps])
        execution.receipt_coverage = sum(1 for step in execution.steps if step.receipt_hash) / max(1, len(execution.steps))
        return execution
