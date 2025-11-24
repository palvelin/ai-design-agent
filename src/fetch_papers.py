import datetime as dt
import urllib.parse
import feedparser
from typing import List, Dict

ARXIV_API_URL = "http://export.arxiv.org/api/query"

COGNITIVE_KEYWORDS = [
    "design cognition",
    "design research",
    "designerly",
    "industrial design",
    "product design",
    "concept design",
    "idea generation",
    "ideation",
    "creative support",
    "creativity support",
    "creativity",
    "sketching",
    "sketch",
    "prototyping",
    "prototype",
    "co-design",
    "codesign",
    "co-creation",
    "human-centred design",
    "human-centered design",
    "participatory design",
    "design space",
    "exploration",
    "divergent thinking",
    "convergent thinking",
]

NEGATIVE_KEYWORDS = [
    "vlsi",
    "rf circuit",
    "antenna",
    "wireless channel",
    "mimo",
    "quantum error correction",
    "cryptography",
    "network traffic",
    "medical image segmentation",
    "brain tumor segmentation",
    "intrusion detection",
    "time series forecasting",
]

def _build_search_query() -> str:
    """
    Rakennetaan arXiv-haku, joka suosii AI + design cognition / industrial design -henkisiä papereita.

    Pääkategoriat:
    - cs.HC (HCI)
    - cs.AI (joskus design-työkalut menevät sinne)
    """
    categories = "(cat:cs.HC OR cat:cs.AI)"

    text_terms = (
        'all:('
        'design OR designer OR "design research" OR "design cognition" OR '
        '"industrial design" OR "product design" OR '
        '"creative support" OR "creativity support" OR '
        'creativity OR "idea generation" OR "concept design" OR '
        'sketching OR prototyping OR "co-design" OR "co-creation"'
        ')'
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

def _is_cognition_relevant(title: str, abstract: str) -> bool:
    text = (title + " " + abstract).lower()
    if any(neg in text for neg in NEGATIVE_KEYWORDS):
        return False
    if any(tok in text for tok in COGNITIVE_KEYWORDS):
        return True
    # Voi halutessa olla vähän löysempi: vaadi esim. "design" + "creativity" tms.
    if "design" in text and ("creativity" in text or "designer" in text or "creative" in text):
        return True
    return False

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

        if not _is_cognition_relevant(title, abstract):
            continue
        
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