from __future__ import annotations

"""Independent raw auditor for the historical NEXUS V8 language archive.

This tool exists specifically to prevent a historical release claim such as
"696,000 utterances" from silently becoming a new R8.2 training fact. It must
be run against the physical archive before DATASET_MANIFEST.raw_replay_permitted
is changed to true.

Usage:
    python -m generations.r82_ru_dialogue.audit_v8_raw \
        /path/NEXUS-FINANCE-v8.0.0-BDH-INSPIRED-FULL.zip \
        --out V8_RAW_AUDIT.json
"""

import argparse
import collections
import hashlib
import io
import json
import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


HISTORICAL_ARCHIVE_SHA256 = "499cf01d42bb4f913a287b42301293edca2780c55203e2d0a45d5dceaefe7b68"
HISTORICAL_ROWS = 696_000
HISTORICAL_DOMAINS = 180
HISTORICAL_CONVERSATION_DOMAINS = 30

TEXT_KEYS = ("text", "utterance", "query", "q", "prompt", "input", "message")
LABEL_KEYS = ("domain", "label", "category", "intent", "class", "target")
SESSION_KEYS = ("session_id", "dialogue_id", "conversation_id", "thread_id", "chat_id")
TURN_KEYS = ("turn_index", "turn_id", "message_index", "role", "speaker")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[0-9a-zа-яё]+", text.lower(), flags=re.IGNORECASE))


def stable64(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


def simhash64(text: str) -> int:
    tokens = normalize_text(text).split()
    if not tokens:
        return 0
    acc = [0] * 64
    for token in tokens:
        v = stable64(token)
        for bit in range(64):
            acc[bit] += 1 if (v >> bit) & 1 else -1
    out = 0
    for bit, score in enumerate(acc):
        if score >= 0:
            out |= 1 << bit
    return out


def hamming64(a: int, b: int) -> int:
    return (a ^ b).bit_count()


@dataclass
class JsonlCandidate:
    logical_name: str
    raw_bytes: bytes


class NearDuplicateEstimator:
    """Streaming SimHash LSH estimate; diagnostic, not a mathematical census."""

    def __init__(self, max_bucket_candidates: int = 128, max_hamming: int = 3) -> None:
        self.max_bucket_candidates = int(max_bucket_candidates)
        self.max_hamming = int(max_hamming)
        self.bands: Dict[Tuple[int, int], List[int]] = collections.defaultdict(list)
        self.near_duplicate_rows = 0
        self.rows_seen = 0

    def add(self, text: str) -> None:
        sig = simhash64(text)
        self.rows_seen += 1
        duplicate = False
        for band in range(4):
            key = (band, (sig >> (band * 16)) & 0xFFFF)
            bucket = self.bands[key]
            for prior in bucket[-self.max_bucket_candidates :]:
                if hamming64(sig, prior) <= self.max_hamming:
                    duplicate = True
                    break
            if duplicate:
                break
        if duplicate:
            self.near_duplicate_rows += 1
        for band in range(4):
            key = (band, (sig >> (band * 16)) & 0xFFFF)
            self.bands[key].append(sig)


def _read_zip_candidates(path: Path, max_nested_depth: int = 2) -> tuple[List[dict], List[JsonlCandidate]]:
    inventory: List[dict] = []
    candidates: List[JsonlCandidate] = []

    def inspect_zip(raw: bytes, prefix: str, depth: int) -> None:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in z.infolist():
                logical = f"{prefix}{info.filename}"
                inventory.append(
                    {
                        "name": logical,
                        "compressed_size": info.compress_size,
                        "uncompressed_size": info.file_size,
                        "crc": info.CRC,
                        "is_dir": info.is_dir(),
                    }
                )
                if info.is_dir():
                    continue
                low = info.filename.lower()
                if low.endswith(".jsonl"):
                    candidates.append(JsonlCandidate(logical, z.read(info)))
                elif low.endswith(".zip") and depth < max_nested_depth:
                    inspect_zip(z.read(info), f"{logical}!/", depth + 1)

    inspect_zip(path.read_bytes(), "", 0)
    return inventory, candidates


def choose_training_candidate(candidates: Sequence[JsonlCandidate]) -> JsonlCandidate:
    if not candidates:
        raise RuntimeError("No JSONL corpus member found in archive or nested ZIPs")
    ranked = sorted(
        candidates,
        key=lambda c: (
            "train_corpus" in c.logical_name.lower(),
            "train" in c.logical_name.lower(),
            len(c.raw_bytes),
        ),
        reverse=True,
    )
    return ranked[0]


def audit_jsonl(candidate: JsonlCandidate) -> dict:
    valid = 0
    invalid = 0
    key_counts = collections.Counter()
    labels = collections.Counter()
    session_keys = collections.Counter()
    turn_keys = collections.Counter()
    role_values = collections.Counter()
    text_key_counts = collections.Counter()
    exact_seen: set[bytes] = set()
    normalized_seen: set[bytes] = set()
    exact_dup = 0
    normalized_dup = 0
    missing_text = 0
    near = NearDuplicateEstimator()
    examples: List[dict] = []

    raw_sha = hashlib.sha256(candidate.raw_bytes).hexdigest()
    for line_number, line in enumerate(candidate.raw_bytes.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            invalid += 1
            continue
        if not isinstance(row, dict):
            invalid += 1
            continue
        valid += 1
        key_counts.update(row.keys())

        label = None
        for key in LABEL_KEYS:
            if key in row and row[key] is not None:
                label = str(row[key])
                labels[label] += 1
                break

        for key in SESSION_KEYS:
            if key in row:
                session_keys[key] += 1
        for key in TURN_KEYS:
            if key in row:
                turn_keys[key] += 1
        if "role" in row:
            role_values[str(row["role"])] += 1

        text = None
        for key in TEXT_KEYS:
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                text = value
                text_key_counts[key] += 1
                break
        if text is None:
            missing_text += 1
            if len(examples) < 5:
                examples.append({"line": line_number, "keys": sorted(row.keys()), "label": label})
            continue

        raw_digest = hashlib.blake2b(text.encode("utf-8"), digest_size=16).digest()
        if raw_digest in exact_seen:
            exact_dup += 1
        else:
            exact_seen.add(raw_digest)

        norm = normalize_text(text)
        norm_digest = hashlib.blake2b(norm.encode("utf-8"), digest_size=16).digest()
        if norm_digest in normalized_seen:
            normalized_dup += 1
        else:
            normalized_seen.add(norm_digest)
        near.add(text)

    conversation_like = [
        label
        for label in labels
        if re.search(r"dialog|conversation|chat|follow|context|turn|memory|resume|anaph|диалог|контекст|памят", label, re.I)
    ]

    return {
        "logical_member": candidate.logical_name,
        "member_uncompressed_bytes": len(candidate.raw_bytes),
        "member_sha256": raw_sha,
        "valid_jsonl_rows": valid,
        "invalid_nonempty_rows": invalid,
        "historical_row_match": valid == HISTORICAL_ROWS,
        "top_level_keys": dict(key_counts.most_common()),
        "text_keys": dict(text_key_counts),
        "label_key_candidates": list(LABEL_KEYS),
        "unique_primary_labels": len(labels),
        "historical_domain_match": len(labels) == HISTORICAL_DOMAINS,
        "label_counts": dict(labels.most_common()),
        "conversation_like_labels_lexical_diagnostic": sorted(conversation_like),
        "conversation_like_label_count": len(conversation_like),
        "historical_conversation_domain_count": HISTORICAL_CONVERSATION_DOMAINS,
        "session_linkage_fields": dict(session_keys),
        "turn_linkage_fields": dict(turn_keys),
        "role_values": dict(role_values),
        "has_explicit_session_linkage": bool(session_keys),
        "has_explicit_turn_linkage": bool(turn_keys),
        "rows_missing_recognized_text": missing_text,
        "exact_duplicate_text_rows": exact_dup,
        "exact_duplicate_fraction": exact_dup / max(1, valid - missing_text),
        "normalized_duplicate_text_rows": normalized_dup,
        "normalized_duplicate_fraction": normalized_dup / max(1, valid - missing_text),
        "near_duplicate_simhash_rows_estimate": near.near_duplicate_rows,
        "near_duplicate_simhash_fraction_estimate": near.near_duplicate_rows / max(1, near.rows_seen),
        "near_duplicate_method": "64-bit token SimHash; 4x16-bit LSH; hamming<=3; diagnostic estimate only",
        "schema_examples_without_recognized_text": examples,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("--out", type=Path, default=Path("V8_RAW_AUDIT.json"))
    ap.add_argument("--allow-sha-mismatch", action="store_true")
    args = ap.parse_args()

    if not args.archive.is_file():
        raise SystemExit(f"archive not found: {args.archive}")
    archive_sha = sha256_file(args.archive)
    sha_match = archive_sha == HISTORICAL_ARCHIVE_SHA256
    if not sha_match and not args.allow_sha_mismatch:
        raise SystemExit(
            f"archive SHA mismatch: got {archive_sha}, expected {HISTORICAL_ARCHIVE_SHA256}; "
            "use --allow-sha-mismatch only for forensic inspection"
        )

    inventory, candidates = _read_zip_candidates(args.archive)
    selected = choose_training_candidate(candidates)
    corpus = audit_jsonl(selected)
    raw_replay_permitted = bool(
        sha_match
        and corpus["historical_row_match"]
        and corpus["historical_domain_match"]
        and corpus["invalid_nonempty_rows"] == 0
    )

    report = {
        "audit_version": "R8.2-V8-RAW-AUDIT-1",
        "archive": str(args.archive),
        "archive_size_bytes": args.archive.stat().st_size,
        "archive_sha256": archive_sha,
        "historical_archive_sha256": HISTORICAL_ARCHIVE_SHA256,
        "archive_sha_matches_historical_release": sha_match,
        "zip_member_count_including_nested": len(inventory),
        "jsonl_candidates": [
            {"logical_name": c.logical_name, "bytes": len(c.raw_bytes)} for c in candidates
        ],
        "selected_training_member": selected.logical_name,
        "corpus": corpus,
        "raw_replay_permitted": raw_replay_permitted,
        "scientific_boundary": (
            "This audit verifies archive/corpus integrity and schema only. It does not reproduce "
            "historical V8 model quality, and it does not make disclosed V8 evaluations fresh blinds."
        ),
        "inventory": inventory,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "archive_sha256",
        "archive_sha_matches_historical_release",
        "selected_training_member",
        "raw_replay_permitted",
    )}, ensure_ascii=False, indent=2))
    print(json.dumps({
        "valid_jsonl_rows": corpus["valid_jsonl_rows"],
        "unique_primary_labels": corpus["unique_primary_labels"],
        "session_linkage": corpus["has_explicit_session_linkage"],
        "turn_linkage": corpus["has_explicit_turn_linkage"],
        "exact_duplicate_fraction": corpus["exact_duplicate_fraction"],
        "normalized_duplicate_fraction": corpus["normalized_duplicate_fraction"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
