"""Rule-based Russian morphology and proof-oriented rhetoric.

This is deliberately transparent. It does not pretend that an ARC controller is
an LLM: regular inflection, agreement, punctuation and rhetorical planning are
explicitly represented and can be checked in tests.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

CASES = ("nomn", "gent", "datv", "accs", "ablt", "loct")

@dataclass(frozen=True, slots=True)
class Noun:
    lemma: str
    gender: str
    animate: bool = False

@dataclass(frozen=True, slots=True)
class Adjective:
    lemma: str

class RussianMorphology:
    """Regular productive paradigms plus an explicit exception lexicon."""
    IRREGULAR = {
        ("человек", "gent", "sing"): "человека", ("человек", "datv", "sing"): "человеку",
        ("человек", "accs", "sing"): "человека", ("человек", "ablt", "sing"): "человеком",
        ("человек", "loct", "sing"): "человеке", ("время", "gent", "sing"): "времени",
        ("время", "datv", "sing"): "времени", ("время", "ablt", "sing"): "временем",
        ("время", "loct", "sing"): "времени", ("цель", "gent", "sing"): "цели",
        ("цель", "datv", "sing"): "цели", ("цель", "accs", "sing"): "цель",
        ("цель", "ablt", "sing"): "целью", ("цель", "loct", "sing"): "цели",
    }

    @staticmethod
    def noun(lemma: str, case: str = "nomn", number: str = "sing", animate: bool = False) -> str:
        lemma = lemma.lower().strip()
        if case not in CASES or number not in {"sing", "plur"}:
            raise ValueError("unknown grammatical form")
        irregular = RussianMorphology.IRREGULAR.get((lemma, case, number))
        if irregular:
            return irregular
        if number == "plur":
            stem = lemma[:-1] if lemma.endswith(("а", "я", "ь")) else lemma
            endings = {
                "nomn": "ы" if lemma.endswith("а") else "и" if lemma.endswith(("я", "ь")) else "ы",
                "gent": "" if lemma.endswith("а") else "ей" if lemma.endswith(("я", "ь")) else "ов",
                "datv": "ам" if not lemma.endswith(("я", "ь")) else "ям",
                "accs": "ов" if animate and not lemma.endswith(("я", "ь")) else "ей" if animate else ("ы" if lemma.endswith("а") else "и"),
                "ablt": "ами" if not lemma.endswith(("я", "ь")) else "ями",
                "loct": "ах" if not lemma.endswith(("я", "ь")) else "ях",
            }
            return stem + endings[case]
        if lemma.endswith("ие"):
            return lemma[:-2] + {"nomn": "ие", "gent": "ия", "datv": "ию", "accs": "ие", "ablt": "ием", "loct": "ии"}[case]
        if lemma.endswith("о"):
            return lemma[:-1] + {"nomn": "о", "gent": "а", "datv": "у", "accs": "о", "ablt": "ом", "loct": "е"}[case]
        if lemma.endswith("е"):
            return lemma[:-1] + {"nomn": "е", "gent": "я", "datv": "ю", "accs": "е", "ablt": "ем", "loct": "е"}[case]
        if lemma.endswith("а"):
            return lemma[:-1] + {"nomn": "а", "gent": "ы", "datv": "е", "accs": "у", "ablt": "ой", "loct": "е"}[case]
        if lemma.endswith("я"):
            return lemma[:-1] + {"nomn": "я", "gent": "и", "datv": "е", "accs": "ю", "ablt": "ей", "loct": "е"}[case]
        if lemma.endswith("ь"):
            return lemma[:-1] + {"nomn": "ь", "gent": "и", "datv": "и", "accs": "ь", "ablt": "ью", "loct": "и"}[case]
        return lemma + {"nomn": "", "gent": "а", "datv": "у", "accs": "а" if animate else "", "ablt": "ом", "loct": "е"}[case]

    @staticmethod
    def adjective(lemma: str, gender: str = "masc", case: str = "nomn", number: str = "sing", animate: bool = False) -> str:
        lemma = lemma.lower().strip()
        if not lemma.endswith(("ый", "ий", "ой")):
            raise ValueError("adjective must be in full masculine dictionary form")
        stem, ending = lemma[:-2], lemma[-2:]
        hard_i = ending == "ий" and (stem.endswith(("г", "к", "х", "ж", "ч", "ш", "щ", "ц")) or stem.endswith("ск"))
        soft = ending == "ий" and not hard_i
        if number == "plur":
            if soft or hard_i:
                table = {"nomn": "ие", "gent": "их", "datv": "им", "accs": "их" if animate else "ие", "ablt": "ими", "loct": "их"}
            else:
                table = {"nomn": "ые", "gent": "ых", "datv": "ым", "accs": "ых" if animate else "ые", "ablt": "ыми", "loct": "ых"}
            return stem + table[case]
        if soft:
            table = {
                "masc": {"nomn": "ий", "gent": "его", "datv": "ему", "accs": "его" if animate else "ий", "ablt": "им", "loct": "ем"},
                "femn": {"nomn": "яя", "gent": "ей", "datv": "ей", "accs": "юю", "ablt": "ей", "loct": "ей"},
                "neut": {"nomn": "ее", "gent": "его", "datv": "ему", "accs": "ее", "ablt": "им", "loct": "ем"},
            }
        elif hard_i:
            table = {
                "masc": {"nomn": "ий", "gent": "ого", "datv": "ому", "accs": "ого" if animate else "ий", "ablt": "им", "loct": "ом"},
                "femn": {"nomn": "ая", "gent": "ой", "datv": "ой", "accs": "ую", "ablt": "ой", "loct": "ой"},
                "neut": {"nomn": "ое", "gent": "ого", "datv": "ому", "accs": "ое", "ablt": "им", "loct": "ом"},
            }
        else:
            table = {
                "masc": {"nomn": ending, "gent": "ого", "datv": "ому", "accs": "ого" if animate else ending, "ablt": "ым", "loct": "ом"},
                "femn": {"nomn": "ая", "gent": "ой", "datv": "ой", "accs": "ую", "ablt": "ой", "loct": "ой"},
                "neut": {"nomn": "ое", "gent": "ого", "datv": "ому", "accs": "ое", "ablt": "ым", "loct": "ом"},
            }
        return stem + table[gender][case]

    @staticmethod
    def phrase(adjective: str, noun: Noun, case: str = "nomn", number: str = "sing") -> str:
        return f"{RussianMorphology.adjective(adjective, noun.gender, case, number, noun.animate)} {RussianMorphology.noun(noun.lemma, case, number, noun.animate)}"

    @staticmethod
    def past(verb_infinitive: str, gender: str = "masc", number: str = "sing") -> str:
        stem = verb_infinitive[:-2] if verb_infinitive.endswith("ть") else verb_infinitive
        return stem + ("ли" if number == "plur" else {"masc": "л", "femn": "ла", "neut": "ло"}[gender])

    @staticmethod
    def tokenize(text: str) -> list[str]:
        return re.findall(r"[А-Яа-яЁё-]+|[.!?,:;—]", text)

    @staticmethod
    def surface_diagnostics(text: str) -> dict[str, object]:
        tokens = RussianMorphology.tokenize(text)
        words = [t.lower() for t in tokens if t[0].isalpha()]
        repetitions = sum(a == b for a, b in zip(words, words[1:]))
        punctuation_ok = bool(re.search(r"[.!?]$", text.strip()))
        capital_ok = bool(text.strip()) and text.strip()[0].isupper()
        double_spaces = "  " in text
        return {
            "tokens": len(words),
            "lexical_diversity": len(set(words)) / max(1, len(words)),
            "adjacent_repetitions": repetitions,
            "punctuation_ok": punctuation_ok,
            "capital_ok": capital_ok,
            "double_spaces": double_spaces,
            "valid": punctuation_ok and capital_ok and not double_spaces and repetitions == 0,
        }


class RussianRhetoric:
    CONNECTORS = ("Во-первых", "Во-вторых", "В-третьих", "Наконец")
    RULE_NAMES = {
        "modus ponens": "правило утверждения основания (modus ponens)",
        "modus tollens": "правило отрицания следствия (modus tollens)",
        "семантическое следование": "семантическое следование",
        "закон тождества": "закон тождества",
    }

    @staticmethod
    def render_argument(thesis: str, premises: Sequence[str], conclusion: str, rule: str) -> str:
        parts = [f"Исходный тезис таков: {thesis.rstrip('.') }."]
        for index, premise in enumerate(premises):
            connector = RussianRhetoric.CONNECTORS[min(index, len(RussianRhetoric.CONNECTORS) - 1)]
            clean = premise.rstrip(".")
            if clean and "А" <= clean[0] <= "Я":
                clean = clean[0].lower() + clean[1:]
            parts.append(f"{connector}, {clean}.")
        parts.append(f"Связь между посылками соответствует правилу «{RussianRhetoric.RULE_NAMES.get(rule, rule)}».")
        clean = conclusion.rstrip(".")
        if clean and "А" <= clean[0] <= "Я":
            clean = clean[0].lower() + clean[1:]
        parts.append(f"Следовательно, {clean}.")
        return " ".join(parts)

    @staticmethod
    def polish(text: str) -> str:
        text = re.sub(r"\s+", " ", text.strip())
        text = re.sub(r"\b(очень)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
        text = text.replace("потому что потому что", "потому что")
        if text and text[-1] not in ".!?":
            text += "."
        return text[0].upper() + text[1:] if text else text

    @staticmethod
    def literary_score(text: str) -> float:
        d = RussianMorphology.surface_diagnostics(text)
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        lengths = [len(RussianMorphology.tokenize(s)) for s in sentences] or [0]
        variation = (max(lengths) - min(lengths)) / max(1, max(lengths))
        score = (
            0.45 * float(d["lexical_diversity"])
            + 0.25 * variation
            + 0.15 * float(d["punctuation_ok"])
            + 0.15 * float(d["capital_ok"])
            - 0.15 * int(d["adjacent_repetitions"])
        )
        return max(0.0, min(1.0, score))
