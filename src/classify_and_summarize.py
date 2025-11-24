import os
import json
from typing import List, Dict
from openai import OpenAI

SYSTEM_PROMPT = """
You are an expert in AI and design research, familiar with Howard et al. (2008) 6-stage design process.

Given metadata about a research paper (title, abstract, year, authors, source),
you must return a STRICT JSON object with the following keys:

- "design_phase": list of strings, subset of:
  ["Establishing a need", "Analysis of task", "Concept design",
   "Embodiment design", "Detail design", "Implementation"]

- "ai_roles": list of short strings describing the role(s) of AI in this work.
- "representations": list of short strings describing main design representations.
- "research_type": list of short strings describing the research angle.
- "summary_short": a 2–3 sentence summary of the paper, in English.
- "implications_for_design_research": list of 2–4 short strings.
- "tags": list of 3–8 short topical tags, lowercase, hyphen-separated.

Return ONLY valid JSON. No markdown, no backticks, no comments.
"""

def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def classify_single_paper(paper: Dict) -> Dict:
    client = _get_client()

    payload = {
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "year": paper.get("year"),
        "source": paper.get("source"),
        "authors": paper.get("authors", []),
        "categories": paper.get("categories", []),
    }

    completion = client.responses.create(
        model="gpt-4o",   # sama malli kuin overviewssa
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
#        response_format={"type": "json_object"},  # <-- TÄRKEÄ
    )

    raw_text = completion.output[0].content[0].text
    # Yritetään varmistaa, että otetaan vain JSON-osa (jos malli vaikka laittaa vahingossa tekstiä ympärille)
    text = raw_text.strip()

    # Jos mukana on vaikka ```json ... ``` -blokkeja
    if "```" in text:
        # Poimitaan vain ensimmäisen { ja viimeisen } välinen osa
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    try:
        enriched = json.loads(text)
    except json.JSONDecodeError:
        print("[classify_and_summarize] JSON parse failed, using fallback.")
        enriched = {
            "design_phase": [],
            "ai_roles": [],
            "representations": [],
            "research_type": [],
            "summary_short": paper.get("abstract", "")[:300],
            "implications_for_design_research": [],
            "tags": [],
        }

    merged = {**paper, **enriched}
    return merged


def enrich_papers_with_llm(papers: List[Dict]) -> List[Dict]:
    """
    Ottaa listan paperi-dictejä (esim. arXiv tai BibTeX),
    kutsuu LLM:ää jokaiselle ja palauttaa rikastetun listan.
    """
    enriched_list: List[Dict] = []
    for p in papers:
        try:
            enriched = classify_single_paper(p)
            enriched_list.append(enriched)
        except Exception as e:
            print(f"[classify_and_summarize] Error for paper {p.get('id')}: {e}")
    print(f"[classify_and_summarize] Enriched {len(enriched_list)} papers.")
    return enriched_list