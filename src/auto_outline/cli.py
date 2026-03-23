"""
CLI entry point: auto-outline init / run / status
"""

import json
import shutil
import sys
from pathlib import Path

import click

from .provider import LLMProvider
from .state import LAYER_FILES, ProjectState

TEMPLATE_SEED = """# Story Seed

## Concept
[Your story concept here — what is this story ABOUT?]

## World-Differentiator
[What makes this world distinct from ours or from generic genre settings?]

## Central Tension
[The core conflict or question driving the story]

## Cost/Constraint
[What limits power, creates stakes, makes choices hard?]

## Sensory Hook
[A specific, visceral image or sensation that anchors the reader]
"""


@click.group()
def main():
    """auto-outline: Seed → Story Bible → Scored Outline"""
    pass


@main.command()
@click.argument("seed_path", required=False, type=click.Path())
@click.option("--dir", "project_dir", default=".", help="Project directory (default: current)")
def init(seed_path, project_dir):
    """Create project directory with template files.

    SEED_PATH: optional path to a seed.txt file to copy in.
    """
    pdir = Path(project_dir).resolve()
    pdir.mkdir(parents=True, exist_ok=True)

    # Create eval_logs directory
    (pdir / "eval_logs").mkdir(exist_ok=True)

    # Copy or create seed.txt
    seed_dest = pdir / "seed.txt"
    if seed_path:
        src = Path(seed_path).resolve()
        if not src.exists():
            click.echo(f"Error: seed file not found: {src}", err=True)
            sys.exit(1)
        shutil.copy2(src, seed_dest)
        click.echo(f"  Copied seed: {src} → {seed_dest}")
    elif not seed_dest.exists():
        seed_dest.write_text(TEMPLATE_SEED)
        click.echo(f"  Created template: {seed_dest}")
        click.echo("  Edit seed.txt with your story concept before running.")

    # Create .env template
    env_path = pdir / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# auto-outline configuration\n"
            "# Set ONE of these:\n"
            "ANTHROPIC_API_KEY=\n"
            "# OPENAI_API_KEY=\n"
            "\n"
            "# Optional: override models\n"
            "# AUTO_OUTLINE_DRAFT_MODEL=claude-sonnet-4-6\n"
            "# AUTO_OUTLINE_EVAL_MODEL=claude-opus-4-6\n"
            "\n"
            "# Optional: custom API base URL\n"
            "# AUTO_OUTLINE_API_BASE=\n"
        )
        click.echo(f"  Created: {env_path}")

    # Initialize state
    state = ProjectState(pdir)
    state.sync_layers()
    state.save()

    click.echo(f"\n✓ Project initialized at {pdir}")
    click.echo("  Next: edit seed.txt, set API key in .env, then run `auto-outline run`")


@main.command()
@click.option("--dir", "project_dir", default=".", help="Project directory")
@click.option("--max-iterations", default=10, help="Maximum evaluation iterations")
def run(project_dir, max_iterations):
    """Execute foundation loop until score thresholds are met."""
    from .engine import run_foundation_loop

    pdir = Path(project_dir).resolve()

    # Verify seed exists
    if not (pdir / "seed.txt").exists():
        click.echo("Error: no seed.txt found. Run `auto-outline init` first.", err=True)
        sys.exit(1)

    # Verify API key
    try:
        provider = LLMProvider(pdir)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"Starting foundation loop (max {max_iterations} iterations)...")
    click.echo(f"  Project: {pdir}")
    click.echo(f"  Provider: {provider.provider.value}")
    click.echo(f"  Draft model: {provider.draft_model}")
    click.echo(f"  Eval model: {provider.eval_model}")

    run_foundation_loop(pdir, provider)

    # Final summary
    state = ProjectState(pdir)
    click.echo(f"\n{'=' * 60}")
    click.echo(
        "FOUNDATION COMPLETE" if state.data["phase"] == "complete" else "FOUNDATION INCOMPLETE"
    )
    click.echo(f"{'=' * 60}")
    click.echo(f"  Foundation score: {state.foundation_score:.2f}")
    click.echo(f"  Lore score:       {state.lore_score:.2f}")
    click.echo(f"  Iterations:       {state.iteration}")
    click.echo(f"  Weakest:          {state.weakest_dimension}")

    # List generated files
    click.echo("\nGenerated files:")
    for layer, filename in LAYER_FILES.items():  # noqa: B007
        path = pdir / filename
        status = "✓" if path.exists() else "✗"
        size = f"({path.stat().st_size:,} bytes)" if path.exists() else ""
        click.echo(f"  {status} {filename} {size}")


@main.command()
@click.option("--dir", "project_dir", default=".", help="Project directory")
@click.option("--json-out", "json_output", is_flag=True, help="Output as JSON")
def status(project_dir, json_output):
    """Show current scores and weakest dimension."""
    pdir = Path(project_dir).resolve()
    state = ProjectState(pdir)
    state.sync_layers()

    if json_output:
        click.echo(json.dumps(state.data, indent=2))
        return

    click.echo(f"Project: {pdir}")
    click.echo(f"Phase:   {state.data['phase']}")
    click.echo("\nScores:")
    click.echo(f"  Foundation: {state.foundation_score:.2f} (target: 7.5)")
    click.echo(f"  Lore:       {state.lore_score:.2f} (target: 7.0)")

    if state.data["scores"]:
        click.echo("\nDimension scores:")
        for dim, score in sorted(state.data["scores"].items()):
            marker = " ← weakest" if dim == state.weakest_dimension else ""
            click.echo(f"  {dim}: {score}{marker}")

    click.echo(f"\nIteration: {state.iteration}")

    click.echo("\nLayers:")
    for layer, filename in LAYER_FILES.items():  # noqa: B007
        path = pdir / filename
        layer_state = state.data["layers"].get(layer, {})
        status_str = layer_state.get("status", "missing")
        size = f"({path.stat().st_size:,} bytes)" if path.exists() else ""
        icon = "✓" if status_str == "complete" else "△" if status_str == "changed" else "✗"
        click.echo(f"  {icon} {filename}: {status_str} {size}")

    if state.data.get("history"):
        click.echo("\nHistory (last 3):")
        for entry in state.data["history"][-3:]:
            click.echo(
                f"  Iter {entry['iteration']}: score={entry['foundation_score']:.2f}, weakest={entry['weakest_dimension']}"
            )


if __name__ == "__main__":
    main()
