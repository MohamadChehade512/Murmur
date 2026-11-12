# Murmur

**Live media monitoring, free to run.** Murmur follows three companies across news (GDELT and Google
News), Hacker News and Bluesky, in English and Arabic, and publishes an hourly dashboard of how often they are mentioned,
how people feel about them, and the words people use.

**Dashboard:** https://mohamadchehade512.github.io/Murmur/
**Data:** [`summary.json`](https://mohamadchehade512.github.io/Murmur/summary.json)

[![CI](https://github.com/MohamadChehade512/Murmur/actions/workflows/ci.yml/badge.svg)](https://github.com/MohamadChehade512/Murmur/actions/workflows/ci.yml)
[![Collect and publish](https://github.com/MohamadChehade512/Murmur/actions/workflows/collect.yml/badge.svg)](https://github.com/MohamadChehade512/Murmur/actions/workflows/collect.yml)

## How it works

```
GDELT, Google News, Hacker News, Bluesky ──► collect ──► clean ──► score ──► keywords ──► data branch (30 days)
Wikipedia page views ─────────────────────────────────────────────────────► summarise ──► GitHub Pages
```

Every hour a GitHub Actions workflow runs the pipeline, saves new mentions to the `data` branch and
publishes the dashboard and `summary.json` to GitHub Pages. Sentiment comes from a multilingual
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
python -m http.server -d public 8000     # view the dashboard at http://localhost:8000
```

For the multilingual model (Python 3.11 to 3.12 recommended):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[model]"
murmur run --sentiment model
```

## Track different companies

Edit [`companies.toml`](companies.toml): each company has a name, colour, aliases that must appear
in a post, phrases to exclude, a GDELT news query (matched in English and Arabic sources), Google
News searches per language, search terms and a Wikipedia article.

## Project layout

```
companies.toml          which companies to follow
src/murmur/
  sources/              one collector per source
  clean.py, text.py     normalise, detect language, filter, de-duplicate
  sentiment.py          lexicon and multilingual model backends
  keywords.py           words and phrases, English and Arabic
  store.py              rolling day files on the data branch
  aggregate.py          builds summary.json
  pipeline.py, cli.py   one full run: `murmur run`
site/                   the static dashboard
tests/                  offline tests with sample API responses
.github/workflows/      CI and the hourly collect-and-publish job
```

## License

MIT
