"""Lightweight source credibility ranking for interview research.

Pure domain-matching layer (no ML). Sorts or truncates raw search results
before they are fed to the synthesis LLM so that high-signal interview-
experience sites and official company sources are prioritized.
"""

import logging
from typing import List, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Higher weight = higher priority. Default for unknown domains is 1.
SOURCE_PRIORITY: Dict[str, int] = {
    "glassdoor.com": 10,
    "leetcode.com": 9,
    "blind.com": 9,
    "teamblind.com": 9,
    "reddit.com": 8,
    "github.com": 10,
    "medium.com": 7,
    "dev.to": 6,
    "techcrunch.com": 5,
    "theverge.com": 5,
    "arxiv.org": 6,
    "quora.com": 3,
    "pinterest.com": 1,
    "tiktok.com": 1,
}


def _domain_weight(url: str) -> int:
    """Return the priority weight for a URL based on its netloc."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        if netloc in SOURCE_PRIORITY:
            return SOURCE_PRIORITY[netloc]
        for domain, weight in SOURCE_PRIORITY.items():
            if domain in netloc:
                return weight
        return 1
    except Exception:
        return 1


def rank_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort sources by credibility weight descending."""
    def sort_key(item: Dict[str, Any]) -> int:
        url = item.get("href") or item.get("url") or ""
        return _domain_weight(url)

    ranked = sorted(sources, key=sort_key, reverse=True)
    used = [r for r in ranked if sort_key(r) > 1]
    discarded = [r for r in ranked if sort_key(r) <= 1]

    if used:
        logger.info(
            f"Source ranking: {len(used)} high-priority sources kept, "
            f"{len(discarded)} low-priority sources demoted."
        )
        for u in used[:5]:
            url = u.get("href") or u.get("url") or "?"
            logger.info(f"  [KEEP] {url}")
    else:
        logger.info("Source ranking: no known high-priority domains found; keeping all sources.")

    return ranked


def truncate_to_top_k(sources: List[Dict[str, Any]], k: int = 15) -> List[Dict[str, Any]]:
    """Return only the top-k highest-ranked sources."""
    ranked = rank_sources(sources)
    kept = ranked[:k]
    dropped = ranked[k:]
    if dropped:
        logger.info(f"Source truncation: dropped {len(dropped)} sources beyond top {k}.")
    return kept