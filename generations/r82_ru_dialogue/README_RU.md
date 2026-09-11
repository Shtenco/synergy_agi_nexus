# NEXUS R8.2 — Russian Cognitive Dialogue Graph

Status: **DESIGN / PRETRAINING CANDIDATE — NOT FROZEN**

R8.2 объединяет доказанные органы исторических NEXUS с текущим R8.1 Unified Graph 100M, но не смешивает их права и не выдаёт component benchmarks за open-domain intelligence.

## Цель

Построить NEXUS, который одновременно:

1. глубоко разбирает русскую задачу как типизированный граф;
2. хранит контекст и умеет безопасно продолжать многоходовый диалог;
3. различает KNOWN / LEARNED_NOW / DERIVED / UNKNOWN;
4. строит несколько reasoning trajectories;
5. проверяет доказуемые утверждения независимым verifier;
6. задаёт уточняющий вопрос, если для точного ответа не хватает переменных;
7. формулирует естественный русский ответ, не добавляя фактов вне утверждённого ClaimSet.

Главный контракт:

```text
Russian input
  -> Context Binder
  -> Semantic Segments
  -> 100M Cognitive Graph Brain
  -> Local Typed Subgraph
  -> Multi-Trajectory Reasoning
  -> ClaimGraph / Evidence Credit / Epistemic Governor
  -> Verified AnswerPlan
  -> Russian Surface Cortex
  -> Grammar/Style/Claim Verification
  -> Final answer
```

## Найденный V8 языковой корпус

Канонический Google Drive archive:

- folder: `СИНЕРГИЯ-ФИНАНС v8.0.0 — NEXUS RECURRENT LATENT — 2026-08-17`
- model/data folder: `01_NEXUS_MODEL_DATASETS_SOURCE`
- file: `NEXUS-FINANCE-v8.0.0-BDH-INSPIRED-FULL.zip`
- Drive file id: `1K9EQPEglYG1jptShOdQPUVZs9IO7RGQ3`
- archive size: `10,721,585` bytes
- historical release SHA-256: `499cf01d42bb4f913a287b42301293edca2780c55203e2d0a45d5dceaefe7b68`

Release audit states:

- 696,000 source language training utterances;
- 180 domains = 150 finance/application + 30 conversation;
- 1,446 knowledge records;
- 2,760 transfer edges;
- recurrent context memory S;
- latent query workspace H;
- hidden refinement 2–8 steps;
- local fast associative memory;
- historical conversation E2E 16/16;
- compact-router heldout 99.6%.

These historical metrics are retained as provenance only. They are **not** a fresh R8.2 benchmark.

## Best-of lineage promoted into R8.2

### R7.2 / structural language core

KEEP:
- CONTENT vs INSTRUCTION disentanglement;
- deterministic/typed structural routing;
- exact authority regression guard.

### R7.9 / R7.17 / V17

KEEP:
- multiple independent reasoning trajectories;
- graph fusion rather than naive averaging;
- diversity/correlation features.

Do not assume that more trajectories automatically imply more truth.

### R7.10 Proof-First

KEEP:
- proof proposal;
- independent proof verification;
- verified native result has sovereign priority.

Proof generator and verifier MUST NOT be the same authority path.

### R7.13

KEEP:
- hypothesis -> test -> evidence update loop;
- unresolved alternatives remain explicit hypotheses rather than forced top-1.

### R7.14 / V13 / V18 Russian layer

KEEP:
- Russian morphology diagnostics;
- agreement/punctuation checks;
- contradiction/entailment checks;
- proof-to-prose critic;
- style/grammar quality heads.

These organs are critics/verifiers, not evidence that NEXUS already is a general Russian autoregressive LLM.

### R7.18

KEEP as historical consolidation base:
- native structural core;
- Proof-First;
- hypothesis/test;
- query cybernetics;
- recurrent memory;
- Evidence Credit.

### R7.32 / R7.33 SUPRA-MA

KEEP:
- Society-of-Minds as evidence society, not democracy;
- ClaimGraph;
- independent-lineage accounting;
- dynamic correlation control;
- adaptive diversity querying;
- abstention/MetaGate.

Synthetic orchestration benchmarks remain orchestration evidence only.

### R7.36

KEEP:
- KNOWN;
- LEARNED_NOW;
- DERIVED;
- UNKNOWN;
- conflicting hypothesis set;
- explicit revision semantics.

### R7.44.3

KEEP unchanged as discourse safety contract:
- AnaphoraBinder;
- PendingSlotFrame;
- HardContextBoundary;
- verified-fact interrupt precedence;
- suspend/resume.

### R7.45 / R7.46 / R8.1

KEEP:
- 240k Russian business/autobusiness/Omsk natural corpus;
- hard-neighbour ontology;
- segment-set parsing;
- 2.5M-node / 30M directed-edge graph substrate;
- Unified Graph 100M shared latent;
- V15 contextual Russian representation and graph bridge.

Do NOT return to `one question -> one domain label`.

### OLGA V12/V13/V17/V18 lineage

KEEP selected ideas only:
- deterministic small-world graph diffusion;
- recurrent state/world prediction;
- multi-model graph fusion;
- Russian logic/style critic;
- x, P x, P^2 x, P^4 x graph polynomial channels.

REJECT benchmark leakage and catalogue-dependent conclusions documented in the V12 audit.

### R7.34

REJECT as promotion candidate because generalization failed.

## Two-contour architecture

R8.2 deliberately separates **thinking** from **surface realization**.

### A. Cognitive Graph Brain

Canonical core remains approximately 100M trainable graph parameters.

Responsibilities:

- semantic segmentation;
- entity/metric/constraint extraction;
- local subgraph activation;
- causal/relation reasoning;
- recurrent workspace;
- hypothesis generation;
- proof/evidence scoring;
- epistemic state;
- query/missing-slot policy;
- AnswerPlan construction.

It does NOT have permission to invent unsupported world facts.

### B. Russian Dialogue Cortex

Responsibilities:

- natural Russian wording;
- discourse markers;
- controlled verbosity;
- coherent references;
- stylistic adaptation;
- answer-plan realization.

The Surface Cortex receives a bounded `AnswerPlan`, not unrestricted authority.

Any surface sentence that introduces a new factual claim must map back to an approved ClaimGraph node or be rejected/regenerated.

## Why a dialogue cortex is necessary

The 100M R8.1 graph model is primarily a cognitive/router/graph system. Excellent classification or segment containment does not imply excellent free-form Russian generation.

The V8 corpus provides a valuable Russian and conversational surface, but its historical runtime was not a demonstrated general-purpose autoregressive LLM. V13/V18 likewise explicitly described themselves as neurosymbolic Russian reasoners/critics rather than general free-form language models.

Therefore R8.2 must train/evaluate the dialogue surface separately rather than infer its quality from reasoning benchmarks.

## Dialogue memory model

Per session:

```text
Turn
  -> entities
  -> claims
  -> user assertions
  -> verified facts
  -> pending slots
  -> unresolved hypotheses
  -> user goal
  -> local dialogue summary
```

Memory classes:

- session fact;
- user-provided fact;
- verified external fact;
- derived value;
- hypothesis;
- rejected claim;
- pending question;
- expired context.

A later turn can bind only through an explicit compatible discourse edge. Bare lexical similarity is not sufficient.

## AnswerPlan contract

The cognitive brain must emit a typed structure similar to:

```json
{
  "intent": "explain|calculate|compare|plan|ask|refuse|summarize",
  "answerable": true,
  "claims": [],
  "derived_values": [],
  "unknowns": [],
  "required_questions": [],
  "recommended_structure": [],
  "tone": "neutral",
  "confidence": 0.0,
  "citations_or_provenance": []
}
```

The dialogue cortex can realize this structure into fluent Russian but cannot silently mutate it.

## Training curriculum

R8.2 training is multi-objective and staged.

### Stage 0 — dataset audit

Before optimization:

- extract the actual V8 archive;
- count rows and domains from raw files;
- calculate per-file SHA-256;
- identify whether utterances contain session/turn ids or only text+domain labels;
- deduplicate exact and near-duplicate rows;
- split by template/style/session family, never by random row only.

No claim that the raw 696k corpus has been replayed until this audit succeeds.

### Stage 1 — Russian representation

Use V8 696k + R7.45 240k, preserving their provenance.

Objectives:
- masked/contrastive semantic representation;
- domain/concept multi-positive alignment;
- morphology/style auxiliary losses;
- V15 teacher distillation as optional regularizer, not ground truth.

### Stage 2 — cognitive graph alignment

Train:

`Russian semantic representation -> entity/metric/domain/relation nodes -> 30M graph`.

Use multi-positive labels and directed relation loss.

### Stage 3 — reasoning trajectories

Train independent initial conditions/priors for:

- proof-first;
- causal;
- counterfactual;
- recurrent planning;
- evidence-credit;
- semantic/domain.

Add trajectory diversity without rewarding disagreement for its own sake.

### Stage 4 — dialogue episodes

If authentic multi-turn V8 sessions exist, use them directly with session-family holdout.

If the 696k corpus contains only isolated utterances, do not falsely call reconstructed sequences raw dialogue. Build synthetic dialogue curriculum as a separate provenance class.

Train:
- anaphora;
- interruption;
- topic switch;
- pending-slot resume;
- correction;
- user fact revision;
- contradiction handling;
- ask-when-missing;
- answer-plan realization.

### Stage 5 — surface realization

Train or attach a Russian Surface Cortex.

Losses:
- next-token / response realization where legitimate target text exists;
- semantic entailment to AnswerPlan;
- unsupported-claim penalty;
- repetition penalty;
- grammar/style critic score;
- entity consistency;
- uncertainty wording consistency.

### Stage 6 — consolidation

Freeze graph geometry periodically and consolidate language/recurrent/trajectory heads without catastrophic forgetting.

## Fresh evaluation required before freeze

Development metrics do not authorize release.

Required suites:

### Cognitive
- multi-domain exact set / containment;
- graph MRR / Hits@k;
- proof exactness;
- contradiction handling;
- UNKNOWN precision/recall;
- missing-variable inquiry;
- causal/counterfactual consistency.

### Russian language
- grammar;
- semantic completeness;
- unsupported claim rate;
- repetition;
- reference resolution;
- style quality;
- concise vs detailed instruction following.

### Dialogue
Create a fresh post-freeze suite of at least 100 multi-turn Russian dialogues, preferably 8–20 turns each, containing:

- normal follow-ups;
- abrupt topic switches;
- interruptions;
- resume;
- corrections;
- conflicting user facts;
- calculations;
- business/technical reasoning;
- missing information;
- deliberate ambiguity;
- requests to explain more simply or more deeply.

Primary dialogue success criterion must combine semantic correctness and safety, not linguistic prettiness alone.

## Freeze rule

Only after training and regressions:

```text
TRAIN
 -> REGRESSIONS
 -> CALIBRATION
 -> CLEAN RELOAD
 -> HASH MANIFEST
 -> FREEZE
 -> NEW BLIND
```

No post-freeze tuning against the new Blind.

## Scientific boundary

R8.2 is currently a construction/training target. The discovery of the V8 archive and the historical component benchmarks do not prove that the new combined system already has excellent free-form Russian dialogue. That claim requires a freshly frozen dialogue benchmark and human/automatic audit after training.
