# Census

[Explore the live site](https://ryanio.github.io/census-lab/) to see which Ethereum NFT collections share holders, which traits recur, and how long each token stays in the same wallet. Each study includes its source data as CSV.

## Field studies

| Study | November 24, 2026 edition | Download |
| --- | --- | --- |
| [Community overlap](https://ryanio.github.io/census-lab/overlap.html) | 50 collections and 1,225 pairs. Mutant Ape Yacht Club and Bored Ape Kennel Club shared 2,872 addresses, or 23.50% and 55.76% of their respective holder lists. | [Pairs](editions/2026-11-24/overlap.csv) · [Crawl windows](editions/2026-11-24/coverage.csv) |
| [Trait studies](https://ryanio.github.io/census-lab/traits.html) | Across 38,900 reported text values, 22 collections use a blue background and ten use the mouth label "Tongue Out". The background palette links 759 labels across 39 collections to example NFTs. | [Traits and floors](editions/2026-11-24/traits.csv) · [Backgrounds](editions/2026-11-24/backgrounds.csv) |
| [Diamond hands](https://ryanio.github.io/census-lab/hands.html) | 54 of 512 Autoglyphs and 13 of 224 DEAFBEEF tokens stayed at their mint-recipient address continuously. | [Autoglyphs](editions/2026-11-24/holds.csv) · [DEAFBEEF](editions/2026-11-24/deafbeef-holds.csv) |

Related publications include [PFP Census](https://ryanio.github.io/pfp-census/) and [Card Census](https://ryanio.github.io/card-census/).

## Reading the data

Overlap counts distinct wallet addresses. An address can hold tokens in custody for many people, and one person can use multiple wallets. The November holder crawl read 2,155 pages between 20:47 and 21:45 UTC, so ownership could change between reads. Using both collections' top 100 holders gave Azuki and Doodles just two shared addresses. Their full lists shared 512. [Address classifications](editions/2026-11-24/account-types.json) · [Original pilot snapshot](pilot-results.json)

The gallery matches category and value across collections after trimming spaces and ignoring case. The shared-trait gallery checks each example against the individual NFT's metadata and links its token ID to OpenSea. Shuffle PFPs rotates between prebuilt lineups of verified examples. Each share page serves its own JPEG and X card metadata directly from GitHub Pages. Copy a dated lineup link to preserve the token choices, or save the visible gallery as a PNG. Exports keep the original spellings. The pictured NFT is one example of a background, and its strip width follows the count within that collection. A floor is the cheapest active listing observed in its payment currency. The ETH ranking compares ETH listings only.

A hold starts when a token changes address. Self-transfers preserve its tenure, while a transfer away and back resets it. The November replay checked the supply and every current owner against Ethereum at block 26,487,430 after processing 3,220 Autoglyphs and 1,004 DEAFBEEF transfer logs. Autoglyph #133 has stayed at its mint address since April 8, 2019. [Mint transaction](https://etherscan.io/tx/0x90fd1a3ece8550cb16c6cc0234d1d4d31522dac4aa480392d44ad905c72f1b63)

## Preview locally

With Python 3.11 or later, run these commands from the repo root. The checked-in datasets are sufficient for a site build. The chart works offline, and example artwork in the trait palette loads from OpenSea's image CDN.

```sh
python3 render.py 2026-11-24
python3 -m pip install -r requirements.txt
python3 -m unittest -v
preview_dir=$(mktemp -d)/site
python3 pages.py "$preview_dir"
python3 -m http.server 8000 --directory "$preview_dir"
```

Open [localhost:8000](http://localhost:8000/). The package includes the latest edition at the root, dated archives, share images, and a sitemap. See [AGENTS.md](AGENTS.md) for the source layout and release workflow.

## Collect a new edition

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
python3 trait_examples.py "editions/$edition"
python3 lineup_art.py "editions/$edition"  # uses ffmpeg for video and rsvg-convert for SVG
python3 render.py "$edition"
python3 -m unittest -v
```

## Study analytics

In GA4 Explorations, break down total users by **Content group** (`overlap`, `traits`, or `hands`) and event name. For each study, divide users who triggered `study_explore` or `share` by users who triggered `page_view` for that study during the same period. Each ratio measures a different behavior.

`study_explore` records a collection switch, browsing a shared trait, shuffling a lineup, or clicking the holding-history CSV. Register `study_action` as an event-scoped custom dimension for the action breakdown. `share` records a successful clipboard copy with `method=copy_link`. Opening a copied link records a page view. These events use the existing GA4 stream on the published site.

## License

Ryan Ghods licenses the original Census Lab code under the [MIT License](LICENSE). Third-party NFT artwork remains subject to its respective rights holders' terms. The bundled icons carry their own [license notices](site/icons/LICENSE).
