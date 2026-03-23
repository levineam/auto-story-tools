"""
Outline generation: produces outline.md with Save the Cat beats, try-fail cycles, MICE threads.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

OUTLINE_SYSTEM = (
    "You are a novel architect with deep knowledge of Save the Cat beats, "
    "Sanderson's plotting principles, Dan Harmon's Story Circle, and MICE Quotient. "
    "You build outlines that an author can draft from without inventing structure "
    "on the fly. Every chapter has beats, emotional arc, and try-fail cycle type. "
    "You never use AI slop words. You write in clean, direct prose."
)

OUTLINE_PROMPT = """Build a complete chapter outline for this story. Target: 22-26 chapters,
~80,000 words total (~3,000-4,000 words per chapter).

SEED CONCEPT:
{seed}

{mystery_section}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

{voice_section}

CRAFT REQUIREMENTS (embedded -- follow strictly):

### Save the Cat Beat Sheet (percentage marks)
| Beat                     | % Mark  | What happens                                    |
|--------------------------|---------|-------------------------------------------------|
| Opening Image            | 0-1%    | Snapshot of status quo before the story          |
| Theme Stated             | ~5%     | Someone (NOT protagonist) hints at the lesson    |
| Setup                    | 1-10%   | Normal world, establish characters, plant seeds  |
| Catalyst                 | ~11%    | Something happens TO the protagonist (external)  |
| Debate                   | 11-23%  | Protagonist resists the call, weighs options     |
| Break Into Two           | ~23%    | Protagonist CHOOSES to enter new world (active)  |
| B Story                  | ~27%    | New character/relationship that carries theme    |
| Fun and Games            | 26-50%  | The promise of the premise delivered             |
| Midpoint                 | ~50%    | False victory OR false defeat. Stakes raised.    |
| Bad Guys Close In        | 50-68%  | Walls closing, allies fracture, pressure mounts  |
| All Is Lost              | ~68%    | Lowest point. Whiff of death (literal or not)    |
| Dark Night of the Soul   | 68-77%  | Protagonist internalizes the theme               |
| Break Into Three         | ~77%    | New info changes everything                      |
| Finale                   | 77-97%  | Gather/Execute/Surprise/Dig Deep/New Plan        |
| Final Image              | ~99%    | Mirror of opening image, showing transformation  |

### Try-Fail Cycle Types
- "Yes, but..." -- goal achieved, new complication (most common)
- "No, and..." -- goal failed, things get worse (most common)
- "No, but..." -- goal failed, silver lining (occasional)
- "Yes, and..." -- goal achieved, things improve (rare, save for climax)
Rule: 60%+ of middle scenes should be "Yes, but" or "No, and"

### MICE Quotient
Four thread types: Milieu, Inquiry, Character, Event
Rule: Threads close in REVERSE order of opening (nested like HTML tags)

### Foreshadowing Rules
- Every planted thread has a planned payoff
- Plant-to-payoff distance of at least 3 chapters
- Rule of three: important threads referenced ~3 times before payoff

BUILD THE OUTLINE WITH:

## Act Structure
Map Act I (0-23%), Act II Part 1 (23-50%), Act II Part 2 (50-77%), Act III (77-100%).

## Chapter-by-Chapter Outline

For EACH chapter:
### Ch N: [Title]
- **POV:** (which character)
- **Location:** Which locations
- **Save the Cat beat:** Which beat this chapter serves
- **% mark:** Where this falls in the story
- **Emotional arc:** Starting emotion → ending emotion
- **Try-fail cycle:** Yes-but / No-and / No-but / Yes-and
- **Beats:** 3-5 specific scene beats
- **Plants:** Foreshadowing elements planted
- **Payoffs:** Foreshadowing elements that pay off here
- **Character movement:** What changes by chapter's end
- **The lie:** How the protagonist's lie is reinforced or challenged
- **~Word count target**

## Foreshadowing Ledger

| # | Thread | Planted (Ch) | Reinforced (Ch) | Payoff (Ch) | Type |
|---|--------|-------------|-----------------|-------------|------|

At LEAST 15 threads. Types: object, dialogue, action, symbolic, structural.
Plant-to-payoff distance must be at least 3 chapters.

STABILITY TRAP COUNTERMEASURES:
- Bad things must stay bad. Not everything resolves cleanly.
- At least 3 chapters should be "quiet" -- character-focused, low-action, emotionally rich
- Vary try-fail types throughout
- The climax must use ESTABLISHED rules from the world bible
- Include irreversible decisions and genuine moral ambiguity
- Information economy: withhold information, don't reveal everything immediately

CONSTRAINTS:
- Catalyst must be external (happens TO the protagonist)
- Break Into Two must be a CHOICE
- Midpoint must reverse trajectory
- All Is Lost must include some form of death (literal or metaphorical)
- Opening and Final Image must mirror each other
- The climax must be mechanically resolvable using established rules
"""


def generate_outline(project_dir: Path, provider: LLMProvider) -> str:
    """Generate outline.md from seed + world + characters."""
    seed = (project_dir / "seed.txt").read_text()
    world = (project_dir / "world.md").read_text()
    characters = (project_dir / "characters.md").read_text()

    mystery_section = ""
    mystery_path = project_dir / "MYSTERY.md"
    if mystery_path.exists():
        mystery_section = f"CENTRAL MYSTERY (author's eyes only -- reader discovers gradually):\n{mystery_path.read_text()}"

    voice_section = ""
    voice_path = project_dir / "voice.md"
    if voice_path.exists():
        voice_section = f"VOICE (tone and register):\n{voice_path.read_text()}"

    prompt = OUTLINE_PROMPT.format(
        seed=seed,
        world=world,
        characters=characters,
        mystery_section=mystery_section,
        voice_section=voice_section,
    )

    print("Generating outline...", file=sys.stderr)
    result = provider.call(
        prompt, system=OUTLINE_SYSTEM, role="draft", temperature=0.5, max_tokens=16000
    )

    out_path = project_dir / "outline.md"
    out_path.write_text(result)
    print(f"  Written: {out_path}", file=sys.stderr)
    return result
