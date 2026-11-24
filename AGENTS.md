# Working on Census

Start from the latest `origin/main` in a worktree under `.claude/worktrees/`. Integrate verified work directly into main with a fast-forward and push. Open a PR only when Ryan asks for one. Never force-push main.

## Edit the source

| Change | Source |
| --- | --- |
| Layout, typography and responsive behavior | `site/template.html`, `site/publication.css` |
| Hero pinning, hover and collection portraits | `site/atlas.js`, `site/portraits/` |
| Cover cards and edition interactions | `site/cover.js`, `site/explorer.js` |
| Permanent routes, canonical URLs and dataset metadata | `discovery.py`, `render.py` |
| Favicon and share images | `social_art.py` and its outputs in `site/assets/` |
| Crawl, ownership replay and edition exports | `cohort.py`, `diamond.py`, `build.py` |

Use the shared template for the editions. Keep PFP Census and Card Census as external links. Preserve dated CSV links and legacy collection fragments when changing navigation. Retain original collection and trait labels in exports.

## Build and check

Run `python3 render.py YYYY-MM-DD` for the affected edition and commit the regenerated HTML with the source. Use the [README preview commands](README.md#preview-locally) to test the Pages package in a fresh directory. Design changes can use the checked-in data. Follow the [collection procedure](README.md#collect-a-new-edition) for an authorized refresh.

Run `python3 -m unittest -v`. For interaction changes, exercise the affected route by direct URL. Check tap, keyboard and mouse input as applicable. For mobile layout work, test a narrow phone, switch collections with long names and rotate with a card pinned or a table expanded. Check that links to downloads still reach the files in the package.

## Release

A main push runs **Check editions**. When publication is requested, dispatch **Publish Census** from main with `gh workflow run pages.yml --ref main`, watch the run to completion, and verify the changed behavior at [the live site](https://ryanio.github.io/census-lab/). GitHub Pages serves this project under `/census-lab/`.
