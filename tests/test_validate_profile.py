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


if __name__ == "__main__":
    unittest.main()
