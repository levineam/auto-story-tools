"""
Seed validation: checks that a seed concept has the four required elements.
"""

from pathlib import Path

from ..provider import LLMProvider

SEED_SYSTEM = (
    "You are a story development editor. You evaluate seed concepts for completeness. "
    "You are terse, direct, and specific. No filler."
)

SEED_VALIDATION_PROMPT = """Evaluate this seed concept for a story. A complete seed needs four elements:

1. WORLD-DIFFERENTIATOR — what makes this world distinct from ours (or from generic fantasy/sci-fi)
2. CENTRAL TENSION — the core conflict or question driving the story
3. COST/CONSTRAINT — what limits power, creates stakes, makes choices hard
4. SENSORY HOOK — a specific, visceral image or sensation that anchors the reader

SEED:
{seed_text}

Respond with JSON (no markdown fences):
{{
  "world_differentiator": {{"present": true/false, "found": "what you found or null", "missing": "what's needed or null"}},
  "central_tension": {{"present": true/false, "found": "...", "missing": "..."}},
  "cost_constraint": {{"present": true/false, "found": "...", "missing": "..."}},
  "sensory_hook": {{"present": true/false, "found": "...", "missing": "..."}},
  "valid": true/false,
  "suggestion": "one-sentence improvement if not valid, null if valid"
}}
"""


def validate_seed(seed_text: str, provider: LLMProvider) -> dict:
    """Validate a seed concept. Returns parsed JSON result."""
    import json

    prompt = SEED_VALIDATION_PROMPT.format(seed_text=seed_text)
    raw = provider.call(prompt, system=SEED_SYSTEM, role="eval", temperature=0.3, max_tokens=2000)

    # Parse JSON from response
    text = raw.strip()
    if text.startswith("```"):
        import re

        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    return json.loads(text)


def load_seed(project_dir: Path) -> str:
    """Load seed.txt from project directory."""
    seed_path = project_dir / "seed.txt"
    if not seed_path.exists():
        raise FileNotFoundError(f"No seed.txt found in {project_dir}")
    text = seed_path.read_text().strip()
    if not text:
        raise ValueError("seed.txt is empty")
    return text
