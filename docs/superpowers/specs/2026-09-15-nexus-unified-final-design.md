# NEXUS Unified Final — Sovereign Russian Cortex Design

**Date:** 2026-09-15  
**Status:** design / pre-implementation  
**Canonical repository:** `Shtenco/agi_nexus`  
**Target:** first reproducible NEXUS generation that combines natural Russian conversation with a sovereign evidence/authority backbone.

## 1. Goal

Build **NEXUS Unified Final V1** as one runtime with a strong generative Russian cortex, while keeping truth-bearing computation outside the cortex.

The cortex is a language surface. It may explain, summarize, converse, reformulate and generate creative text. It must not silently replace or contradict verified results from NEXUS authority, exact computation, memory, business specialists, ARC specialists or world-state specialists.

The target architecture combines the strongest previously validated NEXUS organs:

- **Unified R1.3** — primary authority backbone;
- **R7.18** — evidence/reasoning governor;
- **R7.44.3** — discourse state, anaphora, interruption/resume and context boundaries;
- **R7.2 + R7.14** — Russian language binding and morpholex normalization;
- **R7.45.2** — business specialist only;
- **V10** — ARC/procedural specialist;
- **V12** — WorldGraph/causal-state specialist;
- **Generative cortex** — pluggable LLM trained for natural Russian rendering and conversation.

## 2. Non-goals

This generation does **not**:

- average or merge incompatible NEXUS/LLM tensors;
- give the LLM sovereign authority over exact or verified claims;
- retrain Unified R1.3, R7.18, R7.44.3, R7.2, R7.14, R7.45.2, V10 or V12 in the first iteration;
- claim AGI/SOTA without a named frozen benchmark and artifact digest;
- grant payment, trading, ledger, blockchain or deployment authority;
- expose private chain-of-thought or hidden latent state;
- treat synthetic internal benchmarks as external standardized scores.

## 3. Architectural choice

### Recommended: modular sovereign NEXUS

```text
USER / HISTORY
      |
      v
R7.44.3 DISCOURSE
(topic, anaphora, pending slots, interrupt/resume)
      |
      v
R7.2 + R7.14 LANGUAGE FRONTEND
(intent, normalized semantics, morphology)
      |
      v
R7.18 GOVERNOR / ROUTER
      |
      +----------------------+----------------------+--------------------+
      |                      |                      |                    |
      v                      v                      v                    v
UNIFIED R1.3 AUTHORITY   R7.45.2 BUSINESS       V10 ARC            V12 WORLDGRAPH
(exact/logic/memory)         ORGAN               ORGAN                 ORGAN
      |                      |                      |                    |
      +----------------------+----------------------+--------------------+
                             |
                             v
                       EvidencePacket
                             |
                             v
                    GENERATIVE RU CORTEX
                       (renderer/chat)
                             |
                             v
                    CLAIM/EXACT VERIFIER
                             |
                    +--------+--------+
                    |                 |
                  PASS              FAIL
                    |                 |
                    v                 v
                  FINAL       deterministic render
```

### Rejected alternative A: monolithic distillation

Distilling all authority, logic, memory and specialists directly into one LLM would simplify serving but would destroy the strongest property of the existing NEXUS lineage: independent verification and exact protected outputs. It also makes catastrophic forgetting and silent hallucination much harder to detect.

### Rejected alternative B: permanent multi-LLM ensemble

A permanent Qwen/Ministral/Nanbeige ensemble may increase coverage, but it adds latency, memory cost and failure modes. Multiple cortex candidates are useful during a frozen bakeoff; the promoted V1 runtime should use one primary cortex plus a deterministic fallback. A second cortex may be added later only if measured reliability justifies the cost.

## 4. Component boundaries

### 4.1 Discourse Engine — R7.44.3

Responsibilities:

- topic identity;
- anaphora/coreference such as “а почему?”, “а это?”, “продолжай”;
- pending slots;
- interruptions and resumption;
- hard context boundaries;
- verified-fact precedence across turns.

It produces dialogue state, not the final user answer.

### 4.2 Russian Language Frontend — R7.2 + R7.14

Responsibilities:

- normalize Russian input;
- separate instruction from content;
- preserve entities, numbers and negation;
- emit semantic/operator features for routing;
- improve morphology and multilingual surface handling.

It must not hallucinate factual content.

### 4.3 Evidence Governor — R7.18

Responsibilities:

- decide which authority/specialist evidence is usable;
- rank evidence;
- preserve abstention;
- prevent weak evidence from overriding stronger verified evidence;
- record provenance/credit.

### 4.4 Authority Backbone — Unified R1.3

Unified R1.3 is the primary truth-bearing backbone for:

- exact computation;
- formal/logical results;
- protected memory facts;
- causal/executive decisions covered by the validated authority contract;
- uncertainty/abstention.

The first Unified Final iteration wraps R1.3; it does not alter its learned state or authority policy.

### 4.5 Specialist organs

`R7.45.2 Business`, `V10 ARC` and `V12 WorldGraph` are invoked only on matching routes. They return structured evidence. They do not directly own free-form user-facing prose.

### 4.6 Generative cortex

The cortex owns:

- natural Russian prose;
- conversational tone;
- explanation depth;
- summarization;
- creative/non-factual generation;
- transformation of structured evidence into readable answers.

It does **not** own protected truth.

### 4.7 Final verifier

Every factual/technical response passes through a final verifier. The verifier compares the generated response against protected claims, exact values, prohibitions and abstentions from the `EvidencePacket`.

If the cortex violates a hard invariant, its output is rejected and a deterministic evidence renderer is used instead.

## 5. EvidencePacket contract

All organs communicate with the cortex through a versioned, inspectable contract.

```json
{
  "schema_version": "1.0",
  "request_id": "uuid",
  "locale": "ru",
  "mode": "casual|creative|factual|exact|specialist|mixed",
  "dialogue_state": {
    "topic_id": "...",
    "resolved_references": [],
    "pending_slots": [],
    "resume_target": null
  },
  "authority": {
    "status": "VERIFIED|PARTIAL|UNVERIFIED|ABSTAIN",
    "verified_claims": [
      {
        "claim_id": "C1",
        "type": "fact|number|logic|memory|causal",
        "value": "...",
        "confidence": 1.0,
        "source_component": "unified_r13"
      }
    ],
    "exact_results": [],
    "forbidden_contradictions": [],
    "abstention_reason": null
  },
  "specialists": [],
  "generation_policy": {
    "may_add_unverified_factual_claims": false,
    "may_generate_creative_content": false,
    "must_preserve_claim_ids": ["C1"],
    "must_preserve_numbers": true
  }
}
```

The cortex returns:

```json
{
  "answer": "...",
  "used_claim_ids": ["C1"],
  "provisional_claims": [],
  "follow_up_question": null
}
```

The user sees only `answer` (and normal product-level provenance when applicable), not private hidden reasoning.

## 6. Cortex candidates

The runtime interface must be model-agnostic. Model promotion is determined by a frozen bakeoff, not preference.

### Primary candidate: Qwen3-4B-Instruct-2507

Reasons:

- text-only causal model;
- Apache-2.0;
- 4B parameters;
- strong instruction following and open-ended generation;
- Qwen3 family officially supports Russian among 119 languages/dialects;
- 262K native context;
- mature Transformers/vLLM/SGLang ecosystem;
- size compatible with QLoRA on commodity GPU infrastructure.

### Challenger 1: Ministral-3-3B-Instruct

Reasons:

- smaller language model;
- explicit official Russian support;
- designed for edge deployment;
- useful latency/memory challenger.

### Challenger 2: Nanbeige4.1-3B

Reasons:

- strong small-model reasoning and agent benchmarks;
- a partial HF-layout exists on the user Drive;
- Apache-2.0.

Risk: its own card declares English/Chinese rather than Russian. Russian quality must pass the same blind benchmark before promotion. The Drive copy is incomplete: its index declares two Safetensors shards with `total_size=7,867,274,240`, but the two shard files are not present in Drive discovery.

### Deferred: Qwen3.5-4B

It is a strong newer model, but the V1 goal is a text cortex. Multimodal complexity is unnecessary until the text architecture passes all authority and discourse gates.

## 7. Frozen cortex bakeoff before training

Before any fine-tune, create `RU_CORTEX_BLIND_V1` and freeze its SHA-256. It must not be used in training, prompt construction or synthetic-data generation.

The same prompts and decoding policy are used for all candidates.

### Categories

- 100 ordinary Russian conversation turns;
- 80 explanation/teaching prompts;
- 60 rewriting/summarization prompts;
- 60 multi-turn context/anaphora turns;
- 60 factual questions with known reference answers;
- 40 uncertainty/“I do not know” cases;
- 60 `EvidencePacket` rendering cases;
- 40 adversarial “override the verified answer” cases.

Total: **500 frozen evaluation items** plus multi-turn state.

### Hard gates

A cortex cannot be promoted if any of the following fail:

- protected numeric/exact preservation: **100%**;
- protected verified-claim contradiction rate: **0%**;
- refusal to override protected evidence: **100%**;
- Russian-only requirement where requested: **>=99% turns without accidental language mixing**;
- context/anaphora accuracy: **>=95%**;
- structured-output validity for `RenderedAnswer`: **>=99.5%**;
- no benchmark item present in the training dataset by exact/fuzzy/hash leakage audit.

Quality metrics are reported separately from hard gates; a fluent model that breaks authority is rejected.

## 8. Training data design

The cortex is trained to render and converse, not to absorb NEXUS authority.

### 8.1 `authority_render_sft`

Generate examples from validated NEXUS result artifacts:

```text
user message + dialogue state + EvidencePacket -> natural Russian answer
```

Targets must preserve protected claims exactly in meaning and numbers.

Initial target: **50k–100k examples**.

### 8.2 `dialogue_context_sft`

Use R7.44.3 discourse mechanics to generate multi-turn sessions with:

- anaphora;
- corrections;
- topic switches;
- interruptions;
- resume;
- pending-slot completion;
- verified fact persistence.

Initial target: **30k–60k turns** across at least 5k sessions.

### 8.3 `russian_general_sft`

Use only datasets with documented permissive/reusable licensing and a dataset manifest. The purpose is natural Russian conversation, explanations and writing—not importing unverifiable authority.

Initial target after deduplication: **100k–250k high-quality turns**.

### 8.4 Existing V8 utterances

The 696k SINERGIYA-FINANS utterance corpus must **not** be ingested wholesale because it is heavily finance/domain biased and fresh testing showed out-of-domain routing back into finance.

It may contribute a stratified, deduplicated subset for:

- conversational intent;
- short Russian phrasing;
- financial/business rendering.

Any factual/domain target is tagged with its source and authority status.

### 8.5 Business rendering

R7.45.2 provides structured business evidence over 62 domains. Create **10k–30k** paraphrased rendering examples while preserving its domain result as evidence rather than teaching the cortex to replace the classifier.

### 8.6 ARC/WorldGraph explanation rendering

Create **10k–20k** examples where V10/V12 produce the structured solution and the cortex explains it without changing the result.

### 8.7 Negative/preference pairs

Create pairs such as:

- faithful answer vs. answer that changes an exact number;
- faithful answer vs. answer that contradicts a memory fact;
- correct abstention vs. invented fact;
- concise explanation vs. irrelevant finance-domain fallback;
- correct resume vs. topic/context loss.

These pairs are reserved for a second preference stage only if SFT alone does not meet the hard gates.

## 9. Training stages

### Stage 0 — baseline bakeoff

Run the frozen 500-item cortex benchmark on all available candidate base models. Promote one candidate for training.

### Stage 1 — QLoRA SFT

Default recipe for a 3B–4B promoted model:

- 4-bit NF4 base loading;
- BF16 compute when supported;
- LoRA rank: 32 initially, raise to 64 only if validation warrants it;
- LoRA alpha: 64;
- dropout: 0.05;
- target attention and MLP projection modules;
- sequence length: 4096 for V1 training, with explicit long-context evaluation later;
- packing enabled for short dialogue records;
- effective batch size: 64 tokens/examples equivalent through gradient accumulation;
- optimizer: paged AdamW 8-bit where supported;
- LR: start at `1e-4`, tune from frozen dev set only;
- warmup: 3%;
- cosine decay;
- 1 epoch first pass, second epoch only if dev loss and authority fidelity both improve;
- gradient clipping: 1.0.

No benchmark prompt may enter the training corpus.

### Stage 2 — evidence-faithfulness preference training (conditional)

Run DPO/ORPO only if Stage 1 remains fluent but fails soft faithfulness/preference metrics. Do not use preference training to repair hard exact/authority violations; those require data/contract/verifier fixes.

### Stage 3 — merge and deployment formats

Artifacts:

- base model reference + immutable revision;
- LoRA adapter;
- optional merged Safetensors release;
- GGUF Q4_K_M deployment candidate;
- GGUF Q5_K_M quality candidate;
- tokenizer/config files;
- SHA-256 manifest.

The canonical identity is the unquantized base revision + adapter digest. Quantized files are deployment derivatives.

## 10. Compute boundary

The current ChatGPT execution container has approximately **5.8 GiB RAM and no NVIDIA GPU**, so a real 3B/4B QLoRA run cannot be honestly completed inside this container.

Implementation therefore separates:

1. reproducible dataset/build/eval code that runs locally/CI;
2. a GPU training entrypoint usable on an external CUDA runner;
3. immutable output manifests imported back into `agi_nexus` after training.

Recommended minimum for V1 QLoRA:

- **16 GB VRAM** workable with conservative batch/sequence settings;
- **24 GB VRAM** preferred for faster 4B iteration and 4096-token sequences.

Training scripts must support resume-from-checkpoint and deterministic seed recording.

## 11. Repository layout

```text
agi_nexus/
  nexus_unified/
    contracts/
      evidence_packet.py
      rendered_answer.py
    discourse/
      r744_adapter.py
    language/
      r72_adapter.py
      r714_adapter.py
    governor/
      r718_adapter.py
    authority/
      unified_r13_adapter.py
    specialists/
      business_r7452.py
      arc_v10.py
      worldgraph_v12.py
    cortex/
      base.py
      transformers_cortex.py
      openai_compatible_cortex.py
    verifier/
      protected_claims.py
      exact_guard.py
      output_verifier.py
    orchestrator.py

  training/
    manifests/
    datasets/
    build_authority_render.py
    build_dialogue_context.py
    dedupe_and_leakage_check.py
    train_qlora.py
    train_preference.py
    merge_adapter.py
    export_gguf.md

  benchmarks/
    ru_cortex_blind_v1/
    authority_fidelity_v1/
    discourse_blind_v1/
    legacy_regression/

  provenance/
    component_manifest.json
    dataset_manifest.json
    model_manifest.json
    benchmark_ledger.json
```

Historical artifacts remain in their original locations. Promotion into `agi_nexus` is copy-only or adapter-based with source SHA recorded.

## 12. Runtime routing rules

### Casual/creative

Cortex may answer directly, subject to normal safety and dialogue state. There are no protected factual claims unless another organ contributes them.

### Factual/general knowledge

Cortex may draft an answer, but factual claims are marked provisional unless supported by authority/retrieval/evidence. In strict mode, unsupported factual additions are rejected.

### Exact/logic/memory

Unified R1.3 result is protected. Cortex only renders it.

### Business

R7.45.2 chooses/produces domain evidence. Cortex explains it. The cortex may not silently choose a different business domain result.

### ARC

V10 solution is protected. Cortex may explain the transformation but not change the grid/result.

### WorldGraph/causal state

V12 structured state transition/result is protected. Cortex may narrate the causal chain without changing the state result.

### Mixed requests

The orchestrator decomposes the request into claim/task segments and applies the strictest authority policy required by each segment.

## 13. Final output verification

Verifier checks include:

1. exact numbers and symbols;
2. protected entities and relations;
3. contradiction against verified claims;
4. required abstention/uncertainty;
5. accidental new factual assertions in strict mode;
6. malformed structured cortex output;
7. language-policy violations;
8. context identity and pending-slot consistency.

On failure:

```text
cortex output
   -> reject
   -> deterministic evidence renderer
   -> return safe final answer
   -> record failure telemetry for future training data
```

The user must always receive a usable answer when a deterministic verified answer exists, even if the cortex fails.

## 14. Benchmark/regression gates for Unified Final V1

### Cortex gates

- `RU_CORTEX_BLIND_V1`: reported per category; no hidden averaging over failed hard gates;
- verified-claim preservation: **100%**;
- exact-value preservation: **100%**;
- override-resistance: **100%**;
- structured response validity: **>=99.5%**;
- Russian accidental language-mix rate: **<=1%**;
- discourse/context accuracy: **>=95%**.

### Legacy organ gates

Adapters must reproduce the frozen legacy result or explicitly fail closed.

- Unified R1.3 authority regression: no protected-output drift;
- R7.44.3 original context suite: **25/25** retained, plus new blind context suite;
- R7.18 Blind-31 reference: **156/200 = 78%** retained when reproducing the original protocol;
- R7.45.2 free 20Q reference: **>=15/20** under the same frozen protocol;
- V10 original regression/tests: all pass;
- V12 original regression/tests: all pass.

Cross-benchmark scores must not be compared as if they use the same task distribution.

## 15. Provenance and freeze rules

Every promoted build records:

- Git commit SHA;
- source artifact SHA-256 for every imported organ;
- base cortex model repository + immutable revision;
- tokenizer revision;
- training dataset manifest and row-level source family;
- train/dev/eval split hashes;
- LoRA/merged/GGUF digests;
- decoding configuration;
- benchmark SHA;
- raw outputs;
- failure list;
- environment/package versions.

A benchmark is frozen **before** a model is trained/evaluated against it. Once opened, it is never patched to improve a score.

## 16. Known source-recovery blockers

1. **R7.38.3/X2 weights** are referenced by later R7.44 lineage manifests but were not found as standalone Drive artifacts during the 2026-09-15 audit. R7.44.3 must therefore be reconstructed only from verified available sources, or its missing dependency must be recovered before canonical promotion.
2. **Nanbeige4.1-3B Drive copy** contains config/tokenizer/index but not the two indexed Safetensors shards.
3. **Qwen3-4B-Instruct-2507** is not stored as a complete checkpoint on the current Drive and must be pulled by immutable revision in the GPU training environment if it wins the bakeoff.
4. The current `agi_nexus` migration is incomplete; only `nexus_v13` and `nexus_v18` are presently visible under `generations/` on `main`.
5. The old `R2.1 Qwen3-14B` Drive branch is source/evidence only, not a validated physical 14B inference release.

These blockers are tracked; none may be hidden by replacing “artifact present” with a README claim.

## 17. Implementation phases

### Phase 1 — canonical source recovery

- recover/pin Unified R1.3;
- recover/pin R7.18;
- recover R7.44.3 and all required dependency artifacts;
- recover/pin R7.2/R7.14;
- recover/pin R7.45.2, V10, V12;
- write component manifest and adapter-level regression tests.

### Phase 2 — contracts and orchestrator

- implement `EvidencePacket` and `RenderedAnswer`;
- implement adapters;
- implement routing;
- implement strict verifier and deterministic fallback;
- run without any generative cortex first.

### Phase 3 — frozen benchmark and corpus

- generate and freeze `RU_CORTEX_BLIND_V1`;
- build SFT datasets from non-benchmark sources;
- perform exact/fuzzy/minhash leakage audit;
- publish dataset manifest.

### Phase 4 — cortex bakeoff

- evaluate Qwen3-4B-Instruct-2507;
- evaluate Ministral-3B-Instruct;
- evaluate Nanbeige4.1-3B only if complete weights are available;
- promote the model that passes all hard gates with the best weighted Russian conversational quality/latency score.

### Phase 5 — GPU SFT

- run QLoRA SFT on the promoted cortex;
- evaluate checkpoints without changing the frozen benchmark;
- retain best checkpoint by hard-gate-first selection;
- run preference stage only if justified by measured residual failures.

### Phase 6 — integrated freeze

- full organ regressions;
- full Russian blind suite;
- adversarial authority-override suite;
- package adapter, manifests and GGUF derivatives;
- freeze NEXUS Unified Final V1.

### Phase 7 — optional Ω deployment work

Only after V1 quality is frozen, experiment with Ω-FLASH/model-store compression. Compression and low-bit deployment must never change the authority contract silently.

## 18. Promotion criterion

`NEXUS Unified Final V1` is promoted only when all of the following are true:

1. natural Russian conversation passes the frozen quality gate;
2. protected verified facts/numbers are preserved at 100% on the authority suite;
3. discourse/context gate passes;
4. all available legacy organ regressions pass;
5. every shipped model/artifact has a digest and source manifest;
6. no missing artifact is represented as physically present;
7. the final cortex can be replaced without changing the authority contracts.

## 19. Central invariant

> **The cortex speaks for NEXUS; it does not become NEXUS truth.**

That invariant is the compatibility boundary that allows a stronger future Russian LLM to replace Qwen/Ministral/Nanbeige without retraining or weakening the sovereign NEXUS authority backbone.
