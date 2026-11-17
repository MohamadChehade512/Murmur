# Murmur

**Live media monitoring, free to run.** Murmur follows 137 companies across news (GDELT and Google
News), Hacker News and Bluesky, in English and Arabic, and publishes an hourly dashboard of how often they are mentioned,
how people feel about them, and the words people use. Three are featured; any of the others can be looked up.

**Dashboard:** https://mohamadchehade512.github.io/Murmur/
**Data:** [`summary.json`](https://mohamadchehade512.github.io/Murmur/summary.json) (featured),
[`index.json`](https://mohamadchehade512.github.io/Murmur/index.json) (every company), and
`companies/<id>.json` for each one, e.g. [`companies/nvidia.json`](https://mohamadchehade512.github.io/Murmur/companies/nvidia.json)

[![CI](https://github.com/MohamadChehade512/Murmur/actions/workflows/ci.yml/badge.svg)](https://github.com/MohamadChehade512/Murmur/actions/workflows/ci.yml)
[![Collect and publish](https://github.com/MohamadChehade512/Murmur/actions/workflows/collect.yml/badge.svg)](https://github.com/MohamadChehade512/Murmur/actions/workflows/collect.yml)

## How it works

```
GDELT, Google News, Hacker News, Bluesky ──► collect ──► clean ──► score ──► keywords ──► data branch (30 days)
Wikipedia page views ─────────────────────────────────────────────────────► summarise ──► GitHub Pages
```

Every hour a GitHub Actions workflow runs the pipeline, saves new mentions to the `data` branch and
publishes the dashboard and its JSON files to GitHub Pages. Featured companies are collected every
hour and the rest in rotation, every four hours. Sentiment comes from a multilingual
model that reads English and Arabic, running on the Actions runner's CPU.

- [Architecture](docs/architecture.md): stages, modules, and the `summary.json` schema
- [Data sources and ethics](docs/data-and-ethics.md): what is collected, what is stored, and limits

## Keeping the schedule running

GitHub pauses scheduled workflows in public repositories after 60 days without activity on the
default branch. If that happens, open **Actions → Collect and publish → Enable workflow**, or push
any commit to `main`.

## Cost

$0. GitHub Actions and Pages are free for public repositories, every source is free and keyless,
and no paid AI or cloud services are used.

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                   # offline tests
murmur run --hours 24                    # live run with the English lexicon, writes ./data and ./public
murmur run --hours 24 --all              # every company, not just this hour's group (slower)
python -m http.server -d public 8000     # view the dashboard at http://localhost:8000
```

For the multilingual model (Python 3.11 to 3.12 recommended):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[model]"
murmur run --sentiment model
```

## Track different companies

Edit [`companies.toml`](companies.toml). A company only needs an `id`, `name` and `sector`; aliases,
news queries and search terms default to the name and any Arabic names (`ar`). Add specific
`aliases` and `exclude` phrases when the name is also an everyday word, and set `featured = true` to
collect it every hour and show it on the front page. After adding companies, run **Collect and
publish** from the Actions tab with **all** ticked to fill them in straight away.

## Project layout

```
companies.toml          which companies to follow
src/murmur/
  sources/              one collector per source
  clean.py, text.py     normalise, detect language, filter, de-duplicate
  sentiment.py          lexicon and multilingual model backends
  keywords.py           words and phrases, English and Arabic
  store.py              one file per run on the data branch, 30 days
  aggregate.py          builds summary.json, index.json and companies/*.json
  pipeline.py, cli.py   one full run: `murmur run`
site/                   the static dashboard
tests/                  offline tests with sample API responses
.github/workflows/      CI, the hourly collect-and-publish job, and the weekly data squash
```

## License

MIT
