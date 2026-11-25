"""Package dated editions and put the newest one at the Pages project root."""

import argparse
import shutil
from datetime import date
from pathlib import Path

from discovery import PAGES, ROOT, page_path
from render import SITE, render

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
    shutil.copytree(SITE / "assets", destination / "assets")
    urls = []
    for edition in editions:
        date.fromisoformat(edition.name)
        archive = destination / edition
        archive.mkdir(parents=True)
        for name in ASSETS:
            shutil.copyfile(edition / name, archive / name)
            if edition == editions[-1]:
                shutil.copyfile(edition / name, destination / name)
        base = ROOT if edition == latest else ROOT + edition.as_posix() + "/"
        for entry in PAGES:
            name = page_path(entry) or "index.html"
            html = render(edition, entry, base, standalone=False)
            (archive / name).write_text(html)
            if edition == latest:
                (destination / name).write_text(html)
            urls.append(base + page_path(entry))
    entries = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    (destination / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + entries
        + "</urlset>\n"
    )
    (destination / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    package(parser.parse_args().destination)
