from __future__ import annotations
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

# NOTE: V18 originally imported from nexus_v13 inside agi_olga.
# During migration those modules are placed under generations/nexus_v13.
# Import path is adjusted to relative canonical location.
try:
    from generations.nexus_v13.formal_logic import ProofChecker, CyberneticController
    from generations.nexus_v13.russian_language import RussianMorphology, RussianRhetoric, Noun
except ImportError:  # fallback while sibling generation is still being migrated
    from nexus_v13.formal_logic import ProofChecker, CyberneticController
    from nexus_v13.russian_language import RussianMorphology, RussianRhetoric, Noun

_IMPL = re.compile(r"Если\s+([^.,;]+),\s*то\s+([^.,;]+)", re.IGNORECASE)
_CONC = re.compile(r"Следовательно,\s*([^.!?]+)", re.IGNORECASE)

@dataclass(frozen=True)
class ChainProof:
    valid: bool
    depth: int
    path: tuple[str, ...]
    explanation: str

class RussianGraphLogicRuntime:
    @staticmethod
    def parse_chain(text: str):
        edges = [(a.strip().casefold(), b.strip().casefold()) for a, b in _IMPL.findall(text)]
        m = _CONC.search(text)
        conclusion = m.group(1).strip().casefold() if m else None
        remainder = _CONC.sub('', _IMPL.sub('', text))
        facts = []
        for part in re.split(r'[.!?;]+', remainder):
            p = part.strip(' ,:')
            if p and not p.lower().startswith(('если', 'следовательно', 'тезис', 'цепочка', 'начальное условие', 'поэтому')):
                facts.append(p.casefold())
        return edges, facts, conclusion

    @staticmethod
    def prove_chain(text: str) -> ChainProof:
        edges, facts, conclusion = RussianGraphLogicRuntime.parse_chain(text)
        if not conclusion:
            return ChainProof(False, 0, (), "В тексте отсутствует явно сформулированное заключение.")
        graph = defaultdict(list)
        for a, b in edges:
            graph[a].append(b)
        q = deque((f, (f,)) for f in facts)
        seen = set(facts)
        while q:
            node, path = q.popleft()
            if node == conclusion:
                premises = [f"если {path[i]}, то {path[i+1]}" for i in range(len(path) - 1)]
                return ChainProof(
                    True,
                    max(0, len(path) - 1),
                    path,
                    RussianRhetoric.render_argument(
                        "заключение должно следовать из заданной цепочки",
                        [*premises, f"{path[0]} истинно"],
                        f"{conclusion} истинно",
                        "modus ponens",
                    ),
                )
            for nxt in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, (*path, nxt)))
        return ChainProof(False, 0, (), "Из указанных фактов заключение по цепочке импликаций не выводится.")

    @staticmethod
    def verify_formula(premises: Iterable[str], conclusion: str):
        return ProofChecker.entails(list(premises), conclusion)

    @staticmethod
    def feedback(target: float, observations: Iterable[float]):
        c = CyberneticController(target)
        return [c.update(x) for x in observations]

    @staticmethod
    def inflect(adjective: str, noun: Noun, case: str, number: str = 'sing'):
        return RussianMorphology.phrase(adjective, noun, case, number)
