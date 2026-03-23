"""
Reader panel evaluation: 4 specialist personas evaluate the story concept.

Personas:
  - story_editor:          structure, pacing, beat placement
  - genre_reader:          genre conventions, expectations, fresh angles
  - character_specialist:  arc coherence, distinctiveness, depth
  - world_builder:         lore consistency, iceberg depth, interconnection

Each persona gives 1-10 scores on their domain + commentary + issues list.
Consensus items are issues flagged by 3+ personas.
"""

import sys
from pathlib import Path

from ..provider import LLMProvider
from .foundation_judge import parse_json_response

PANEL_SYSTEM = (
    "You are a panel of four specialist readers evaluating a story concept from "
    "planning documents (not finished prose). Each persona has a distinct lens. "
    "Be rigorous, specific, and disagree when warranted. "
    "Respond with valid JSON only — no markdown fences, no preamble."
)

PANEL_PROMPT = """Evaluate these story planning documents from four specialist perspectives.

You are four distinct readers. Each reader evaluates through their own lens.
Score 1-10, with 10 reserved for work that genuinely surprises you.
Score calibration: 7+ means a professional could execute from this without inventing material.

---
VOICE DEFINITION:
{voice}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

OUTLINE:
{outline}

FORESHADOWING LEDGER:
{foreshadowing}

CANON:
{canon}
---

READER 1 — STORY EDITOR
Lens: structure, pacing, beat placement, Save the Cat alignment, act breaks.
Score these sub-dimensions (1-10):
  - act_structure: clear act breaks, midpoint, dark night, climax
  - pacing: beat density, no dead zones, tension escalation
  - setup_payoff: major setups have corresponding payoffs
  - chapter_clarity: each chapter has POV, goal, conflict, outcome
What is the single biggest structural problem that would stall a writer?

READER 2 — GENRE READER
Lens: genre conventions, reader expectations, fresh angles vs. tired tropes.
Score these sub-dimensions (1-10):
  - genre_fit: concept fits genre conventions readers expect
  - trope_freshness: familiar elements twisted or subverted meaningfully
  - market_positioning: comparable titles evident, clear shelf placement
  - hook_strength: logline / premise hook is compelling to this genre's fans
What is the single most genre-damaging weakness?

READER 3 — CHARACTER SPECIALIST
Lens: arc coherence, character distinctiveness, relational dynamics, wound/want/need chains.
Score these sub-dimensions (1-10):
  - arc_coherence: character arcs complete convincing transformation
  - voice_distinctiveness: characters sound and think differently from each other
  - wound_want_need: wound drives want, want obscures need, arc resolves need
  - relational_dynamics: relationships have their own arcs and tensions
What is the single most character-damaging weakness?

READER 4 — WORLD-BUILDER
Lens: lore consistency, iceberg depth, systemic interconnection, speculative rigor.
Score these sub-dimensions (1-10):
  - lore_consistency: no contradictions in rules, history, geography, culture
  - iceberg_depth: author clearly knows more than is on the page
  - systemic_interconnection: changing one lore element cascades to others plausibly
  - speculative_rigor: magic/technology/society has internal logic and costs
What is the single most world-damaging weakness?

Respond with JSON exactly:
{{
  "story_editor": {{
    "scores": {{
      "act_structure": N,
      "pacing": N,
      "setup_payoff": N,
      "chapter_clarity": N
    }},
    "overall": N,
    "commentary": "2-3 sentences on what works and what doesn't",
    "issues": ["specific issue 1", "specific issue 2"]
  }},
  "genre_reader": {{
    "scores": {{
      "genre_fit": N,
      "trope_freshness": N,
      "market_positioning": N,
      "hook_strength": N
    }},
    "overall": N,
    "commentary": "2-3 sentences on what works and what doesn't",
    "issues": ["specific issue 1", "specific issue 2"]
  }},
  "character_specialist": {{
    "scores": {{
      "arc_coherence": N,
      "voice_distinctiveness": N,
      "wound_want_need": N,
      "relational_dynamics": N
    }},
    "overall": N,
    "commentary": "2-3 sentences on what works and what doesn't",
    "issues": ["specific issue 1", "specific issue 2"]
  }},
  "world_builder": {{
    "scores": {{
      "lore_consistency": N,
      "iceberg_depth": N,
      "systemic_interconnection": N,
      "speculative_rigor": N
    }},
    "overall": N,
    "commentary": "2-3 sentences on what works and what doesn't",
    "issues": ["specific issue 1", "specific issue 2"]
  }}
}}
"""

# Weights for panel_score: all personas contribute equally
PERSONA_WEIGHTS = {
    "story_editor": 0.25,
    "genre_reader": 0.25,
    "character_specialist": 0.25,
    "world_builder": 0.25,
}

# Map persona issues to foundation dimensions for consensus → targeting
PERSONA_TO_DIMENSION = {
    "story_editor": ["outline_completeness", "foreshadowing_balance"],
    "genre_reader": ["outline_completeness", "voice_clarity"],
    "character_specialist": ["character_depth", "character_distinctiveness"],
    "world_builder": ["world_depth", "lore_interconnection", "iceberg_depth"],
}


def evaluate_reader_panel(project_dir: Path, provider: LLMProvider) -> dict:
    """
    Run the 4-persona reader panel evaluation.

    Returns:
        {
            "personas": {
                "story_editor": {"scores": {...}, "overall": N, "commentary": "...", "issues": [...]},
                "genre_reader": {...},
                "character_specialist": {...},
                "world_builder": {...},
            },
            "consensus_items": [...],   # issues flagged by 3+ personas
            "panel_score": float,       # weighted average of persona overall scores
        }
    """

    def load(name: str) -> str:
        path = project_dir / name
        return path.read_text() if path.exists() else "(not yet generated)"

    prompt = PANEL_PROMPT.format(
        voice=load("voice.md"),
        world=load("world.md"),
        characters=load("characters.md"),
        outline=load("outline.md"),
        foreshadowing=load("foreshadowing.md"),
        canon=load("canon.md"),
    )

    print("Running reader panel evaluation...", file=sys.stderr)
    raw = provider.call(
        prompt,
        system=PANEL_SYSTEM,
        role="eval",
        temperature=0.3,
        max_tokens=8000,
    )

    try:
        parsed = parse_json_response(raw)
    except (ValueError, Exception) as exc:
        print(f"  ⚠ Reader panel parse error: {exc}", file=sys.stderr)
        return _empty_panel()

    personas = {}
    for persona_key in ("story_editor", "genre_reader", "character_specialist", "world_builder"):
        raw_p = parsed.get(persona_key, {})
        personas[persona_key] = {
            "scores": raw_p.get("scores", {}),
            "overall": float(raw_p.get("overall", 0)),
            "commentary": raw_p.get("commentary", ""),
            "issues": raw_p.get("issues", []),
        }

    panel_score = sum(personas[k]["overall"] * w for k, w in PERSONA_WEIGHTS.items())

    consensus_items = _find_consensus(personas)

    return {
        "personas": personas,
        "consensus_items": consensus_items,
        "panel_score": round(panel_score, 2),
    }


def _find_consensus(personas: dict) -> list[str]:
    """
    Find issues flagged by 3 or more personas.

    Similarity heuristic: normalise issue text to lowercase tokens and check
    for >= 3-word overlap between any two issues across personas. This catches
    paraphrased versions of the same complaint without requiring exact matches.
    """
    all_issues: list[tuple[str, str]] = []  # (persona, issue_text)
    for persona_key, data in personas.items():
        for issue in data.get("issues", []):
            all_issues.append((persona_key, issue.lower()))

    if not all_issues:
        return []

    # Build overlap clusters: two issues are "similar" if they share ≥3 content words
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "in",
        "of",
        "to",
        "and",
        "or",
        "but",
        "for",
        "on",
        "at",
        "with",
        "it",
        "this",
        "that",
        "not",
        "no",
        "be",
        "by",
        "as",
        "so",
        "do",
    }

    def content_tokens(text: str) -> set[str]:
        import re

        tokens = re.findall(r"[a-z']+", text)
        return {t for t in tokens if t not in stopwords and len(t) > 2}

    token_sets = [(persona, content_tokens(issue)) for persona, issue in all_issues]

    # For each issue, count how many OTHER personas have a "similar" issue
    n = len(token_sets)
    consensus: list[str] = []
    seen_indices: set[int] = set()

    for i in range(n):
        if i in seen_indices:
            continue
        p_i, t_i = token_sets[i]
        agreeing_personas = {p_i}
        cluster_indices = [i]

        for j in range(n):
            if i == j or j in seen_indices:
                continue
            p_j, t_j = token_sets[j]
            if p_j == p_i:
                continue  # same persona, doesn't count
            overlap = len(t_i & t_j)
            if overlap >= 3:
                agreeing_personas.add(p_j)
                cluster_indices.append(j)

        if len(agreeing_personas) >= 3:
            # Use the first (longest) issue text as the canonical representative
            representative = all_issues[i][1]
            consensus.append(representative)
            seen_indices.update(cluster_indices)

    return consensus


def _empty_panel() -> dict:
    """Return an empty panel result on parse failure."""
    empty_persona = {
        "scores": {},
        "overall": 0.0,
        "commentary": "",
        "issues": [],
    }
    return {
        "personas": {
            "story_editor": dict(empty_persona),
            "genre_reader": dict(empty_persona),
            "character_specialist": dict(empty_persona),
            "world_builder": dict(empty_persona),
        },
        "consensus_items": [],
        "panel_score": 0.0,
    }


def panel_consensus_to_dimensions(consensus_items: list[str], personas: dict) -> list[str]:
    """
    Map consensus items back to foundation judge dimensions.

    Returns a list of dimension names that the panel consensus suggests
    need the most improvement, in priority order.
    """
    if not consensus_items:
        return []

    dimension_votes: dict[str, int] = {}
    for persona_key, dims in PERSONA_TO_DIMENSION.items():  # noqa: B007
        persona_issues = personas.get(persona_key, {}).get("issues", [])
        # If this persona contributed to any consensus item, vote for its dims
        for item in consensus_items:
            for p_issue in persona_issues:
                if item[:30] in p_issue.lower() or p_issue.lower()[:30] in item:
                    for d in dims:
                        dimension_votes[d] = dimension_votes.get(d, 0) + 1
                    break

    if not dimension_votes:
        # Fallback: vote all dims for all agreeing persona types
        for _persona_key, dims in PERSONA_TO_DIMENSION.items():
            for d in dims:
                dimension_votes[d] = dimension_votes.get(d, 0) + 1

    return sorted(dimension_votes, key=lambda dim: dimension_votes[dim], reverse=True)
