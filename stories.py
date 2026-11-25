"""Render edition-specific findings from the records used by each explorer."""

from html import escape


def overlap_story(data):
    p = max(data["pairs"], key=lambda pair: pair["shared"])
    a, b = (escape(data["names"][p[key]]) for key in ("a", "b"))
    rows = []
    for side, name in (("a", a), ("b", b)):
        share = p[f"pct_{side}"]
        rows.append(
            f'<div class="share-line"><img alt="" src="{data["portraits"].get(p[side], "")}">'
            f'<span>{name}<small>{p[f"holders_{side}"]:,} holder addresses</small></span>'
            f'<b>{share:g}%</b><meter min="0" max="100" value="{share}" aria-label="{name} overlap"></meter></div>'
        )
    return (
        '<article class="finding"><h2>One pair, two percentages</h2>'
        f'<p>{a} and {b} share {p["shared"]:,} addresses, the largest raw overlap in this edition. '
        'Start from either side and the count stays the same. The percentage changes because each collection has a different holder population.</p>'
        + "".join(rows)
        + f'<p class="note">Read the bars as shares of each holder population. A shared address can be a person, a vault or a custodian.</p>' + '</article>'
    )


def holds_story(data):
    figures = []
    for series in data["holdings"].values():
        rows = sorted(series["rows"], key=lambda row: row["token"])
        count = sum(r["continuous"] for r in rows)
        dots = "".join('<i class="kept"></i>' if r["continuous"] else "<i></i>" for r in rows)
        figures.append(
            f'<figure><figcaption><b>{escape(series["name"])}</b> {count:,} of {len(rows):,} stayed</figcaption>'
            f'<div class="token-field" aria-hidden="true">{dots}</div></figure>'
        )
    returned = sum(row["returned"] for series in data["holdings"].values() for row in series["rows"])
    homecoming = (
        "One work returned to its mint recipient after leaving."
        if returned == 1 else f"{returned:,} works returned to their mint recipient after leaving."
    )
    return (
        '<article class="finding"><h2>Who kept the original?</h2>'
        '<p>Each square is one artwork, ordered by token number. Dark squares stayed at their mint-recipient address through the snapshot. '
        'Pale squares changed addresses at least once, even if the work eventually came back.</p>'
        '<div class="hold-fields">' + "".join(figures) + f'</div><p class="note">{homecoming} The transfer history distinguishes a homecoming from an unbroken hold.</p></article>'
    )
