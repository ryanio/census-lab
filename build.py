"""Build a self-contained edition and CSVs from completed crawls."""

import argparse
import csv
import itertools
import json
from pathlib import Path

from cohort import SLUGS
from render import HOLD_COLLECTIONS, render


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
    traits = {s: load(cache / "traits" / (s + ".json")) for s in SLUGS}
    trait_rows = [
        {"slug": s, **row, "floors": json.dumps(row["floors"], separators=(",", ":"))}
        for s, batch in traits.items()
        for row in batch["rows"]
    ]
    write_csv(output / "traits.csv", trait_rows)
    verified = 0
    for slug in HOLD_COLLECTIONS:
        series = load(output / f"{slug}.json")
        verified += series["supply"]
        filename = "holds.csv" if slug == "autoglyphs" else f"{slug}-holds.csv"
        write_csv(output / filename, series["rows"])
    windows = [
        {
            "slug": s,
            "holder_start": b["start"],
            "holder_finish": b["finish"],
            "pages": b["pages"],
            "holders": len(holders[s]),
            "traits_start": traits[s]["start"],
            "traits_finish": traits[s]["finish"],
            "palette_start": palette[s]["start"],
            "palette_finish": palette[s]["finish"],
        }
        for s, b in holder_data.items()
    ]
    write_csv(output / "coverage.csv", windows)
    write_csv(output / "overlap.csv", pairs)
    write_csv(output / "backgrounds.csv", colors)
    (output / "index.html").write_text(render(output))
    print(
        len(pairs),
        "pairs,",
        len(colors),
        "labels,",
        verified,
        "verified tokens",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("edition")
    build(parser.parse_args().edition)
