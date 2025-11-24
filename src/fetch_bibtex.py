import os
from typing import List, Dict

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode


def load_bibtex(path: str) -> List[Dict]:
    """
    Loads a BibTeX file exported from Paperpile and converts entries into
    the unified paper structure used by the rest of the agent pipeline.

    Expected output fields:
        - id
        - title
        - abstract
        - authors
        - year
        - source
        - published
        - categories
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"BibTeX file not found: {path}")

    print(f"[fetch_bibtex] Loading BibTeX: {path}")

    with open(path, "r") as bibtex_file:
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    papers: List[Dict] = []

    for entry in bib_database.entries:
        # Skip items missing title
        if "title" not in entry:
            continue

        # Unique ID
        entry_id = entry.get("ID", entry.get("title", "untitled")).replace(" ", "_")

        # Authors
        if "author" in entry:
            authors = [a.strip() for a in entry["author"].split(" and ")]
        else:
            authors = []

        # Source (journal, booktitle, or "bibtex")
        source = (
            entry.get("journal")
            or entry.get("booktitle")
            or entry.get("publisher")
            or "bibtex"
        )

        # Year handling
        try:
            year = int(entry.get("year", "0"))
        except ValueError:
            year = 0

        # Abstract if Paperpile exported it
        abstract = entry.get("abstract", "").strip()

        papers.append(
            {
                "id": f"bib:{entry_id}",
                "title": entry.get("title", "").strip(),
                "authors": authors,
                "abstract": abstract,
                "year": year,
                "source": source,
                "published": str(year) if year else "",
                "categories": ["bibtex"],
            }
        )

    print(f"[fetch_bibtex] Loaded {len(papers)} entries from BibTeX.")

    return papers