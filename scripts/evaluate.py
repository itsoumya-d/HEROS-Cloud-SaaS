#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from heros_cloud.eval import run_evaluation  # noqa: E402

result = run_evaluation()
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results" / "eval.json").write_text(json.dumps(result, indent=2) + "\n")
print("| Metric | Baseline | PLLB-governed |")
print("|---|---:|---:|")
for key in ["completion_rate", "receipt_coverage", "policy_applications"]:
    print(f"| {key} | {result['baseline'][key]} | {result['governed'][key]} |")
print(f"\nDraft policies: {len(result['draft_policies'])}, approved: {result['approved_policies']}")
print(f"Completion delta: {result['completion_delta']:+.2%}")
