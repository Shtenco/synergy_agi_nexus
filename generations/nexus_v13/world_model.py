"""Trainable latent world model for the NEXUS operator space.

The base NEXUS policy maps a task to a 256-dimensional belief state. V13 adds
an explicit transition model p(z_next, reward, done | z, action, goal, memory)
and a non-parametric episodic memory. The transition core uses a deterministic
small-world graph over eight 32-dimensional state factors.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import heapq
from typing import Sequence

import torch
from torch import nn
import torch.nn.functional as F


def _small_world_matrix(nodes: int = 8, local_degree: int = 2, shortcuts: int = 3) -> torch.Tensor:
    if nodes < 4 or local_degree < 2 or local_degree % 2:
        raise ValueError("invalid small-world topology")
    adjacency = torch.eye(nodes, dtype=torch.float32)
    radius = local_degree // 2
    for i in range(nodes):
        for distance in range(1, radius + 1):
            j = (i + distance) % nodes
            adjacency[i, j] = adjacency[j, i] = 1.0
    candidates = []
    for i in range(nodes):
        for j in range(i + 1, nodes):
            if adjacency[i, j] == 0:
                digest = hashlib.sha256(f"NEXUS-V13-WM:{i}:{j}".encode()).digest()
                candidates.append((digest, i, j))
    for _, i, j in sorted(candidates)[:shortcuts]:
        adjacency[i, j] = adjacency[j, i] = 1.0
    return adjacency / adjacency.sum(-1, keepdim=True).clamp_min(1.0)


@dataclass(frozen=True, slots=True)
class WorldTransition:
    state: torch.Tensor
    action: int
    next_state: torch.Tensor
    progress: float
    terminal: bool


class EpisodicWorldMemory:
    """Cosine-addressed replay memory; mutable experience is not a model weight."""

    def __init__(self, capacity: int = 4096):
        self.capacity = int(capacity)
        self._items: list[WorldTransition] = []
        self._cursor = 0

    def __len__(self) -> int:
        return len(self._items)

    def add(self, transition: WorldTransition) -> None:
        item = WorldTransition(
            transition.state.detach().cpu().float(),
            int(transition.action),
            transition.next_state.detach().cpu().float(),
            float(transition.progress),
            bool(transition.terminal),
        )
        if len(self._items) < self.capacity:
            self._items.append(item)
        else:
            self._items[self._cursor] = item
            self._cursor = (self._cursor + 1) % self.capacity

    def retrieve(self, state: torch.Tensor, action: int, k: int = 8) -> tuple[torch.Tensor, float, float]:
        candidates = [item for item in self._items if item.action == int(action)]
        if not candidates:
            return torch.zeros_like(state), 0.0, 1.0
        query = F.normalize(state.detach().cpu().float().reshape(1, -1), dim=-1)[0]
        scored = []
        for item in candidates:
            key = F.normalize(item.state.reshape(1, -1), dim=-1)[0]
            scored.append((float(torch.dot(query, key)), item))
        chosen = heapq.nlargest(min(k, len(scored)), scored, key=lambda pair: pair[0])
        weights = torch.softmax(torch.tensor([score for score, _ in chosen]), dim=0)
        next_state = sum(weight * item.next_state for weight, (_, item) in zip(weights, chosen))
        progress = float(sum(float(weight) * item.progress for weight, (_, item) in zip(weights, chosen)))
        uncertainty = 1.0 - max(score for score, _ in chosen)
        return next_state.to(state.device), progress, max(0.0, uncertainty)


class LatentWorldModel(nn.Module):
    """Small-world latent dynamics for planning over NEXUS operators."""

    def __init__(self, state_dim: int = 256, actions: int = 30, action_dim: int = 64):
        super().__init__()
        if state_dim % 8:
            raise ValueError("state_dim must be divisible by eight")
        self.state_dim = state_dim
        self.actions = actions
        self.factor_dim = state_dim // 8
        self.action_embedding = nn.Embedding(actions, action_dim)
        self.action_to_factors = nn.Linear(action_dim, state_dim)
        self.goal_projection = nn.Linear(state_dim, state_dim)
        self.memory_projection = nn.Linear(state_dim, state_dim)
        self.factor_q = nn.Linear(self.factor_dim, self.factor_dim)
        self.factor_k = nn.Linear(self.factor_dim, self.factor_dim)
        self.factor_v = nn.Linear(self.factor_dim, self.factor_dim)
        self.transition_in = nn.Linear(state_dim * 4, state_dim * 2)
        self.transition_out = nn.Linear(state_dim * 2, state_dim)
        self.norm = nn.LayerNorm(state_dim)
        self.progress_head = nn.Sequential(nn.Linear(state_dim, 64), nn.GELU(), nn.Linear(64, 1))
        self.terminal_head = nn.Sequential(nn.Linear(state_dim, 64), nn.GELU(), nn.Linear(64, 1))
        self.uncertainty_head = nn.Sequential(nn.Linear(state_dim, 64), nn.GELU(), nn.Linear(64, 1))
        self.inverse_head = nn.Linear(state_dim * 2, actions)
        self.register_buffer("transition_graph", _small_world_matrix(), persistent=True)

    def _graph_context(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        batch = state.shape[0]
        factors = state.reshape(batch, 8, self.factor_dim)
        action_factors = self.action_to_factors(self.action_embedding(action)).reshape(batch, 8, self.factor_dim)
        x = factors + action_factors
        q, k, v = self.factor_q(x), self.factor_k(x), self.factor_v(x)
        logits = torch.matmul(q, k.transpose(-1, -2)) / (self.factor_dim ** 0.5)
        support = self.transition_graph.to(dtype=state.dtype, device=state.device)
        logits = logits + torch.log(support.clamp_min(1e-6))
        logits = logits.masked_fill(support.unsqueeze(0) <= 0, -1e4)
        p = torch.softmax(logits, dim=-1)
        h1 = p @ v
        h2 = p @ h1
        h4 = p @ (p @ h2)
        return (0.60 * h1 + 0.28 * h2 + 0.12 * h4).reshape(batch, self.state_dim)

    def forward(
        self,
        state: torch.Tensor,
        action: torch.Tensor,
        goal: torch.Tensor | None = None,
        memory: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        goal = torch.zeros_like(state) if goal is None else goal
        memory = torch.zeros_like(state) if memory is None else memory
        graph = self._graph_context(state, action)
        fused = torch.cat(
            [state, graph, self.goal_projection(goal), self.memory_projection(memory)],
            dim=-1,
        )
        delta = self.transition_out(F.gelu(self.transition_in(fused)))
        next_state = self.norm(state + F.gelu(delta))
        return {
            "next_state": next_state,
            "progress": self.progress_head(next_state).squeeze(-1),
            "terminal_logit": self.terminal_head(next_state).squeeze(-1),
            "uncertainty": F.softplus(self.uncertainty_head(next_state).squeeze(-1)),
            "inverse_logits": self.inverse_head(torch.cat([state, next_state], dim=-1)),
        }

    @staticmethod
    def loss(
        prediction: dict[str, torch.Tensor],
        next_state: torch.Tensor,
        progress: torch.Tensor,
        terminal: torch.Tensor,
        action: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        latent_huber = F.smooth_l1_loss(prediction["next_state"], next_state)
        cosine = 1.0 - F.cosine_similarity(prediction["next_state"], next_state, dim=-1).mean()
        progress_loss = F.mse_loss(torch.sigmoid(prediction["progress"]), progress)
        terminal_loss = F.binary_cross_entropy_with_logits(prediction["terminal_logit"], terminal)
        inverse_loss = F.cross_entropy(prediction["inverse_logits"], action)
        residual = (prediction["next_state"] - next_state).pow(2).mean(-1).detach()
        uncertainty_loss = F.mse_loss(prediction["uncertainty"], residual)
        total = (
            latent_huber
            + 0.35 * cosine
            + 0.35 * progress_loss
            + 0.25 * terminal_loss
            + 0.20 * inverse_loss
            + 0.05 * uncertainty_loss
        )
        return total, {
            "latent_huber": float(latent_huber.detach()),
            "cosine_loss": float(cosine.detach()),
            "progress_loss": float(progress_loss.detach()),
            "terminal_loss": float(terminal_loss.detach()),
            "inverse_loss": float(inverse_loss.detach()),
        }

    @torch.no_grad()
    def imagine(
        self,
        state: torch.Tensor,
        action_sequences: Sequence[Sequence[int]],
        goal: torch.Tensor | None = None,
        memory: EpisodicWorldMemory | None = None,
    ) -> list[dict[str, object]]:
        if state.ndim == 1:
            state = state.unsqueeze(0)
        results = []
        for sequence in action_sequences:
            current = state.clone()
            total_progress = 0.0
            total_uncertainty = 0.0
            trace = []
            for action_value in sequence:
                action = torch.tensor([int(action_value)], device=current.device)
                retrieved = None
                if memory is not None:
                    retrieved, _, _ = memory.retrieve(current[0], int(action_value))
                    retrieved = retrieved.unsqueeze(0)
                prediction = self(current, action, goal=goal, memory=retrieved)
                current = prediction["next_state"]
                progress_value = float(torch.sigmoid(prediction["progress"])[0])
                uncertainty_value = float(prediction["uncertainty"][0])
                terminal_value = float(torch.sigmoid(prediction["terminal_logit"])[0])
                total_progress += progress_value
                total_uncertainty += uncertainty_value
                trace.append(
                    {
                        "action": int(action_value),
                        "progress": progress_value,
                        "terminal": terminal_value,
                        "uncertainty": uncertainty_value,
                    }
                )
            score = total_progress - 0.15 * total_uncertainty - 0.02 * len(sequence)
            results.append({"sequence": tuple(sequence), "score": score, "state": current[0], "trace": trace})
        return sorted(results, key=lambda item: float(item["score"]), reverse=True)
