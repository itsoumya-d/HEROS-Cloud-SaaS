# SPDX-License-Identifier: MIT
from .types import Workflow

FAMILIES = {
    "migration": ["inspect_schema", "expand_column", "backfill", "drop_column", "validate"],
    "invoice": ["calculate_tax", "create_invoice", "send_invoice", "reconcile"],
    "crm": ["load_account", "update_account", "merge_records", "sync"],
    "compliance": ["collect_evidence", "attest_control", "archive"],
}
RISKY = {
    "migration": "drop_column",
    "invoice": "send_invoice",
    "crm": "merge_records",
    "compliance": "attest_control",
}


def generate_workflows(count: int = 50) -> list[Workflow]:
    workflows = []
    families = list(FAMILIES)
    for index in range(count):
        family = families[index % len(families)]
        actions = FAMILIES[family]
        steps = tuple({"action": action, "risk": action == RISKY[family]} for action in actions)
        workflows.append(
            Workflow(
                id=f"wf-{index+1:03d}",
                family=family,
                title=f"{family} workflow {index+1}",
                steps=steps,
                risk_action=RISKY[family],
            )
        )
    return workflows
