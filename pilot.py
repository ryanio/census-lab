"""Run the three bounded Ethereum ERC-721 pilots using the public OpenSea API."""
import itertools
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

COLLECTIONS = {
    "azuki": "0xed5af388653567af2f388e6224dc7c4b3241c544",
    "doodles-official": "0x8a90cab2b38dba80c64b7734e58ee1db38b8992e",
    "pudgypenguins": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
}


def get(path, **params):
    url = "https://api.opensea.io/api/v2/" + path
    if params:
        url += "?" + urlencode(params, doseq=True)
    request = Request(url, headers={
        "x-api-key": os.environ["OPENSEA_API_KEY"], "User-Agent": "census-lab/0.1",
    })
    for attempt in range(4):
        time.sleep(0.2)
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if attempt == 3 or error.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(max(2 ** attempt, int(error.headers.get("Retry-After") or 0)))


def overlap():
    cohorts = {}
    for slug in COLLECTIONS:
        page = get(f"collections/{slug}/holders", limit=100)
        cohorts[slug] = {row["address"].lower() for row in page["holders"]}
    return [
        {"a": a, "b": b, "addresses_a": len(left), "addresses_b": len(right),
         "shared": len(left & right)}
        for (a, left), (b, right) in itertools.combinations(cohorts.items(), 2)
    ]


def traits(slug):
    traits = get(f"traits/{slug}")
    listings = get(f"traits/{slug}/floors")
    floors = {}
    for row in listings["floors"]:
        key = row["trait_type"], row["value"]
        floors.setdefault(key, {})[row["payment_token_symbol"]] = row["floor_price"]
    return [
        {"category": category, "value": value, "count": count,
         "chain": listings["chain"], "floors": floors.get((category, value), {})}
        for category, values in sorted(traits["counts"].items())
        if traits["categories"][category] == "string"
        for value, count in sorted(values.items())
    ]


def hold(contract, token):
    path = f"chain/ethereum/contract/{contract}/nfts/{token}"
    nft = get(path)["nft"]
    result = {"token": token, "url": nft["opensea_url"], "status": "unknown"}
    owners = nft.get("owners") or []
    if nft["token_standard"] != "erc721" or len(owners) != 1:
        return result
    owner = owners[0]["address"].lower()
    page = get("events/" + path, event_type=["transfer", "sale"], limit=50)
    moves = []
    for event in page["asset_events"]:
        source, target = ((event["seller"], event["buyer"]) if event["event_type"] == "sale"
                          else (event["from_address"], event["to_address"]))
        if source.lower() != target.lower():
            moves.append((event["event_timestamp"], target.lower(), event.get("transfer_type")))
    if moves:
        latest = max(row[0] for row in moves)
        recipients = {dest for ts, dest, _ in moves if ts == latest}
        if recipients == {owner} and (not page.get("next") or latest > min(
            event["event_timestamp"] for event in page["asset_events"]
        )):
            result.update(status="owner matches latest indexed move",
                          since_utc=datetime.fromtimestamp(latest, timezone.utc).date().isoformat(),
                          mint_at_latest=any(ts == latest and kind == "mint" for ts, _, kind in moves))
    return result


def main():
    started = datetime.now(timezone.utc).isoformat()
    snapshot = {"started_utc": started, "top_100_overlap": overlap(),
                "traits": {slug: traits(slug) for slug in COLLECTIONS},
                "holds": {slug: [hold(contract, token) for token in (1, 2, 3)]
                          for slug, contract in COLLECTIONS.items()}}
    snapshot["finished_utc"] = datetime.now(timezone.utc).isoformat()
    path = Path(__file__).with_name("pilot-results.json")
    path.write_text(json.dumps(snapshot, indent=2) + "\n")


if __name__ == "__main__":
    main()
