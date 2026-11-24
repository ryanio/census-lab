"""Render a standalone Census edition from its checked-in CSV and JSON records."""

import argparse
import csv
import json
from pathlib import Path

SITE = Path(__file__).parent / "site"


def read_csv(path):
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def render(directory):
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
    snapshot = {
        "edition": directory.name,
        "names": {slug: names[slug] for slug in cohort},
        "pairs": pairs,
        "colors": colors,
        "diamond": json.loads((directory / "autoglyphs.json").read_text()),
    }
    page = (SITE / "template.html").read_text()
    for marker, source in [
        ("STYLE", "publication.css"),
        ("COVER", "cover.js"),
        ("EXPLORER", "explorer.js"),
    ]:
        page = page.replace(f"/*__{marker}__*/", (SITE / source).read_text())
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
