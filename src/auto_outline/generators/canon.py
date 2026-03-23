"""
Canon generation: extract all hard facts into a structured database.
Target: 400+ entries before foundation exit.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

CANON_SYSTEM = (
    "You are a continuity editor extracting hard facts from story planning documents. "
    "You are precise, exhaustive, and never invent facts not in the source material. "
    "Every entry must be traceable to a specific statement in the source documents."
)

CANON_PROMPT = """Extract EVERY hard fact from these planning documents into a structured canon database.
A "hard fact" is anything a writer must not contradict: names, ages, dates, physical descriptions,
rules of the speculative system, geography, relationships, established events.

SOURCE DOCUMENTS:

=== SEED ===
{seed}

=== WORLD BIBLE ===
{world}

=== CHARACTER REGISTRY ===
{characters}

=== OUTLINE ===
{outline}

FORMAT THE OUTPUT AS CANON.MD with these categories:

## Geography
- Specific facts about locations, distances, physical properties

## Timeline
- Dated events, ages, durations

## System Rules
- Hard rules of the speculative/magic system (costs, limitations)

## Character Facts
- Ages, physical descriptions, habits, relationships
- One entry per fact

## Political / Factional
- Who controls what, alliances, conflicts

## Cultural
- Customs, taboos, laws, festivals

## Established Events
- Events that have already happened in the story's past

## Contradictions Found
- Any discrepancies between source documents (flag these)

RULES:
- One fact per bullet point. Short. Specific. Checkable.
- Include the source (world.md, characters.md, outline.md) in parentheses.
- Aim for 80-120 entries minimum. Be exhaustive.
- If two documents give slightly different details, note the discrepancy.
- DO NOT invent facts. Only record what's explicitly stated.
"""


def generate_canon(project_dir: Path, provider: LLMProvider) -> str:
    """Generate canon.md by extracting facts from all planning docs."""
    seed = (project_dir / "seed.txt").read_text()
    world = (project_dir / "world.md").read_text()
    characters = (project_dir / "characters.md").read_text()

    outline = ""
    outline_path = project_dir / "outline.md"
    if outline_path.exists():
        outline = outline_path.read_text()

    prompt = CANON_PROMPT.format(seed=seed, world=world, characters=characters, outline=outline)

    print("Extracting canon database...", file=sys.stderr)
    result = provider.call(
        prompt, system=CANON_SYSTEM, role="draft", temperature=0.2, max_tokens=16000
    )

    out_path = project_dir / "canon.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
