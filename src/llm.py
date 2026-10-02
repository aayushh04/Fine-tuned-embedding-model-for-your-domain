"""Minimal chat-LLM wrapper around a local Hugging Face causal LM (no API key needed).

Used for synthetic question generation (Phase 2) and answer generation (Phase 7).
"""
from __future__ import annotations

from typing import Sequence

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class LocalChat:
    def __init__(self, name: str, device: str | None = None, dtype=torch.float16):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(name, padding_side="left")
        self.model = AutoModelForCausalLM.from_pretrained(
            name, torch_dtype=dtype if self.device == "cuda" else torch.float32
        ).to(self.device).eval()

    @torch.inference_mode()
    def generate(self, conversations: Sequence[list[dict]], max_new_tokens: int = 200,
                 temperature: float = 0.0, top_p: float = 0.9) -> list[str]:
        """Generate one reply per conversation (a list of {"role","content"} messages)."""
        prompts = [self.tok.apply_chat_template(c, tokenize=False, add_generation_prompt=True)
                   for c in conversations]
        batch = self.tok(prompts, return_tensors="pt", padding=True).to(self.device)
        kwargs = dict(max_new_tokens=max_new_tokens, pad_token_id=self.tok.pad_token_id)
        if temperature > 0:
            kwargs.update(do_sample=True, temperature=temperature, top_p=top_p)
        else:
            kwargs.update(do_sample=False)
        out = self.model.generate(**batch, **kwargs)
        new_tokens = out[:, batch["input_ids"].shape[1]:]
        return [t.strip() for t in self.tok.batch_decode(new_tokens, skip_special_tokens=True)]
