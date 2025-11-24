import os
import json
from typing import List, Dict
from openai import OpenAI

PHASES = [
    "Establishing a need",
    "Analysis of task",
    "Concept design",
    "Embodiment design",
    "Detail design",
    "Implementation",
]


SYSTEM_PROMPT = """
You are an expert in AI and design research, familiar with Howard et al. (2008) 6-stage design process.

Given metadata about a research paper (title, abstract, year, authors, source),
you must return a STRICT JSON object with the following keys:

- "design_phase": list of strings, subset of:
  ["Establishing a need", "Analysis of task", "Concept design",
   "Embodiment design", "Detail design", "Implementation"]

- "ai_roles": list of short strings describing the role(s) of AI in this work.
  For example: ["idea generation", "evaluation", "optimization",
  "simulation", "documentation", "analysis", "interaction", "co-creation"].

- "representations": list of short strings describing main design representations.
  Examples: ["text", "sketch", "image", "3D model", "CAD", "code",
  "prototype", "interface", "behaviour", "data visualization"].

- "research_type": list of short strings describing the research angle.
  Examples: ["methodology", "tool development", "theory building",
  "protocol analysis", "lab study", "field study", "case study",
  "practice-based research"].

- "summary_short": a 2–3 sentence summary of the paper, in English.

- "implications_for_design_research": list of 2–4 bullet-style strings
  (no leading bullet characters) describing what this paper implies for
  design research.

- "tags": list of 3–8 short topical tags, lowercase, hyphen-separated
  e.g. ["generative-design", "creativity-support", "protocol-analysis"].

Return ONLY valid JSON. No comments, no extra text.
"""


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def classify_single_paper(paper: Dict) -> Dict:
    """
    Syöttää yhden raw-paperin LLM:lle ja palauttaa yhdistetyn dictin,
    jossa myös design_phase ym. kentät.
    """
    client = _get_client()

    # Käytetään vain oleellisia kenttiä promptissa
    payload = {
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "year": paper.get("year"),
        "source": paper.get("source"),
        "authors": paper.get("authors", []),
        "categories": paper.get("categories", []),
    }

    completion = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
#        response_format={"type": "json_object"},
    )

    raw_text = completion.output[0].content[0].text

    try:
        enriched = json.loads(raw_text)
    except json.JSONDecodeError:
        # fallback: jos jotain menee pieleen, annetaan minimaalinen rakenne
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
    enriched_list = []
    for p in papers:
        try:
            enriched = classify_single_paper(p)
            enriched_list.append(enriched)
        except Exception as e:
            print(f"[classify_and_summarize] Error for paper {p.get('id')}: {e}")
    print(f"[classify_and_summarize] Enriched {len(enriched_list)} papers.")
    return enriched_list