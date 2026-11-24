import json
import struct
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from discovery import PAGES, ROOT, page_path
from pages import package


class DiscoveryTests(unittest.TestCase):
    def test_package_exposes_every_study_and_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary) / "site"
            package(site)
            sitemap = ElementTree.parse(site / "sitemap.xml")
            urls = {loc.text for loc in sitemap.iterfind(".//{*}loc")}
            for key in PAGES:
                with self.subTest(key=key):
                    url = ROOT + page_path(key)
                    self.assertIn(url, urls)
                    page = (site / (page_path(key) or "index.html")).read_text()
                    self.assertIn(f'rel="canonical" href="{url}"', page)
                    self.assertIn(f'property="og:url" content="{url}"', page)
                    self.assertIn(f'content="{ROOT}assets/{key}.png"', page)
                    image = (site / "assets" / (key + ".png")).read_bytes()
                    self.assertEqual(struct.unpack(">II", image[16:24]), (1200, 630))
                    raw = page.split('<script type="application/ld+json">', 1)[1].split(
                        "</script>", 1
                    )[0]
                    for item in json.loads(raw)["@graph"]:
                        for download in item.get("distribution", []):
                            self.assertTrue(
                                (
                                    site / download["contentUrl"].removeprefix(ROOT)
                                ).is_file()
                            )
