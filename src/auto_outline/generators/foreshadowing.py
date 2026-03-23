"""
Foreshadowing ledger: extract and track all plant-payoff pairs.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

FORESHADOW_SYSTEM = (
    "You are a continuity editor specializing in foreshadowing analysis. "
    "You track every planted thread and its payoff with precision. "
    "You never miss a setup without a payoff, or a payoff without a setup."
)

FORESHADOW_PROMPT = """Build a comprehensive foreshadowing ledger for this story.
Track every planted element and its planned payoff.

OUTLINE:
{outline}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

MYSTERY (author-only):
{mystery}

BUILD THE LEDGER:

## Foreshadowing Ledger

For EACH thread:

### Thread N: [Name]
- **Type:** object / dialogue / action / symbolic / structural
- **Plant:** Chapter N — [what's planted and how]
- **Reinforcement(s):** Chapter N — [how it's echoed/reinforced]
- **Payoff:** Chapter N — [how it pays off]
- **Subtlety:** high / medium / low
- **Rule of Three:** Does it appear 3+ times before payoff? yes/no

## Summary Table

| # | Thread | Planted (Ch) | Reinforced (Ch) | Payoff (Ch) | Type | Subtlety |
|---|--------|-------------|-----------------|-------------|------|----------|

REQUIREMENTS:
- At least 15 tracked threads
- Plant-to-payoff distance of at least 3 chapters for every thread
- Types distributed across all 5 categories
- At least 3 threads at HIGH subtlety (reader unlikely to notice on first read)
- Every thread must have both a plant AND a payoff (no orphans)
- Rule of three for at least 5 threads

## Orphan Check
List any planted elements that lack payoffs.
List any payoffs that lack plants.

## Red Herring Tracking
List any deliberate misdirections and where they're resolved.
"""


def generate_foreshadowing(project_dir: Path, provider: LLMProvider) -> str:
    """Generate foreshadowing.md from outline + world + characters + mystery."""
    outline = (project_dir / "outline.md").read_text()
    world = (project_dir / "world.md").read_text()
    characters = (project_dir / "characters.md").read_text()

    mystery = ""
    mystery_path = project_dir / "MYSTERY.md"
    if mystery_path.exists():
        mystery = mystery_path.read_text()

    prompt = FORESHADOW_PROMPT.format(
        outline=outline, world=world, characters=characters, mystery=mystery
    )

    print("Building foreshadowing ledger...", file=sys.stderr)
    result = provider.call(prompt, system=FORESHADOW_SYSTEM, role="draft", temperature=0.4)

    out_path = project_dir / "foreshadowing.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
