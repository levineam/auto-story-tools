"""
Voice discovery: trial passages in different registers, selected voice with exemplars and anti-exemplars.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

VOICE_SYSTEM = (
    "You are a prose stylist and voice designer. You discover the right voice for a story "
    "by writing trial passages in different registers and analyzing what works. "
    "You have deep knowledge of narrative voice, from Le Guin's prose philosophy to "
    "Ishiguro's restraint to McCarthy's rhythm. You never use AI slop words."
)

VOICE_PROMPT = """Discover the right narrative voice for this story. This is VOICE.MD --
the definitive guide to HOW this story should sound on the page.

SEED CONCEPT:
{seed}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

PROCESS:
1. Write 3 trial passages (~200 words each) in distinctly different registers:
   - Trial A: Sparse, stripped-down (Hemingway/McCarthy register)
   - Trial B: Dense, literary (Le Guin/Ishiguro register)
   - Trial C: Immediate, visceral (first-person-feeling third-person)

2. Analyze each trial: what works, what doesn't, what fits the world.

3. Declare the chosen voice with specific parameters.

OUTPUT FORMAT:

## Voice Trials

### Trial A: [Register Name]
[~200 words of the story's opening scene in this voice]
**Assessment:** What works, what doesn't.

### Trial B: [Register Name]
[~200 words of the same scene in this voice]
**Assessment:** What works, what doesn't.

### Trial C: [Register Name]
[~200 words of the same scene in this voice]
**Assessment:** What works, what doesn't.

## Selected Voice

### Tone
One-sentence description of the overall feel.

### POV
Person, tense, whose perspective, and limitations.

### Rhythm
How sentence length varies. What the default mode sounds like.
Short sentences for: [what]
Long sentences for: [what]

### Vocabulary Wells
The 2-3 domains this character/narrator draws metaphors and vocabulary from.
Example: a musician thinks in intervals and resonance; a merchant thinks in
contracts and margins.

### Influences
2-3 published authors whose voice this echoes (and HOW, specifically).

### Exemplar Paragraph
The ~100-word paragraph that IS this voice at its best. Written fresh.

### Anti-Exemplars
2-3 example paragraphs of what this voice must NOT sound like:
- Generic fantasy prose
- AI-default prose (the tapestry of delving)
- Wrong register for this world

### Guardrails
- Banned words specific to this project
- Maximum em dashes per paragraph
- Show-don't-tell rules for this voice
- Sentence length targets (mean, min, max)

CRAFT RULES (embedded):
- Style IS the fantasy (Le Guin). The prose creates the world.
- Specificity over abstraction. Not "a bird" but "a jay."
- Metaphors from the CHARACTER'S experience, not a thesaurus.
- Rhythm variation: short, then long, then short again.
- Restraint: power from what's left OUT, not piled on.
- No AI slop: delve, tapestry, myriad, multifaceted, testament, embark, etc.
- No fiction AI tells: "a sense of," "couldn't help but feel," "eyes widened,"
  "the air was thick with," "a wave of X washed over," "a knowing smile"
"""


def generate_voice(project_dir: Path, provider: LLMProvider) -> str:
    """Generate voice.md from seed + world + characters."""
    seed = (project_dir / "seed.txt").read_text()
    world = (project_dir / "world.md").read_text()
    characters = (project_dir / "characters.md").read_text()

    prompt = VOICE_PROMPT.format(seed=seed, world=world, characters=characters)

    print("Discovering voice...", file=sys.stderr)
    result = provider.call(prompt, system=VOICE_SYSTEM, role="draft", temperature=0.8)

    out_path = project_dir / "voice.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
