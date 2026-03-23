"""
Provider abstraction for direct API keys and optional bridge/proxy transports.

Repository contract:
- Plain provider API keys work by default
- Gateway / proxy / OAuth-backed transports remain optional
- No hard dependency on any specific runtime (including OpenClaw)
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
    """Unified LLM provider with role-based model selection and optional transport overrides."""

    def __init__(self, project_dir: Path | None = None):
        if project_dir:
            load_dotenv(project_dir / ".env")
        else:
            load_dotenv()

        self.explicit_provider = os.environ.get("AUTO_OUTLINE_PROVIDER", "").strip().lower()
        self.generic_api_key = os.environ.get("AUTO_OUTLINE_API_KEY", "")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        self.api_base = os.environ.get("AUTO_OUTLINE_API_BASE", "")
        self.auth_header_override = os.environ.get("AUTO_OUTLINE_AUTH_HEADER", "").strip()
        self.auth_scheme_override = os.environ.get("AUTO_OUTLINE_AUTH_SCHEME", "").strip().lower()

        # Model config — generation and evaluation should differ
        self.draft_model = os.environ.get("AUTO_OUTLINE_DRAFT_MODEL", "claude-sonnet-4-6")
        self.eval_model = os.environ.get("AUTO_OUTLINE_EVAL_MODEL", "claude-opus-4-6")

        self.provider = self._detect_provider()
        self.api_key = self._resolve_api_key()
        self.auth_header = self._resolve_auth_header()
        self.auth_scheme = self._resolve_auth_scheme()

    def _detect_provider(self) -> ProviderType:
        if self.explicit_provider:
            try:
                return ProviderType(self.explicit_provider)
            except ValueError as exc:
                raise RuntimeError(
                    "AUTO_OUTLINE_PROVIDER must be 'anthropic' or 'openai'."
                ) from exc

        if self.anthropic_key:
            return ProviderType.ANTHROPIC
        if self.openai_key:
            return ProviderType.OPENAI
        if self.generic_api_key:
            raise RuntimeError(
                "AUTO_OUTLINE_PROVIDER is required when AUTO_OUTLINE_API_KEY is set."
            )

        raise RuntimeError(
            "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or use "
            "AUTO_OUTLINE_PROVIDER + AUTO_OUTLINE_API_KEY for bridge mode."
        )

    def _resolve_api_key(self) -> str:
        if self.generic_api_key:
            return self.generic_api_key

        if self.provider == ProviderType.ANTHROPIC and self.anthropic_key:
            return self.anthropic_key
        if self.provider == ProviderType.OPENAI and self.openai_key:
            return self.openai_key

        env_name = (
            "ANTHROPIC_API_KEY" if self.provider == ProviderType.ANTHROPIC else "OPENAI_API_KEY"
        )
        raise RuntimeError(f"Missing API key for provider '{self.provider.value}'. Set {env_name}.")

    def _resolve_auth_header(self) -> str:
        if self.auth_header_override:
            return self.auth_header_override
        if self.provider == ProviderType.ANTHROPIC:
            return "x-api-key"
        return "Authorization"

    def _resolve_auth_scheme(self) -> str:
        if self.auth_scheme_override:
            scheme = self.auth_scheme_override.lower()
            if scheme not in {"bearer", "raw"}:
                raise RuntimeError("AUTO_OUTLINE_AUTH_SCHEME must be 'bearer' or 'raw'.")
            return scheme
        if self.provider == ProviderType.ANTHROPIC:
            return "raw"
        return "bearer"

    def _get_base_url(self) -> str:
        if self.api_base:
            return self.api_base.rstrip("/")
        if self.provider == ProviderType.ANTHROPIC:
            return "https://api.anthropic.com"
        return "https://api.openai.com"

    def _auth_headers(self) -> dict[str, str]:
        value = self.api_key if self.auth_scheme == "raw" else f"Bearer {self.api_key}"
        return {self.auth_header: value}

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
            **self._auth_headers(),
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
            **self._auth_headers(),
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
