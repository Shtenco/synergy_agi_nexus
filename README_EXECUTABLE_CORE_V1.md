# AGI NEXUS executable root v1

This branch turns the new canonical root into an evidence registry before any historical code migration.

It deliberately does **not** copy NEXUS generations out of `agi_olga` yet. It first records generation identity, benchmark claim tier and migration requirements so that later migration is evidence-driven rather than version-number-driven.

Run locally:

```bash
python -m pip install -e .
python -m pytest -q
```

The first executable invariant is simple: a discovered branch, a synthetic score, a documented generation and a reproduced frozen release are different evidence classes and cannot be silently relabelled.
