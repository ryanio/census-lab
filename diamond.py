"""Reconstruct ERC-721 address tenures at a finalized block."""

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pilot import get

CONTRACT = "0xd4e4078ca3495de5b1d4db434bebc5a986197782"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40


def request(url, body=None):
    for attempt in range(5):
        try:
            req = Request(
                url,
                data=json.dumps(body).encode() if body else None,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "census-lab",
                },
            )
            with urlopen(req, timeout=45) as response:
                return json.load(response)
        except HTTPError as err:
            if attempt == 4 or err.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"Provider HTTP {err.code}") from None
            time.sleep(2**attempt)


def rpc(calls):
    url = "https://eth-mainnet.g.alchemy.com/v2/" + os.environ["ALCHEMY_API_KEY"]
    responses = request(
        url,
        [
            {"id": i, "jsonrpc": "2.0", "method": m, "params": p}
            for i, (m, p) in enumerate(calls)
        ],
    )
    by_id = {r["id"]: r for r in responses}
    if any("result" not in by_id[i] for i in range(len(calls))):
        raise RuntimeError("RPC read failed")
    return [by_id[i]["result"] for i in range(len(calls))]


def logs(end, contract):
    page = 1
    while True:
        query = {
            "chainid": 1,
            "module": "logs",
            "action": "getLogs",
            "address": contract,
            "topic0": TRANSFER,
            "fromBlock": 0,
            "toBlock": end,
            "page": page,
            "offset": 1000,
            "apikey": os.environ["ETHERSCAN_API_KEY"],
        }
        for attempt in range(5):
            reply = request("https://api.etherscan.io/v2/api?" + urlencode(query))
            if reply["status"] == "1" or reply.get("message") == "No records found":
                break
            if "rate limit" not in str(reply["result"]).lower() or attempt == 4:
                raise RuntimeError(
                    "Explorer rejected log query: " + str(reply["message"])
                )
            time.sleep(2**attempt)
        rows = reply["result"]
        yield from rows
        if len(rows) < 1000:
            return
        page += 1
        time.sleep(0.5)


def replay(rows, contract=CONTRACT):
    state = {}
    seen = set()
    for row in sorted(
        rows,
        key=lambda r: (int(r["blockNumber"], 16), int(r["logIndex"][2:] or "0", 16)),
    ):
        key = row["blockNumber"], row["logIndex"]
        if (
            key in seen
            or row["address"].lower() != contract
            or row["topics"][0] != TRANSFER
        ):
            raise ValueError("Duplicate or unexpected log")
        seen.add(key)
        _, sender, recipient, token = row["topics"]
        sender, recipient = "0x" + sender[-40:], "0x" + recipient[-40:]
        token = int(token, 16)
        old = state.get(token)
        if (old["owner"] if old else ZERO) != sender:
            raise ValueError(f"Broken ownership history for {token}")
        if sender == recipient:
            continue
        state[token] = {
            "owner": recipient,
            "original": old["original"] if old else recipient,
            "continuous": old is None,
            "since": int(row["timeStamp"], 16),
            "transaction": row["transactionHash"],
        }
    return {t: v for t, v in state.items() if v["owner"] != ZERO}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--contract", default=CONTRACT, type=str.lower)
    parser.add_argument("--block", type=int)
    args = parser.parse_args()
    contract = args.contract
    if rpc([("eth_chainId", [])])[0] != "0x1":
        raise ValueError("Ethereum mainnet required")
    block = rpc([("eth_getBlockByNumber", ["finalized", False])])[0]
    if args.block is not None:
        if not 0 <= args.block <= int(block["number"], 16):
            raise ValueError("Block must be finalized")
        block = rpc([("eth_getBlockByNumber", [hex(args.block), False])])[0]
    height = block["number"]
    events = list(logs(int(height, 16), contract))
    state = replay(events, contract)

    def call(data):
        return "eth_call", [{"to": contract, "data": data}, height]

    supply = int(rpc([call("0x18160ddd")])[0], 16)
    tokens = sorted(state)
    if len(tokens) != supply or not supply:
        raise ValueError("Supply mismatch")
    for start in range(0, supply, 50):
        group = tokens[start : start + 50]
        owners = rpc([call(f"0x6352211e{t:064x}") for t in group])
        if any(
            int(owner, 16) != int(state[t]["owner"], 16)
            for t, owner in zip(group, owners)
        ):
            raise ValueError("ownerOf mismatch")
    rows = []
    for token in tokens:
        v = state[token]
        rows.append(
            {
                "token": token,
                "since": datetime.fromtimestamp(v["since"], UTC).isoformat(),
                "continuous": v["continuous"],
                "returned": v["owner"] == v["original"] and not v["continuous"],
                "transaction": v["transaction"],
            }
        )
    sample = {}
    for token in tokens[:3]:
        owners = get(f"chain/ethereum/contract/{contract}/nfts/{token}")["nft"][
            "owners"
        ]
        sample[token] = (
            len(owners) == 1 and owners[0]["address"].lower() == state[token]["owner"]
        )
    result = {
        "contract": contract,
        "block": int(height, 16),
        "hash": block["hash"],
        "timestamp": int(block["timestamp"], 16),
        "supply": supply,
        "logs": len(events),
        "indexed_owner_matches": sample,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        result["block"], supply, len(events), sum(r["continuous"] for r in rows), sample
    )


if __name__ == "__main__":
    main()
