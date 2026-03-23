# auto-outline

Standalone foundation engine: **Seed → Story Bible → Scored Outline**

Extracts the foundation-phase logic from [autonovel](https://github.com/NousResearch/autonovel) into a reusable CLI/library. Generates a complete story bible (world, characters, outline, voice, canon, mystery, foreshadowing) from a seed concept, then iteratively evaluates and improves until quality thresholds are met.

## Quick Start

```bash
# Install
cd auto-outline
uv sync

# Initialize a project
auto-outline init --dir my-story
cd my-story

# Edit seed.txt with your concept, set API key in .env
# Then run the foundation loop
auto-outline run

# Check progress
auto-outline status
```

## CLI Commands

### `auto-outline init [SEED_PATH]`
Creates a project directory with template files:
- `seed.txt` — your story concept (or copies from SEED_PATH)
- `.env` — API key configuration
- `state.json` — progress tracking

### `auto-outline run`
Executes the foundation loop:
1. Validates the seed concept
2. Generates all layers: world → characters → voice → mystery → outline → canon → foreshadowing
3. Evaluates with LLM judge + mechanical slop detection + cross-layer consistency checks
4. Identifies weakest dimension, regenerates that layer
5. Repeats until `foundation_score > 7.5` and `lore_score > 7.0` (max 10 iterations)

### `auto-outline status`
Shows current scores, weakest dimension, layer status, and iteration history.

## Output Files

| File | Purpose |
|------|---------|
| `seed.txt` | Input: story concept |
| `world.md` | World bible (lore, magic, geography, factions, culture) |
| `characters.md` | Character registry (wound/want/need/lie, sliders, speech patterns) |
| `outline.md` | Chapter outline (Save the Cat beats, try-fail cycles, MICE threads) |
| `voice.md` | Voice discovery (trials, selected voice, guardrails) |
| `canon.md` | Hard facts database (400+ entries target) |
| `MYSTERY.md` | Central mystery (author-only) |
| `foreshadowing.md` | Foreshadowing ledger (plant → payoff tracking) |
| `state.json` | Progress state (resumable) |
| `eval_logs/` | Evaluation history (JSON) |

## Configuration

Set in `.env`:

```env
# Required: one of these
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional: model overrides
AUTO_OUTLINE_DRAFT_MODEL=claude-sonnet-4-6
AUTO_OUTLINE_EVAL_MODEL=claude-opus-4-6

# Optional: custom API base
AUTO_OUTLINE_API_BASE=https://api.anthropic.com
```

The evaluation model intentionally differs from the generation model to avoid self-congratulation bias.

## Craft Knowledge

All craft frameworks are embedded directly into generation prompts:
- **Sanderson's Laws** — magic system costs/limitations
- **Save the Cat** — beat sheet structure
- **Wound/Want/Need/Lie** — character psychology
- **MICE Quotient** — thread tracking
- **Le Guin's prose philosophy** — style as world-building
- **Anti-slop** — mechanical detection of AI writing patterns
- **Stability Trap countermeasures** — genuine change, irreversible decisions

## Architecture

```
auto_outline/
├── cli.py                  # Click CLI (init/run/status)
├── engine.py               # Foundation loop orchestrator
├── provider.py             # LLM provider abstraction (Anthropic/OpenAI)
├── state.py                # State management (state.json)
├── generators/             # Layer generators
│   ├── seed.py             # Seed validation
│   ├── world.py            # World bible
│   ├── characters.py       # Character registry
│   ├── outline.py          # Chapter outline
│   ├── voice.py            # Voice discovery
│   ├── canon.py            # Canon database
│   ├── mystery.py          # Central mystery
│   └── foreshadowing.py    # Foreshadowing ledger
└── evaluation/             # Evaluation system
    ├── mechanical.py       # Regex-based slop detection
    ├── foundation_judge.py # LLM-based scoring
    └── consistency.py      # Cross-layer checks
```

## Schema Compatibility

Output format follows the shared story bible schema defined in SUP-198. See `deliverables/SUP-198-schemas.md` for the canonical JSON schema definitions.
