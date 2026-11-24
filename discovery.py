"""Publish stable page identities and first-party dataset citations."""

import json
from html import escape

ROOT = "https://ryanio.github.io/census-lab/"
PAGES = {
    "home": ("Census | Ethereum NFT field studies", "Home", ()),
    "overlap": (
        "NFT holder overlap map | Census",
        "Overlap map",
        ("overlap.csv", "coverage.csv"),
    ),
    "traits": (
        "NFT trait frequencies and listing floors | Census",
        "Traits",
        ("traits.csv", "backgrounds.csv"),
    ),
    "hands": (
        "Diamond hands: NFT holding histories | Census",
        "Diamond hands",
        ("holds.csv", "deafbeef-holds.csv"),
    ),
}
AUTHOR = {
    "@type": "Person",
    "name": "Ryan Ghods",
    "url": "https://ryanio.com/",
    "sameAs": ["https://x.com/r_alx_z", "https://github.com/ryanio"],
}


def page_path(entry):
    return "" if entry == "home" else entry + ".html"


def descriptions(data):
    names = data["names"]
    strongest = max(data["pairs"], key=lambda p: p["shared"])
    traits = sum(
        len(values) for groups in data["traits"].values() for values in groups.values()
    )
    holds = list(data["holdings"].values())
    return {
        "home": f"Explore holder overlap across {len(names)} Ethereum NFT collections, trait frequencies and listing floors, and onchain holding histories. Field studies by Ryan Ghods.",
        "overlap": f"Across {len(data['pairs']):,} NFT collection pairs, {names[strongest['a']]} and {names[strongest['b']]} share the most holder addresses ({strongest['shared']:,}).",
        "traits": f"Explore {traits:,} text trait values across {len(names)} Ethereum NFT collections. Compare rare and common traits, listed ETH floors, and illustrated backgrounds.",
        "hands": f"Of {sum(series['supply'] for series in holds):,} verified tokens across {' and '.join(series['name'] for series in holds)}, {sum(r['continuous'] for series in holds for r in series['rows'])} have stayed at their mint-recipient address continuously.",
    }


def metadata(entry, data, base, description):
    title, _, files = PAGES[entry]
    url = base + page_path(entry)
    image = ROOT + "assets/" + entry + ".png"
    date = data["edition"]
    graph = [
        {
            "@type": "WebSite",
            "@id": ROOT + "#website",
            "url": ROOT,
            "name": "Census",
            "creator": AUTHOR,
        }
    ]
    page = {
        "@type": "CollectionPage" if entry == "home" else "WebPage",
        "@id": url + "#page",
        "url": url,
        "name": title,
        "description": description,
        "inLanguage": "en",
        "isPartOf": {"@id": ROOT + "#website"},
        "image": image,
        "author": AUTHOR,
    }
    graph.append(page)
    if files:
        dataset = {
            "@type": "Dataset",
            "@id": url + "#dataset",
            "url": url,
            "name": title.split(" | ")[0] + " (" + date + ")",
            "description": description,
            "datePublished": date,
            "creator": AUTHOR,
            "distribution": [
                {
                    "@type": "DataDownload",
                    "contentUrl": ROOT + "editions/" + date + "/" + file,
                    "encodingFormat": "text/csv",
                    "name": file,
                }
                for file in files
            ],
        }
        page["mainEntity"] = {"@id": dataset["@id"]}
        graph.append(dataset)
    else:
        page["hasPart"] = [
            {"@type": "WebPage", "url": base + page_path(key), "name": PAGES[key][0]}
            for key in PAGES
            if key != "home"
        ]
    tags = [
        f"<title>{escape(title)}</title>",
        f'<link rel="sitemap" type="application/xml" href="{ROOT}sitemap.xml">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="icon" type="image/svg+xml" href="{ROOT}assets/favicon.svg">',
        f'<link rel="icon" type="image/png" sizes="48x48" href="{ROOT}assets/favicon.png">',
        f'<link rel="apple-touch-icon" sizes="180x180" href="{ROOT}assets/apple-touch-icon.png">',
    ]
    properties = {
        "og:type": "website",
        "og:site_name": "Census",
        "og:locale": "en_US",
        "og:title": title,
        "og:description": description,
        "og:url": url,
        "og:image": image,
        "og:image:type": "image/png",
        "og:image:width": "1200",
        "og:image:height": "630",
        "og:image:alt": title,
    }
    for key, value in properties.items():
        tags.append(f'<meta property="{key}" content="{escape(value, quote=True)}">')
    for key, value in {
        "description": description,
        "author": AUTHOR["name"],
        "theme-color": "#19171e",
        "robots": "max-image-preview:large",
        "twitter:card": "summary_large_image",
        "twitter:creator": "@r_alx_z",
        "twitter:title": title,
        "twitter:description": description,
        "twitter:image": image,
        "twitter:image:alt": title,
    }.items():
        tags.append(f'<meta name="{key}" content="{escape(value, quote=True)}">')
    payload = json.dumps(
        {"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False
    ).replace("<", r"\u003c")
    tags.append(f'<script type="application/ld+json">{payload}</script>')
    return "\n".join(tags)
