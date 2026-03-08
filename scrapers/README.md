# Scrapers

This module implements the **Data Acquisition** layer of the Social Reaction Analysis platform. It uses [Crawl4AI](https://github.com/unclecode/crawl4ai) (v0.8.0) — an open-source, LLM-friendly web crawler — to collect raw data from publicly accessible Greek news websites and feed it into the downstream NLP and analysis pipeline.

---

## Role in the Project Pipeline

```
[ Scrapers (Crawl4AI) ] ──► [ NLP & Semantic Analysis ] ──► [ LLM Processing ] ──► [ Backend API ] ──► [ Frontend Map & Dashboard ]
```

The scrapers are the entry point of the data pipeline. They run on a scheduled or on-demand basis, extracting articles and posts that may relate to one of the five defined categories of social reaction in Greece.

---

## Tracked Categories

All scrapers are oriented toward detecting content that falls under the following reaction categories:

| # | Category | Examples |
|---|----------|---------|
| 1 | **Mass Mobilization & Street Actions** | Rallies, demonstrations, marches, blockades, occupations |
| 2 | **Labor & Economic Reaction** | Strikes, boycotts |
| 3 | **Institutional & Political Behavior** | Election abstention, political stances |
| 4 | **Digital Reaction** | Hashtag campaigns, hacktivism, whistleblowing |
| 5 | **Conflict Reaction** | Violent incidents, clashes |

---

## Crawl4AI

The scraper module is built on top of **Crawl4AI 0.8.0**, which provides:

- **`AsyncWebCrawler`** — headless Chromium browser automation via Playwright.
- **Clean Markdown output** — raw HTML is automatically converted to LLM-ready text.
- **`BrowserConfig` / `CrawlerRunConfig`** — fine-grained control over page timeouts, caching, wait conditions, and stealth mode.
- **Deep crawling** — BFS/DFS strategies with crash recovery (`resume_state`) and prefetch mode.
- **Apache 2.0 license** — fully open-source.

All spider classes in this module inherit from `BaseScraper` (see `base_scraper.py`), which wraps `AsyncWebCrawler` with a polite crawl-delay loop and a consistent record-extraction interface.

---

## Data Sources

### News Websites
Web crawlers target Greek news portals and aggregate content that may report on social reactions. Configured sources (see `config.py`):

| Source | Seed URLs |
|--------|-----------|
| **protothema.gr** | `/greece/`, `/politics/` |
| **kathimerini.gr** | `/politics/`, `/society/` |
| **iefimerida.gr** | `/ellada`, `/politiki` |

Additional sources (regional portals, labor publications) can be added by appending entries to `NEWS_SOURCES` in `config.py`.

---

## Directory Structure

```
scrapers/
├── README.md
├── __init__.py
├── config.py                    # Source URLs, keywords, .env loading
├── base_scraper.py              # Abstract base wrapping Crawl4AI's AsyncWebCrawler
├── run_all.py                   # Entrypoint — runs all registered scrapers
├── news/
│   ├── __init__.py
│   ├── base_news_spider.py      # Shared news extraction logic + keyword filter
│   ├── iefimerida.py            # Concrete spider for iefimerida.gr
│   ├── kathimerini.py           # Concrete spider for kathimerini.gr
│   └── protothema.py            # Concrete spider for protothema.gr
└── utils/
    ├── __init__.py
    └── storage.py               # Saves records as .ndjson to data/raw/
```

### Architecture

```
BaseScraper (base_scraper.py)          ← wraps AsyncWebCrawler, defines crawl() loop
    └── BaseNewsSpider (base_news_spider.py)  ← adds keyword filter + default article extraction
            ├── ProtothemaScraper (protothema.py)  ← concrete spider (override _extract_articles for site-specific logic)
            ├── KathimeriniScraper (kathimerini.py)
            └── IefimeriadaScraper (iefimerida.py)
```

To add a new news source:
1. Create a file in `news/` (e.g., `ert.py`).
2. Subclass `BaseNewsSpider`.
3. Set `source_name` and `seed_urls`.
4. Optionally override `_extract_articles()` for precise CSS/XPath selection.
5. Register the class in `SCRAPER_CLASSES` inside `run_all.py`.

---

## Setup

### Prerequisites

- Python 3.10+
- A `.env` file at the project root containing the required API keys (see [Configuration](#configuration))

### Install Dependencies

```bash
# From the project root, inside the virtual environment
pip install -r requirements.txt

# Crawl4AI post-install setup (installs Playwright's Chromium)
crawl4ai-setup

# Verify installation
crawl4ai-doctor
```

If Chromium fails to install automatically:

```bash
python -m playwright install --with-deps chromium
```

---

## Configuration

Sensitive credentials and tunable parameters are managed via the `.env` file at the project root. **Never commit this file.**

| Variable | Description |
|----------|-------------|

| `SCRAPE_INTERVAL_SECONDS` | How often the scheduled crawl runs (default: `3600`) |
| `OUTPUT_DIR` | Directory where raw scraped data is saved (default: `data/raw/`) |
| `REQUEST_DELAY_SECONDS` | Politeness delay between HTTP requests (default: `2`) |

Greek reaction keywords used to filter crawled content are defined in `REACTION_KEYWORDS` inside `config.py`. Add or remove terms there to refine the relevance filter.

---

## Usage

### Run all scrapers

```bash
python -m scrapers.run_all
```

This will:
1. Instantiate every scraper registered in `SCRAPER_CLASSES`.
2. Crawl each source's seed URLs using Crawl4AI's headless browser.
3. Filter articles by Greek social-reaction keywords.
4. Save matching records as `.ndjson` under `data/raw/<source_name>/<YYYY-MM-DD>.ndjson`.

### Run a single spider directly (example)

```python
import asyncio
from scrapers.news.protothema import ProtothemaScraper
from scrapers.utils.storage import save_records

async def main():
    scraper = ProtothemaScraper()
    records = await scraper.crawl()
    save_records(records, scraper.source_name)

asyncio.run(main())
```

---

## Output Format

Each scraper produces newline-delimited JSON (`.ndjson`) files saved under `data/raw/<source_name>/`, with the following structure per record:

```json
{
  "source": "protothema",
  "url": "https://...",
  "title": "...",
  "body": "...",
  "published_at": "2026-02-22T10:30:00+02:00",
  "scraped_at": "2026-02-22T11:00:00+02:00",
  "lang": "el",
  "category_hint": null
}
```

- `body` contains clean Markdown text generated by Crawl4AI from the page HTML.
- `published_at` is `null` by default; site-specific spiders can override `_extract_articles()` to parse the article date.
- `category_hint` is populated only when the scraper can determine the category with high confidence from headline keywords; otherwise classification is deferred to the NLP module.

---

## Ethical & Legal Considerations

- All scrapers respect `robots.txt` rules.
- Request rate limiting and polite crawl delays are enforced via `REQUEST_DELAY_SECONDS` for all news spiders.
- No personal data beyond what is publicly available is stored.
- Crawl4AI is licensed under the Apache 2.0 License.
