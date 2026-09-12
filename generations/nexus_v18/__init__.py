"""NEXUS V18 — Unified Internal Small-World Intelligence.

Provenance: copied from Shtenco/agi_olga@68023d51825eeefe5432263c863468e44636d862
  path: nexus_v18/
Original source remains authoritative for historical R&D.
"""
from .model import NexusV18Unified, ARCGraphRanker, RussianSmallWorldReasoner, SmallWorldDynamics
from .system import NexusV18System
from .russian_runtime import RussianGraphLogicRuntime, ChainProof

__all__ = [
    'NexusV18Unified',
    'ARCGraphRanker',
    'RussianSmallWorldReasoner',
    'SmallWorldDynamics',
    'NexusV18System',
    'RussianGraphLogicRuntime',
    'ChainProof',
]
