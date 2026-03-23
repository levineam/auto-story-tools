"""
Provider abstraction: Anthropic, OpenAI, or configurable base URL.
Supports separate models for generation vs evaluation (avoid self-congratulation bias).
"""

import hashlib
import os
from enum import Enum
from pathlib import Path

import httpx
from dotenv import load_dotenv


class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMProvider:
    """Unified LLM provider with role-based model selection."""

    def __init__(self, project_dir: Path | None = None):
        if project_dir:
            load_dotenv(project_dir / ".env")
        else:
            load_dotenv()

        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        self.api_base = os.environ.get("AUTO_OUTLINE_API_BASE", "")

        # Model config — generation and evaluation should differ
        self.draft_model = os.environ.get("AUTO_OUTLINE_DRAFT_MODEL", "claude-sonnet-4-6")
        self.eval_model = os.environ.get("AUTO_OUTLINE_EVAL_MODEL", "claude-opus-4-6")

        # Detect provider
        self.provider = self._detect_provider()

    def _detect_provider(self) -> ProviderType:
        if self.anthropic_key:
            return ProviderType.ANTHROPIC
        if self.openai_key:
            return ProviderType.OPENAI
        raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

    def _get_base_url(self) -> str:
        if self.api_base:
            return self.api_base
        if self.provider == ProviderType.ANTHROPIC:
            return "https://api.anthropic.com"
        return "https://api.openai.com"

    def call(
        self,
        prompt: str,
        *,
        system: str = "",
        role: str = "draft",
        temperature: float = 0.7,
        max_tokens: int = 16000,
    ) -> str:
        """Call the LLM. role='draft' uses draft model, role='eval' uses eval model."""
        model = self.draft_model if role == "draft" else self.eval_model

        if self.provider == ProviderType.ANTHROPIC:
            return self._call_anthropic(prompt, system, model, temperature, max_tokens)
        return self._call_openai(prompt, system, model, temperature, max_tokens)

    def _call_anthropic(
        self, prompt: str, system: str, model: str, temperature: float, max_tokens: int
    ) -> str:
        base = self._get_base_url()
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        resp = httpx.post(f"{base}/v1/messages", headers=headers, json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def _call_openai(
        self, prompt: str, system: str, model: str, temperature: float, max_tokens: int
    ) -> str:
        base = self._get_base_url()
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        resp = httpx.post(f"{base}/v1/chat/completions", headers=headers, json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def content_hash(text: str) -> str:
    """SHA-256 content hash for change detection."""
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()[:16]}"
