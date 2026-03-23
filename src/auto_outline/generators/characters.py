"""
Character generation: produces characters.md from seed + world.
Ports Wound/Want/Need/Lie, three-slider profiles, speech patterns directly into prompts.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

CHAR_SYSTEM = (
    "You are a character designer for literary fiction with deep knowledge of "
    "wound/want/need/lie frameworks, Sanderson's three sliders, and dialogue "
    "distinctiveness. You create characters who feel like real people with "
    "contradictions, secrets, and speech patterns you can hear. "
    "You never use AI slop words (delve, tapestry, myriad, utilize, leverage, "
    "facilitate, multifaceted, synergy, paradigm, plethora). "
    "You write in clean, direct prose."
)

CHAR_PROMPT = """Build a complete character registry for this story. This is CHARACTERS.MD --
the definitive reference for WHO exists, what drives them, how they speak, and what secrets they carry.

SEED CONCEPT:
{seed}

WORLD BIBLE (the world these characters inhabit):
{world}

{voice_section}

CHARACTER CRAFT REQUIREMENTS (embedded -- follow strictly):

### The Three Sliders (Sanderson)
Every character has three independent dials (0-10):
  PROACTIVITY -- Do they drive the plot or react to it?
  LIKABILITY  -- Does the reader empathize with them?
  COMPETENCE  -- Are they good at what they do?

Rule: compelling = HIGH on at least TWO, or HIGH on one with clear growth.
All three low = boring. All three high from start = Mary Sue.

### Wound / Want / Need / Lie Framework
A causal chain -- each element causes the next:
  GHOST (backstory event) -> WOUND (ongoing damage) -> LIE (false belief to cope)
    -> WANT (external goal driven by Lie -- wrong solution)
    -> NEED (internal truth that will actually heal -- opposes the Lie)

Rules:
  - Want and Need must be IN TENSION
  - Lie statable in one sentence. Truth is its direct opposite.
  - Ghost causally explains the Lie.

### Dialogue Distinctiveness (8 dimensions)
1. Vocabulary level (syllable count, reading level)
2. Sentence length and structure (terse vs verbose)
3. Contractions and formality ("cannot" vs "can't")
4. Verbal tics and catchphrases (unique per character)
5. Question vs statement ratio (curious vs authoritative)
6. Interruption patterns (dominant vs submissive)
7. Metaphor domain (soldier = military metaphors, farmer = land)
8. Directness vs indirectness ("Leave." vs "Isn't it getting late?")

Test: Remove all dialogue tags. Can you tell who's speaking? If no, characters need differentiation.

### Arc Types
  - POSITIVE: Lie -> Truth (growth)
  - FLAT: Truth -> Truth (changes the world)
  - NEGATIVE: Truth -> Lie, or Lie -> deeper Lie (fall)

BUILD THE REGISTRY WITH:

For the PROTAGONIST and 2-3 MAJOR CHARACTERS:
- Name, age, role
- Ghost/Wound/Want/Need/Lie chain (causally linked)
- Three sliders with numbers (0-10) and justification
- Arc type and trajectory
- Speech pattern (all 8 dimensions + example lines)
- Physical appearance (specific, not generic)
- Physical habits and unconscious tells
- At least 2 secrets (things that would change the story if revealed)
- Key relationships mapped to other characters
- Thematic role (what question does this character embody?)

For the ANTAGONIST:
- Full depth equal to the protagonist. Not a villain -- someone whose interests conflict.
- Their own wound/want/need/lie (they should be understandable)

For 2-3 SUPPORTING CHARACTERS:
- Lighter treatment but still: sliders, speech distinctiveness, one secret, relationships

STABILITY TRAP COUNTERMEASURES:
- Characters must end TRULY different from how they began
- Include at least one character who makes irreversible decisions
- Create genuine moral ambiguity -- the "right" choice should be unclear
- No character who is purely right or purely wrong

IMPORTANT:
- Characters must INTERCONNECT. Their wants should conflict with each other.
- Every secret should change the story if revealed.
- Speech patterns must pass the no-tags test.
- Give the protagonist habits that come from their wound/gift/situation.
- The antagonist should be as fully realized as the protagonist.
- Check that no two characters share the same rhetorical formula in dialogue.
- Target ~3000-4000 words. Dense character work, not padding.
"""


def generate_characters(project_dir: Path, provider: LLMProvider) -> str:
    """Generate characters.md from seed + world."""
    seed = (project_dir / "seed.txt").read_text()
    world = (project_dir / "world.md").read_text()

    voice_section = ""
    voice_path = project_dir / "voice.md"
    if voice_path.exists():
        voice_section = f"VOICE IDENTITY:\n{voice_path.read_text()}"

    prompt = CHAR_PROMPT.format(seed=seed, world=world, voice_section=voice_section)

    print("Generating character registry...", file=sys.stderr)
    result = provider.call(prompt, system=CHAR_SYSTEM, role="draft", temperature=0.7)

    out_path = project_dir / "characters.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
