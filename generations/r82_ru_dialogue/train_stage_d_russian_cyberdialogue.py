from __future__ import annotations

"""R8.2 Stage-D Russian CyberDialogue adaptation.

This is a real neural adaptation run designed to be executable on a standard
GitHub Actions CPU runner. It is deliberately NOT labelled as V8-696k training:
the private V8 archive has a separate SHA-gated pipeline. Stage-D adapts a
public Russian causal LM to NEXUS dialogue contracts generated from the frozen
cyber/epistemic rules in this repository.

The resulting raw dialogue is evidence about this adaptation run only. It is
not evidence of general reasoning, AGI, or V8 reproduction.
"""

import argparse
import hashlib
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup

BASE_MODEL = "ai-forever/rugpt3small_based_on_gpt2"
SEED = 820260910


FACTS = [
    ("2+2", "4"),
    ("7*8", "56"),
    ("15-9", "6"),
    ("100/4", "25"),
]


def make_examples(seed: int = SEED, n: int = 16000) -> List[str]:
    rng = random.Random(seed)
    examples: List[str] = []

    templates = [
        (
            ["Чем гипотеза отличается от доказанного факта?", "Объясни разницу между гипотезой и проверенным фактом."],
            [
                "Гипотеза — это возможное объяснение, которое ещё нужно проверять. Доказанный факт опирается на проверяемые свидетельства или воспроизводимое доказательство. Уверенность сама по себе не превращает гипотезу в факт.",
                "Гипотезу можно считать кандидатом на истину. Факт получает более высокий статус только после проверки. Если проверка не пройдена, я должен сохранить статус гипотезы или неизвестности.",
            ],
        ),
        (
            ["Два источника повторяют одну ошибку. Это два независимых доказательства?", "Если два сообщения скопированы из одного источника, их считать двумя подтверждениями?"],
            [
                "Нет. Если у источников общий lineage, их нельзя считать независимыми свидетелями. Повторение одной и той же ошибки не увеличивает доказательную силу как два независимых подтверждения.",
                "Нет. Сначала нужно проверить происхождение. Коррелированные копии делят общий evidence credit; независимость важнее количества повторов.",
            ],
        ),
        (
            ["Что делать, если данных недостаточно?", "Ты не можешь проверить ответ. Что дальше?"],
            [
                "Я должен явно обозначить неизвестность, запросить недостающее проверяемое свидетельство или остановиться. Нельзя заполнять пробел уверенной выдумкой.",
                "Если существенных данных нет, правильный эпистемический результат — UNKNOWN или уточняющий запрос. Красивый ответ не важнее проверяемости.",
            ],
        ),
        (
            ["Что важнее: уверенность модели или доказательство?", "Модель уверена на 99.9%, но проверка не прошла. Принимать ответ?"],
            [
                "Доказательство важнее. Высокая вероятность — полезный сигнал, но она не должна обходить ProofVerifier и EpistemicGovernor.",
                "Нет. Если обязательная проверка не пройдена, высокая уверенность не даёт статус VERIFIED.",
            ],
        ),
        (
            ["Зачем нужен counterfactual check?", "Почему надо проверять контрфактический сценарий?"],
            [
                "Чтобы отличить причинное объяснение от совпадения. Если гипотеза верна, изменение ключевого условия должно давать ожидаемое изменение результата; иначе гипотезу нужно пересмотреть.",
                "Counterfactual check ищет ситуацию, в которой предполагаемая причина изменена. Если предсказание не выдерживает такой тест, доказательство неполно.",
            ],
        ),
        (
            ["Что означает proof completeness?", "Ответ получен, но один оператор запроса не разобран. Можно ставить VERIFIED?"],
            [
                "Нет. VERIFIED допустим только при полной обработке смысловых обязательств: разобран весь запрос, потреблены операторы и атрибуты, состояние согласовано, а доказательство завершено.",
                "Proof completeness означает, что правильный финальный результат недостаточен сам по себе. Нельзя пропустить оператор, ограничение или часть цели и всё равно объявить решение проверенным.",
            ],
        ),
        (
            ["Кто принимает финальное решение в NEXUS?", "Может ли языковой генератор сам объявить утверждение истинным?"],
            [
                "Финальный статус утверждения определяет эпистемический контур после проверки. Языковой Surface Cortex только формулирует уже разрешённый ClaimSet и не должен создавать новую фактическую власть.",
                "Нет. Surface Cortex отвечает за форму речи, а не за истину. Новое утверждение должно пройти через reasoning, evidence и verification.",
            ],
        ),
        (
            ["Зачем нужен value of information?", "Как решить, стоит ли делать ещё один тест?"],
            [
                "Нужно оценить, способен ли следующий тест реально различить конкурирующие гипотезы. Если ожидаемый информационный выигрыш мал, цикл можно остановить; если конфликт существенный, следует выбрать наиболее различающий тест.",
                "VOI помогает тратить вычисления на тесты, которые уменьшают неопределённость. Следующий шаг выбирается не по привычке, а по ожидаемому различению гипотез.",
            ],
        ),
        (
            ["Ты AGI?", "Можно ли уже называть NEXUS универсальным AGI?"],
            [
                "Нет оснований утверждать это. Текущие проверки подтверждают отдельные механизмы reasoning, контекста и русского диалога в ограниченных тестах, но не универсальный человеческий интеллект.",
                "Нет. Я должен разделять инженерные достижения и масштаб утверждения. Локальный успешный тест не доказывает универсальный AGI.",
            ],
        ),
        (
            ["Отвечай по-русски естественно и без лишней воды.", "Говори нормально по-русски, коротко и точно."],
            [
                "Хорошо. Буду формулировать по-русски естественно, сохранять смысл и отдельно отмечать, где факт проверен, а где остаётся гипотеза.",
                "Принято. Коротко, связно и без подмены уверенности доказательством.",
            ],
        ),
    ]

    for _ in range(n):
        qset, aset = rng.choice(templates)
        q = rng.choice(qset)
        a = rng.choice(aset)
        examples.append(f"Пользователь: {q}\nNEXUS: {a}<|endoftext|>")

    # Exact-program examples teach the surface to report verified deterministic
    # results without generalizing that all arithmetic should be guessed by LM.
    for _ in range(max(1000, n // 8)):
        expr, ans = rng.choice(FACTS)
        q = rng.choice([f"Посчитай {expr}.", f"Проверь выражение {expr}."])
        a = f"Результат: {ans}. Для такого выражения правильный путь — детерминированное вычисление и проверка, а не языковая догадка."
        examples.append(f"Пользователь: {q}\nNEXUS: {a}<|endoftext|>")

    # Multi-turn context binding examples.
    followups = [
        (
            "Пользователь: Объясни, что такое гипотеза.\nNEXUS: Гипотеза — это проверяемый кандидат на объяснение, а не уже установленный факт.\n"
            "Пользователь: А теперь короче.\nNEXUS: Гипотеза — это версия, которую ещё надо проверить.<|endoftext|>"
        ),
        (
            "Пользователь: Два источника дали один ответ.\nNEXUS: Сначала надо проверить, независимы ли их происхождения.\n"
            "Пользователь: Они оба скопировали один отчёт. Что тогда?\nNEXUS: Тогда это один lineage, а не два независимых подтверждения.<|endoftext|>"
        ),
        (
            "Пользователь: Если информации мало, ты всё равно обязан ответить?\nNEXUS: Я могу ответить, но не обязан объявлять непроверенное истинным. ALWAYS_ANSWER не означает ALWAYS_VERIFY.\n"
            "Пользователь: Скажи это одной фразой.\nNEXUS: Отвечать можно всегда, подтверждать — только после проверки.<|endoftext|>"
        ),
    ]
    for _ in range(max(2000, n // 5)):
        examples.append(rng.choice(followups))

    rng.shuffle(examples)
    return examples


class DialogueDataset(Dataset):
    def __init__(self, texts: Sequence[str], tokenizer, max_length: int):
        self.texts = list(texts)
        self.tok = tokenizer
        self.max_length = max_length
    def __len__(self): return len(self.texts)
    def __getitem__(self, idx):
        e = self.tok(
            self.texts[idx], truncation=True, max_length=self.max_length,
            padding="max_length", return_tensors="pt"
        )
        input_ids = e["input_ids"][0]
        attn = e["attention_mask"][0]
        labels = input_ids.clone()
        labels[attn == 0] = -100
        return {"input_ids": input_ids, "attention_mask": attn, "labels": labels}


def generate(model, tok, prompt: str, max_new: int = 120) -> str:
    model.eval()
    encoded = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = model.generate(
            **encoded,
            max_new_tokens=max_new,
            do_sample=True,
            temperature=0.65,
            top_p=0.90,
            repetition_penalty=1.08,
            pad_token_id=tok.eos_token_id,
            eos_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0][encoded["input_ids"].shape[1]:], skip_special_tokens=True)
    if "Пользователь:" in text:
        text = text.split("Пользователь:", 1)[0]
    if "NEXUS:" in text:
        text = text.split("NEXUS:", 1)[0]
    return text.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("stage_d_out"))
    ap.add_argument("--examples", type=int, default=16000)
    ap.add_argument("--steps", type=int, default=320)
    ap.add_argument("--max-length", type=int, default=192)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    random.seed(SEED); torch.manual_seed(SEED)
    texts = make_examples(SEED, args.examples)
    corpus_sha = hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()
    split = max(1, int(len(texts) * 0.95))
    train_texts, val_texts = texts[:split], texts[split:]

    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    model.config.use_cache = False

    # Freeze lower blocks: Stage-D is a dialogue adaptation, not a claim that we
    # retrained the Russian foundation model from scratch.
    for p in model.parameters(): p.requires_grad = False
    transformer = getattr(model, "transformer", None)
    blocks = list(getattr(transformer, "h", []))
    for block in blocks[-3:]:
        for p in block.parameters(): p.requires_grad = True
    for module in [getattr(transformer, "ln_f", None), getattr(model, "lm_head", None)]:
        if module is not None:
            for p in module.parameters(): p.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    ds = DialogueDataset(train_texts, tok, args.max_length)
    loader = DataLoader(ds, batch_size=args.batch, shuffle=True, generator=torch.Generator().manual_seed(SEED))
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=3e-5, weight_decay=0.01)
    sched = get_cosine_schedule_with_warmup(opt, max(10, args.steps // 20), args.steps)

    model.train(); opt.zero_grad(set_to_none=True)
    losses: List[float] = []
    step = 0; micro = 0; t0 = time.time()
    while step < args.steps:
        for batch in loader:
            out = model(**batch)
            loss = out.loss / args.grad_accum
            loss.backward(); micro += 1
            if micro % args.grad_accum != 0:
                continue
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
            step += 1
            losses.append(float(loss.item() * args.grad_accum))
            if step % 20 == 0:
                print(json.dumps({"step": step, "loss20": sum(losses[-20:]) / len(losses[-20:])}), flush=True)
            if step >= args.steps: break

    # deterministic-ish validation loss on first 64 examples
    model.eval(); vals = []
    vds = DialogueDataset(val_texts[:64], tok, args.max_length)
    with torch.no_grad():
        for b in DataLoader(vds, batch_size=2): vals.append(float(model(**b).loss.item()))

    model.config.use_cache = True
    model.save_pretrained(args.out / "model", safe_serialization=True)
    tok.save_pretrained(args.out / "model")

    prompts = [
        "Привет. Кто ты и как ты должен рассуждать?",
        "Чем гипотеза отличается от доказанного факта?",
        "Если два источника скопировали одну и ту же ошибку, это два доказательства?",
        "А теперь скажи ответ короче.",
        "Если ты уверен на 99.9%, но проверка не прошла, что делать?",
        "Почему нельзя объявить VERIFIED, если часть запроса не разобрана?",
        "Что делать при противоречащих друг другу данных?",
        "Можно ли уже назвать тебя универсальным AGI?",
    ]
    transcript = []
    context = ""
    for i, q in enumerate(prompts, 1):
        full = (context + f"Пользователь: {q}\nNEXUS:")[-1800:]
        a = generate(model, tok, full)
        transcript.append({"turn": i, "user": q, "model": a})
        context = (context + f"Пользователь: {q}\nNEXUS: {a}\n")[-1800:]

    md = [
        "# NEXUS R8.2 Stage-D Russian CyberDialogue — RAW MODEL TRANSCRIPT",
        "",
        "> Raw neural output. No manual correction. This run does NOT include the private V8-696k archive.",
        "",
    ]
    for r in transcript:
        md += [f"**Пользователь:** {r['user']}", "", f"**NEXUS:** {r['model']}", ""]
    (args.out / "DIALOGUE_RAW.md").write_text("\n".join(md), encoding="utf-8")

    report = {
        "version": "R8.2-STAGE-D-RUSSIAN-CYBERDIALOGUE-1",
        "base_model": BASE_MODEL,
        "data_provenance": "SYNTHETIC_DIALOGUE_FROM_FROZEN_NEXUS_CONTRACTS",
        "v8_696k_used": False,
        "corpus_examples_total": len(texts),
        "train_examples": len(train_texts),
        "validation_examples": len(val_texts),
        "corpus_sha256": corpus_sha,
        "optimizer_steps": args.steps,
        "max_length": args.max_length,
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_fraction": trainable / total,
        "train_loss_first20": sum(losses[:20]) / max(1, len(losses[:20])),
        "train_loss_last20": sum(losses[-20:]) / max(1, len(losses[-20:])),
        "validation_loss_64": sum(vals) / max(1, len(vals)),
        "validation_perplexity_64": math.exp(min(20.0, sum(vals) / max(1, len(vals)))),
        "elapsed_seconds": time.time() - t0,
        "dialogue_turns": transcript,
        "scientific_boundary": [
            "This is Stage-D synthetic dialogue adaptation, not V8-696k reproduction.",
            "Dialogue quality is shown as raw transcript, not a claimed blind score.",
            "Language-model loss is not proof of reasoning correctness.",
            "Proof/CyberLogic/Epistemic authority remains a separate runtime layer.",
        ],
    }
    (args.out / "TRAINING_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
