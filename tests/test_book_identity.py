from __future__ import annotations

import unittest

from book_core.identity import (
    CANONICAL_BOOK_ROLES,
    LEGACY_BOOK_ROLE_ALIASES,
    BookIdentity,
    build_book_identity,
    canonical_role_from_legacy,
)


class BookIdentityTests(unittest.TestCase):
    def test_canonical_roles_are_frozen(self) -> None:
        self.assertEqual(
            CANONICAL_BOOK_ROLES,
            frozenset({"primary", "supplementary", "reference", "translation"}),
        )

    def test_legacy_roles_map_deterministically(self) -> None:
        self.assertEqual(
            LEGACY_BOOK_ROLE_ALIASES,
            {
                "main": "primary",
                "supplementary": "supplementary",
                "reference": "reference",
                "english": "translation",
            },
        )
        self.assertEqual(canonical_role_from_legacy("main"), "primary")
        self.assertEqual(canonical_role_from_legacy("english"), "translation")

    def test_build_identity_uses_current_compatibility_rule(self) -> None:
        identity = build_book_identity("book_a", "v7", "main")
        self.assertEqual(
            identity,
            BookIdentity(
                book_id="book_a",
                logical_book_id="book_a",
                book_version_id="book_a@v7",
                role="primary",
            ),
        )

    def test_canonical_input_role_is_not_a_legacy_alias(self) -> None:
        with self.assertRaises(ValueError):
            canonical_role_from_legacy("primary")

    def test_blank_identity_parts_fail_closed(self) -> None:
        for book_id, version, role in [
            ("", "v1", "main"),
            ("book", "", "main"),
            ("book", "v1", ""),
        ]:
            with self.subTest(book_id=book_id, version=version, role=role):
                with self.assertRaises(ValueError):
                    build_book_identity(book_id, version, role)


if __name__ == "__main__":
    unittest.main()
