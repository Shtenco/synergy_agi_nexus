from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class FormalIR:
    kind: str
    args: Dict[str, Any]
    source: str
    compiler_rule: str

@dataclass(frozen=True)
class ProofObject:
    kind: str
    premises: Dict[str, Any]
    conclusion: Any
    derivation: str
    solver_rule: str

@dataclass(frozen=True)
class Verification:
    status: str
    reason: str
    recomputed: Any = None

def dump_obj(x):
    return asdict(x) if hasattr(x, '__dataclass_fields__') else x
