from __future__ import annotations

import asyncio
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    source: str
    published: str
    url: str
    sentiment: str
    description: str = ""


def _safe_title(entry) -> str:
    raw = getattr(entry, "title", "") or ""
    return re.sub(r"<[^>]+>", "", raw).strip()


def _safe_source(entry) -> str:
    try:
        return entry.source.title
    except Exception:
        pass
    try:
        return entry.tags[0].term
    except Exception:
        pass
    return "—"


def _safe_published(entry) -> str:
    return getattr(entry, "published", "") or ""


def _safe_link(entry) -> str:
    return getattr(entry, "link", "") or ""


def _safe_description(entry) -> str:

    desc = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""

    desc = re.sub(r"<[^>]+>", "", desc).strip()

    return desc[:500] if desc else ""


def _fetch_news_sync(
    symbol: str,
    lang: str = "pt-BR",
    gl: str = "BR",
    ceid: str = "BR:pt",
    max_items: int = 8,
    company_name: str = "",
) -> list[NewsItem]:
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser não instalado. Instale com: pip install feedparser")
        return []

    name_clean = re.sub(
        r"\b(S\.?A\.?|S/A|Inc\.?|Corp\.?|Ltd\.?|Ltda\.?|S\.?E\.?|PLC)\b",
        "",
        company_name or "",
        flags=re.I,
    ).strip()
    search_term = name_clean if len(name_clean) >= 3 else symbol
    if gl == "BR":
        query = urllib.parse.quote(f"{search_term}")
    else:
        query = urllib.parse.quote(f"{search_term} stock")
    url = f"https://news.google.com/rss/search?q={query}&hl={lang}&gl={gl}&ceid={ceid}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        with urllib.request.urlopen(req, timeout=7) as resp:
            raw = resp.read()
        feed = feedparser.parse(raw)
    except Exception as e:
        logger.warning("Erro ao buscar RSS para %s (%s): %s", symbol, search_term, e)
        return []

    items: list[NewsItem] = []
    for entry in (feed.entries or [])[:max_items]:
        title = _safe_title(entry)
        if not title:
            continue
        items.append(
            NewsItem(
                title=title,
                source=_safe_source(entry),
                published=_safe_published(entry),
                url=_safe_link(entry),
                sentiment="neutral",
                description=_safe_description(entry),
            )
        )
    return items


async def fetch_news(
    symbol: str, asset_type: str = "br_stock", company_name: str = "", max_items: int = 8
) -> list[NewsItem]:
    loop = asyncio.get_event_loop()

    items = await loop.run_in_executor(
        None, _fetch_news_sync, symbol, "pt-BR", "BR", "BR:pt", max_items, company_name
    )

    return items


def news_sentiment_summary(items: list[NewsItem]) -> str:
    if not items:
        return "Sem notícias recentes encontradas."
    return f"{len(items)} notícia(s) recente(s) encontrada(s)."


async def analyze_news_with_ai(
    items: list[NewsItem], symbol: str, company_name: str = ""
) -> dict[str, Any]:
    if not items:
        return {
            "sentiment": "neutral",
            "score": 5.0,
            "summary": "Sem notícias recentes encontradas.",
            "impact": "low",
            "key_topics": [],
            "ai_enabled": False,
        }

    return {
        "sentiment": "neutral",
        "score": 5.0,
        "summary": news_sentiment_summary(items),
        "impact": "low",
        "key_topics": [],
        "ai_enabled": False,
    }
