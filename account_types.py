"""Classify shared addresses for the pilot triangle; bytecode cannot identify custodians."""

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

from diamond import rpc
from pilot import COLLECTIONS


def main(edition):
    directory = Path("editions") / edition
    snapshot = json.loads((directory / "autoglyphs.json").read_text())
    block = hex(snapshot["block"])
    info = rpc([("eth_chainId", []), ("eth_getBlockByNumber", [block, False])])
    if info[0] != "0x1" or info[1]["hash"] != snapshot["hash"]:
        raise ValueError("Wrong chain or block")
    cache = Path(".cache") / edition / "holders"
    sets = {
        s: set(json.loads((cache / (s + ".json")).read_text())["addresses"])
        for s in COLLECTIONS
    }
    pairs = {(a, b): sets[a] & sets[b] for a, b in itertools.combinations(sets, 2)}
    wallets = sorted(set.union(*pairs.values()))
    types = {}
    for offset in range(0, len(wallets), 50):
        batch = wallets[offset : offset + 50]
        codes = rpc([("eth_getCode", [w, block]) for w in batch])
        for wallet, code in zip(batch, codes, strict=True):
            if code == "0x":
                types[wallet] = "empty_code"
            elif code.startswith("0xef0100") and len(code) == 48:
                types[wallet] = "delegated"
            else:
                types[wallet] = "contract_code"
    rows = [
        {"a": a, "b": b, "counts": Counter(types[w] for w in pair)}
        for (a, b), pair in pairs.items()
    ]
    (directory / "account-types.json").write_text(
        json.dumps({"block": snapshot["block"], "pairs": rows}, indent=2) + "\n"
    )
    print(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("edition")
    main(parser.parse_args().edition)
