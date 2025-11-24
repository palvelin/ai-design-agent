from .fetch_papers import fetch_new_papers
from .classify_and_summarize import enrich_papers_with_llm
from .utils import update_jsonl_db
from .update_knowledge_base import update_knowledge_markdown


def main():
    # 1) Hae uudet paperit arXivista (viimeiset 2 päivää, max 40 tulosta)
    raw_papers = fetch_new_papers(days_back=365, max_results=30)

    if raw_papers:
        # 2) Rikasta LLM:llä (design_phase jne.)
        structured_papers = enrich_papers_with_llm(raw_papers)

        # 3) Päivitä JSONL-tietokanta (deduplikointi id:n perusteella)
        update_jsonl_db("data/papers_structured.jsonl", structured_papers)
    else:
        print("[main] No new raw papers fetched.")

    # 4) Päivitä living synthesis (overview.md + by_design_phase.md)
    update_knowledge_markdown(
        db_path="data/papers_structured.jsonl",
        knowledge_dir="knowledge",
    )


if __name__ == "__main__":
    main()