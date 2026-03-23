"""Tests for provider detection and configuration."""

import pytest

from auto_outline.provider import LLMProvider, ProviderType, content_hash


class TestProviderDetection:
    """Provider auto-detection from environment."""

    def test_anthropic_detected(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = LLMProvider()
        assert provider.provider == ProviderType.ANTHROPIC

    def test_openai_detected(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        provider = LLMProvider()
        assert provider.provider == ProviderType.OPENAI

    def test_anthropic_preferred(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        provider = LLMProvider()
        assert provider.provider == ProviderType.ANTHROPIC

    def test_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="No API key found"):
            LLMProvider()


class TestModelConfig:
    """Model override configuration."""

    def test_default_models(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("AUTO_OUTLINE_DRAFT_MODEL", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_EVAL_MODEL", raising=False)
        provider = LLMProvider()
        assert provider.draft_model == "claude-sonnet-4-6"
        assert provider.eval_model == "claude-opus-4-6"

    def test_custom_models(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("AUTO_OUTLINE_DRAFT_MODEL", "claude-haiku-4-5")
        monkeypatch.setenv("AUTO_OUTLINE_EVAL_MODEL", "claude-sonnet-4-6")
        provider = LLMProvider()
        assert provider.draft_model == "claude-haiku-4-5"
        assert provider.eval_model == "claude-sonnet-4-6"


class TestContentHash:
    """Content hashing for change detection."""

    def test_deterministic(self):
        assert content_hash("hello") == content_hash("hello")

    def test_different_content(self):
        assert content_hash("hello") != content_hash("world")

    def test_format(self):
        h = content_hash("test")
        assert h.startswith("sha256:")
        assert len(h) == 23  # "sha256:" + 16 hex chars
