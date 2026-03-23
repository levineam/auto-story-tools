"""
Foundation engine: the iterative loop that generates → evaluates → targets weakest → iterates.
Runs until foundation_score > 7.5 and lore_score > 7.0.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from .evaluation.consistency import check_consistency
from .evaluation.foundation_judge import evaluate_foundation, extract_dimension_scores
from .evaluation.mechanical import slop_score
from .evaluation.reader_panel import evaluate_reader_panel, panel_consensus_to_dimensions
from .generators.canon import generate_canon
from .generators.characters import generate_characters
from .generators.foreshadowing import generate_foreshadowing
from .generators.mystery import generate_mystery
from .generators.outline import generate_outline
from .generators.seed import load_seed, validate_seed
from .generators.voice import generate_voice
from .generators.world import generate_world
from .provider import LLMProvider
from .state import ProjectState

FOUNDATION_THRESHOLD = 7.5
LORE_THRESHOLD = 7.0
MAX_ITERATIONS = 10
PLATEAU_DELTA = 0.2  # min score improvement to avoid plateau declaration

# Map weakest dimension to the generator that can improve it
DIMENSION_TO_GENERATOR = {
    "world_depth": "world",
    "lore_interconnection": "world",
    "iceberg_depth": "world",
    "character_depth": "characters",
    "character_distinctiveness": "characters",
    "outline_completeness": "outline",
    "foreshadowing_balance": "foreshadowing",
    "internal_consistency": "canon",
    "voice_clarity": "voice",
    "canon_coverage": "canon",
}

# Generation order for initial pass
GENERATION_ORDER = [
    ("voice", generate_voice, ["seed.txt", "world.md", "characters.md"]),
    ("world", generate_world, ["seed.txt"]),
    ("characters", generate_characters, ["seed.txt", "world.md"]),
    ("mystery", generate_mystery, ["seed.txt", "world.md", "characters.md"]),
    ("outline", generate_outline, ["seed.txt", "world.md", "characters.md"]),
    ("canon", generate_canon, ["seed.txt", "world.md", "characters.md"]),
    ("foreshadowing", generate_foreshadowing, ["outline.md", "world.md", "characters.md"]),
]

REGENERATORS = {
    "world": generate_world,
    "characters": generate_characters,
    "outline": generate_outline,
    "voice": generate_voice,
    "canon": generate_canon,
    "mystery": generate_mystery,
    "foreshadowing": generate_foreshadowing,
}

# Files belonging to each layer
LAYER_FILES = {
    "world": ["world.md"],
    "characters": ["characters.md"],
    "outline": ["outline.md"],
    "voice": ["voice.md"],
    "canon": ["canon.md"],
    "mystery": ["MYSTERY.md"],
    "foreshadowing": ["foreshadowing.md"],
}


def _initial_generation(project_dir: Path, provider: LLMProvider, state: ProjectState):
    """Generate all missing layers in dependency order."""
    # Always need seed first
    seed_text = load_seed(project_dir)

    # Validate seed
    print("\n=== Validating seed ===", file=sys.stderr)
    validation = validate_seed(seed_text, provider)
    if not validation.get("valid", False):
        print("  ⚠ Seed validation issues:", file=sys.stderr)
        for key in ["world_differentiator", "central_tension", "cost_constraint", "sensory_hook"]:
            v = validation.get(key, {})
            if not v.get("present", True):
                print(f"    Missing {key}: {v.get('missing', 'unknown')}", file=sys.stderr)
        suggestion = validation.get("suggestion")
        if suggestion:
            print(f"  Suggestion: {suggestion}", file=sys.stderr)
        print("  Proceeding anyway (seed is usable)...", file=sys.stderr)

    # Generate in order, skipping what exists
    # First pass: voice needs world+characters, but world needs seed, characters need world
    # So we go: world → characters → voice → mystery → outline → canon → foreshadowing

    ordered = [
        ("world", generate_world),
        ("characters", generate_characters),
        ("voice", generate_voice),
        ("mystery", generate_mystery),
        ("outline", generate_outline),
        ("canon", generate_canon),
        ("foreshadowing", generate_foreshadowing),
    ]

    for layer_name, generator in ordered:
        if state.layer_exists(layer_name):
            print(f"\n=== {layer_name} already exists, skipping ===", file=sys.stderr)
            continue
        print(f"\n=== Generating {layer_name} ===", file=sys.stderr)
        generator(project_dir, provider)

    state.sync_layers()
    state.save()


def _run_evaluation(project_dir: Path, provider: LLMProvider) -> dict:
    """Run full evaluation: LLM judge + mechanical slop + consistency + reader panel."""
    # LLM judge
    judge_result = evaluate_foundation(project_dir, provider)

    # Mechanical slop check on all text layers
    slop_results = {}
    for name in ["world.md", "characters.md", "outline.md", "voice.md"]:
        path = project_dir / name
        if path.exists():
            slop_results[name] = slop_score(path.read_text())

    # Consistency check
    consistency = check_consistency(project_dir, provider)

    # Reader panel
    panel_result = evaluate_reader_panel(project_dir, provider)

    return {
        "judge": judge_result,
        "slop": slop_results,
        "consistency": consistency,
        "panel": panel_result,
    }


def _save_layer_snapshots(project_dir: Path, layer: str) -> dict[str, str | None]:
    """
    Save in-memory copies of layer files before regeneration.
    Returns a dict mapping filename → content (or None if missing).
    """
    snapshots: dict[str, str | None] = {}
    for filename in LAYER_FILES.get(layer, []):
        path = project_dir / filename
        snapshots[filename] = path.read_text() if path.exists() else None
    return snapshots


def _restore_layer_snapshots(project_dir: Path, snapshots: dict[str, str | None]):
    """Restore layer files from in-memory snapshots."""
    for filename, content in snapshots.items():
        path = project_dir / filename
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(content)


def _quick_foundation_score(project_dir: Path, provider: LLMProvider) -> float:
    """
    Quick evaluation (LLM judge only, no panel, no consistency).
    Returns foundation_score for keep/discard comparison.
    """
    judge_result = evaluate_foundation(project_dir, provider)
    dim_scores = extract_dimension_scores(judge_result)

    lore_dims = ["world_depth"]
    char_dims = ["character_depth"]
    struct_dims = ["outline_completeness", "foreshadowing_balance"]
    craft_dims = ["internal_consistency"]

    def avg(dims):
        vals = [dim_scores.get(d, 0) for d in dims]
        return sum(vals) / len(vals) if vals else 0.0

    lore = avg(lore_dims)
    char = avg(char_dims)
    struct = avg(struct_dims)
    craft = avg(craft_dims)

    return round(lore * 0.4 + char * 0.3 + struct * 0.2 + craft * 0.1, 2)


def _regenerate_weakest(
    project_dir: Path,
    provider: LLMProvider,
    weakest: str,
    eval_result: dict,
    current_foundation_score: float,
    state: ProjectState,
) -> str:
    """
    Regenerate the layer targeted by the weakest dimension with keep/discard logic.

    Returns "keep" or "discard" indicating what happened.
    """
    layer = DIMENSION_TO_GENERATOR.get(weakest, "world")
    generator = REGENERATORS.get(layer)

    if not generator:
        print(f"  No generator for layer '{layer}', skipping", file=sys.stderr)
        return "skip"

    # Get improvement suggestion from judge
    judge = eval_result.get("judge", {})
    dim_data = judge.get(weakest, {})
    gap = dim_data.get("gap", "")
    fix = dim_data.get("fix", "")

    print(f"\n=== Regenerating {layer} (weakest: {weakest}) ===", file=sys.stderr)
    if gap:
        print(f"  Gap: {gap}", file=sys.stderr)
    if fix:
        print(f"  Fix: {fix}", file=sys.stderr)

    # --- KEEP/DISCARD: save current layer files before regeneration ---
    snapshots = _save_layer_snapshots(project_dir, layer)

    # Also save cascaded layers
    cascade_layer = None
    cascade_snapshots: dict[str, str | None] = {}
    if layer == "world" or layer == "characters":
        cascade_layer = "canon"
        cascade_snapshots = _save_layer_snapshots(project_dir, "canon")
    elif layer == "outline":
        cascade_layer = "foreshadowing"
        cascade_snapshots = _save_layer_snapshots(project_dir, "foreshadowing")

    # Regenerate
    generator(project_dir, provider)

    # Cascaded regeneration
    if layer == "world":
        print("  Cascading: regenerating canon after world change...", file=sys.stderr)
        generate_canon(project_dir, provider)
    elif layer == "characters":
        print("  Cascading: regenerating canon after character change...", file=sys.stderr)
        generate_canon(project_dir, provider)
    elif layer == "outline":
        print("  Cascading: regenerating foreshadowing after outline change...", file=sys.stderr)
        generate_foreshadowing(project_dir, provider)

    # Quick re-evaluate to check if score improved
    print("  Quick re-evaluation for keep/discard...", file=sys.stderr)
    new_score = _quick_foundation_score(project_dir, provider)

    if new_score >= current_foundation_score:
        action = "keep"
        print(f"  ✓ KEEP: score {current_foundation_score:.2f} → {new_score:.2f}", file=sys.stderr)
    else:
        action = "discard"
        print(
            f"  ✗ DISCARD: score dropped {current_foundation_score:.2f} → {new_score:.2f}, "
            f"restoring previous version",
            file=sys.stderr,
        )
        _restore_layer_snapshots(project_dir, snapshots)
        if cascade_layer and cascade_snapshots:
            _restore_layer_snapshots(project_dir, cascade_snapshots)

    # Log decision in state history
    state.data["history"].append(
        {
            "event": "keep_discard",
            "timestamp": datetime.now(UTC).isoformat(),
            "layer": layer,
            "weakest_dimension": weakest,
            "score_before": current_foundation_score,
            "score_after": new_score,
            "action": action,
        }
    )

    return action


def _check_plateau(state: ProjectState) -> bool:
    """
    Check if the last 2 eval iterations show a foundation_score delta < PLATEAU_DELTA.
    Returns True if plateau detected.
    """
    # Filter to eval-iteration entries only (not keep_discard events)
    eval_entries = [
        h
        for h in state.data.get("history", [])
        if isinstance(h.get("action", ""), str) and h.get("action", "").startswith("eval-iteration")
    ]

    if len(eval_entries) < 2:
        return False

    last_two = eval_entries[-2:]
    score_a = last_two[0].get("foundation_score", 0.0)
    score_b = last_two[1].get("foundation_score", 0.0)
    delta = abs(score_b - score_a)

    if delta < PLATEAU_DELTA:
        print(
            f"  ⚠ Plateau detected: foundation_score delta {delta:.3f} < {PLATEAU_DELTA} "
            f"({score_a:.2f} → {score_b:.2f})",
            file=sys.stderr,
        )
        return True

    return False


def _append_results_tsv(
    project_dir: Path,
    iteration: int,
    eval_result: dict,
    dim_scores: dict,
    weakest: str | None,
    action: str,
):
    """Append a row to results.tsv in the project directory."""
    tsv_path = project_dir / "results.tsv"
    header = (
        "iteration\ttimestamp\tfoundation_score\tlore_score\tweakest_dimension"
        "\tworld_depth\tcharacter_depth\toutline_completeness\tforeshadowing_balance"
        "\tinternal_consistency\tslop_penalty_avg\tconsistency_score\tpanel_score\taction"
    )

    write_header = not tsv_path.exists()

    # Extract slop penalty average
    slop = eval_result.get("slop", {})
    slop_values: list[float] = []
    for v in slop.values():
        if isinstance(v, dict):
            penalty_raw = v.get("penalty", v.get("score", 0))
            slop_values.append(float(penalty_raw or 0.0))
        elif isinstance(v, (int, float)):
            slop_values.append(float(v))
    slop_avg = round(sum(slop_values) / len(slop_values), 3) if slop_values else 0.0

    # Consistency score: use violation count as inverse proxy (fewer = better)
    consistency = eval_result.get("consistency", {})
    if isinstance(consistency, dict):
        violations = consistency.get("violations", [])
        n_violations = len(violations) if isinstance(violations, list) else 0
        # Translate to a 0-10 score: 0 violations = 10, each violation -1 down to min 0
        consistency_score = max(0.0, 10.0 - n_violations)
    else:
        consistency_score = 0.0

    # Panel score
    panel = eval_result.get("panel", {})
    panel_score_raw = panel.get("panel_score", 0.0) if isinstance(panel, dict) else 0.0
    panel_score = float(panel_score_raw or 0.0)

    # Judge for lore/foundation
    judge = eval_result.get("judge", {})
    lore_score_raw = judge.get("lore_score", 0.0) if isinstance(judge, dict) else 0.0
    foundation_score_raw = judge.get("overall_score", 0.0) if isinstance(judge, dict) else 0.0
    lore_score = float(lore_score_raw or 0.0)
    foundation_score = float(foundation_score_raw or 0.0)

    row = "\t".join(
        str(x)
        for x in [
            iteration,
            datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            foundation_score,
            lore_score,
            weakest or "",
            dim_scores.get("world_depth", 0),
            dim_scores.get("character_depth", 0),
            dim_scores.get("outline_completeness", 0),
            dim_scores.get("foreshadowing_balance", 0),
            dim_scores.get("internal_consistency", 0),
            slop_avg,
            consistency_score,
            panel_score,
            action,
        ]
    )

    with tsv_path.open("a") as f:
        if write_header:
            f.write(header + "\n")
        f.write(row + "\n")


def _pick_target_dimension(
    weakest: str | None,
    eval_result: dict,
) -> str | None:
    """
    Choose which dimension to target for regeneration.

    If the panel consensus overlaps with the judge's weakest dimension,
    prioritise accordingly. Panel consensus narrows the candidate set
    to dimensions backed by 3+ personas.
    """
    if not weakest:
        return None

    panel = eval_result.get("panel", {})
    consensus_items = panel.get("consensus_items", []) if isinstance(panel, dict) else []
    personas = panel.get("personas", {}) if isinstance(panel, dict) else {}

    if not consensus_items:
        return weakest

    panel_dims = panel_consensus_to_dimensions(consensus_items, personas)

    if weakest in panel_dims:
        # Panel agrees with judge — use judge's weakest (already confirmed)
        return weakest

    # Panel disagrees — prefer the first panel-suggested dimension that has a generator
    for dim in panel_dims:
        if dim in DIMENSION_TO_GENERATOR:
            print(
                f"  Panel consensus overrides judge weakest: {weakest} → {dim}",
                file=sys.stderr,
            )
            return dim

    # No overlap found — fall back to judge's weakest
    return weakest


def run_foundation_loop(project_dir: Path, provider: LLMProvider) -> dict:
    """
    Main entry point: run the foundation loop until thresholds are met.
    Returns final evaluation result.
    """
    state = ProjectState(project_dir)

    # Initial generation of missing layers
    _initial_generation(project_dir, provider, state)

    # Iterative evaluation loop
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"ITERATION {iteration} / {MAX_ITERATIONS}", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)

        # Full evaluation (judge + slop + consistency + panel)
        eval_result = _run_evaluation(project_dir, provider)
        judge = eval_result["judge"]

        # Extract scores
        dim_scores = extract_dimension_scores(judge)
        state.update_scores(dim_scores)

        foundation = state.foundation_score
        lore = state.lore_score
        weakest = state.weakest_dimension

        # Panel reporting
        panel = eval_result.get("panel", {})
        panel_score = panel.get("panel_score", 0.0) if isinstance(panel, dict) else 0.0
        consensus = panel.get("consensus_items", []) if isinstance(panel, dict) else []

        print(
            f"\n  Foundation score: {foundation:.2f} (target: {FOUNDATION_THRESHOLD})",
            file=sys.stderr,
        )
        print(f"  Lore score:       {lore:.2f} (target: {LORE_THRESHOLD})", file=sys.stderr)
        print(f"  Panel score:      {panel_score:.2f}", file=sys.stderr)
        print(f"  Weakest:          {weakest}", file=sys.stderr)
        print("  Dimension scores:", file=sys.stderr)
        for d, s in sorted(dim_scores.items()):
            marker = " ← weakest" if d == weakest else ""
            print(f"    {d}: {s}{marker}", file=sys.stderr)
        if consensus:
            print(f"  Panel consensus issues ({len(consensus)}):", file=sys.stderr)
            for item in consensus[:3]:
                print(f"    • {item}", file=sys.stderr)

        # Record iteration
        state.record_iteration(dim_scores, f"eval-iteration-{iteration}")
        state.sync_layers()
        state.save()

        # Save eval log
        eval_dir = project_dir / "eval_logs"
        eval_dir.mkdir(exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        log_path = eval_dir / f"{ts}_foundation_iter{iteration}.json"
        log_path.write_text(json.dumps(eval_result, indent=2, default=str))
        print(f"  Eval log: {log_path}", file=sys.stderr)

        # Append to results.tsv
        _append_results_tsv(project_dir, iteration, eval_result, dim_scores, weakest, "eval")

        # Check thresholds
        if foundation >= FOUNDATION_THRESHOLD and lore >= LORE_THRESHOLD:
            print(
                f"\n✓ Foundation complete! Score {foundation:.2f} meets threshold.", file=sys.stderr
            )
            state.data["phase"] = "complete"
            state.save()
            _append_results_tsv(
                project_dir, iteration, eval_result, dim_scores, weakest, "complete"
            )
            return eval_result

        # Plateau detection (requires at least 2 eval iterations in history)
        if _check_plateau(state):
            print(
                "\n⚠ Plateau: stopping early (score not improving).",
                file=sys.stderr,
            )
            state.data["phase"] = "plateau"
            state.save()
            _append_results_tsv(project_dir, iteration, eval_result, dim_scores, weakest, "plateau")
            return eval_result

        # Pick target dimension (panel consensus can override judge weakest)
        target = _pick_target_dimension(weakest, eval_result)

        # Regenerate with keep/discard logic
        if target:
            regen_action = _regenerate_weakest(
                project_dir, provider, target, eval_result, foundation, state
            )
            state.sync_layers()
            state.save()
            _append_results_tsv(
                project_dir, iteration, eval_result, dim_scores, target, regen_action
            )

    print(
        f"\n⚠ Max iterations ({MAX_ITERATIONS}) reached. Best score: {state.foundation_score:.2f}",
        file=sys.stderr,
    )
    return eval_result
