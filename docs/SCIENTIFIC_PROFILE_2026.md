# NEXUS — scientific profile of hybrid graph intelligence

## Research contribution

NEXUS is the canonical destination for **validated generations of an integrated reasoning architecture**. The meaningful design idea is to combine learned representations with graph-structured reasoning and formal contracts, while preserving exact provenance across model versions. The historical OLGA source and the canonical NEXUS authority have deliberately different roles.

## Existing algorithms

The [V18 model](../generations/nexus_v18/model.py) defines an ARCGraphRanker using feature adaptation, 8 learned candidate slots of width 48, three fast small-world processing blocks and a separate candidate-level graph-processing stage. It also defines RussianSmallWorldReasoner with character embeddings, pooled sequence slots and separate quality, rule, depth and validity heads, plus a SmallWorldDynamics research component.

The [AI proposal contract](../contracts/ai_proposal_v1.py) requires task type, model identity, declared limitations, bounded confidence and whether human authorization is necessary. Its role is to prevent a prediction from silently becoming a payment or capital decision.

## Mathematical structure and falsifiability

For a masked candidate collection with model scores s(i), candidate probabilities can be derived for analysis via

$$
p_i=\frac{\exp(s_i)}{\sum_{j\in V}\exp(s_j)},\qquad i\in V,
$$

where V includes only valid candidates. This is an interpretation model, not a guarantee of calibrated correctness. Distinguish exact program execution, learned ranking quality, cross-task generalization and uncertainty calibration.

## Scientific programme

Preserve frozen model digests, train/validation/test identity and task-level outputs. Compare a rule-only solver, graph-enhanced frozen solver, neural candidate ranker and hybrid controller on the same held-out tasks with the same number of attempts. Measure exact-match accuracy, memory and compute cost, confidence intervals and negative controls. For Russian-language tasks, test syntactic, semantic and logical consistency separately.

## Product significance

Inspectable, modular reasoning with immutable benchmark provenance can serve scientific assistants, code review, data reasoning and agent planning. The defining value is **structured cognitive inference with evidence and an explicit authorization boundary**, not an unsupported assertion of universal AGI.

[ARC V18](../generations/nexus_v18/model.py) · [AI proposal](../contracts/ai_proposal_v1.py) · [Benchmark contract](../contracts/benchmark_suite_v1.py)
