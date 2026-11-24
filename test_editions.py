"""Cross-check the shareable artifacts against their embedded edition data."""

import csv
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


class Snapshot(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_data = False
        self.payload = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_data = dict(attrs).get("id") == "data"

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_data = False

    def handle_data(self, data):
        if self.in_data:
            self.payload += data


class EditionTests(unittest.TestCase):
    def test_published_artifacts(self):
        paths = sorted(Path("editions").glob("*/index.html"))
        self.assertTrue(paths)
        for page in paths:
            with self.subTest(edition=page.parent.name):
                html = Snapshot()
                html.feed(page.read_text())
                data = json.loads(html.payload)
                self.assertEqual(data["edition"], page.parent.name)
                n = len(data["names"])
                self.assertEqual(len(data["pairs"]), n * (n - 1) // 2)
                for pair in data["pairs"]:
                    self.assertLessEqual(
                        pair["shared"], min(pair["holders_a"], pair["holders_b"])
                    )
                    self.assertLessEqual(pair["top100_shared"], pair["shared"])
                d = json.loads((page.parent / "autoglyphs.json").read_text())
                self.assertEqual(data["diamond"], d)
                self.assertEqual(len({row["token"] for row in d["rows"]}), d["supply"])
                for filename, expected in [
                    ("coverage", n),
                    ("overlap", len(data["pairs"])),
                    ("backgrounds", len(data["colors"])),
                    ("holds", d["supply"]),
                ]:
                    with (page.parent / (filename + ".csv")).open() as file:
                        self.assertEqual(len(list(csv.DictReader(file))), expected)
