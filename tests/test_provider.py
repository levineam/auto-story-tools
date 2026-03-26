"""Tests for provider detection and transport configuration."""

import pytest

from auto_outline.provider import LLMProvider, ProviderType, content_hash


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class TestProviderDetection:
    """Provider auto-detection from environment."""

    def test_anthropic_detected(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_PROVIDER", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_API_KEY", raising=False)
        provider = LLMProvider()
        assert provider.provider == ProviderType.ANTHROPIC

    def test_openai_detected(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.delenv("AUTO_OUTLINE_PROVIDER", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_API_KEY", raising=False)
        provider = LLMProvider()
        assert provider.provider == ProviderType.OPENAI

    def test_anthropic_preferred(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("AUTO_OUTLINE_PROVIDER", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_API_KEY", raising=False)
        provider = LLMProvider()
        assert provider.provider == ProviderType.ANTHROPIC

    def test_generic_bridge_requires_provider(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_PROVIDER", raising=False)
        monkeypatch.setenv("AUTO_OUTLINE_API_KEY", "bridge-token")
        with pytest.raises(RuntimeError, match="AUTO_OUTLINE_PROVIDER is required"):
            LLMProvider()

    def test_explicit_provider_with_generic_bridge_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("AUTO_OUTLINE_PROVIDER", "openai")
        monkeypatch.setenv("AUTO_OUTLINE_API_KEY", "bridge-token")
        provider = LLMProvider()
        assert provider.provider == ProviderType.OPENAI
        assert provider.api_key == "bridge-token"

    def test_invalid_explicit_provider_raises(self, monkeypatch):
        monkeypatch.setenv("AUTO_OUTLINE_PROVIDER", "weird")
        monkeypatch.setenv("AUTO_OUTLINE_API_KEY", "bridge-token")
        with pytest.raises(RuntimeError, match="AUTO_OUTLINE_PROVIDER"):
            LLMProvider()

    def test_missing_matching_key_for_explicit_provider_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("AUTO_OUTLINE_PROVIDER", "anthropic")
        monkeypatch.delenv("AUTO_OUTLINE_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="Missing API key for provider 'anthropic'"):
            LLMProvider()

    def test_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_PROVIDER", raising=False)
        monkeypatch.delenv("AUTO_OUTLINE_API_KEY", raising=False)
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


class TestTransportConfig:
    def test_openai_default_auth_headers(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")

        captured = {}

        def fake_post(url, headers, json, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return DummyResponse({"choices": [{"message": {"content": "ok"}}]})

        monkeypatch.setattr("auto_outline.provider.httpx.post", fake_post)

        provider = LLMProvider()
        result = provider.call("hello", system="system")

        assert result == "ok"
        assert captured["url"] == "https://api.openai.com/v1/chat/completions"
        assert captured["headers"]["Authorization"] == "Bearer sk-openai"
        assert captured["headers"]["Content-Type"] == "application/json"

    def test_anthropic_default_auth_headers(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        captured = {}

        def fake_post(url, headers, json, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return DummyResponse({"content": [{"text": "ok"}]})

        monkeypatch.setattr("auto_outline.provider.httpx.post", fake_post)

        provider = LLMProvider()
        result = provider.call("hello")

        assert result == "ok"
        assert captured["url"] == "https://api.anthropic.com/v1/messages"
        assert captured["headers"]["x-api-key"] == "sk-ant"
        assert captured["headers"]["anthropic-version"] == "2023-06-01"

    def test_bridge_mode_supports_custom_auth_header_and_scheme(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("AUTO_OUTLINE_PROVIDER", "anthropic")
        monkeypatch.setenv("AUTO_OUTLINE_API_KEY", "oauth-bridge-token")
        monkeypatch.setenv("AUTO_OUTLINE_API_BASE", "https://bridge.example.com/root/")
        monkeypatch.setenv("AUTO_OUTLINE_AUTH_HEADER", "Authorization")
        monkeypatch.setenv("AUTO_OUTLINE_AUTH_SCHEME", "bearer")

        captured = {}

        def fake_post(url, headers, json, timeout):
            captured["url"] = url
            captured["headers"] = headers
            return DummyResponse({"content": [{"text": "bridged"}]})

        monkeypatch.setattr("auto_outline.provider.httpx.post", fake_post)

        provider = LLMProvider()
        result = provider.call("hello")

        assert result == "bridged"
        assert provider.provider == ProviderType.ANTHROPIC
        assert captured["url"] == "https://bridge.example.com/root/v1/messages"
        assert captured["headers"]["Authorization"] == "Bearer oauth-bridge-token"
        assert "x-api-key" not in captured["headers"]

    def test_invalid_auth_scheme_raises(self, monkeypatch):
        monkeypatch.setenv("AUTO_OUTLINE_PROVIDER", "openai")
        monkeypatch.setenv("AUTO_OUTLINE_API_KEY", "bridge-token")
        monkeypatch.setenv("AUTO_OUTLINE_AUTH_SCHEME", "token")
        with pytest.raises(RuntimeError, match="AUTO_OUTLINE_AUTH_SCHEME"):
            LLMProvider()


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
