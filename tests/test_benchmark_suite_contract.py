import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"contracts"/"benchmark_suite_v1.py"
s=importlib.util.spec_from_file_location("b",P);b=importlib.util.module_from_spec(s);assert s and s.loader;s.loader.exec_module(b)

def test_generated_suite_not_model_quality_claim():
    x=b.consume_benchmark_suite({"benchmark_run_id":"r","benchmark":"B","task_count":40,"suite_sha256":"1"*64,"generated_suite_only":True,"agi_claim_authority":False,"model_quality_claim_authority":False})
    assert x["agi_claim_authority"] is False

def test_suite_cannot_claim_agi():
    with pytest.raises(ValueError):
        b.consume_benchmark_suite({"benchmark_run_id":"r","benchmark":"B","task_count":40,"suite_sha256":"1"*64,"generated_suite_only":True,"agi_claim_authority":True,"model_quality_claim_authority":False})
