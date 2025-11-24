import os
import json
from collections import defaultdict
from typing import List, Dict

from openai import OpenAI


# -----------------------
# Perusasetukset
# -----------------------

PHASES = [
    "Establishing a need",
    "Analysis of task",
    "Concept design",
    "Embodiment design",
    "Detail design",
    "Implementation",
]


def load_structured_papers(path: str) -> List[Dict]:
    """Read JSONL file with one paper per line."""
    if not os.path.exists(path):
        print(f"[update_knowledge_base] No file at {path}, skipping.")
        return []

    papers = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                papers.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[update_knowledge_base] Skipping invalid JSON line: {line[:80]}...")
    return papers


def group_papers_by_phase(papers: List[Dict]) -> Dict[str, List[Dict]]:
    """Group papers into Howard et al. (2008) phases."""
    grouped = defaultdict(list)
    for p in papers:
        phases = p.get("design_phase") or []
        if not isinstance(phases, list):
            phases = [phases]
        if not phases:
            # If no phase given, you might want to assign "Unknown" or skip
            continue
        for phase in phases:
            grouped[phase].append(p)
    return grouped


# -----------------------
# LLM-apufunktiot
# -----------------------

def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")
    return OpenAI(api_key=api_key)


def call_llm_markdown(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI model and return markdown text."""
    client = get_client()
    response = client.responses.create(
        model="gpt-4.1-mini",  # voit vaihtaa isompaan malliin tarvittaessa
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
#        response_format={"type": "json_object"}
    )
    # responses API: output -> list, then content -> list, then .text
    return response.output[0].content[0].text


# -----------------------
# Markdownin generointi
# -----------------------

def build_phase_context_snippet(papers: List[Dict], max_papers: int = 30) -> str:
    """
    Rakennetaan lyhyt "context"-teksti LLM:lle:
    listataan max_papers uusinta paperia (vuoden + otsikon + lyhyen summar).
    """
    # sort by year (and maybe id) descending for recency
    papers_sorted = sorted(papers, key=lambda p: p.get("year", 0), reverse=True)
    snippet_lines = []
    for p in papers_sorted[:max_papers]:
        title = p.get("title", "Untitled")
        year = p.get("year", "NA")
        summary = p.get("summary_short", "") or p.get("abstract", "")[:300]
        implications = p.get("implications_for_design_research") or []
        snippet_lines.append(f"- ({year}) **{title}**")
        if summary:
            snippet_lines.append(f"  - Summary: {summary}")
        if implications:
            for imp in implications[:2]:
                snippet_lines.append(f"  - Implication: {imp}")
    return "\n".join(snippet_lines)


def generate_phase_markdown(phase: str, papers: List[Dict]) -> str:
    """
    Pyytää LLM:ää tekemään Markdown-osion yhdelle design-vaiheelle:
    - Key themes
    - Recent developments (last 6–12 months)
    - Open research questions
    """
    if not papers:
        return f"## {phase}\n\n_There are currently no classified papers for this phase._\n"

    context = build_phase_context_snippet(papers)

    system_prompt = """
You are an expert in design cognition and design research, familiar with:
- Simon (bounded rationality, problem spaces)
- Schön (reflection-in-action, knowing-in-action)
- Cross, Dorst, Gero and contemporary design cognition work
- Industrial design practice and studio-based work

You are NOT writing for computer scientists. 
Assume the reader is an experienced design researcher (especially industrial design) 
with limited interest in ML technicalities.

You receive a list of papers related to ONE design phase. 
Many of them may use AI/ML methods.

Your job is to interpret these papers through a DESIGN COGNITION lens, not an ML lens.

Write a concise Markdown section with this structure:

## {phase_name}

### Key themes
- Focus on how designers think, act, decide, or collaborate in this phase.
- Avoid ML jargon unless truly necessary.

### Recent developments
- Explain how AI is changing design cognition or practice in this phase.
- When you mention technical methods (e.g. transformers, RL, diffusion), 
  explain in one short phrase what they enable for designers.

### Open research questions
- Pose questions about design cognition, creativity, collaboration, and tools.
- Avoid technical implementation details.

Style:
- Clear, analytic, no fluff.
- Short paragraphs and bullet points.
- Prefer design-cognition language (e.g. framing, reflection, co-evolution, fixation, externalisation) over ML jargon.
"""
    user_prompt = f"""
This design phase: {phase}

Here is a list of related papers with short summaries and implications:

{context}

Based on this, write the Markdown section as specified in the system prompt.
Do NOT talk about "the list above" explicitly; just use it as background knowledge.
"""

    return call_llm_markdown(system_prompt, user_prompt)


def generate_overview_markdown(papers: List[Dict]) -> str:
    """
    Luodaan koko kentän overview. Tässä katsotaan kaikkia papereita:
    - general trends across phases
    - evolution over time
    - important tensions / opportunities
    """
    if not papers:
        return "# AI & Design Research Overview\n\n_No papers in database yet._\n"

    # Build a compressed context listing
    context_lines = []
    # Sort by year ascending to show evolution
    papers_sorted = sorted(papers, key=lambda p: p.get("year", 0))
    for p in papers_sorted[-80:]:  # limit context to last ~80 papers
        title = p.get("title", "Untitled")
        year = p.get("year", "NA")
        phases = p.get("design_phase") or []
        summary = p.get("summary_short", "") or p.get("abstract", "")[:300]
        context_lines.append(f"- ({year}) {title}")
        if phases:
            context_lines.append(f"  - Phases: {', '.join(phases)}")
        if summary:
            context_lines.append(f"  - Summary: {summary}")
    context = "\n".join(context_lines)

    system_prompt = """
You are a design cognition researcher summarising recent AI & design work 
for an audience of experienced design researchers (industrial design, interaction design), 
not computer scientists.

Write a high-level Markdown overview called:

# AI & Design Research – Living Overview

Your focus:
- How AI is shaping design cognition, design practice, and designer–tool relationships.
- Connect to well-known design cognition ideas (without long history lessons):
  Simon (problem–solution space), Schön (reflection-in-action), Dorst (frame creation),
  Gero (FBS, design protocols), etc.

Structure your answer like this:

# AI & Design Research – Living Overview

## Big picture
- Emphasise design cognition and practice, not algorithms.

## Where AI is entering the design process
- Describe roles of AI in different design phases, in designer-centred terms.

## Emerging research themes
- Use language like: external representations, co-evolution, fixation, 
  exploration vs exploitation, human–AI co-creation, material thinking.

## Methodological patterns
- Talk about protocol studies, lab vs studio settings, think-aloud, 
  diary studies, research-through-design, etc.
- Mention ML methods only briefly and only when needed to understand the study.

## Gaps and opportunities
- Focus on what we still don’t know about designers’ thinking and practice with AI.

Write clearly and analytically, in short paragraphs. 
Avoid technical ML jargon and mathematical detail.
"""
    user_prompt = f"""
Here is a sample of papers with year, title, phases and short summaries:

{context}

Using this, write the overview as specified in the system prompt.
"""

    # Generate the LLM-written overview
    overview_md = call_llm_markdown(system_prompt, user_prompt)

    # ---------- FOUNDATIONS BLOCK INSERTION ----------
    FOUNDATIONS_BLOCK = """
## Foundations in Design Cognition

This living overview builds on established traditions in design cognition. 
The foundational assumptions come from classic work such as:

- **Herbert A. Simon** – design as search in an ill-structured problem–solution space; bounded rationality; heuristics instead of optimization.
- **Donald Schön** – reflection-in-action and knowing-in-action; the iterative “conversation with materials” that shapes problem framing and solution development.
- **Nigel Cross** – designerly ways of knowing; visual and material thinking; expertise and sketching as cognitive scaffolding.
- **Kees Dorst** – frame creation; co-evolution of problem and solution spaces; abductive reasoning as the core of design.
- **John S. Gero** – FBS (Function–Behaviour–Structure) transformations; situated cognition; design protocol analysis.

Alongside these canonical perspectives, this overview also assumes familiarity with 
**design space thinking**:

- **Exploration vs exploitation** – expanding versus narrowing the design space; broad search for possibilities versus refinement and optimization.
- **Informing vs filtering** – representations, feedback, and tools can *inform* designers by increasing the visibility of possibilities, or *filter* the space by constraining choices.
- **External representations** – sketches, models, prototypes, diagrams, and prompts act as cognitive partners, shaping what designers see, consider, and reinterpret.
- **Role of prototyping** – physical and digital prototypes support embodied cognition, exploratory experimentation, and rapid reframing through feedback from materials.

This overview also draws on research on **creative cognition** in design:

- **Divergence** – generating many, varied ideas (fluency), shifting between categories (flexibility), and reaching unusual or remote associations (originality).
- **Convergence** – evaluating, selecting, structuring, and developing ideas (elaboration); reducing the design space without premature fixation.
- **Fixation & defixation strategies** – the tension between creativity, precedence, and reuse; how tools and representations expand or restrict the search space.

Industrial design practice often integrates these principles in fluid, iterative processes where designers move between:

- framing and reframing  
- divergent concept generation  
- convergent interpretation and decision-making  
- prototyping and material exploration  
- negotiating constraints, opportunities, and meaning  

The synthesis below examines how **recent AI-supported design research** interacts with these foundational ideas:  
whether it expands or contracts the design space, alters framing activities, affects exploration/exploitation balance, introduces new forms of external representation, or reshapes the dynamics of reflective practice and creativity.
    """.strip()

    # Prepend the foundations section and preserve the remainder of the LLM output
    overview_md = (
        "# AI & Design Research – Living Overview\n\n"
        + FOUNDATIONS_BLOCK
        + "\n\n"
        + overview_md.split("\n", 1)[-1]
    )
    # ---------- END FOUNDATIONS BLOCK INSERTION ----------

    return overview_md


# -----------------------
# Pääfunktio
# -----------------------

def update_knowledge_markdown(
    db_path: str = "data/papers_structured.jsonl",
    knowledge_dir: str = "knowledge",
):
    """
    Päivittää:
      - knowledge/overview.md
      - knowledge/by_design_phase.md
    käyttäen data/papers_structured.jsonl -tietokantaa.
    """
    os.makedirs(knowledge_dir, exist_ok=True)

    papers = load_structured_papers(db_path)
    if not papers:
        print("[update_knowledge_base] No papers found, creating placeholder files.")
        overview_md = "# AI & Design Research – Living Overview\n\n_No papers yet._\n"
        phases_md = "# AI & Design Research by Design Phase\n\n_No papers yet._\n"
    else:
        grouped = group_papers_by_phase(papers)

        # 1) Overview
        print("[update_knowledge_base] Generating overview.md ...")
        overview_md = generate_overview_markdown(papers)

        # 2) By design phase
        print("[update_knowledge_base] Generating by_design_phase.md ...")
        phase_sections = ["# AI & Design Research by Design Phase\n"]
        for phase in PHASES:
            phase_papers = grouped.get(phase, [])
            section_md = generate_phase_markdown(phase, phase_papers)
            phase_sections.append(section_md)
        phases_md = "\n\n".join(phase_sections)

    # Write files
    overview_path = os.path.join(knowledge_dir, "overview.md")
    phases_path = os.path.join(knowledge_dir, "by_design_phase.md")

    with open(overview_path, "w", encoding="utf-8") as f:
        f.write(overview_md)

    with open(phases_path, "w", encoding="utf-8") as f:
        f.write(phases_md)

    print(f"[update_knowledge_base] Updated {overview_path} and {phases_path}.")