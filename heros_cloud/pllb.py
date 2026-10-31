# SPDX-License-Identifier: MIT
"""Policy Learning with a Language Bottleneck.

After a batch of workflow executions, synthesise explicit natural-language rules
from risk-gate events and failures. Humans approve them before the next episode.
No model weights are updated.
"""

from __future__ import annotations

import hashlib

from .policies import PolicyRule, PolicyStore
from .types import Execution, Workflow


class PolicyLearner:
    def __init__(self, store: PolicyStore):
        self.store = store

    def distill(self, workflows: list[Workflow], executions: list[Execution]) -> list[PolicyRule]:
        by_id = {workflow.id: workflow for workflow in workflows}
        observations: dict[tuple[str, str], list[Execution]] = {}
        for execution in executions:
            workflow = by_id[execution.workflow_id]
            for step in execution.steps:
                if step.action == workflow.risk_action:
                    observations.setdefault((workflow.family, step.action), []).append(execution)
        drafts = []
        for (family, action), batch in sorted(observations.items()):
            failures = sum(1 for item in batch if not item.success)
            rule = PolicyRule(
                id="pol-" + hashlib.sha256(f"{family}:{action}".encode()).hexdigest()[:8],
                text=(
                    f"When a {family.replace('_', ' ')} workflow includes {action}, require a "
                    f"human-approved rollback plan and a verified backup before execution. "
                    f"Observed baseline failures: {failures}/{len(batch)}."
                ),
                family=family,
                action=action,
            )
            if self.store.add(rule):
                drafts.append(rule)
        return drafts

    def approve_all(self) -> int:
        approved = 0
        for rule in self.store.rules:
            if rule.status != "approved":
                self.store.approve(rule.id)
                approved += 1
        return approved
