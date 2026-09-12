from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import validate_profile


VALID_SVG = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'


class ValidateProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.readme = self.root / "README.md"
        self.assets = self.root / "assets"
        self.assets.mkdir()
        (self.assets / "baseline.svg").write_text(VALID_SVG, encoding="utf-8")

    def errors_for(self, readme: str) -> list[str]:
        self.readme.write_text(readme, encoding="utf-8")
        errors, _, _ = validate_profile.validate(self.root, self.readme)
        return errors

    def write_svg(self, name: str) -> None:
        (self.assets / name).write_text(VALID_SVG, encoding="utf-8")

    def test_real_missing_markdown_link_fails(self) -> None:
        errors = self.errors_for("[missing](missing.svg)\n")
        self.assertIn("missing local reference: missing.svg", errors)

    def test_reference_inside_fenced_block_is_ignored(self) -> None:
        errors = self.errors_for("```markdown\n[example](missing.svg)\n```\n")
        self.assertEqual([], errors)

    def test_unclosed_fenced_block_fails(self) -> None:
        errors = self.errors_for("```markdown\n[example](missing.svg)\n")
        self.assertIn("README.md contains an unclosed fenced code block", errors)
        self.assertNotIn("missing local reference: missing.svg", errors)

    def test_reference_inside_html_comment_is_ignored(self) -> None:
        errors = self.errors_for("<!-- [example](missing.svg) -->\n")
        self.assertEqual([], errors)

    def test_reference_inside_inline_code_is_ignored(self) -> None:
        errors = self.errors_for("`[example](missing.svg)`\n")
        self.assertEqual([], errors)

    def test_reference_inside_indented_code_is_ignored(self) -> None:
        errors = self.errors_for("    [example](missing.svg)\n")
        self.assertEqual([], errors)

    def test_real_html_attributes_outside_ignored_regions_are_validated(self) -> None:
        errors = self.errors_for(
            '<a href="missing.html"><img src="missing.svg" '
            'srcset="missing-dark.svg 2x" /></a>\n'
        )
        self.assertIn("missing local reference: missing.html", errors)
        self.assertIn("missing local reference: missing.svg", errors)
        self.assertIn("missing local reference: missing-dark.svg", errors)

    def test_valid_local_srcset_passes(self) -> None:
        self.write_svg("example.svg")
        errors = self.errors_for('<source srcset="./assets/example.svg" />\n')
        self.assertEqual([], errors)

    def test_missing_local_srcset_fails(self) -> None:
        errors = self.errors_for('<source srcset="./assets/missing.svg" />\n')
        self.assertIn("missing local reference: ./assets/missing.svg", errors)

    def test_multiple_srcset_candidates_are_validated(self) -> None:
        self.write_svg("a.svg")
        errors = self.errors_for(
            '<img srcset="./assets/a.svg 1x, ./assets/b.svg 2x" />\n'
        )
        self.assertNotIn("missing local reference: ./assets/a.svg", errors)
        self.assertIn("missing local reference: ./assets/b.svg", errors)

    def test_external_srcset_urls_are_ignored(self) -> None:
        errors = self.errors_for(
            '<img srcset="https://example.com/a.svg 1x, '
            'https://example.com/b.svg 2x" />\n'
        )
        self.assertEqual([], errors)

    def test_repository_escaping_srcset_fails(self) -> None:
        errors = self.errors_for('<img srcset="../outside.svg 1x" />\n')
        self.assertIn(
            "local reference escapes the repository: ../outside.svg", errors
        )

    def test_valid_reference_style_local_link_passes(self) -> None:
        self.write_svg("header.svg")
        errors = self.errors_for(
            "[diagram][header]\n\n[header]: ./assets/header.svg\n"
        )
        self.assertEqual([], errors)

    def test_missing_reference_style_local_target_fails(self) -> None:
        errors = self.errors_for(
            "[diagram][header]\n\n[header]: ./assets/missing.svg\n"
        )
        self.assertIn("missing local reference: ./assets/missing.svg", errors)

    def test_external_reference_style_target_is_ignored(self) -> None:
        errors = self.errors_for(
            "[documentation][docs]\n\n[docs]: https://example.com/docs\n"
        )
        self.assertEqual([], errors)

    def test_reference_style_image_is_validated(self) -> None:
        errors = self.errors_for(
            "![Architecture][architecture]\n\n"
            "[architecture]: ./assets/missing-architecture.svg\n"
        )
        self.assertIn(
            "missing local reference: ./assets/missing-architecture.svg", errors
        )

    def test_unused_reference_definition_is_not_validated(self) -> None:
        errors = self.errors_for("[unused]: ./assets/missing.svg\n")
        self.assertEqual([], errors)

    def test_reference_style_syntax_in_ignored_regions_is_ignored(self) -> None:
        errors = self.errors_for(
            "<!-- [comment][missing]\n[missing]: missing-comment.svg -->\n"
            "`[inline][missing]`\n\n"
            "    [indented][missing]\n\n"
            "```markdown\n[fenced][missing]\n```\n"
        )
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
