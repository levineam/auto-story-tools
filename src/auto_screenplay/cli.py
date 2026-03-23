"""Scaffold CLI for the future auto-screenplay adapter."""

import click


@click.group()
def main() -> None:
    """auto-screenplay: Outline → Fountain screenplay (planned)."""


@main.command()
def status() -> None:
    """Show scaffold status."""
    click.echo("auto-screenplay is scaffolded but not implemented yet.")
    click.echo("Current repo focus: auto-outline foundation engine.")


if __name__ == "__main__":
    main()
