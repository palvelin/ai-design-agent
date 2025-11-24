from .fetch_papers import fetch_new_papers
from .classify_and_summarize import enrich_papers_with_llm
from .utils import update_jsonl_db, load_jsonl_db
from .update_knowledge_base import update_knowledge_markdown
from .fetch_bibtex import load_bibtex
from .fetch_bibtex_url import download_paperpile_bib
from dotenv import load_dotenv
load_dotenv()

def main():
    structured_papers = []

    DB_PATH = "data/papers_structured.jsonl"
    BIB_PATH = "data/paperpile.bib"
    MAX_BIB_PER_RUN = 30  # voit säätää 10–50 välillä

    # 0) Lue nykyinen tietokanta ja kerää id:t
    existing_papers = load_jsonl_db(DB_PATH)
    existing_ids = {p["id"] for p in existing_papers}
    print(f"[main] Existing DB has {len(existing_ids)} papers.")

    # 1) Hae uudet arXiv-paperit ja suodata vain aidosti uudet id:t
    raw_papers = fetch_new_papers(days_back=365, max_results=30)
    raw_papers = [p for p in raw_papers if p["id"] not in existing_ids]

    if raw_papers:
        print(f"[main] Enriching {len(raw_papers)} NEW arXiv papers with LLM...")
        arxiv_structured = enrich_papers_with_llm(raw_papers)
        structured_papers.extend(arxiv_structured)
    else:
        print("[main] No NEW arXiv papers to enrich.")

    # Try downloading latest Paperpile export locally (only if PAPERPILE_BIB_URL is set)
    download_paperpile_bib("data/paperpile.bib")   

    # 2) Lataa Paperpile (BibTeX) -kirjasto
    try:
        bib_papers = load_bibtex(BIB_PATH)
    except FileNotFoundError:
        print(f"[main] No {BIB_PATH} found, skipping BibTeX papers.")
        bib_papers = []

    # Suodata pois ne BibTeX-paperit, jotka ovat jo tietokannassa
    bib_papers = [p for p in bib_papers if p["id"] not in existing_ids]

    # Raja: rikastetaan vain MAX_BIB_PER_RUN per ajo
    if len(bib_papers) > MAX_BIB_PER_RUN:
        print(f"[main] Limiting BibTeX enrichment to {MAX_BIB_PER_RUN} papers (out of {len(bib_papers)} new).")
        bib_papers = bib_papers[:MAX_BIB_PER_RUN]

    if bib_papers:
        print(f"[main] Enriching {len(bib_papers)} NEW BibTeX papers with LLM...")
        bib_structured = enrich_papers_with_llm(bib_papers)
        structured_papers.extend(bib_structured)
    else:
        print("[main] No NEW BibTeX papers to enrich.")

    # 3) Päivitä JSONL-tietokanta, jos jotain uutta tuli
    if structured_papers:
        update_jsonl_db(DB_PATH, structured_papers)
    else:
        print("[main] No structured papers to add to database.")

    # 4) Päivitä living synthesis (overview.md + by_design_phase.md)
    update_knowledge_markdown(
        db_path=DB_PATH,
        knowledge_dir="knowledge",
    )
if __name__ == "__main__":
    main()