"""Regenerate publication artwork with librsvg (rsvg-convert)."""

import base64
import math
import subprocess
from pathlib import Path

SITE = Path(__file__).parent / "site"
OUT = SITE / "assets"
PALETTE = ["#cbb3ff", "#9681e0", "#85cac5", "#efaa88", "#dbd89b"]


def raster(svg, path, width, height):
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(path)],
        input=svg.encode(),
        check=True,
    )


def art(key):
    if key == "traits":
        tiles = []
        for i, slug in enumerate(
            [
                "azuki",
                "mfers",
                "doodles-official",
                "pudgypenguins",
                "boredapeyachtclub",
                "milady",
                "cool-cats-nft",
                "deadfellaz",
                "moonbirds",
            ]
        ):
            pic = base64.b64encode(
                (SITE / "portraits" / (slug + ".webp")).read_bytes()
            ).decode()
            tiles.append(
                f'<image x="{727 + (i % 3) * 136}" y="{115 + (i // 3) * 136}" width="131" height="131" xlink:href="data:image/webp;base64,{pic}"/>'
            )
        return "".join(tiles)
    if key == "hands":
        return "".join(
            f'<rect x="{734 + x * 21}" y="{120 + y * 21}" width="16" height="16" fill="{["#365846", "#8da684", "#c6edac"][(x * x + y * y + x * y) % 3]}"/>'
            for x in range(19)
            for y in range(19)
        )
    parts = []

    def point(angle, r):
        return f"{935 + r * math.cos(angle):.2f} {321 + r * math.sin(angle):.2f}"

    for i in range(60):
        a = 2 * math.pi * i / 60
        b = a + 1.6 + 0.9 * math.sin(i * 0.22)
        parts.append(
            f'<path d="M{point(a, 190)} Q935 321 {point(b, 190)}" stroke="{PALETTE[i % 5]}" stroke-width="{2 + i % 6}" fill="none" opacity=".72"/>'
        )
    for r in [194, 205, 228]:
        parts.append(
            f'<circle cx="935" cy="321" r="{r}" stroke="#91859d" stroke-width="1" fill="none"/>'
        )
    return "".join(parts)


def main():
    favicon = (OUT / "favicon.svg").read_text()
    for size, name in [(48, "favicon.png"), (180, "apple-touch-icon.png")]:
        raster(favicon, OUT / name, size, size)
    covers = {
        "home": ("Who holds", "what?", "Field studies of Ethereum NFTs."),
        "overlap": ("Community", "overlap", "Which collections share holders?"),
        "traits": ("Trait", "studies", "Explore rarity and listed floors."),
        "hands": ("Diamond", "hands", "How long has each wallet held its NFT?"),
    }
    for key, (first, second, sub) in covers.items():
        color = {"traits": "#f2b895", "hands": "#c6edac"}.get(key, "#cbb3ff")
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="630">
        <rect width="1200" height="630" fill="#19171e"/><path d="M66 98H1134M66 546H1134" stroke="#58515d"/>
        <text x="66" y="68" fill="#f4f1e9" font-family="Georgia,serif" font-style="italic" font-size="40">Census</text>
        <text x="66" y="265" fill="#f4f1e9" font-family="Georgia,serif" font-size="102">{first}</text>
        <text x="66" y="375" fill="{color}" font-family="Georgia,serif" font-style="italic" font-size="117">{second}</text>
        <text x="70" y="460" fill="#ddd6dd" font-family="Arial,sans-serif" font-size="29">{sub}</text>
        {art(key)}<text x="68" y="593" font-family="monospace" font-size="20" fill="#c9c3ce">Ethereum field studies  /  Ryan Ghods</text></svg>'''
        raster(svg, OUT / (key + ".png"), 1200, 630)


if __name__ == "__main__":
    main()
