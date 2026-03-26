# Integrations and transport patterns

`auto-story-tools` is designed to work in two layers:

1. **Core runtime** — generic CLI + story pipeline
2. **Optional integrations** — gateways, proxies, OAuth-backed transports, or hosted runtimes

## Core rule

> **Works with plain API keys by default; supports gateway/proxy transports as optional integrations.**

## Default mode: direct provider API keys

This is the standard setup and the one the README optimizes for.

```env
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
```

No adapter is required.

## Generic bridge mode: proxy or gateway

Some users have a proxy, hosted gateway, or OAuth-backed transport that exposes a standard OpenAI-compatible or Anthropic-compatible API.

For those cases, the core runtime supports a **generic bridge configuration**:

```env
AUTO_OUTLINE_PROVIDER=openai
AUTO_OUTLINE_API_KEY=your-bridge-token
AUTO_OUTLINE_API_BASE=https://your-proxy.example.com
AUTO_OUTLINE_AUTH_HEADER=Authorization
AUTO_OUTLINE_AUTH_SCHEME=Bearer
```

This keeps the story engine generic while still allowing external auth systems.

### Why this exists

OAuth tokens often cannot be dropped directly into tools that expect vendor API keys.
A bridge layer solves that by translating OAuth-backed access into a normal API surface.

The repo should support that pattern **without** baking any single gateway product into the core.

## Supported generic transport knobs

- `AUTO_OUTLINE_PROVIDER` — `openai` or `anthropic`
- `AUTO_OUTLINE_API_KEY` — generic token for bridge/proxy mode
- `AUTO_OUTLINE_API_BASE` — override base URL
- `AUTO_OUTLINE_AUTH_HEADER` — override auth header name
- `AUTO_OUTLINE_AUTH_SCHEME` — `bearer` or `raw`

## Optional OpenClaw setup

OpenClaw is treated as one optional integration, not the default runtime.

See [`../integrations/openclaw/README.md`](../integrations/openclaw/README.md).

## Design guardrails

Good:

- generic transport config in the provider layer
- optional integration docs in `integrations/`
- examples for direct API keys and bridge mode

Bad:

- requiring OpenClaw to run the core CLI
- hardcoding a specific gateway endpoint into the provider
- assuming OAuth is always available
- merging machine-specific launch scripts into the default setup flow
