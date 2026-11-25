import unittest

from lineup_cards import landing, variants


class LineupCardsTests(unittest.TestCase):
    def test_published_variants_preserve_sorted_collection_order_and_token_pools(self):
        examples = {
            "z": [{"token": "9", "traits": [["eyes", "blue"]]}],
            "a": [{"token": i, "traits": [["eyes", "blue"]]} for i in ("3", "4", "7")],
        }
        cards = variants("sample", examples)['["eyes","blue"]']
        self.assertEqual(cards["slugs"], ["a", "z"])
        rounds = cards["rounds"]
        self.assertEqual(rounds[0]["ids"], ["3", "9"])
        self.assertEqual({tuple(r["ids"]) for r in rounds}, {("3", "9"), ("4", "9"), ("7", "9")})
        self.assertEqual(len({r["path"] for r in rounds}), 3)

    def test_share_metadata_is_present_before_javascript_runs(self):
        page = landing("Eyes & glasses", "Two PFPs", "https://example.org/card/", "https://example.org/?x=1&y=2")
        self.assertIn('name="twitter:image" content="https://example.org/card/card.jpg"', page)
        self.assertIn('href="https://example.org/?x=1&amp;y=2"', page)
        self.assertIn("Eyes &amp; glasses", page)
