# HEROS-Cloud-SaaS Results

## Environment

| Item | Value |
|---|---|
| Date | 2026-10-31 |
| OS | macOS (Apple Silicon) |
| Python | 3.14.0 |
| Tests | 6/6 passing |
| Workflows | 50 synthetic (30 train / 20 held-out) |

## PLLB evaluation

Command: `python scripts/evaluate.py`

| Metric | Baseline | PLLB-governed |
|---|---:|---:|
| Completion rate | 0.7000 | 1.0000 |
| Receipt coverage | 1.0000 | 1.0000 |
| Policy applications | 0 | 20 |
| Draft policies | — | 4 |
| Approved policies | — | 4 |

Completion delta: **+30.00 percentage points**.

The four rules correspond to the risky action in each workflow family:
`drop_column` (migration), `send_invoice` (invoice), `merge_records` (CRM), and
`attest_control` (compliance). Each rule requires a human-approved rollback plan
and verified backup before execution. Baseline failures are deterministic:
35% of ungated risky steps fail.

## Tests

`python -m unittest discover -s tests -v` — 6 tests:

- 50 workflows across 4 families,
- baseline failures with 100% receipt coverage and Merkle roots,
- PLLB distill → 4 rules → approve → held-out completion improves to 100%,
- evaluation result shape,
- HTTP policy/execution lifecycle and pricing tiers.

## Not executed

- **Voice/audio studio** — no WebRTC/Whisper/VAD environment or microphone.
- **React/Next UI and Mobbin-driven conversion funnel** — Mobbin MCP unavailable.
- **OCI k3s, Oracle Autonomous AI Database, Prometheus/Grafana/Loki** — no cloud
  credentials.
- **Hugging Face Spaces/model/dataset cards** — no HF authentication.
- **Billing, customers, ARR** — no production deployment or payments.

## Reproduce

```bash
cd repos/HEROS-Cloud-SaaS
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/evaluate.py
python -m heros_cloud.server --port 8790
```
