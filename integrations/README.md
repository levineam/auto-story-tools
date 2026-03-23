# Optional integrations

This directory holds environment-specific adapters and setup guides.

## Repository boundary

The core repository contract is:

> **Works with plain API keys by default; supports gateway/proxy transports as optional integrations.**

So:

- `src/auto_outline/` and future core packages stay generic
- direct provider API keys are the default path
- environment-specific transport glue belongs here

## What belongs here

Examples:

- OpenClaw setup docs
- gateway / proxy wrappers
- optional credential bridge scripts
- environment-specific launch examples

## What does not belong here

These should not become core assumptions:

- mandatory gateway dependencies
- OAuth-only login in the default CLI path
- Andrew-specific paths, secrets, or runtime assumptions
- hardcoded vendor proxies in the main provider implementation

## Transport rule

The core runtime may support **generic transport configuration** such as:

- provider family (`openai` / `anthropic`)
- base URL override
- auth header override
- auth scheme override

That is acceptable because it is reusable across many environments.

What stays out of the core is any setup that assumes one specific gateway product or local workstation layout.
