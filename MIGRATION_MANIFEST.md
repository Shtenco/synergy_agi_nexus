# NEXUS Migration Manifest

**Date:** 2026-09-12  
**Policy:** Copy-only. Original sources in `Shtenco/agi_olga` are never deleted or modified by this migration.  
**Canonical target:** `Shtenco/agi_nexus`  
**Source of truth (R&D lineage):** `Shtenco/agi_olga` @ `68023d51825eeefe5432263c863468e44636d862`

## Structure

```text
agi_nexus/
  generations/
    smallworld_v11/     # SmallWorld AGI V11 foundation
    nexus_600k/         # NEXUS-600K (600,000 params)
    nexus_v13/          # World model + Russian logic
    nexus_v16/          # Distributed / five-node
    nexus_v17/          # Four-way fusion teachers
    nexus_v18/          # Unified standalone (611,257 params) — preferred current generation
    collective/         # Multi-node consensus layer
  omega_flash/          # NEXUS Ω-FLASH architecture
  contracts/            # Inference / identity contracts (future)
  provenance/           # SHA, freeze markers, reports
  MIGRATION_MANIFEST.md # this file
```

## Migration status

| Generation | Status | Source path in agi_olga | Notes |
|---|---|---|---|
| NEXUS V18 | **IN PROGRESS** | `nexus_v18/` | First batch placed |
| NEXUS-600K | pending | `nexus_600k/` | |
| SmallWorld V11 | pending | `smallworld_agi/` | |
| NEXUS V13 | pending | `nexus_v13/` | Required by V18 russian_runtime |
| V16 / V17 / Collective | pending | `nexus_v16/`, `nexus_v17/`, `nexus_collective/` | |
| Ω-FLASH | already present | `NEXUS_OMEGA_FLASH_V1.md` | |

## Rules

1. Never delete or rewrite history in `agi_olga`.
2. Every promoted file keeps a provenance note (source repo + path + SHA).
3. Binary checkpoints are referenced by SHA only until separately imported.
4. Promotion to "canonical" requires independent benchmark evidence (see `agi_nexus` README).
