"""Build an edition's shared-trait artwork index from public NFT metadata."""

import argparse
import csv
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pilot import get


def key(category, value):
    return category.strip().lower(), value.strip().lower()


def targets(directory):
    labels = defaultdict(dict)
    with (directory / "traits.csv").open(newline="") as source:
        for row in csv.DictReader(source):
            labels[key(row["category"], row["value"])][row["slug"]] = (
                row["category"], row["value"]
            )
    collections = defaultdict(dict)
    for label, members in labels.items():
        if len(members) > 1:
            for slug, original in members.items():
                collections[slug][label] = original
    return collections


def collect(slug, labels):
    missing = set(labels)
    examples = []

    def inspect(items):
        for item in items:
            image = item.get("display_image_url") or item.get("image_url") or ""
            url = item.get("opensea_url") or ""
            if (item.get("collection") != slug or item.get("is_disabled")
                    or not image.startswith("https://") or not url.startswith("https://opensea.io/")):
                continue
            matches = sorted({
                key(t["trait_type"], t["value"]) for t in item.get("traits") or []
                if isinstance(t.get("value"), str) and isinstance(t.get("trait_type"), str)
            } & missing)
            if matches:
                examples.append({"token": item["identifier"], "url": url, "image": image, "traits": matches})
                missing.difference_update(matches)

    endpoint = f"collection/{slug}/nfts"
    inspect(get(endpoint, limit=50)["nfts"])
    for label in sorted(missing):
        if label in missing:
            category, value = labels[label]
            query = json.dumps([{"traitType": category, "value": value}])
            inspect(get(endpoint, traits=query, limit=4)["nfts"])
    print(f"{slug}: {len(labels) - len(missing)}/{len(labels)}", flush=True)
    return slug, examples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edition", type=Path)
    directory = parser.parse_args().edition
    collections = targets(directory)
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = [workers.submit(collect, slug, labels) for slug, labels in sorted(collections.items())]
        result = dict(future.result() for future in futures)
    path = directory / "trait-examples.json"
    staged = path.with_suffix(".tmp")
    staged.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    staged.replace(path)


if __name__ == "__main__":
    main()
