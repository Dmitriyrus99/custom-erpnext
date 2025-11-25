#!/usr/bin/env python3
"""Merge `.env.example` with secret fragments produced by render_env_from_secrets."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List


def parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def load_lines(path: Path) -> List[str]:
    return path.read_text().splitlines()


def write_output(lines: Iterable[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def render_env(
    template_path: Path,
    extra_paths: List[Path],
) -> List[str]:
    base_lines = load_lines(template_path)
    base_values = parse_env_file(template_path)
    merged: Dict[str, str] = dict(base_values)

    for extra in extra_paths:
        if not extra.exists():
            raise FileNotFoundError(f"Extra file {extra} does not exist")
        merged.update(parse_env_file(extra))

    rendered: List[str] = []
    seen_keys = set()

    for raw_line in base_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            rendered.append(raw_line)
            continue

        key, _, default_value = raw_line.partition("=")
        key = key.strip()
        seen_keys.add(key)
        value = merged.get(key, default_value.strip())
        rendered.append(f"{key}={value}")

    for key in sorted(merged.keys()):
        if key in seen_keys:
            continue
        rendered.append(f"{key}={merged[key]}")

    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Render .env from template + secret fragments.")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path(".env.example"),
        help="Template with default placeholders",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(".env"),
        help="Destination .env file",
    )
    parser.add_argument(
        "--extra-file",
        "-e",
        type=Path,
        action="append",
        default=[],
        help="Additional secret fragments (repeatable)",
    )

    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Template {args.input} not found")

    rendered_lines = render_env(args.input, args.extra_file)
    write_output(rendered_lines, args.output)


if __name__ == "__main__":
    main()
