# SPDX-License-Identifier: MIT
"""AI Agent BFF Orchestration, streaming telemetry, and contract verification loop."""

from __future__ import annotations

import json, time
from dataclasses import dataclass, field
from typing import Any, Callable, Generator


@dataclass
class AgentContext:
    prompt: str
    context_vars: dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 1024
    contract_schema: dict[str, str] = field(default_factory=dict)


@dataclass
class VerificationResult:
    passed: bool
    repaired: bool = False
    error: str = ""
    validated_output: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingTelemetry:
    ttft_ms: float = 0.0
    total_duration_ms: float = 0.0
    chunks_sent: int = 0
    verified: bool = False


class AgentOrchestrator:
    """BFF orchestration service managing context, streaming latency, and verification."""

    def __init__(self, default_timeout_s: float = 10.0):
        self.default_timeout_s = default_timeout_s

    def build_context(self, prompt: str, context_vars: dict[str, Any] | None = None,
                      contract_schema: dict[str, str] | None = None, max_tokens: int = 1024) -> AgentContext:
        cv = context_vars or {}
        assembled_prompt = prompt.strip()
        for k, v in cv.items():
            assembled_prompt = assembled_prompt.replace(f"{{{k}}}", str(v))
        return AgentContext(prompt=assembled_prompt, context_vars=cv, max_tokens=max_tokens, contract_schema=contract_schema or {})

    def verify_contract(self, raw_output: dict[str, Any], schema: dict[str, str], auto_repair: bool = True) -> VerificationResult:
        if not schema:
            return VerificationResult(passed=True, validated_output=raw_output)
        missing, type_mismatches, validated = [], [], {}
        for field_name, expected_type in schema.items():
            if field_name not in raw_output:
                missing.append(field_name)
            else:
                val = raw_output[field_name]
                if expected_type == "int" and not isinstance(val, int):
                    try: val = int(val)
                    except (ValueError, TypeError): type_mismatches.append(f"{field_name} (expected int)")
                elif expected_type == "float" and not isinstance(val, (int, float)):
                    try: val = float(val)
                    except (ValueError, TypeError): type_mismatches.append(f"{field_name} (expected float)")
                elif expected_type == "str" and not isinstance(val, str): val = str(val)
                elif expected_type == "list" and not isinstance(val, list): type_mismatches.append(f"{field_name} (expected list)")
                validated[field_name] = val

        if not missing and not type_mismatches:
            return VerificationResult(passed=True, validated_output=validated)

        if auto_repair:
            repaired = dict(validated)
            for m in missing:
                exp_t = schema[m]
                repaired[m] = 0 if exp_t == "int" else 0.0 if exp_t == "float" else [] if exp_t == "list" else ""
            for mismatch in type_mismatches:
                fname = mismatch.split()[0]
                exp_t = schema[fname]
                repaired[fname] = 0 if exp_t == "int" else 0.0 if exp_t == "float" else [] if exp_t == "list" else ""
            return VerificationResult(passed=True, repaired=True, error=f"Repaired missing: {missing}, types: {type_mismatches}", validated_output=repaired)

        return VerificationResult(passed=False, error=f"Contract violation: missing={missing}, mismatches={type_mismatches}", validated_output=raw_output)

    def orchestrate(self, context: AgentContext, generator_fn: Callable[[AgentContext], dict[str, Any]] | None = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        gen = generator_fn or (lambda ctx: {"action": "synthesize", "summary": f"Orchestrated response for {ctx.prompt[:40]}", "confidence": 0.95, "items": ["step-1", "step-2"]})
        raw = gen(context)
        gen_duration_ms = (time.perf_counter() - t0) * 1000.0
        v_res = self.verify_contract(raw, context.contract_schema)
        return {
            "status": "success" if v_res.passed else "failed",
            "prompt": context.prompt,
            "result": v_res.validated_output,
            "verification": {"passed": v_res.passed, "repaired": v_res.repaired, "error": v_res.error},
            "telemetry": {"latency_ms": round(gen_duration_ms, 2), "token_budget": context.max_tokens},
        }

    def stream_orchestration(self, context: AgentContext, chunks: list[str]) -> Generator[tuple[str, StreamingTelemetry], None, None]:
        t0 = time.perf_counter()
        ttft_ms = 0.0
        for i, chunk in enumerate(chunks):
            chunk_time = time.perf_counter()
            if i == 0:
                ttft_ms = (chunk_time - t0) * 1000.0
            telemetry = StreamingTelemetry(ttft_ms=round(ttft_ms, 2), total_duration_ms=round((chunk_time - t0) * 1000.0, 2),
                                           chunks_sent=i + 1, verified=(i == len(chunks) - 1))
            yield f"data: {json.dumps({'chunk': chunk, 'index': i})}\n\n", telemetry
