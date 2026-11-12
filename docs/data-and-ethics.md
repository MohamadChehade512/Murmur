# Data sources and ethics

Murmur only uses public sources through their official, free APIs. It does not scrape pages
against a site's terms, log in as anyone, or collect private data.

| Source | Access | Limits we respect |
| --- | --- | --- |
| [GDELT DOC 2.0](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) | Free, no key | One request every 5 seconds (enforced in `http.py`). |
| [Hacker News via Algolia](https://hn.algolia.com/api) | Free, no key | A handful of requests per hour. |
| [Bluesky search](https://docs.bsky.app/docs/api/app-bsky-feed-search-posts) | Free, no login on `api.bsky.app` | A handful of requests per hour. |
| [Wikimedia page views](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/) | Free, no key | Descriptive User-Agent, one request per company per hour. |

## What we store

- For every mention: a link, the time, the source, the language, a sentiment label and the keywords
  extracted from it.
- For news articles only: the headline, so the dashboard can link to it.
- **Never** the text of people's posts or comments. Text is held in memory while a run scores it,
  then discarded.
- Data is kept for 30 days, then deleted.

## Limits of the analysis

- Sentiment is automated and approximate, especially for sarcasm and short posts.
- Relevance is based on company names and products, so some off-topic mentions slip through
  (for example, "Nikola Tesla").
- Coverage reflects what each source indexes, not the whole internet.

Murmur is a portfolio project. It is not affiliated with the companies it follows or with any
commercial media monitoring provider.
