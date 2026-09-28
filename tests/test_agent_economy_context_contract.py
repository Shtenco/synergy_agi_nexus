import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"contracts"/"agent_economy_context_v1.py"
s=importlib.util.spec_from_file_location("a",P);a=importlib.util.module_from_spec(s);assert s and s.loader;s.loader.exec_module(a)

def test_agent_economy_context_is_non_authoritative():
    p={"run_id":"r","tick":1,"active_agents":2,"external_assets":"10","internal_assets":"20","external_revenue":"1","mandate_mode":"simulation","payment_authority":False,"accounting_authority":False}
    x=a.consume_agent_economy_simulation(p)
    assert x["authorization"] is False
    assert x["simulation_context_only"] is True

def test_agent_economy_cannot_self_promote_payment():
    p={"run_id":"r","tick":1,"active_agents":2,"external_assets":"10","internal_assets":"20","external_revenue":"1","mandate_mode":"live","payment_authority":True,"accounting_authority":False}
    with pytest.raises(ValueError): a.consume_agent_economy_simulation(p)
