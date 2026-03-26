# auto-story-tools

Autonomous story generation pipeline: **seed → story bible → screenplay/novel**.

Feed it a story concept. It builds a complete story bible (world, characters, outline, voice, canon, mystery, foreshadowing), then iteratively evaluates and improves until quality thresholds are met. The output is a structured foundation that screenwriters and novelists can draft from.

Inspired by [NousResearch/autonovel](https://github.com/NousResearch/autonovel).

## Repository contract

**Works with plain API keys by default; supports gateway/proxy transports as optional integrations.**

That is the top-level architecture rule for this repo:

- the core runtime is generic and standalone
- direct `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` is the default path
- OpenClaw, gateway, proxy, or OAuth-based transports belong in `integrations/`, not in the core package

## What's inside

| Package | Status | What it does |
|---------|--------|-------------|
| `auto_outline` | ✅ Working | Seed → Story Bible → Scored Outline |
| `auto_screenplay` | 🚧 Planned | Outline → Fountain screenplay |

## Quick start

```bash
# Clone and install
git clone https://github.com/levineam/auto-story-tools.git
cd auto-story-tools
uv sync

# Set your API key
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY or OPENAI_API_KEY

# Initialize a project
auto-outline init --dir my-story
cd my-story

# Edit seed.txt with your story concept, then run
auto-outline run

# Check progress anytime
auto-outline status
```

## How it works

### Foundation loop

1. **Validate** the seed concept (world differentiator, central tension, cost/constraint, sensory hook)
2. **Generate** all layers in dependency order: world → characters → voice → mystery → outline → canon → foreshadowing
3. **Evaluate** with three independent systems:
   - LLM judge (different model than the writer to avoid self-congratulation)
   - Mechanical slop detector (regex-based, no LLM needed)
   - Cross-layer consistency checker
   - Reader panel (4 specialist personas)
4. **Target** the weakest dimension and regenerate that layer
5. **Keep/discard** based on score comparison (if worse, restore previous version)
6. **Repeat** until `foundation_score > 7.5` and `lore_score > 7.0` (or max iterations)

### Output files

| File | Purpose |
|------|---------|
| `seed.txt` | Your story concept (input) |
| `world.md` | World bible — lore, magic system, geography, factions, culture |
| `characters.md` | Character registry — wound/want/need/lie, three sliders, speech patterns |
| `outline.md` | Chapter outline — Save the Cat beats, try-fail cycles, MICE threads |
| `voice.md` | Voice discovery — trial passages, selected register, exemplars |
| `canon.md` | Hard facts database — every established fact, cross-referenced |
| `MYSTERY.md` | Central mystery — author-only answer key |
| `foreshadowing.md` | Plant → payoff ledger |
| `state.json` | Progress state (resumable) |
| `eval_logs/` | Evaluation history (JSON) |
| `results.tsv` | Experiment log — scores, decisions, iterations |

## Configuration

Set in `.env` (see `.env.example`):

```env
# Default mode: direct provider keys
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...

# Optional generic bridge mode
# AUTO_OUTLINE_PROVIDER=openai
# AUTO_OUTLINE_API_KEY=bridge-token
# AUTO_OUTLINE_API_BASE=https://your-proxy.example.com
# AUTO_OUTLINE_AUTH_HEADER=Authorization
# AUTO_OUTLINE_AUTH_SCHEME=Bearer

# Optional: model overrides
AUTO_OUTLINE_DRAFT_MODEL=claude-sonnet-4-6
AUTO_OUTLINE_EVAL_MODEL=claude-opus-4-6
```

The evaluation model intentionally differs from the generation model. This prevents the writer from grading its own homework.

### Optional gateway / proxy transports

The default install path is still plain provider API keys.

If you want to run through a gateway, proxy, or agent runtime instead, keep that transport outside the core package and point the runtime at a compatible base URL:

```env
OPENAI_API_KEY=proxy-or-gateway-token
AUTO_OUTLINE_API_BASE=https://your-proxy.example.com
```

For OpenClaw-specific setup, see [`integrations/openclaw/`](integrations/openclaw/). For the generic transport pattern, see [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

## Craft knowledge

All frameworks are embedded directly into generation and evaluation prompts:

- **Sanderson's Laws** — magic system costs and limitations
- **Save the Cat** — beat sheet structure
- **Wound/Want/Need/Lie** — character psychology (K.M. Weiland)
- **MICE Quotient** — thread tracking (Orson Scott Card / Sanderson)
- **Three Sliders** — proactivity, likability, competence (Sanderson)
- **Anti-slop detection** — mechanical regex + LLM-based (ported from autonovel)
- **Stability Trap countermeasures** — forcing genuine change, irreversible decisions

See `docs/CRAFT.md`, `docs/ANTI-SLOP.md`, and `docs/ANTI-PATTERNS.md` for the full reference.

## Architecture

```
repo/
├── src/
│   ├── auto_outline/           # Generic foundation engine
│   │   ├── cli.py              # Click CLI (init / run / status)
│   │   ├── engine.py           # Foundation loop orchestrator
│   │   ├── provider.py         # Generic LLM transport abstraction
│   │   ├── state.py            # State management (state.json)
│   │   ├── generators/         # Layer generators
│   │   └── evaluation/         # Evaluation system
│   └── auto_screenplay/        # Screenplay adapter (planned)
├── integrations/              # Optional environment-specific setup
│   └── openclaw/              # Optional OpenClaw transport/docs
└── docs/                      # Architecture, craft, and integration docs
```

See `docs/ARCHITECTURE.md` for the full design document.

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
pytest

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new adapters (auto-novel, auto-serial, etc.).

## Credits

- [NousResearch/autonovel](https://github.com/NousResearch/autonovel) — the pipeline architecture, craft reference docs, and anti-slop framework that inspired this project
- [slop-forensics](https://github.com/sam-paech/slop-forensics) — statistical analysis of AI writing patterns
- Save the Cat (Blake Snyder), K.M. Weiland, Brandon Sanderson, Orson Scott Card, Ursula K. Le Guin — the craft frameworks

## License

MIT
