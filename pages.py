"""Package dated editions and put the newest one at the Pages project root."""

import argparse
import shutil
from datetime import date
from pathlib import Path

from render import render

ASSETS = (
    "index.html",
    "backgrounds.csv",
    "coverage.csv",
    "holds.csv",
    "overlap.csv",
    "account-types.json",
    "autoglyphs.json",
    "deafbeef.json",
    "deafbeef-holds.csv",
    "traits.csv",
)


def package(destination):
    editions = sorted(path.parent for path in Path("editions").glob("*/index.html"))
    if not editions:
        raise ValueError("No editions to publish")
    latest = editions[-1]
    if (latest / "index.html").read_text() != render(latest):
        raise ValueError(f"Rebuild {latest} before packaging")
    destination.mkdir(parents=True, exist_ok=False)
    for edition in editions:
        date.fromisoformat(edition.name)
        archive = destination / edition
        archive.mkdir(parents=True)
        for name in ASSETS:
            shutil.copyfile(edition / name, archive / name)
            if edition == editions[-1]:
                shutil.copyfile(edition / name, destination / name)
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    package(parser.parse_args().destination)
