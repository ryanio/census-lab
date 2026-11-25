"""Render a standalone Census edition from its checked-in CSV and JSON records."""

import argparse
import base64
import csv
import json
from html import escape
from pathlib import Path

from stories import holds_story, overlap_story
from lineup_cards import variants
from discovery import PAGES, ROOT, descriptions, metadata, page_path

HOLD_COLLECTIONS = {"autoglyphs": "Autoglyphs", "deafbeef": "DEAFBEEF"}

SITE = Path(__file__).parent / "site"


def read_csv(path):
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def render(directory, entry="home", base=ROOT, *, standalone=True):
    pairs = read_csv(directory / "overlap.csv")
    for pair in pairs:
        for key in ("shared", "holders_a", "holders_b", "top100_shared"):
            pair[key] = int(pair[key])
        for key in ("pct_a", "pct_b"):
            pair[key] = float(pair[key])
    colors = read_csv(directory / "backgrounds.csv")
    for row in colors:
        row["count"] = int(row["count"])
    names = json.loads((SITE.parent / "names.json").read_text())
    # An edition's coverage fixes its cohort even when later issues add collections.
    cohort = [row["slug"] for row in read_csv(directory / "coverage.csv")]
    portraits = {}
    for slug in cohort:
        path = SITE / "portraits" / f"{slug}.webp"
        if path.exists():
            portraits[slug] = "data:image/webp;base64," + base64.b64encode(
                path.read_bytes()
            ).decode("ascii")
    trait_index = {}
    for row in read_csv(directory / "traits.csv"):
        category = trait_index.setdefault(row["slug"], {}).setdefault(
            row["category"], []
        )
        category.append([row["value"], int(row["count"]), json.loads(row["floors"])])
    holdings = {}
    for slug, name in HOLD_COLLECTIONS.items():
        series = json.loads((directory / f"{slug}.json").read_text())
        holdings[slug] = {"name": name, **series}
    examples = directory / "trait-examples.json"
    tokens = json.loads(examples.read_text()) if (standalone or entry == "traits") and examples.exists() else {}
    snapshot = {
        "traitExamples": tokens,
        "lineupCards": variants(directory.name, tokens) if (directory / "lineup-art").exists() else {},
        "portraits": portraits,
        "edition": directory.name,
        "names": {slug: names[slug] for slug in cohort},
        "pairs": pairs,
        "colors": colors,
        "holdings": holdings,
        "traits": trait_index,
    }
    page = (SITE / "template.html").read_text()
    page = page.replace("<!--__OVERLAP_STORY__-->", overlap_story(snapshot))
    page = page.replace("<!--__HOLDS_STORY__-->", holds_story(snapshot))
    summaries = descriptions(snapshot)
    page = page.replace(
        "<!--__METADATA__-->", metadata(entry, snapshot, base, summaries[entry])
    )
    page = page.replace("__ENTRY__", entry).replace("__DATE__", directory.name)
    nav = "".join(
        f'<a data-tab="{key}" href="{page_path(key)}">{label}</a>'
        for key, (_, label, _) in PAGES.items()
        if key != "home"
    )
    page = page.replace("<!--__NAV__-->", nav)
    for key in PAGES:
        page = page.replace(f"__VISIBLE_{key}__", "" if key == entry else "hidden")
        page = page.replace(f"<!--__SUMMARY_{key}__-->", escape(summaries[key]))
    for marker, source in [
        ("STYLE", "publication.css"),
        ("COVER", "cover.js"),
        ("ATLAS", "atlas.js"),
        ("SHARED_TRAITS", "shared-traits.js"),
        ("EXPLORER", "explorer.js"),
    ]:
        page = page.replace(f"/*__{marker}__*/", (SITE / source).read_text())
    symbols = []
    for asset in sorted((SITE / "icons").glob("*.svg")):
        drawing = asset.read_text().split(">", 1)[1].rsplit("</svg>", 1)[0]
        symbols.append(
            f'<symbol id="icon-{asset.stem}" viewBox="0 0 24 24">{drawing}</symbol>'
        )
    license_text = (SITE / "icons" / "LICENSE").read_text()
    sprite = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" aria-hidden="true" style="position:absolute"><desc>'
        + escape(license_text)
        + "</desc>"
        + "".join(symbols)
        + "</svg>"
    )
    page = page.replace("<!--__ICONS__-->", sprite)
    encoded = json.dumps(snapshot, separators=(",", ":")).replace("<", r"\u003c")
    return page.replace('"__EDITION_DATA__"', encoded)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edition")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    directory = Path("editions") / args.edition
    page = directory / "index.html"
    html = render(directory)
    if args.check:
        if page.read_text() != html:
            parser.exit(1, f"{page} needs rebuilding\n")
    else:
        page.write_text(html)
