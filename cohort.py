"""Collect one dated edition from OpenSea. Private cache contains wallet addresses."""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError

from pilot import get, traits

SLUGS = list(json.loads(Path(__file__).with_name("names.json").read_text()))


def now():
    return datetime.now(UTC).isoformat()


def collect(slug, kind):
    if kind == "traits":
        return {"rows": traits(slug)}
    if kind == "holders":
        addresses, cursors, top = set(), set(), []
        params = {"limit": 100}
        pages = 0
        while True:
            page = get(f"collections/{slug}/holders", **params)
            batch = [h["address"].lower() for h in page["holders"]]
            if not pages:
                top = batch
            addresses.update(batch)
            pages += 1
            cursor = page.get("next")
            if not cursor:
                break
            if cursor in cursors or pages >= 500:
                raise ValueError(f"Pagination did not terminate for {slug}")
            cursors.add(cursor)
            params["cursor"] = cursor
        return {"addresses": sorted(addresses), "top": top, "pages": pages}
    response = get(f"traits/{slug}")
    rows = []
    for category, values in response["counts"].items():
        if response["categories"].get(category) != "string":
            continue
        if category.strip().casefold() not in {
            "background",
            "background color",
            "backgrounds",
        }:
            continue
        for value, count in sorted(values.items()):
            filters = [{"traitType": category, "value": value}]
            items = get(f"collection/{slug}/nfts", traits=json.dumps(filters), limit=1)[
                "nfts"
            ]
            example = items[0] if items else {}
            rows.append(
                {
                    "category": category,
                    "value": value,
                    "count": count,
                    "url": example.get("opensea_url"),
                    "image": example.get("display_image_url"),
                }
            )
    return {"rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("edition")
    parser.add_argument("kind", choices=["holders", "palette", "traits"])
    args = parser.parse_args()
    directory = Path(".cache") / args.edition / args.kind
    directory.mkdir(parents=True, exist_ok=True)

    def one(slug):
        path = directory / (slug + ".json")
        if path.exists():
            return
        start = now()
        for attempt in range(3):
            try:
                data = collect(slug, args.kind)
                break
            except (TimeoutError, URLError) as error:
                if attempt == 2 or getattr(error, "code", None) in (400, 401, 403, 404):
                    raise
                time.sleep(2**attempt)
        data.update(start=start, finish=now())
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        tmp.replace(path)
        print(
            args.kind,
            slug,
            len(data.get("addresses", data.get("rows", []))),
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(one, SLUGS))


if __name__ == "__main__":
    main()
