# NEXUS Ω-FLASH V1 — compressed-capacity / small-working-set LLM

Status: R&D / falsification-first architecture

## Goal

Run a large-capacity language model without requiring the whole model to reside in VRAM or DRAM. The target is not "compress 70B by multiplying benchmark ratios". The target is a four-stage system:

1. **Primary model representation compression** — 2-bit / 1-bit / sub-1-bit or binary-factorized weights.
2. **Structure-aware lossless storage** — only where an additional exact compression win exists.
3. **Small active working set** — route/predict the weights or organs required for the next computation and keep the hottest set in cache/RAM.
4. **NVMe cold cortex** — cold model capacity remains on SSD and is fetched asynchronously in independent random-access tiles.

The architecture must preserve a RAW/compute-native fallback for high-entropy packed weights.

## Authority boundaries

- NEXUS inference architecture and routing: `Shtenco/agi_nexus`.
- Compression/archive algorithms: `Shtenco/ai_compress`.
- Temporal/shared-model compression research: `Shtenco/qr_compress`.
- Host/runtime orchestration: `Shtenco/synergy_meta_os` and `Shtenco/turbo_linux`.
- Historical NEXUS/compression lineage: `Shtenco/agi_olga` is R&D source only.

No codec implementation should be duplicated into `agi_nexus`. NEXUS consumes a versioned ModelStore contract exported by `ai_compress`.

## Existing SHTENCO mechanisms to reuse

### `ai_compress`

Use the consolidated Tier-1 portfolio rather than treating legacy names as independent magic compressors:

- **OMNIA Tier-1 v2** — verified route portfolio and RAW fallback.
- **UMC-256** — content-defined segmentation plus MDL/dynamic-programming expert selection.
- **Gabriel Horn Random-Access** — explicit access-amplification objective and independent range restoration.
- **GRAAL-AIS** — model/tensor-aware segmentation, stable object keys, selective restore and cross-version deduplication.
- **GRAAL-IGC / Infoton** — graph communities, references, XOR/splice patches.
- **TSC-X / DeepCompress / Spatial RAM lineage** — byte-plane, delta, Morton/tiling/SoA layouts.
- **SABF-X** — low-latency statistics/routing and RAW fallback.
- **Entropy backends** — Zstd, Brotli, LZMA, zlib, rANS/Huffman where appropriate.

### `qr_compress`

Use **QTD3 temporal-external-LZ / FastCDC references** for model families, checkpoints, adapters and fine-tunes that share a base model. QTD3 is not counted as free compression of a cold-start base model; the shared model bytes remain part of total cold storage accounting.

### Historical lineage recovered from `agi_olga`

Preserve useful mechanisms, not marketing names: EGD-256/Graal dictionaries, HACE-X cascades, AMCE-100X ensembles, RSX transforms, SLOTA/SHTZIP predictive/BWT paths, BIP39 packing for actual BIP39 text only, and the extended reversible primitive set. Promotion requires evidence on real model tensors.

## Key rule: do not entropy-compress everything

A packed, balanced 1-bit stream can be close to Shannon-incompressible. A uniform 2-bit stream can also be incompressible. Therefore:

```text
if expected_exact_saving <= decode_and_IO_cost:
    store compute-native RAW packed representation
else:
    store independently decodable compressed tile
```

This is essential. A 5–8 GB sub-1-bit model must not be assumed to become 30× smaller merely because OMNIA achieved a high geometric-mean ratio on a heterogeneous compression corpus.

## Proposed NEXUS ModelStore hierarchy

```text
L0  registers
    current partial sums / LUT fragments / decoded fixed-format fragments

L1/L2
    hottest compute-native binary/ternary tiles

L3
    hot factor tiles, route tables, codebooks

DRAM HOT
    KV cache, activations, hot model tiles, prefetch queue

DRAM WARM
    quickly decodable lossless tiles / predicted-next organs

NVMe HOT
    contiguous co-activation communities, compute-native or fast codec

NVMe COLD
    cold independently addressable tiles, stronger lossless codec where profitable

TEMPORAL MODEL STORE
    QTD3/GRAAL cross-version references for checkpoints/adapters/model families
```

## Tile directory

Every independently addressable tile should record at least:

```text
tensor/object id
logical layer / organ / expert id
logical offset and length
physical SSD offset and stored length
primary numeric representation (FP16/BF16/INT4/2bit/ternary/binary-factor)
lossless storage route
scale/codebook references
co-activation community id
hotness/prefetch class
SHA-256 or equivalent integrity digest
format version
```

The directory must permit direct lookup without scanning preceding variable-length records.

## Codec placement by data class

| Data class | First representation | Lossless/storage treatment |
|---|---|---|
| Balanced packed binary factors | compute-native 1 bit | RAW unless measured correlation exists |
| Correlated binary factor rows | binary packed | row reorder / XOR-lag / graph ref / OMNIA candidate |
| Ternary weights with strong zero mass | packed ternary | zero bitmap / fixed-format code + optional fast entropy wrapper |
| Uniform 2-bit weights | compute-native 2 bit | usually RAW |
| Sparse activation/router masks | bitset / index deltas | RLE/delta/rANS/Zstd candidate |
| FP16/BF16 scales | byte-plane / SoA | ZipNN-like byte grouping, TSC-X, delta/shuffle + fast entropy |
| Codebooks | compact native | dedup + fast lossless if profitable |
| KV cache | separate runtime policy | paged + quantized; do not mix with immutable weight archive |
| Checkpoint/fine-tune delta | native delta | QTD3/GRAAL cross-version references + residual codec |

## Runtime rule

The steady-state path should avoid `SSD -> decompress whole layer -> RAM -> compute`.

Preferred path:

```text
hidden state
  -> activation/organ predictor
  -> next tile ids
  -> async contiguous NVMe prefetch
  -> compressed/compute-native tile arrives in DRAM
  -> decode directly into the smallest useful cache/register representation
  -> GEMV/LUT/bitwise kernel
  -> retain hot tile / evict cold tile
```

For compute-native binary/ternary tiles there may be no entropy decompression step at all.

## OMNIA-LLM objective

Extend the existing MDL route objective from archive size/latency toward inference cost:

```text
J(tile, route) =
    stored_bytes
  + λ_decode * decode_latency
  + λ_io * expected_bytes_read_per_use
  + λ_amp * random_access_amplification
  + λ_miss * expected_cache_miss_cost
  + λ_energy * estimated_energy
  + λ_quality * quality_loss
```

For purely lossless routes, `quality_loss = 0`. Primary quantization/factorization is evaluated separately against perplexity/task quality before the lossless storage route is selected.

## External research anchors

The architecture should be benchmarked against, not merely compared rhetorically with:

- NanoQuant — low-rank binary factorization / sub-1-bit PTQ.
- BitNet / BitNet.cpp — native ternary/low-bit compute.
- ParetoQ and other 2-bit baselines — practical quality/size frontier.
- Apple `LLM in a Flash` — flash-aware locality and bundled reads.
- PowerInfer-2 — neuron-cluster storage/scheduling and I/O-compute overlap.
- T-MAC — table-lookup low-bit CPU kernels.
- ZipNN — tensor-aware lossless model compression/byte grouping.
- ZipServ (ASPLOS 2026) — load-compressed/compute-decompressed fused kernels.

## Falsification ladder

Do not begin with an unmeasured 70B deployment. Use the same pipeline at increasing scale:

1. **Synthetic entropy controls** — balanced binary, biased binary, sparse masks, ternary, correlated factors, scales.
2. **Real tensor slices** from a small open model — BF16/FP16 and quantized representations.
3. **7B/8B complete model** — compare GGUF/Q2/Q4, primary low-bit representation, and Ω-Store.
4. **14B/32B** under explicit RAM caps.
5. **70B** only after access traces prove that active bytes/token are low enough.

For every level collect:

```text
logical parameter count
effective BPW
bytes on SSD
peak RSS / peak VRAM
bytes read from SSD per generated token
read IOPS and sequential-read fraction
prefetch precision / recall
cache-hit ratio
access amplification
decode GB/s
TTFT
tokens/s
energy/token
perplexity and task-quality delta
exact lossless round-trip for storage wrappers
```

## Initial success criteria

A storage win alone is insufficient. Promotion requires all of:

- exact restoration for lossless wrappers;
- no forced expansion of incompressible packed tiles;
- materially lower SSD bytes/token than naive layer streaming;
- cache-hit ratio high enough that NVMe is not touched for most hot reuse;
- decode overhead hidden by or smaller than I/O saved;
- measured quality loss attributable only to the primary low-bit representation and within a preregistered bound;
- end-to-end tokens/s improvement or a model-size capability impossible for the baseline under the same RAM/VRAM cap.

## Implemented probe

`Shtenco/ai_compress/compression_lab/nexus_omega_store_probe.py` is the first bridge. It evaluates independent fixed-size tiles across RAW, OMNIA Speed, OMNIA Balanced and Gabriel Random-Access, verifies exact reconstruction, and scores storage against decode latency and random-access amplification.

The next implementation step is a real `OmegaModelStore` container with an indexed tile directory plus adapters for Safetensors/GGUF tensor boundaries and an activation-trace-driven hot/cold layout.
