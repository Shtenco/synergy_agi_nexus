"""Formal proof and cybernetic feedback layer for Russian reasoning.

The proof layer follows classical inference. Cybernetic control is treated as the
separate post-1955 goal/error/feedback tradition, not mislabeled as Stalin-era
cybernetics.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import itertools, re
from typing import Iterable, Mapping, Sequence
_TOKEN = re.compile(r"\s*(<->|->|[()!&|]|[A-Za-zА-Яа-яЁё_][\wА-Яа-яЁё]*)")

class Formula:
    def __init__(self, text: str):
        self.text = text
        self.tokens = [m.group(1) for m in _TOKEN.finditer(text)]
        if not self.tokens and text.strip():
            raise ValueError("empty formula")
        self.position = 0
        self.tree = self._equivalence()
        if self.position != len(self.tokens):
            raise ValueError(f"unexpected token {self.tokens[self.position]}")

    def _peek(self, value=None):
        return self.position < len(self.tokens) and (value is None or self.tokens[self.position] == value)

    def _take(self, value=None):
        if not self._peek(value):
            raise ValueError(f"expected {value or 'token'}")
        token = self.tokens[self.position]
        self.position += 1
        return token

    def _equivalence(self):
        node = self._implication()
        while self._peek("<->"):
            self._take()
            node = ("<->", node, self._implication())
        return node

    def _implication(self):
        node = self._or()
        if self._peek("->"):
            self._take()
            node = ("->", node, self._implication())
        return node

    def _or(self):
        node = self._and()
        while self._peek("|"):
            self._take()
            node = ("|", node, self._and())
        return node

    def _and(self):
        node = self._not()
        while self._peek("&"):
            self._take()
            node = ("&", node, self._not())
        return node

    def _not(self):
        if self._peek("!"):
            self._take()
            return ("!", self._not())
        if self._peek("("):
            self._take()
            node = self._equivalence()
            self._take(")")
            return node
        token = self._take()
        if token in {"<->", "->", "&", "|", "!", "(", ")"}:
            raise ValueError("expected proposition")
        return ("var", token)

    def variables(self):
        found = set()

        def walk(node):
            if node[0] == "var":
                found.add(node[1])
            else:
                for child in node[1:]:
                    walk(child)

        walk(self.tree)
        return tuple(sorted(found))

    def evaluate(self, values: Mapping[str, bool]):
        def ev(node):
            op = node[0]
            if op == "var":
                return bool(values[node[1]])
            if op == "!":
                return not ev(node[1])
            left, right = ev(node[1]), ev(node[2])
            if op == "&":
                return left and right
            if op == "|":
                return left or right
            if op == "->":
                return (not left) or right
            if op == "<->":
                return left == right
            raise ValueError(op)

        return ev(self.tree)


@dataclass(frozen=True, slots=True)
class Proposition:
    text: str
    formula: Formula = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "formula", Formula(self.text))


@dataclass(frozen=True, slots=True)
class ProofResult:
    valid: bool
    rule: str
    counterexample: dict[str, bool] | None
    explanation: str


class ProofChecker:
    @staticmethod
    def entails(premises: Sequence[str | Proposition], conclusion: str | Proposition) -> ProofResult:
        p = [x if isinstance(x, Proposition) else Proposition(x) for x in premises]
        c = conclusion if isinstance(conclusion, Proposition) else Proposition(conclusion)
        variables = sorted({v for x in [*p, c] for v in x.formula.variables()})
        for bits in itertools.product((False, True), repeat=len(variables)):
            a = dict(zip(variables, bits))
            if all(x.formula.evaluate(a) for x in p) and not c.formula.evaluate(a):
                return ProofResult(False, "контрпример", a, "Посылки истинны, а заключение ложно при указанной оценке.")
        rule = ProofChecker._recognize([x.text.replace(" ", "") for x in p], c.text.replace(" ", ""))
        return ProofResult(True, rule, None, "Заключение необходимо следует из посылок во всех допустимых оценках.")

    @staticmethod
    def _recognize(premises: Sequence[str], conclusion: str):
        known = set(premises)
        for premise in premises:
            if "->" in premise:
                left, right = premise.split("->", 1)
                left = left.strip("()")
                right = right.strip("()")
                if left in known and right == conclusion:
                    return "modus ponens"
                if f"!{right}" in known and f"!{left}" == conclusion:
                    return "modus tollens"
        if len(premises) == 1 and premises[0] == conclusion:
            return "закон тождества"
        return "семантическое следование"

    @staticmethod
    def check_non_contradiction(statements: Iterable[str]):
        normalized = {s.replace(" ", "") for s in statements}
        for s in normalized:
            inverse = s[1:] if s.startswith("!") else "!" + s
            if inverse in normalized:
                return False, (s, inverse)
        return True, None

    @staticmethod
    def syllogism_all_all(subject: str, middle: str, predicate: str):
        return {
            "major": f"Все {middle} суть {predicate}.",
            "minor": f"Все {subject} суть {middle}.",
            "conclusion": f"Следовательно, все {subject} суть {predicate}.",
            "schema": "Barbara AAA-1",
        }


@dataclass(slots=True)
class CyberneticController:
    """Stable goal/error/feedback controller with integral anti-windup."""

    target: float
    gain: float = 0.90
    integral_gain: float = 0.005
    damping: float = 0.05
    integral_limit: float = 40.0
    integral: float = 0.0
    previous_error: float = 0.0

    def update(self, observation: float):
        error = self.target - float(observation)
        self.integral = max(-self.integral_limit, min(self.integral_limit, self.integral + error))
        derivative = error - self.previous_error
        control = self.gain * error + self.integral_gain * self.integral + self.damping * derivative
        self.previous_error = error
        return {"target": self.target, "observation": float(observation), "error": error, "feedback": control}
