# R8.2 Russian Cognitive Dialogue — training protocol

Status: prerelease development protocol. No freeze, no new blind.

## 1. Separate the objectives

The model has two distinct quality targets:

### Cognitive quality

- correct task decomposition;
- multi-domain graph coverage;
- exact calculation/proof correctness;
- causal and counterfactual coherence;
- evidence/provenance discipline;
- explicit UNKNOWN when information is insufficient;
- useful Active Inquiry;
- context safety.

### Dialogue quality

- fluent natural Russian;
- coherent multi-turn references;
- no robotic domain-label phrasing;
- no repetition loops;
- concise answer when requested;
- deep structured answer when requested;
- stable terminology/entities/numbers;
- graceful uncertainty;
- answer-plan completeness;
- no new unsupported claims introduced by surface realization.

Neither objective substitutes for the other.

## 2. Data provenance classes

Every example must have one of:

- `V8_RAW_LANGUAGE`;
- `R745_RAW_DOMAIN_LANGUAGE`;
- `VERIFIED_SYMBOLIC`;
- `SYNTHETIC_COMPOSITION`;
- `SYNTHETIC_DIALOGUE`;
- `TEACHER_DISTILLATION`;
- `USER_SESSION_LEARNED`;
- `GRAPH_PROCEDURAL`.

Metrics must be stratified by provenance.

## 3. V8 raw archive gate

Before replaying the historical V8 corpus:

1. extract `NEXUS-FINANCE-v8.0.0-BDH-INSPIRED-FULL.zip`;
2. enumerate all members;
3. locate the training corpus member(s);
4. count valid JSONL records independently;
5. hash the raw extracted members;
6. count unique domain labels;
7. identify the 30 conversation domains;
8. inspect whether turn/session linkage exists;
9. measure exact duplicate and near-duplicate rate;
10. write `V8_RAW_AUDIT.json`.

Only then set `raw_replay_permitted=true`.

Historical release audit says 696,000 utterances, but R8.2 must independently verify the raw files.

## 4. Corpus split

Never use a simple random-row split as the primary language proof.

Prefer, in order:

1. held-out dialogue/session families;
2. held-out paraphrase/style families;
3. held-out templates;
4. held-out concept combinations;
5. random row split only as a secondary diagnostic.

No final blind item may be used in training or threshold tuning.

## 5. Stage A — representation pretraining

Inputs:

- V8 raw 696k after audit;
- R7.45 raw 240k;
- trusted symbolic language examples from R7.2/R7.10/V13/V18;
- morphology/style corruption pairs.

Loss:

```text
L_repr =
    1.00 * L_semantic_contrastive
  + 0.70 * L_domain_multilabel
  + 0.35 * L_entity_metric
  + 0.25 * L_morphology
  + 0.20 * L_style_rank
  + 0.10 * L_V15_distill
```

V15 is a teacher regularizer, not authority.

## 6. Stage B — semantic-to-graph multi-positive alignment

For every utterance predict a set, not one class:

```text
entities + metrics + constraints + domains + causal/relation nodes
```

Loss:

```text
L_graph =
    1.00 * L_multi_positive_nodes
  + 0.70 * L_directed_relation
  + 0.35 * L_graph_contrastive
  + 0.25 * L_text_graph_alignment
  + 0.15 * L_calibration
```

Keep the 30M procedural graph marked as a training substrate rather than verified factual ground truth.

## 7. Stage C — recurrent reasoning society

Use six or more trajectories with the same shared latent brain but distinct priors/adapters:

- proof-first;
- causal;
- counterfactual;
- recurrent planning/world-model;
- evidence-credit/claim-graph;
- semantic/domain.

Train trajectory diversity on *useful complementary evidence*, not disagreement itself.

```text
L_reason =
    L_answer_plan
  + 0.5 * L_proof
  + 0.4 * L_epistemic
  + 0.4 * L_missing_slot
  + 0.3 * L_claim_graph
  + 0.2 * L_world_transition
  + 0.05 * L_diversity
```

Verified native proof remains outside learned voting.

## 8. Stage D — context/dialogue training

Preserve R7.44.3 sovereign context behavior.

Curriculum classes:

- direct follow-up;
- explicit anaphora;
- bare-why new topic;
- hard topic switch;
- pending-slot interruption;
- resume suspended task;
- verified fact interrupt;
- user correction;
- conflicting user assertions;
- temporal change;
- ask when data is missing;
- multi-domain question across 2–4 segments;
- simplify previous answer;
- deepen previous answer;
- summarize previous answer;
- challenge/counterargument.

R7.44 tests remain regression guards and are never replaced by a neural score.

## 9. Stage E — Russian Surface Cortex

The Surface Cortex consumes `AnswerPlan + approved ClaimSet + dialogue context`.

It does not receive permission to create facts.

Training targets, when legitimate response text exists:

```text
L_surface =
    L_token_or_response
  + 0.75 * L_claim_entailment
  + 0.50 * L_entity_number_consistency
  + 0.35 * L_semantic_completeness
  + 0.25 * L_grammar_style
  + 0.20 * L_context_reference
  + 0.15 * L_repetition
  + 1.00 * L_unsupported_claim
```

Unsupported factual assertion carries the largest safety penalty.

### Candidate surface engines

A surface engine may be:

- an R8.2-native Russian autoregressive decoder;
- a stronger frozen pretrained language model;
- a distillation student.

A foreign/pretrained generator is always subordinate. It cannot overwrite Verified/Derived ClaimSet fields.

Do not promote Qwen3-14B or another model to canonical Surface Cortex without a reproducible Russian dialogue evaluation.

## 10. Stage F — critic-guided realization

Use V13/V18-style Russian critics as auxiliary scoring/checking layers:

- grammar;
- agreement;
- punctuation;
- logic;
- style;
- repetition;
- contradiction;
- proof prose.

Critic scores can trigger reranking/regeneration. They cannot validate factual truth on their own.

## 11. Consolidation and anti-forgetting

At milestones:

- freeze graph embeddings temporarily;
- consolidate language/dialogue heads;
- run R7.2 structural regression;
- run R7.44 context regression;
- run proof integrity;
- run epistemic memory regression;
- check graph MRR/Hits;
- resume joint training only if regressions pass.

## 12. Development metrics

### Cognitive

- multi-label micro/macro F1;
- exact-set;
- graph containment@3/5/10;
- graph MRR, Hits@1/3/10;
- proof exact;
- causal consistency;
- counterfactual consistency;
- UNKNOWN precision/recall;
- missing-slot query accuracy;
- ECE/Brier.

### Dialogue

- answer-plan semantic completeness;
- unsupported factual claim rate;
- entity consistency;
- numeric consistency;
- anaphora accuracy;
- context-switch safety;
- resume correctness;
- correction/revision correctness;
- grammar score;
- style score;
- repetition rate;
- human preference / rubric score on fresh held-out dialogues.

## 13. Freeze gates

Minimum release gates should include:

- R7.2 regression: no degradation;
- R7.44 context contracts: no degradation;
- proof authority violations: 0;
- foreign/surface authority override violations: 0;
- unsupported claim rate below preregistered threshold;
- semantic multi-domain metrics above preregistered threshold;
- graph metrics not catastrophically degraded;
- calibration measured on unseen development set;
- clean reload reproduces metrics;
- all model/data/code hashes recorded.

Then freeze.

## 14. Post-freeze Russian Dialogue Blind

Create after freeze.

Recommended scale:

- >=100 dialogues;
- 8–20 turns/dialogue;
- >=1,000 total turns;
- unseen names/numbers/domain combinations;
- no exact V8 template replay;
- mix of business, technical, logic, everyday explanatory and uncertain tasks.

Each dialogue should contain a sampled subset of:

- follow-up;
- topic switch;
- interrupt/resume;
- missing data;
- correction;
- contradiction;
- calculation;
- multi-step plan;
- counterargument;
- explain simply;
- explain deeply;
- summarize;
- remember only valid session facts.

Primary success is not BLEU/perplexity. Primary success is:

```text
correct + context-safe + epistemically honest + fluent Russian
```

No tuning after opening the blind.
