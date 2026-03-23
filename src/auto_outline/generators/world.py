"""
World generation: produces world.md from seed concept.
Ports craft knowledge directly into prompts.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

WORLD_SYSTEM = (
    "You are a worldbuilder with deep knowledge of Sanderson's Laws, "
    "Le Guin's prose philosophy, and TTRPG-quality lore design. "
    "You write world bibles that are specific, interconnected, and imply depth "
    "beyond what's stated. You never use AI slop words (delve, tapestry, myriad, "
    "utilize, leverage, facilitate, multifaceted, synergy, paradigm, plethora, "
    "testament, embark, endeavor, encompass, elucidate, juxtapose, holistic, "
    "catalyze, realm, landscape). You write in clean, direct prose. "
    "Every rule has a cost. Every cultural detail implies a history. "
    "Every location has a sensory signature."
)

WORLD_PROMPT = """Build a complete world bible for this story. This is the WORLD.MD file --
the definitive reference for everything that EXISTS in this world. A writer should be able
to resolve any worldbuilding question from this document alone.

SEED CONCEPT:
{seed}

{voice_section}

CRAFT REQUIREMENTS (embedded -- follow these strictly):

MAGIC/SPECULATIVE SYSTEM:
- Hard rules with COSTS and LIMITATIONS (Sanderson's Second Law: limitations >= powers)
- Costs must DRIVE PLOT DECISIONS, not be decorative
- Trace implications through society, economy, law, religion, warfare
- At least 2-3 societal implications explored in depth
- No new powers that weren't foreshadowed
- System must be TESTABLE: could you write a courtroom scene, a contract negotiation,
  AND a confrontation without inventing new rules?

HISTORY:
- Timeline of events creating PRESENT-DAY TENSIONS (not backdrop)
- Every historical event maps to a current faction conflict or character motivation
- Decorative history (cool but plot-irrelevant) counts AGAINST quality, not for it

GEOGRAPHY:
- Locations distinct with sensory signatures (sight, sound, smell minimum)
- Two different scenes in two different locations must feel meaningfully different
- Economy that creates class tension

WORLDBUILDING PRINCIPLES:
- Iceberg: imply more than you state. 2-3 unexplained but intriguing facts per section
- Interconnection: pulling one thread should move everything. Removing the magic system
  should collapse the political structure.
- Concrete over abstract: not "the city was old" but specific sensory details
- Culture generates conflict: customs and taboos that create story tension

STABILITY TRAP COUNTERMEASURES:
- Include genuine moral ambiguity in the world's power structures
- Create factions where no side is purely right
- Build in costs that can't be circumvented
- World should have problems that resist easy solutions

STRUCTURE THE DOCUMENT WITH THESE SECTIONS:

## Cosmology & History
Timeline of major events. Focus on events creating present-day tensions.
Founding myth, key turning points, recent events that matter to the plot.

## Magic/Speculative System
### Hard Rules
Specific, testable rules. What happens when you break them.
COSTS and LIMITATIONS prominently featured.

### Societal Implications
How does this system shape: governance, commerce, education, class,
crime, family life, childhood, aging?

## Geography
Physical layout, districts/regions, natural features.
Neighboring places (at least 2-3). Sensory signatures for each location.

## Factions & Politics
Who holds power, who wants it, who's being crushed by it.
At least 3-4 factions with opposing interests.

## Bestiary / Flora / Natural World
What's unique about the natural world?

## Cultural Details
Customs, taboos, festivals, food, clothing, coming-of-age rituals.
Things that make daily life feel SPECIFIC.

## Internal Consistency Rules
Hard constraints a writer must not violate. What's possible and what's not.

IMPORTANT:
- Be SPECIFIC. Name districts, describe them, give sensory signatures.
- Every rule has a COST or LIMITATION stated alongside it.
- Facts should INTERCONNECT across sections.
- Write in clean, direct prose. No slop. No filler.
- Target ~3000-4000 words. Dense, not padded.
"""


def generate_world(project_dir: Path, provider: LLMProvider) -> str:
    """Generate world.md from seed (and voice if available)."""
    seed = (project_dir / "seed.txt").read_text()

    voice_section = ""
    voice_path = project_dir / "voice.md"
    if voice_path.exists():
        voice_section = f"VOICE IDENTITY (the tone and register):\n{voice_path.read_text()}"

    prompt = WORLD_PROMPT.format(seed=seed, voice_section=voice_section)

    print("Generating world bible...", file=sys.stderr)
    result = provider.call(prompt, system=WORLD_SYSTEM, role="draft", temperature=0.7)

    out_path = project_dir / "world.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
