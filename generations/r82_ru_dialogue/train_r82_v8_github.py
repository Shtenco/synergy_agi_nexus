from __future__ import annotations

"""GitHub-runnable R8.2 V8 trainer.

This is intentionally split into two learned organs:
1) semantic/domain router trained over the full audited V8 corpus;
2) compact recurrent Russian Surface Cortex trained on a deterministic reservoir
   of the same corpus plus any real dialogue pairs discoverable in the raw rows.

It does NOT claim that a language-model loss proves reasoning. CyberLogic,
ProofVerifier, ContextBinder and EpistemicGovernor remain separate authorities.
"""

import argparse
import collections
import hashlib
import io
import json
import math
import os
import random
import re
import time
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score

import torch
from torch import nn

from .audit_v8_raw import (
    HISTORICAL_ARCHIVE_SHA256,
    _read_zip_candidates,
    choose_training_candidate,
    normalize_text,
    sha256_file,
)

TEXT_KEYS = ("text", "utterance", "query", "q", "prompt", "input", "message")
LABEL_KEYS = ("domain", "domain_id", "label", "category", "intent", "class", "target")
RESPONSE_KEYS = ("response", "answer", "reply", "assistant", "output", "completion")
SESSION_KEYS = ("session_id", "dialogue_id", "conversation_id", "thread_id", "chat_id")
TURN_KEYS = ("turn_index", "turn_id", "message_index")
ROLE_KEYS = ("role", "speaker")


def iter_rows(raw: bytes) -> Iterator[dict]:
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            yield row


def first_str(row: Mapping[str, object], keys: Sequence[str]) -> Optional[str]:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None and key in LABEL_KEYS:
            return str(value)
    return None


def template_family(text: str) -> str:
    s = normalize_text(text)
    s = re.sub(r"\b\d+(?:[.,]\d+)?\b", "<num>", s)
    s = re.sub(r"\b[0-9a-f]{8,}\b", "<id>", s)
    return s[:180]


def split_is_holdout(text: str, pct: int = 10) -> bool:
    h = hashlib.blake2b(template_family(text).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big") % 100 < pct


def scan_corpus(raw: bytes, reservoir_size: int, seed: int) -> dict:
    rng = random.Random(seed)
    labels = collections.Counter()
    key_counts = collections.Counter()
    response_pairs: List[Tuple[str, str]] = []
    reservoir: List[str] = []
    rows = 0
    text_rows = 0
    labelled_rows = 0
    response_field_pairs = 0
    session_turn_pairs = 0
    last_user: Dict[str, str] = {}

    for row in iter_rows(raw):
        rows += 1
        key_counts.update(row.keys())
        text = first_str(row, TEXT_KEYS)
        label = first_str(row, LABEL_KEYS)
        if label is not None:
            labels[label] += 1
            labelled_rows += 1
        if text is None:
            continue
        text_rows += 1

        if len(reservoir) < reservoir_size:
            reservoir.append(text)
        else:
            j = rng.randrange(text_rows)
            if j < reservoir_size:
                reservoir[j] = text

        resp = first_str(row, RESPONSE_KEYS)
        if resp:
            if len(response_pairs) < 100_000:
                response_pairs.append((text, resp))
            response_field_pairs += 1

        session = first_str(row, SESSION_KEYS)
        role = (first_str(row, ROLE_KEYS) or "").lower()
        if session:
            if role in {"user", "human", "пользователь", "client"}:
                last_user[session] = text
            elif role in {"assistant", "bot", "nexus", "ассистент"} and session in last_user:
                if len(response_pairs) < 100_000:
                    response_pairs.append((last_user[session], text))
                session_turn_pairs += 1
                last_user.pop(session, None)

    return {
        "rows": rows,
        "text_rows": text_rows,
        "labelled_rows": labelled_rows,
        "labels": labels,
        "key_counts": key_counts,
        "reservoir": reservoir,
        "response_pairs": response_pairs,
        "response_field_pairs": response_field_pairs,
        "session_turn_pairs": session_turn_pairs,
    }


def train_router(raw: bytes, classes: Sequence[str], out_dir: Path, batch_size: int = 4096) -> dict:
    vectorizer = HashingVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        n_features=2**17,
        alternate_sign=False,
        norm="l2",
        lowercase=True,
    )
    clf = SGDClassifier(
        loss="log_loss",
        alpha=2e-6,
        penalty="l2",
        random_state=82026,
        average=True,
    )
    class_array = np.array(sorted(classes), dtype=object)
    first = True
    bx: List[str] = []
    by: List[str] = []
    train_n = 0
    hold_text: List[str] = []
    hold_y: List[str] = []

    def flush() -> None:
        nonlocal first, train_n, bx, by
        if not bx:
            return
        X = vectorizer.transform(bx)
        y = np.array(by, dtype=object)
        if first:
            clf.partial_fit(X, y, classes=class_array)
            first = False
        else:
            clf.partial_fit(X, y)
        train_n += len(bx)
        bx, by = [], []

    for row in iter_rows(raw):
        text = first_str(row, TEXT_KEYS)
        label = first_str(row, LABEL_KEYS)
        if not text or label is None or label not in classes:
            continue
        if split_is_holdout(text, pct=10):
            if len(hold_text) < 80_000:
                hold_text.append(text)
                hold_y.append(label)
            continue
        bx.append(text); by.append(label)
        if len(bx) >= batch_size:
            flush()
    flush()
    if first:
        raise RuntimeError("No labelled training rows found")

    pred = clf.predict(vectorizer.transform(hold_text)) if hold_text else np.array([], dtype=object)
    metrics = {
        "train_rows": train_n,
        "holdout_rows": len(hold_text),
        "family_split": "blake2b(normalized-number-masked-template) mod 100 < 10",
        "accuracy": float(accuracy_score(hold_y, pred)) if hold_text else None,
        "macro_f1": float(f1_score(hold_y, pred, average="macro", zero_division=0)) if hold_text else None,
        "classes": len(classes),
        "warning": "Internal family-hash holdout; not a fresh external benchmark.",
    }
    joblib.dump({"vectorizer": vectorizer, "classifier": clf, "classes": list(class_array)}, out_dir / "r82_v8_router.joblib")
    return metrics


class SurfaceGRU(nn.Module):
    def __init__(self, vocab_size: int, emb: int = 192, hidden: int = 384, layers: int = 2):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb)
        self.gru = nn.GRU(emb, hidden, layers, batch_first=True, dropout=0.10 if layers > 1 else 0.0)
        self.head = nn.Linear(hidden, vocab_size)
    def forward(self, x, h=None):
        y, h = self.gru(self.emb(x), h)
        return self.head(y), h


def build_surface_text(reservoir: Sequence[str], response_pairs: Sequence[Tuple[str, str]]) -> Tuple[str, str]:
    chunks: List[str] = []
    mode = "V8_RAW_LANGUAGE_ONLY"
    for text in reservoir:
        chunks.append(text.strip() + "\n")
    if response_pairs:
        mode = "V8_RAW_PLUS_DISCOVERED_DIALOGUE"
        # Real discoverable pairs are repeated to make their conditional
        # structure visible to the compact cortex without relabelling them.
        for user, assistant in response_pairs[:50_000]:
            chunks.append(f"Пользователь: {user}\nNEXUS: {assistant}\n<КОНЕЦ>\n")
            chunks.append(f"Пользователь: {user}\nNEXUS: {assistant}\n<КОНЕЦ>\n")
    return "".join(chunks), mode


def train_surface(text: str, out_dir: Path, steps: int, seed: int) -> dict:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    chars = collections.Counter(text)
    vocab_chars = [c for c, _ in chars.most_common(508)]
    specials = ["<PAD>", "<UNK>"]
    itos = specials + [c for c in vocab_chars if c not in specials]
    stoi = {c: i for i, c in enumerate(itos)}
    ids = torch.tensor([stoi.get(c, 1) for c in text], dtype=torch.long)
    if len(ids) < 10_000:
        raise RuntimeError("Surface corpus unexpectedly small")

    device = torch.device("cpu")
    model = SurfaceGRU(len(itos)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2.5e-3, weight_decay=0.01)
    loss_fn = nn.CrossEntropyLoss()
    seq_len = 144
    batch = 24
    gen = torch.Generator().manual_seed(seed)
    losses: List[float] = []
    model.train()
    t0 = time.time()
    for step in range(1, steps + 1):
        starts = torch.randint(0, len(ids) - seq_len - 1, (batch,), generator=gen)
        x = torch.stack([ids[s:s+seq_len] for s in starts]).to(device)
        y = torch.stack([ids[s+1:s+seq_len+1] for s in starts]).to(device)
        logits, _ = model(x)
        loss = loss_fn(logits.reshape(-1, len(itos)), y.reshape(-1))
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        losses.append(float(loss.item()))
        if step % 100 == 0:
            print(json.dumps({"surface_step": step, "loss100": float(np.mean(losses[-100:]))}), flush=True)

    ckpt = {
        "state_dict": model.state_dict(),
        "itos": itos,
        "config": {"emb": 192, "hidden": 384, "layers": 2},
        "seed": seed,
        "steps": steps,
    }
    torch.save(ckpt, out_dir / "r82_russian_surface_gru.pt")
    return {
        "parameters": int(sum(p.numel() for p in model.parameters())),
        "vocab_size": len(itos),
        "training_chars": len(ids),
        "steps": steps,
        "loss_first100": float(np.mean(losses[:100])) if losses else None,
        "loss_last100": float(np.mean(losses[-100:])) if losses else None,
        "elapsed_s": time.time() - t0,
    }


@torch.no_grad()
def generate(model: SurfaceGRU, stoi: Mapping[str, int], itos: Sequence[str], prompt: str, max_new: int = 260, temperature: float = 0.72, top_k: int = 36) -> str:
    model.eval()
    ids = [stoi.get(c, 1) for c in prompt]
    x = torch.tensor([ids], dtype=torch.long)
    logits, h = model(x)
    cur = x[:, -1:]
    out: List[str] = []
    for _ in range(max_new):
        logits, h = model(cur, h)
        z = logits[:, -1, :] / max(0.1, temperature)
        if top_k:
            vals, idx = torch.topk(z, min(top_k, z.shape[-1]))
            probs = torch.softmax(vals, dim=-1)
            pick = idx.gather(-1, torch.multinomial(probs, 1))
        else:
            pick = torch.multinomial(torch.softmax(z, dim=-1), 1)
        cur = pick
        ch = itos[int(pick.item())]
        if ch not in {"<PAD>", "<UNK>"}:
            out.append(ch)
        if "".join(out).endswith("<КОНЕЦ>"):
            break
    return "".join(out).strip()


def dialogue_probe(out_dir: Path, prompts: Sequence[str]) -> dict:
    ckpt = torch.load(out_dir / "r82_russian_surface_gru.pt", map_location="cpu")
    itos = ckpt["itos"]; stoi = {c: i for i, c in enumerate(itos)}
    cfg = ckpt["config"]
    model = SurfaceGRU(len(itos), cfg["emb"], cfg["hidden"], cfg["layers"])
    model.load_state_dict(ckpt["state_dict"])
    history = ""
    rows = []
    for i, prompt in enumerate(prompts, 1):
        prefix = history + f"Пользователь: {prompt}\nNEXUS:"
        reply = generate(model, stoi, itos, prefix, max_new=280)
        # Keep only the first model turn if it begins generating another role.
        for marker in ("\nПользователь:", "\nNEXUS:"):
            if marker in reply:
                reply = reply.split(marker, 1)[0].strip()
        rows.append({"turn": i, "user": prompt, "model": reply})
        history = (history + f"Пользователь: {prompt}\nNEXUS: {reply}\n")[-3500:]
    md = ["# NEXUS R8.2 V8 learned surface — raw dialogue probe", "", "This is raw model output; it is not hand-corrected and not a quality claim.", ""]
    for r in rows:
        md += [f"**Пользователь:** {r['user']}", "", f"**NEXUS:** {r['model']}", ""]
    (out_dir / "DIALOGUE_RAW.md").write_text("\n".join(md), encoding="utf-8")
    return {"turns": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("--out", type=Path, default=Path("r82_train_out"))
    ap.add_argument("--surface-reservoir", type=int, default=100_000)
    ap.add_argument("--surface-steps", type=int, default=1800)
    ap.add_argument("--seed", type=int, default=820260910)
    ap.add_argument("--allow-sha-mismatch", action="store_true")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    archive_sha = sha256_file(args.archive)
    if archive_sha != HISTORICAL_ARCHIVE_SHA256 and not args.allow_sha_mismatch:
        raise SystemExit(f"V8 SHA mismatch: {archive_sha}")
    inventory, candidates = _read_zip_candidates(args.archive)
    candidate = choose_training_candidate(candidates)
    scan = scan_corpus(candidate.raw_bytes, args.surface_reservoir, args.seed)
    classes = sorted(scan["labels"])
    print(json.dumps({"rows": scan["rows"], "text_rows": scan["text_rows"], "labels": len(classes), "pairs": len(scan["response_pairs"])}, ensure_ascii=False), flush=True)

    router_metrics = train_router(candidate.raw_bytes, classes, args.out)
    surface_text, surface_mode = build_surface_text(scan["reservoir"], scan["response_pairs"])
    surface_metrics = train_surface(surface_text, args.out, args.surface_steps, args.seed)
    dialogue = dialogue_probe(args.out, [
        "Привет. Кто ты и что умеешь?",
        "Объясни простыми словами, чем гипотеза отличается от доказанного факта.",
        "А теперь скажи это короче.",
        "Если два источника повторяют одну и ту же ошибку, это два независимых доказательства?",
        "Что ты должен делать, если данных недостаточно?",
        "Вернёмся к первому вопросу: какая у тебя главная задача?",
    ])

    report = {
        "version": "R8.2-V8-GITHUB-TRAIN-1",
        "archive_sha256": archive_sha,
        "selected_member": candidate.logical_name,
        "selected_member_sha256": hashlib.sha256(candidate.raw_bytes).hexdigest(),
        "rows": scan["rows"],
        "text_rows": scan["text_rows"],
        "labelled_rows": scan["labelled_rows"],
        "unique_labels": len(classes),
        "response_field_pairs_found": scan["response_field_pairs"],
        "session_turn_pairs_found": scan["session_turn_pairs"],
        "dialogue_pairs_used": len(scan["response_pairs"]),
        "surface_mode": surface_mode,
        "router": router_metrics,
        "surface": surface_metrics,
        "dialogue_probe": dialogue,
        "scientific_boundary": [
            "Router holdout is internal family-hash development evidence, not an external blind.",
            "Surface LM loss measures language modeling only, not reasoning correctness.",
            "Raw dialogue output is not hand-edited.",
            "CyberLogic/Proof/Epistemic authority remains outside the learned Surface Cortex.",
        ],
    }
    (args.out / "TRAINING_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "CORPUS_KEYS.json").write_text(json.dumps(dict(scan["key_counts"]), ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "DOMAIN_COUNTS.json").write_text(json.dumps(dict(scan["labels"].most_common()), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
