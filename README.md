# Census

One monorepo and one GitHub Pages site for future census editions. The shared header opens Community overlap, Trait census and Diamond hands. [PFP Census](https://ryanio.github.io/pfp-census/) and [Card Census](https://ryanio.github.io/card-census/) stay on their existing sites.

## November 24 edition

Open [the local edition](editions/2026-11-24/index.html) in a browser. Its homepage opens all three editions and each selected collection has its own URL fragment. The data and charts work offline. Example artwork loads from OpenSea's image CDN.

| Edition | Result |
| --- | --- |
| Community overlap | Of 1,225 pairs, Mutant Ape Yacht Club and Bored Ape Kennel Club shared the most addresses (2,872). These were 23.50% of Mutant Ape holders and 55.76% of Kennel Club holders. Among the original three, Azuki and Doodles went from last in the top-100 pilot (2) to first across the full lists (512). Azuki and Pudgy Penguins shared 335, Doodles and Pudgy Penguins 290. |
| Trait census | 38,900 collection-specific text trait values across 50 collections. Explore rare and common values or rank listed ETH floors within each category. The background palette illustrates 759 original labels from 39 collections. |
| Diamond hands | Replayed 3,220 Autoglyphs and 1,004 DEAFBEEF Transfer logs. Both supplies and all 736 current owners matched Ethereum at finalized block 26,487,430. Continuous mint holds totaled 54 of 512 Autoglyphs and 13 of 224 DEAFBEEF tokens. The longest current hold was [Autoglyph #133](https://etherscan.io/tx/0x90fd1a3ece8550cb16c6cc0234d1d4d31522dac4aa480392d44ad905c72f1b63), since April 8, 2019. |

The 50 Ethereum collections are a fixed editorial sample drawn from the PFP Census collection list. The holder crawl exhausted 2,155 pages across two collection batches from 20:47 to 21:45 UTC. Holder quantities can change during pagination. The map reports addresses, including staking and custody contracts. Of the 512 shared Azuki and Doodles addresses, 427 had empty bytecode, 72 had EIP-7702 delegation code and 13 had other contract code at the pinned block. Wallet operators and beneficial ownership remain unidentified. [Coverage](editions/2026-11-24/coverage.csv) · [All pairs](editions/2026-11-24/overlap.csv) · [Account types](editions/2026-11-24/account-types.json)

The palette retains each artist's labels. Strip width follows count within the selected collection, and the imagery comes from an example NFT. Seven example links were checked against item metadata. The holding clock measures time at an address and resets after a transfer to another wallet, including an eventual return. Autoglyphs #1, #2 and #3 also matched OpenSea's current indexed owners and latest move dates. [Backgrounds](editions/2026-11-24/backgrounds.csv) · [Holding histories](editions/2026-11-24/holds.csv)

## Site design and offline builds

Edit the layout in `site/template.html`, the shared type, color and spacing rules in `site/publication.css`, and the edition interactions in `site/explorer.js`. The study registry in `site/cover.js` supplies each header link and cover card. The hero in `site/atlas.js` uses the actual ribbon paths as hover and tap targets. Hover cards show the collections, their shared address count and the percentage of each holder list. Portraits are bundled from the URLs in `site/portraits/sources.json`; Lucide icons and their license are in `site/icons/`. The overlap ribbons use pair counts, the background contact sheet shows sample NFTs, and each holding-history tile represents one token.

Run `python3 render.py 2026-11-24` to rebuild the standalone HTML from the checked-in edition records. Use `--check` to detect a stale build. The output runs from disk and at a Pages project subpath.

## Refresh and preview

Use Python 3.11 or later from the repo root. OpenSea reads use `OPENSEA_API_KEY`, the log replay also uses `ETHERSCAN_API_KEY` and `ALCHEMY_API_KEY`. Choose a fresh UTC date for a new crawl. Completed collections for a date are cached locally to resume interrupted runs.

```sh
edition=$(date -u +%F)
python3 cohort.py "$edition" holders
python3 cohort.py "$edition" palette
python3 cohort.py "$edition" traits
python3 diamond.py "editions/$edition/autoglyphs.json"
block=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["block"])' "editions/$edition/autoglyphs.json")
python3 diamond.py "editions/$edition/deafbeef.json" --contract 0xd754937672300ae6708a51229112de4017810934 --block "$block"
python3 account_types.py "$edition"
python3 build.py "$edition"
python3 -m unittest -v
```

## Publish the shared site

The Pages package puts the newest edition at the project root and retains dated editions under `editions/YYYY-MM-DD/`. It includes the HTML, CSVs and aggregate JSON. To preview that package locally, run `python3 pages.py /tmp/census-site` with a fresh destination, then `python3 -m http.server --directory /tmp/census-site`.

When ready to launch, select GitHub Actions as the repository's Pages source and dispatch **Publish Census** on main. Pull requests run offline checks. Crawls and publication are manual.

## Original three-collection pilot

The sample covers Azuki, Doodles and Pudgy Penguins on Ethereum. Run `python3 pilot.py` with `OPENSEA_API_KEY` in the environment to replace the snapshot. Python's standard library is sufficient. The run makes 27 requests before retries and records its UTC start and finish times.

| Edition | First observation | Coverage |
| --- | --- | --- |
| Community overlap | Azuki and Pudgy Penguins shared 5 addresses, Doodles and Pudgy Penguins shared 3, and Azuki and Doodles shared 2. | First 100 holder addresses per collection, ordered by holdings. Custodial and contract wallets included. |
| Trait census | The most frequent background in each collection was Off White D for Azuki (1,990), green for Doodles (748) and Blue for Pudgy Penguins (1,587). | 892 collection-specific text category/value pairs. An empty floors object means no matching listed floor in the response. Floors are asking prices grouped by chain and currency. |
| Diamond hands | Doodle #2 had the earliest latest indexed move in the sample, June 24, 2022. | Token IDs 1, 2 and 3 from each contract. All nine current owner addresses matched the latest indexed change of address. This convenience sample cannot establish a collection record or a minter retention rate. |
