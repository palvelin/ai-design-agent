import datetime as dt
import urllib.parse
import feedparser
from typing import List, Dict

ARXIV_API_URL = "http://export.arxiv.org/api/query"


def _build_search_query() -> str:
    """
    Rakennetaan arXiv-haku, joka suosii AI + design / HCI -henkisiä papereita.

    Voit myöhemmin säätää tätä stringiä:
    - lisää/poista hakusanoja
    - säädä kategorioita (cat:cs.CL tms.)
    """
    # arXiv query syntax:
    # (cat:cs.AI OR cat:cs.HC ...) AND all:(design OR "design research" OR "human-computer interaction" ...)
    categories = "(cat:cs.AI OR cat:cs.HC OR cat:cs.LG OR cat:stat.ML)"
    text_terms = (
        'all:(design OR designer OR "design research" OR '
        '"human-computer interaction" OR creativity OR "generative design")'
    )
    return f"{categories} AND {text_terms}"


def _query_arxiv(search_query: str, max_results: int = 40) -> feedparser.FeedParserDict:
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = ARXIV_API_URL + "?" + urllib.parse.urlencode(params)
    feed = feedparser.parse(url)
    return feed


def fetch_new_papers(days_back: int = 2, max_results: int = 40) -> List[Dict]:
    """
    Hakee viimeisen `days_back` päivän aikana julkaistuja papereita,
    jotka osuvat AI + design -hakuun.

    Palauttaa listan dict-olioita, joilla kentät:
    - id, title, abstract, authors, year, source, published, categories
    """
    search_query = _build_search_query()
    feed = _query_arxiv(search_query, max_results=max_results)

    if not getattr(feed, "entries", None):
        print("[fetch_papers] No entries from arXiv.")
        return []

    now_utc = dt.datetime.utcnow()
    papers: List[Dict] = []

    for entry in feed.entries:
        # entry.published: esim. "2025-03-10T12:34:56Z"
        try:
            published_dt = dt.datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            # Jos formaatti yllättää, hypätään yli
            continue

        age_days = (now_utc - published_dt).days
        if days_back is not None and age_days > days_back:
            # vanhempi kuin ikkunamme → skip
            continue

        paper_id = entry.id  # esim. "http://arxiv.org/abs/2501.01234v1"
        title = entry.title.strip()
        abstract = entry.summary.strip()
        authors = [a.name for a in getattr(entry, "authors", [])] or []
        categories = [t["term"] for t in getattr(entry, "tags", [])] if hasattr(entry, "tags") else []

        paper = {
            "id": paper_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": published_dt.year,
            "source": "arxiv",
            "published": published_dt.isoformat(),
            "categories": categories,
        }
        papers.append(paper)

    print(f"[fetch_papers] Fetched {len(papers)} recent papers from arXiv.")
    return papers