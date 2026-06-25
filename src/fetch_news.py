"""
AI Policy News Digest — RSS Fetcher & Ranker
Fetches from curated sources, scores by relevance + recency, picks top N stories.
No scraping — uses only public RSS feeds.
"""

import feedparser
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional
import html as html_lib


# ---------------------------------------------------------------------------
# Sources — all public RSS feeds (no scraping, no API keys needed)
# ---------------------------------------------------------------------------
RSS_SOURCES = [
    # Think tanks & policy institutes
    {"name": "Tech Policy Press",   "url": "https://www.techpolicy.press/feed/",                                     "weight": 1.3},
    {"name": "CSIS AI",             "url": "https://www.csis.org/programs/wadhwani-ai-center/feed",                   "weight": 1.3},
    {"name": "Brookings Tech",      "url": "https://www.brookings.edu/topic/technology-innovation/feed/",             "weight": 1.2},
    {"name": "RAND AI",             "url": "https://www.rand.org/topics/artificial-intelligence.xml",                 "weight": 1.2},
    {"name": "Stanford HAI",        "url": "https://hai.stanford.edu/news/rss.xml",                                  "weight": 1.1},
    {"name": "Georgetown CSET",     "url": "https://cset.georgetown.edu/feed/",                                      "weight": 1.2},
    # News outlets
    {"name": "MIT Tech Review",     "url": "https://www.technologyreview.com/feed/",                                  "weight": 1.2},
    {"name": "The Verge AI",        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",       "weight": 1.0},
    {"name": "Ars Technica Policy", "url": "https://feeds.arstechnica.com/arstechnica/policy",                        "weight": 1.0},
    # International / EU
    {"name": "EU Digital Strategy", "url": "https://digital-strategy.ec.europa.eu/en/rss.xml",                       "weight": 1.1},
    # Podcast show notes
    {"name": "Hard Fork (NYT)",     "url": "https://feeds.simplecast.com/l2i9YnTd",                                  "weight": 0.9},
]

# ---------------------------------------------------------------------------
# Relevance keywords — higher matches = higher score
# ---------------------------------------------------------------------------
POLICY_KEYWORDS = [
    "regulation", "regulatory", "governance", "policy", "legislation", "law",
    "executive order", "congress", "senate", "white house", "eu ai act",
    "nist", "ftc", "fcc", "digital omnibus", "preempt", "enforcement",
    "ai safety", "ai risk", "alignment", "foundation model", "frontier ai",
    "large language model", "llm", "generative ai", "anthropic", "openai",
    "deepmind", "national security", "cybersecurity", "surveillance",
    "algorithmic", "bias", "transparency", "accountability",
    "china", "us-china", "geopolitic", "export control", "chip", "semiconductor",
    "workforce", "automation", "democracy", "disinformation", "misinformation",
    "election", "platform", "social media", "data privacy", "public policy",
]

BOOST_KEYWORDS = [
    "executive order", "eu ai act", "regulation passed", "signed into law",
    "enforcement", "fine", "penalty", "preempt", "ban", "prohibited",
    "new law", "new policy", "new rules",
]

# User-Agent header — prevents most feed-level 403s
UA = "Mozilla/5.0 (compatible; AIDigestBot/1.0; +https://github.com)"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    summary: str
    published: datetime
    score: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clean_html(raw: str) -> str:
    """Strip HTML tags and decode entities, return plain text."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html_lib.unescape(text)
    return " ".join(text.split())


def parse_date(entry) -> datetime:
    """Parse feedparser entry date into UTC-aware datetime."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def score_item(item: NewsItem, source_weight: float = 1.0) -> float:
    """
    Score = keyword relevance (0–4) + boost (0–2) + recency (0–3).
    Multiplied by source weight.
    """
    text = (item.title + " " + item.summary).lower()

    keyword_hits = sum(1 for kw in POLICY_KEYWORDS if kw in text)
    relevance = min(keyword_hits * 0.35, 4.0)

    boost = sum(0.5 for kw in BOOST_KEYWORDS if kw in text)
    boost = min(boost, 2.0)

    age_hours = (datetime.now(timezone.utc) - item.published).total_seconds() / 3600
    recency = max(3.0 - (age_hours / 24), 0.0)

    return round((relevance + boost + recency) * source_weight, 3)


def fetch_rss(url: str) -> feedparser.FeedParserDict:
    """Fetch RSS with proper User-Agent to avoid 403s."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
    return feedparser.parse(raw)


def fetch_source(source: dict, cutoff_hours: int = 72) -> list[NewsItem]:
    """Fetch one RSS source; return NewsItems published within cutoff window."""
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)

    try:
        feed = fetch_rss(source["url"])

        for entry in feed.entries[:25]:
            pub = parse_date(entry)
            if pub < cutoff:
                continue

            # Get best available summary text
            summary_raw = ""
            if hasattr(entry, "content") and entry.content:
                summary_raw = entry.content[0].get("value", "")
            elif hasattr(entry, "summary"):
                summary_raw = entry.summary

            item = NewsItem(
                title=clean_html(entry.get("title", "Untitled")),
                url=entry.get("link", ""),
                source=source["name"],
                summary=clean_html(summary_raw)[:600],
                published=pub,
            )
            item.score = score_item(item, source.get("weight", 1.0))
            items.append(item)

    except urllib.error.HTTPError as e:
        print(f"  [WARN] HTTP {e.code} for {source['name']}")
    except urllib.error.URLError as e:
        print(f"  [WARN] URL error for {source['name']}: {e.reason}")
    except Exception as e:
        print(f"  [WARN] Failed {source['name']}: {type(e).__name__}: {e}")

    return items


def deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    """Remove duplicates by URL, then by fuzzy title match."""
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    deduped: list[NewsItem] = []

    for item in items:
        if item.url in seen_urls:
            continue
        seen_urls.add(item.url)

        title_words = set(item.title.lower().split())
        overlap = max(
            (len(title_words & set(t.lower().split())) / max(len(title_words), 1))
            for t in seen_titles
        ) if seen_titles else 0.0

        if overlap < 0.65:
            deduped.append(item)
            seen_titles.append(item.title)

    return deduped


def get_top_stories(n: int = 3, cutoff_hours: int = 72) -> list[NewsItem]:
    """Fetch all sources, deduplicate, rank by score, return top n."""
    all_items: list[NewsItem] = []

    for source in RSS_SOURCES:
        fetched = fetch_source(source, cutoff_hours=cutoff_hours)
        all_items.extend(fetched)
        status = f"{len(fetched)} items" if fetched else "0 items (blocked or no recent content)"
        print(f"  {source['name']}: {status}")

    if not all_items:
        print("  [WARN] No items fetched from any source.")
        return []

    deduped = deduplicate(all_items)
    deduped.sort(key=lambda x: x.score, reverse=True)
    return deduped[:n]
