"""
Central mystery generation: MYSTERY.md (author-only document).
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

MYSTERY_SYSTEM = (
    "You are a mystery architect. You design central questions that drive entire stories, "
    "with layered reveals, red herrings, and a resolution that feels both surprising and "
    "inevitable. You think like a chess player: every clue placed with intent."
)

MYSTERY_PROMPT = """Design the central mystery for this story. This is MYSTERY.MD --
an AUTHOR-ONLY document. The reader never sees this. It's the answer key.

SEED CONCEPT:
{seed}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

BUILD THE MYSTERY WITH:

## Central Question
The one question the story is really asking. State it clearly.

## The Answer
What actually happened / what's really going on. Be specific.
This must be mechanically consistent with the world bible's rules.

## Clue Progression
How the reader (and protagonist) discover the truth, chapter by chapter.
For each clue:
- What is revealed
- Where it appears (approximately)
- What the reader THINKS it means at first
- What it ACTUALLY means

## Red Herrings
At least 2-3 false leads:
- What the reader is led to believe
- When it's planted
- When/how it's debunked

## The Three Revelations
1. PARTIAL TRUTH (~40% mark): What the protagonist first learns
2. TWISTED TRUTH (~65% mark): How understanding deepens/changes
3. FULL TRUTH (~80% mark): The complete picture

## Thematic Resonance
How the mystery's answer connects to the protagonist's lie/need.
The mystery should not just be a puzzle -- solving it should force
the protagonist to confront their internal lie.

CONSTRAINTS:
- The answer must be consistent with ALL established world rules
- Clues must be fair: a reader could theoretically piece it together
- The answer should recontextualize earlier scenes
- No supernatural/magic-based solutions that weren't established
- The mystery should be personal to the protagonist, not just intellectual
"""


def generate_mystery(project_dir: Path, provider: LLMProvider) -> str:
    """Generate MYSTERY.md from seed + world + characters."""
    seed = (project_dir / "seed.txt").read_text()
    world = (project_dir / "world.md").read_text()
    characters = (project_dir / "characters.md").read_text()

    prompt = MYSTERY_PROMPT.format(seed=seed, world=world, characters=characters)

    print("Designing central mystery...", file=sys.stderr)
    result = provider.call(prompt, system=MYSTERY_SYSTEM, role="draft", temperature=0.6)

    out_path = project_dir / "MYSTERY.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
