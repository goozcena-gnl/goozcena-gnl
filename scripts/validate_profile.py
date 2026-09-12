"""Lightweight, dependency-free validation for the profile repository."""

from __future__ import annotations

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
HTML_COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)
INLINE_CODE = re.compile(r"(`+)(.*?)\1")
REFERENCE_USE = re.compile(r"!?\[[^\]]*\]\[([^\]]+)\]")
REFERENCE_DEFINITION = re.compile(
    r"^[ \t]{0,3}\[([^\]]+)\]:[ \t]*(?:<([^>]+)>|(\S+))",
    re.MULTILINE,
)


class ReferenceHTMLParser(HTMLParser):
    """Collect link-like attributes from rendered HTML fragments."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del tag
        for name, value in attrs:
            if value is None:
                continue
            if name in {"href", "src"}:
                self.references.append(value)
            elif name == "srcset":
                self.references.extend(srcset_urls(value))

    handle_startendtag = handle_starttag


def strip_fenced_code(text: str) -> tuple[str, bool]:
    """Remove fenced regions and report whether every fence was closed."""

    outside: list[str] = []
    fence_character = ""
    fence_length = 0

    for line in text.splitlines(keepends=True):
        if not fence_character:
            match = FENCE_OPEN.match(line)
            if match:
                marker = match.group(1)
                fence_character = marker[0]
                fence_length = len(marker)
                outside.append("\n" if line.endswith(("\n", "\r")) else "")
            else:
                outside.append(line)
            continue

        closing = line.strip()
        if (
            len(closing) >= fence_length
            and set(closing) == {fence_character}
        ):
            fence_character = ""
            fence_length = 0
        outside.append("\n" if line.endswith(("\n", "\r")) else "")

    return "".join(outside), not fence_character


def blank_region(match: re.Match[str]) -> str:
    """Blank ignored content while retaining its line structure."""

    return "".join("\n" if character == "\n" else " " for character in match.group())


def strip_indented_code(text: str) -> str:
    """Remove four-space code blocks without hiding nested HTML attributes."""

    outside: list[str] = []
    in_code_block = False
    previous_line_blank = True

    for line in text.splitlines(keepends=True):
        indented = line.startswith("    ") or line.startswith("\t")
        if indented and (in_code_block or previous_line_blank):
            in_code_block = True
            outside.append("\n" if line.endswith(("\n", "\r")) else "")
            previous_line_blank = False
            continue

        if in_code_block and not line.strip():
            outside.append(line)
            previous_line_blank = True
            continue

        in_code_block = False
        outside.append(line)
        previous_line_blank = not line.strip()

    return "".join(outside)


def rendered_regions(text: str) -> tuple[str, bool]:
    """Remove the limited set of Markdown regions that do not render links."""

    text, fences_closed = strip_fenced_code(text)
    text = HTML_COMMENT.sub(blank_region, text)
    text = strip_indented_code(text)
    text = INLINE_CODE.sub(blank_region, text)
    return text, fences_closed


def srcset_urls(value: str) -> list[str]:
    """Return the URL portion of each normal srcset candidate."""

    return [
        candidate.split()[0]
        for item in value.split(",")
        if (candidate := item.strip())
    ]


def normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def references_in(text: str) -> tuple[list[str], list[str]]:
    references = MARKDOWN_LINK.findall(text)
    parser = ReferenceHTMLParser()
    parser.feed(text)
    parser.close()

    definitions: dict[str, str] = {}
    for match in REFERENCE_DEFINITION.finditer(text):
        label, angle_target, plain_target = match.groups()
        definitions.setdefault(
            normalize_reference_label(label), angle_target or plain_target
        )

    missing_definitions: list[str] = []
    for label in REFERENCE_USE.findall(text):
        normalized_label = normalize_reference_label(label)
        if normalized_label in definitions:
            references.append(definitions[normalized_label])
        else:
            missing_definitions.append(label)

    return references + parser.references, missing_definitions


def local_target(reference: str, repo_root: Path, readme: Path) -> Path | None:
    reference = html.unescape(reference).strip().strip("<>")
    if not reference or reference.startswith(("#", "//")):
        return None

    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None

    target = (readme.parent / unquote(parsed.path)).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as error:
        raise ValueError(f"local reference escapes the repository: {reference}") from error
    return target


def validate(repo_root: Path, readme: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []

    if not readme.is_file():
        errors.append("README.md is missing")
        text = ""
    else:
        text = readme.read_text(encoding="utf-8")

    rendered_text, fences_closed = rendered_regions(text)
    if not fences_closed:
        errors.append("README.md contains an unclosed fenced code block")

    references, missing_definitions = references_in(rendered_text)
    for label in sorted(set(missing_definitions)):
        errors.append(f"missing reference definition: {label}")
    for reference in sorted(set(references)):
        try:
            target = local_target(reference, repo_root, readme)
        except ValueError as error:
            errors.append(str(error))
            continue
        if target is not None and not target.exists():
            errors.append(f"missing local reference: {reference}")

    svg_files = sorted(repo_root.rglob("*.svg"))
    if not svg_files:
        errors.append("no repository-hosted SVG files found")
    for svg_file in svg_files:
        try:
            svg_root = ElementTree.parse(svg_file).getroot()
        except (ElementTree.ParseError, OSError) as error:
            errors.append(f"invalid SVG {svg_file.relative_to(repo_root)}: {error}")
            continue
        if svg_root.tag.rsplit("}", 1)[-1] != "svg":
            errors.append(f"invalid SVG root element: {svg_file.relative_to(repo_root)}")

    return errors, len(set(references)), len(svg_files)


def main() -> int:
    errors, reference_count, svg_count = validate(ROOT, README)

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"Validated README structure, {reference_count} references, "
        f"and {svg_count} SVG file(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
