# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Workflow:
    id: str
    family: str
    title: str
    steps: tuple[dict, ...]
    risk_action: str


@dataclass
class StepResult:
    action: str
    status: str
    detail: str
    receipt_hash: str


@dataclass
class Execution:
    workflow_id: str
    family: str
    success: bool
    steps: list[StepResult] = field(default_factory=list)
    policies_applied: list[str] = field(default_factory=list)
    merkle_root: str = ""
    receipt_coverage: float = 0.0
