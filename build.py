"""Build a self-contained edition and CSVs from completed crawls."""

import argparse
import csv
import itertools
import json
from pathlib import Path

from cohort import SLUGS


def load(path):
    return json.loads(path.read_text())


def write_csv(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(edition):
    cache = Path(".cache") / edition
    output = Path("editions") / edition
    names = load(Path("names.json"))
    holder_data = {slug: load(cache / "holders" / (slug + ".json")) for slug in SLUGS}
    holders = {slug: set(batch["addresses"]) for slug, batch in holder_data.items()}
    pairs = []
    for a, b in itertools.combinations(SLUGS, 2):
        shared = len(holders[a] & holders[b])
        pairs.append(
            {
                "a": a,
                "b": b,
                "shared": shared,
                "holders_a": len(holders[a]),
                "holders_b": len(holders[b]),
                "pct_a": round(100 * shared / len(holders[a]), 2),
                "pct_b": round(100 * shared / len(holders[b]), 2),
                "top100_shared": len(
                    set(holder_data[a]["top"]) & set(holder_data[b]["top"])
                ),
            }
        )
    palette = {s: load(cache / "palette" / (s + ".json")) for s in SLUGS}
    colors = [
        dict(slug=s, **row) for s, batch in palette.items() for row in batch["rows"]
    ]
    diamond = load(output / "autoglyphs.json")
    windows = [
        {
            "slug": s,
            "holder_start": b["start"],
            "holder_finish": b["finish"],
            "pages": b["pages"],
            "holders": len(holders[s]),
            "palette_start": palette[s]["start"],
            "palette_finish": palette[s]["finish"],
        }
        for s, b in holder_data.items()
    ]
    write_csv(output / "coverage.csv", windows)
    write_csv(output / "overlap.csv", pairs)
    write_csv(output / "backgrounds.csv", colors)
    write_csv(output / "holds.csv", diamond["rows"])
    data = {
        "edition": edition,
        "names": names,
        "pairs": pairs,
        "colors": colors,
        "diamond": diamond,
    }
    encoded = json.dumps(data, separators=(",", ":")).replace("<", r"\u003c")
    page = Path("template.html").read_text().replace('"__EDITION_DATA__"', encoded)
    (output / "index.html").write_text(page)
    print(
        len(pairs),
        "pairs,",
        len(colors),
        "labels,",
        len(diamond["rows"]),
        "verified tokens",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("edition")
    build(parser.parse_args().edition)
