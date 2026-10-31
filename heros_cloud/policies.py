# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field


@dataclass
class PolicyRule:
    id: str
    text: str
    family: str
    action: str
    status: str = "draft"
    source: str = "pllb"
    approvals: int = 0

    def matches(self, family: str, action: str) -> bool:
        return self.status == "approved" and self.family == family and self.action == action


class PolicyStore:
    def __init__(self):
        self.rules: list[PolicyRule] = []

    def add(self, rule: PolicyRule) -> bool:
        if any(existing.text == rule.text for existing in self.rules):
            return False
        self.rules.append(rule)
        return True

    def approve(self, rule_id: str) -> bool:
        for rule in self.rules:
            if rule.id == rule_id:
                rule.status = "approved"
                rule.approvals += 1
                return True
        return False

    def approved(self) -> list[PolicyRule]:
        return [rule for rule in self.rules if rule.status == "approved"]

    def render(self) -> str:
        return "\n".join(f"- [{rule.status}] {rule.text}" for rule in self.rules)
