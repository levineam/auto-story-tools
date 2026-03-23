"""
LLM-based foundation evaluation.
Uses a different model than generation to avoid self-congratulation bias.
"""

import json
import re
import sys
from pathlib import Path

from ..provider import LLMProvider

JUDGE_SYSTEM = (
    "You are a literary critic and novel editor. "
    "You evaluate fiction planning documents with precision. "
    "Always respond with valid JSON. No markdown fences, no preamble -- just the JSON object."
)

FOUNDATION_PROMPT = """Evaluate these story planning documents.

SCORING CALIBRATION:
  9-10: Could not improve with a month of focused editorial work.
        Published-novel quality. Reserve 10 for work that SURPRISES you.
  7-8:  Strong. A skilled author could draft from this. Minor gaps.
  5-6:  Functional but thin. Major gaps or generic choices.
  3-4:  Sketchy. More questions than answers.
  1-2:  Placeholder or stub.
  0:    Empty or missing.

  A score of 8+ requires ZERO major gaps. Err toward lower scores.

MANDATORY: For EVERY dimension, identify:
  (a) The single biggest GAP or WEAKNESS
  (b) A specific, actionable improvement to raise the score

VOICE DEFINITION:
{voice}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

OUTLINE:
{outline}

CANON:
{canon}

FORESHADOWING:
{foreshadowing}

CROSS-CHECKS:
1. Check dialogue for AI rhetorical tics shared across characters
2. Check for missing NEGATIVE SPACE -- gaps that would block drafting
3. Check for CONVENIENT GAPS vs DELIBERATE MYSTERY
4. Cross-reference dates, ages, timelines for contradictions

Score these dimensions (gap + improvement required for each):

LORE & WORLDBUILDING:
- world_depth: Magic/speculative system with costs and limitations.
  Could a writer resolve the climactic conflict using only established rules?
  Costs plot-driving? At least 3 societal implications? System testable?
- lore_interconnection: Does changing one element force changes in others?
- iceberg_depth: Implied depth vs stated depth. Author knows the answers?

CHARACTER:
- character_depth: Wound/want/need/lie chains causally linked.
  Want and Need in tension? Lie follows from wound?
- character_distinctiveness: No-tags dialogue test passes?
  No shared rhetorical formulas across characters?

STRUCTURE:
- outline_completeness: Chapters with beats, POV, emotional arc, try-fail type.
  Save the Cat beats at correct percentage marks.
- foreshadowing_balance: Every planted thread has a planned payoff.
  Plant-to-payoff distance at least 3 chapters.

CRAFT:
- internal_consistency: Cross-ref dates, ages, character counts.
  Contradictions found?
- voice_clarity: Voice specific and actionable? Exemplars demonstrate it?
- canon_coverage: Facts logged and sufficient to catch contradictions?

Respond with JSON:
{{
  "world_depth": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "lore_interconnection": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "iceberg_depth": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "character_depth": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "character_distinctiveness": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "outline_completeness": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "foreshadowing_balance": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "internal_consistency": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "voice_clarity": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "canon_coverage": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "contradictions_found": ["list any factual contradictions"],
  "overall_score": N,
  "lore_score": N,
  "weakest_dimension": "...",
  "top_3_improvements": ["ranked list of the 3 highest-leverage improvements"]
}}

WEIGHTING: lore/worldbuilding 40%, character 30%, structure 20%, craft 10%.

FINAL CHECK: If overall_score > 7, re-read your gap lists. If any gap
would force a writer to stop and invent something during drafting,
your score is too high. Revise down.
"""


def parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\" and in_string:
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1], strict=False)

    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        fixed = re.sub(r"(?<!\\)\n", "\\n", text)
        return json.loads(fixed, strict=False)


def evaluate_foundation(project_dir: Path, provider: LLMProvider) -> dict:
    """Run LLM-based foundation evaluation. Returns structured scores."""

    def load(name):
        path = project_dir / name
        return path.read_text() if path.exists() else "(not yet generated)"

    prompt = FOUNDATION_PROMPT.format(
        voice=load("voice.md"),
        world=load("world.md"),
        characters=load("characters.md"),
        outline=load("outline.md"),
        canon=load("canon.md"),
        foreshadowing=load("foreshadowing.md"),
    )

    print("Running foundation evaluation (LLM judge)...", file=sys.stderr)
    raw = provider.call(prompt, system=JUDGE_SYSTEM, role="eval", temperature=0.3, max_tokens=16000)
    return parse_json_response(raw)


def extract_dimension_scores(result: dict) -> dict:
    """Extract per-dimension scores from evaluation result."""
    dims = [
        "world_depth",
        "lore_interconnection",
        "iceberg_depth",
        "character_depth",
        "character_distinctiveness",
        "outline_completeness",
        "foreshadowing_balance",
        "internal_consistency",
        "voice_clarity",
        "canon_coverage",
    ]
    scores = {}
    for d in dims:
        if d in result and isinstance(result[d], dict):
            scores[d] = result[d].get("score", 0)
        elif d in result and isinstance(result[d], (int, float)):
            scores[d] = result[d]
    return scores
