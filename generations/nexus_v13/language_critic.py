"""Compact character-CNN critic for Russian grammar, logic and style."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import torch
from torch import nn
import torch.nn.functional as F


ALPHABET = " _-—.,:;!?()0123456789абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
CHAR_TO_ID = {char: index + 1 for index, char in enumerate(ALPHABET)}


def encode_texts(texts: Sequence[str], max_length: int = 180) -> torch.Tensor:
    rows = []
    for text in texts:
        ids = [CHAR_TO_ID.get(char.lower(), 1) for char in text[:max_length]]
        rows.append(ids + [0] * (max_length - len(ids)))
    return torch.tensor(rows, dtype=torch.long)


@dataclass(frozen=True, slots=True)
class CriticScores:
    grammar: float
    logic: float
    style: float
    overall: float


class RussianLogicStyleCritic(nn.Module):
    """Fast multi-scale character critic; it ranks prose rather than generating it."""

    def __init__(self, embedding: int = 32, channels: int = 72):
        super().__init__()
        self.embedding = nn.Embedding(len(CHAR_TO_ID) + 1, embedding, padding_idx=0)
        self.conv3 = nn.Conv1d(embedding, channels, kernel_size=3, padding=1)
        self.conv5 = nn.Conv1d(embedding, channels, kernel_size=5, padding=2)
        self.conv9 = nn.Conv1d(embedding, channels, kernel_size=9, padding=4)
        self.shared = nn.Sequential(
            nn.Linear(channels * 3, 128), nn.GELU(), nn.Dropout(0.08), nn.LayerNorm(128)
        )
        self.heads = nn.Linear(128, 4)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        x = self.embedding(tokens).transpose(1, 2)
        mask = tokens.ne(0).unsqueeze(1)
        pools = []
        for conv in (self.conv3, self.conv5, self.conv9):
            h = F.gelu(conv(x)).masked_fill(~mask, -1e4)
            pools.append(h.amax(-1))
        return self.heads(self.shared(torch.cat(pools, dim=-1)))

    @staticmethod
    def loss(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return F.binary_cross_entropy_with_logits(logits, labels)

    @torch.no_grad()
    def score(self, texts: Sequence[str], device: str = "cpu") -> list[CriticScores]:
        self.eval().to(device)
        values = torch.sigmoid(self(encode_texts(texts).to(device))).cpu().tolist()
        return [CriticScores(*map(float, row)) for row in values]
