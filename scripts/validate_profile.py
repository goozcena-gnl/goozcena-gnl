"""Lightweight, dependency-free validation for the profile repository."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_LINK = re.compile(r"\b(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
FENCE = re.compile(r"^\s*```", re.MULTILINE)


def local_target(reference: str) -> Path | None:
    reference = html.unescape(reference).strip().strip("<>")
    if not reference or reference.startswith(("#", "//")):
        return None

    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None

    target = (README.parent / unquote(parsed.path)).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(f"local reference escapes the repository: {reference}") from error
    return target


def main() -> int:
    errors: list[str] = []

    if not README.is_file():
        errors.append("README.md is missing")
        text = ""
    else:
        text = README.read_text(encoding="utf-8")

    if len(FENCE.findall(text)) % 2:
        errors.append("README.md contains an unclosed fenced code block")

    references = MARKDOWN_LINK.findall(text) + HTML_LINK.findall(text)
    for reference in sorted(set(references)):
        try:
            target = local_target(reference)
        except ValueError as error:
            errors.append(str(error))
            continue
        if target is not None and not target.exists():
            errors.append(f"missing local reference: {reference}")

    svg_files = sorted(ROOT.rglob("*.svg"))
    if not svg_files:
        errors.append("no repository-hosted SVG files found")
    for svg_file in svg_files:
        try:
            root = ElementTree.parse(svg_file).getroot()
        except (ElementTree.ParseError, OSError) as error:
            errors.append(f"invalid SVG {svg_file.relative_to(ROOT)}: {error}")
            continue
        if root.tag.rsplit("}", 1)[-1] != "svg":
            errors.append(f"invalid SVG root element: {svg_file.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"Validated README structure, {len(set(references))} references, "
        f"and {len(svg_files)} SVG file(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
