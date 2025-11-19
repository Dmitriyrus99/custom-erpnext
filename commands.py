"""CLI hooks for Ferum Custom app needed by bench."""

from __future__ import annotations

import click

from frappe import _  # type: ignore[import-untyped]


@click.command("ferum_custom")
def ferum_custom() -> None:
    """Placeholder command group for Ferum Custom app."""
    click.echo(_("Ferum Custom commands are registered within the app modules."))
