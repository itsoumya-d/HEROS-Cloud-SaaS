# HEROS-Cloud-SaaS

A composition layer for HEROS Cloud: a workflow execution studio governed by
**Policy Learning with a Language Bottleneck (PLLB)**.

Workflows run through a deterministic engine that emits a cryptographic receipt
for every step. After a batch of executions, PLLB observes risk-gate events and
failures and synthesises explicit natural-language policy rules. A human reviews
and approves those rules; the next episode runs with the approved policies and
produces a higher completion rate.

## PLLB loop

```
batch of workflows
        │
        ▼
  execute + receipts
        │  risk gates / failures
        ▼
  synthesise linguistic rules
  "When a migration includes drop_column,
   require a human-approved rollback plan..."
        │
        ▼
  human approves / edits rules
        │
        ▼
  next episode with approved policy
```

No model weights are updated. The only learned state is the human-readable policy
store.

## Composition

The API is designed to sit in front of the HEROS modules:

| HEROS component | Integration point |
|---|---|
| HEROS-RL / forge | migration-risk steps |
| HEROS-Firewall | approval and receipt semantics |
| edgeinfer-v2 | local command/embedding edge |
| peervault datamesh | shared policy/vector state |
| GraphRAG-CodeAudit | audit evidence retrieval |
| RouteLLM-Gateway | model routing for text/voice commands |

This repository implements the workflow, policy, approval, receipt, evaluation,
and API layers with a deterministic simulator. The external modules are not
vendored or deployed here.

## Results

`python scripts/evaluate.py` on 50 workflows (30 train, 20 held-out):

| Metric | Baseline | PLLB-governed |
|---|---:|---:|
| Completion rate | 70.0% | **100.0%** |
| Receipt coverage | 100% | 100% |
| Policy applications | 0 | 20 |

PLLB distilled **4** rules, all approved; completion improved **+30 percentage
points** on held-out workflows. `results/eval.json` contains the full evidence.

This is a deterministic simulation, not a customer deployment or ARR result.

## API

```bash
python -m heros_cloud.server --port 8790
# GET  /health
# GET  /v1/pricing
# GET  /v1/policies
# GET  /v1/receipts
# POST /v1/workflows/execute   {"id": "wf-049"}
# POST /v1/pllb/distill
# POST /v1/policies/approve    {"id": "pol-..."}
# POST /v1/evaluate
```

Pricing tiers: Free $0, Pro **$299/mo**, Enterprise **$999/mo**. These are API
data, not a claim of live billing or revenue.

## Tests

```bash
python -m unittest discover -s tests -v
```

6 tests cover workflow generation, baseline failure/receipt coverage, PLLB
distillation/approval/improvement, evaluation shape, and the HTTP policy and
execution lifecycle.

## Limitations

- **No real voice/audio.** Text commands are the interface; WebRTC/Whisper/Silero
  VAD were not available.
- **No hosted UI/dashboard.** Mobbin MCP was unavailable; the JSON API is the
  deliverable. The pricing tiers are not a checkout flow.
- **No OCI k3s, Oracle Autonomous AI Database, or Hugging Face deployment.**
  Cloud/HF credentials were unavailable.
- **No $200k ARR claim.** No customers, billing, or production traffic.
- The workflow simulator is synthetic and deterministic; it is not a production
  CRM, ledger, or migration system.

## License

MIT. Copyright (c) 2024-2026 Soumya Debnath.
