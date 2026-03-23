"""
Cross-layer consistency checks.
Runs every iteration to verify:
- Outline references only existing lore
- Character abilities match system rules
- Foreshadowing threads balance
- Canon facts don't contradict across layers
"""

import sys
from pathlib import Path

from ..provider import LLMProvider

CONSISTENCY_SYSTEM = (
    "You are a continuity editor performing cross-reference checks between "
    "story planning documents. You are pedantic, precise, and flag every "
    "inconsistency no matter how small. Respond with valid JSON only."
)

CONSISTENCY_PROMPT = """Perform cross-layer consistency checks on these planning documents.

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

OUTLINE:
{outline}

CANON:
{canon}

FORESHADOWING LEDGER:
{foreshadowing}

CHECK EACH OF THESE:

1. OUTLINE ↔ WORLD: Does the outline reference any locations, rules, or lore
   elements that don't exist in the world bible? List each.

2. OUTLINE ↔ CHARACTERS: Does the outline reference any characters not in the
   registry? Do character abilities used in the outline match what's established?

3. CHARACTER ↔ WORLD: Do character abilities match the speculative/magic system
   rules? Does a character violate any established limitations?

4. FORESHADOWING ↔ OUTLINE: Does every planted thread in the foreshadowing
   ledger correspond to an actual scene in the outline? Are there orphaned
   plants or payoffs?

5. CANON CONTRADICTIONS: Cross-reference all canon facts against the source
   documents. Flag any that disagree.

6. TIMELINE: Check ages, dates, and durations for mathematical consistency.

7. MISSING ELEMENTS: What does the outline need that doesn't exist yet?
   Locations mentioned but not described? Characters referenced but not defined?

Respond with JSON:
{{
  "outline_world_violations": ["list of things outline refs that world doesn't define"],
  "outline_character_violations": ["list of things outline refs that characters don't define"],
  "character_world_violations": ["character abilities that violate world rules"],
  "foreshadowing_orphans": {{"unplanted_payoffs": ["payoffs with no plant"], "unpaid_plants": ["plants with no payoff"]}},
  "canon_contradictions": ["specific contradictions found"],
  "timeline_issues": ["age/date/duration errors"],
  "missing_elements": ["things needed but not defined"],
  "consistency_score": N,
  "critical_issues": ["issues that would block drafting"],
  "total_violations": N
}}

Be exhaustive. A clean check is score 10. Each violation drops the score.
3+ critical issues caps the score at 5.
"""


def check_consistency(project_dir: Path, provider: LLMProvider) -> dict:
    """Run cross-layer consistency checks."""
    from .foundation_judge import parse_json_response

    def load(name):
        path = project_dir / name
        return path.read_text() if path.exists() else "(not yet generated)"

    prompt = CONSISTENCY_PROMPT.format(
        world=load("world.md"),
        characters=load("characters.md"),
        outline=load("outline.md"),
        canon=load("canon.md"),
        foreshadowing=load("foreshadowing.md"),
    )

    print("Running cross-layer consistency checks...", file=sys.stderr)
    raw = provider.call(
        prompt, system=CONSISTENCY_SYSTEM, role="eval", temperature=0.3, max_tokens=8000
    )
    return parse_json_response(raw)
