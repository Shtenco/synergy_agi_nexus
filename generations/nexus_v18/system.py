from __future__ import annotations
from pathlib import Path
import torch
from .model import NexusV18Unified
from .russian_runtime import RussianGraphLogicRuntime

# encode_texts lives in V13 language_critic in the original tree
try:
    from generations.nexus_v13.language_critic import encode_texts
except ImportError:
    from nexus_v13.language_critic import encode_texts


class NexusV18System:
    def __init__(self, checkpoint: str | Path):
        self.checkpoint_path = Path(checkpoint)
        data = torch.load(self.checkpoint_path, map_location='cpu', weights_only=True)
        self.meta = {k: v for k, v in data.items() if k != 'model'}
        self.model = NexusV18Unified(data['arc_input_dim'], data['language_vocab'])
        self.model.load_state_dict(data['model'], strict=True)
        self.model.eval()
        self.arc_mean = data['arc_feature_mean']
        self.arc_std = data['arc_feature_std']
        self.logic = RussianGraphLogicRuntime()

    @torch.no_grad()
    def score_arc_candidates(self, raw_features: torch.Tensor, mask: torch.Tensor):
        x = (raw_features - self.arc_mean.to(raw_features)) / self.arc_std.to(raw_features)
        return self.model.arc(x, mask)[0]

    @torch.no_grad()
    def analyze_russian(self, texts: list[str]):
        return self.model.language(encode_texts(texts, max_length=256))

    @torch.no_grad()
    def predict_transition(self, state: torch.Tensor, action: torch.Tensor):
        return self.model.world(state, action)

    def prove_russian_chain(self, text: str):
        return self.logic.prove_chain(text)

    def parameter_report(self):
        return self.model.parameter_report()
