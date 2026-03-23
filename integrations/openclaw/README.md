# OpenClaw integration (optional)

This directory is intentionally separate from the core runtime.

## Rule

**auto-story-tools works with plain API keys by default.**
Gateway, proxy, OAuth, or agent-runtime transports are optional integrations layered on top.

That means:

- `src/auto_outline/` stays generic and reusable
- the core package must run with direct `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- any OpenClaw-specific bootstrap, auth, routing, or transport glue belongs here instead of in the core package

## Current integration pattern

The core runtime already supports proxy-style transports via:

- `OPENAI_API_KEY`
- `AUTO_OUTLINE_API_BASE`

So if OpenClaw exposes an OpenAI-compatible or Anthropic-compatible transport, you can point the core runtime at that endpoint without changing the story engine itself.

Example:

```bash
export OPENAI_API_KEY="your-gateway-or-proxy-token"
export AUTO_OUTLINE_API_BASE="https://your-gateway.example.com"
auto-outline run --dir my-story
```

## What belongs in this directory

Examples of acceptable OpenClaw-specific additions:

- wrapper scripts that source OpenClaw-managed credentials
- gateway/proxy transport setup
- OpenClaw skill packaging
- docs for running inside an OpenClaw agent environment
- adapter code that converts OpenClaw runtime configuration into the generic env vars the core expects

## What does NOT belong here

These should stay out of the core package unless they become generic across environments:

- hard dependency on OpenClaw libraries
- assumptions that a gateway is always present
- OAuth-only auth paths in the default CLI flow
- Andrew-specific paths, configs, or agent assumptions

## Repository contract

If an integration disappears, the core repo should still work with a normal `.env` file and direct provider API keys.
