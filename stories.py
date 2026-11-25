"""Render edition-specific findings from the records used by each explorer."""

from datetime import date
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
    ranked = sorted(data["pairs"], key=lambda row: row["top100_shared"], reverse=True)
    leader = ranked[0]
    first, second = (escape(data["names"][leader[side]]) for side in ("a", "b"))
    leaders = (f'The top-holder lists tell a different part of the story. {first} and {second} '
               f'share {leader["top100_shared"]:,} addresses among their respective top 100, '
               'the highest count in the sample.')
    return (
        '<article class="finding"><h2>One pair, two percentages</h2>'
        f'<p>{a} and {b} share {p["shared"]:,} addresses, the largest raw overlap in this edition. '
        'Start from either side and the count stays the same. The percentage changes because each collection has a different holder population.</p>'
        + "".join(rows)
        + f'<p class="story-end">{leaders}</p></article>'
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
    returns = [(series, row) for series in data["holdings"].values()
               for row in series["rows"] if row["returned"]]
    homecoming = f"{len(returns):,} works returned to their mint recipient after leaving."
    if len(returns) == 1:
        series, row = returns[0]
        day = date.fromisoformat(row["since"][:10])
        url = "https://etherscan.io/tx/" + escape(row["transaction"])
        homecoming = (
            f'One square has a round trip behind it. {escape(series["name"])} #{row["token"]} '
            f'<a href="{url}">returned to its mint address</a> on {day:%B} {day.day}, {day.year}. '
            'Its current hold starts with that return.'
        )
    return (
        '<article class="finding"><h2>Who kept the original?</h2>'
        '<p>Each square is one artwork, ordered by token number. Dark squares stayed at their mint-recipient address through the snapshot. '
        'Pale squares changed addresses at least once, even if the work eventually came back.</p>'
        '<div class="hold-fields">' + "".join(figures) + f'</div><p class="story-end">{homecoming}</p></article>'
    )
