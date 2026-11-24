# Census lab

Three pilots for future editions of [PFP Census](https://ryanio.github.io/pfp-census/) and [Card Census](https://ryanio.github.io/card-census/). Each edition can have its own site, share cards and CSV downloads. This repo holds the shared collector and a dated [pilot snapshot](pilot-results.json).

## November 24 pilot

The sample covers Azuki, Doodles and Pudgy Penguins on Ethereum. Run `python3 pilot.py` with `OPENSEA_API_KEY` in the environment to replace the snapshot. Python's standard library is sufficient. The run makes 27 requests before retries and records its UTC start and finish times.

| Edition | First observation | Coverage |
| --- | --- | --- |
| Community overlap | Azuki and Pudgy Penguins shared 5 addresses, Doodles and Pudgy Penguins shared 3, and Azuki and Doodles shared 2. | First 100 holder addresses per collection, ordered by holdings. Custodial and contract wallets included. |
| Trait census | The most frequent background in each collection was Off White D for Azuki (1,990), green for Doodles (748) and Blue for Pudgy Penguins (1,587). | 892 collection-specific text category/value pairs. An empty floors object means no matching listed floor in the response. Floors are asking prices grouped by chain and currency. |
| Diamond hands | Doodle #2 had the earliest latest indexed move in the sample, June 24, 2022. | Token IDs 1, 2 and 3 from each contract. All nine current owner addresses matched the latest indexed change of address. This convenience sample cannot establish a collection record or a minter retention rate. |

## Proposed next round

1. **Community overlap map.** Finish paging the same three holder lists, then expand to 25 collections. Show shared addresses and the percentage of each collection's holders they represent. Compare neighbor rankings against the top-100 pilot. Identify custody and staking contracts before interpreting a shared address as a collector. Prototype a clickable map with a share card for each collection's closest neighbors.
2. **Trait census.** Build a background palette from the same 25 collections. Size each swatch by NFT count and show the original label and an example NFT when selected. Preserve exact labels in the CSV. Review aliases before grouping colors across collections. Look up listing depth and observation time before featuring a high floor.
3. **Diamond hands census.** Reconstruct ERC-721 transfer histories for one full collection from onchain logs. Reconcile live supply and owners at one block, handle burns and remints, and distinguish a continuous hold since mint from a token that returned to its first owner. Compare a sample to the API. Show a holding-duration distribution, the longest verified holds and the fraction still at their original mint-recipient address. Report unresolved histories separately.

After the methods hold up, package each edition as a static site with dated CSVs and per-collection share pages. Decide on refresh frequency from measured crawl cost and keep publication as a separate decision.
