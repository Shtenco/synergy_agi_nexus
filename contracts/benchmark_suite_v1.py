from __future__ import annotations
from typing import Any

UPSTREAM_CONTRACT_ID="synergy.ai.benchmark-suite/v1"

def consume_benchmark_suite(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("generated_suite_only") is not True:
        raise ValueError("benchmark suite provenance missing")
    if bool(payload.get("agi_claim_authority")) or bool(payload.get("model_quality_claim_authority")):
        raise ValueError("generated suite cannot self-promote AGI/model-quality claims")
    digest=str(payload.get("suite_sha256","")).lower()
    if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid suite digest")
    count=int(payload.get("task_count",0))
    if count<=0:
        raise ValueError("empty benchmark suite")
    return {
        "kind":"BENCHMARK_SUITE",
        "benchmark_run_id":str(payload["benchmark_run_id"]),
        "benchmark":str(payload["benchmark"]),
        "task_count":count,
        "suite_sha256":digest,
        "generated_suite_only":True,
        "agi_claim_authority":False,
        "model_quality_claim_authority":False,
    }
