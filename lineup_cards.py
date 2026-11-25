"""Build crawler-readable GitHub Pages links for the edition's shuffle choices."""
import hashlib
import io
import json
import random
import sys
import zipfile
from collections import defaultdict
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from html.parser import HTMLParser

from discovery import ROOT


class PublishedLineup(HTMLParser):
    target = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("id") == "open":
            self.target = attrs.get("href")


def featured(edition):
    result = defaultdict(list)
    for path in Path("site/assets/lineups", edition).glob("*/index.html"):
        parser = PublishedLineup()
        parser.feed(path.read_text())
        params = parse_qs(urlsplit(parser.target).query)
        result[params["category"][0], params["trait"][0]].append(params["tokens"][0].split("."))
    return result


def variants(edition, examples):
    groups = defaultdict(lambda: defaultdict(list))
    for slug, tokens in examples.items():
        for token in tokens:
            for category, label in token["traits"]:
                groups[category, label][slug].append(token["token"])
    result = {}
    published = featured(edition)
    for (category, label), members in groups.items():
        key = json.dumps([category, label], ensure_ascii=False, separators=(",", ":"))
        short = hashlib.sha256(key.encode()).hexdigest()[:12]
        rng = random.Random(edition + short)
        pools = []
        for slug in sorted(members):
            first, *rest = members[slug]
            rng.shuffle(rest)
            pools.append([first, *rest])
        choices = [[pool[i % len(pool)] for pool in pools] for i in range(max(map(len, pools)))]
        for ids in published[category, label]:
            if len(ids) == len(pools) and all(token in pool for token, pool in zip(ids, pools)) and ids not in choices:
                choices.append(ids)
        rounds = []
        for ids in choices:
            signature = hashlib.sha256(".".join(ids).encode()).hexdigest()[:12]
            rounds.append({"ids": ids, "path": short + "/" + signature})
        result[key] = {"slugs": sorted(members), "rounds": rounds}
    return result


def landing(title, description, canonical, target):
    title, description, url, target = map(escape, (title, description, canonical, target))
    image = url + "card.jpg"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<meta property="og:type" content="website"><meta property="og:url" content="{url}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{description}">
<meta property="og:image" content="{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}"><meta name="twitter:image:alt" content="{description}"></head>
<body><a href="{target}" id="open">Open {title}</a><script>location.replace(document.getElementById("open").href)</script></body></html>'''


def build(directory, out):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    from contextlib import ExitStack
    examples = json.loads((directory / "trait-examples.json").read_text())
    names = json.loads(Path("names.json").read_text())
    edition = directory.name
    fonts = [ImageFont.load_default(size=size) for size in (22, 45, 17)]
    with ExitStack() as stack:
        archives = {slug: stack.enter_context(zipfile.ZipFile(directory / "lineup-art" / (slug + ".zip"))) for slug in examples}
        for slug, tokens in examples.items():
            for token in tokens:
                if token["image"].split("?")[0].lower().endswith((".mp4", ".webm")):
                    path = out / directory / "stills" / slug / (token["token"] + ".webp")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archives[slug].read(path.name))
        @lru_cache(maxsize=512)
        def tile(slug, token):
            return Image.open(io.BytesIO(archives[slug].read(token + ".webp"))).convert("RGB")
        for key, group in variants(edition, examples).items():
            category, value = json.loads(key)
            slugs = group["slugs"]
            order = sorted(range(len(slugs)), key=lambda i: (names[slugs[i]].lower(), slugs[i]))
            for variant in group["rounds"]:
                ids = variant["ids"]
                for expanded in ([False, True] if len(slugs) > 6 else [False]):
                    visible = order if expanded else order[:6]
                    rel = variant["path"] + ("/all" if expanded else "")
                    dest = out / directory / "lineups" / rel
                    dest.mkdir(parents=True, exist_ok=True)
                    canvas = Image.new("RGB", (1200, 630), "#f4e6d7")
                    draw = ImageDraw.Draw(canvas)
                    draw.text((34, 16), "Census   /   Trait studies", fill="#493523", font=fonts[0])
                    draw.text((32, 44), value.title(), fill="#302013", font=fonts[1])
                    cols = min(len(visible), 3 if len(visible) <= 6 else max(4, round((len(visible)*1.9)**.5)))
                    rows = (len(visible) + cols - 1) // cols
                    side = min(389, 1150 // cols - 8, 518 // rows - 27)
                    for pos,i in enumerate(visible):
                        row, col = divmod(pos, cols)
                        ncol = min(cols, len(visible) - row * cols)
                        x = (1200 - ncol*(side+10)+10)//2 + col*(side+10)
                        y = 102 + row*(side+27)
                        canvas.paste(ImageOps.contain(tile(slugs[i],ids[i]), (side,side)), (x,y))
                        caption = names[slugs[i]]
                        if draw.textlength(caption, font=fonts[2]) > side:
                            caption = "#" + ids[i]
                        draw.text((x,y+side+2), caption, font=fonts[2], fill="#302013")
                    canvas.save(dest/"card.jpg", quality=73)
                    route = ROOT + directory.as_posix() + "/"
                    query = {"category":category,"trait":value,"tokens":".".join(ids)}
                    if expanded: query["all"] = "1"
                    (dest/"index.html").write_text(landing(value.title()+" · Census", f"{len(visible)} PFPs with the {value} trait. Open the lineup to explore each token.", route+"lineups/"+rel+"/", route+"traits.html?"+urlencode(query)))


if __name__ == "__main__":
    for edition in Path("editions").glob("*/lineup-art"):
        build(edition.parent, Path(sys.argv[1]))
