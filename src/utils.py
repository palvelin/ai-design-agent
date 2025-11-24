import os
import json
from typing import List, Dict


def load_jsonl_db(db_path: str) -> List[Dict]:
    """
    Lataa JSONL-tietokannan listaksi dict-olioita.
    Jos tiedostoa ei ole, palauttaa tyhjän listan.
    """
    records: List[Dict] = []
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # ohitetaan mahdolliset rikkinäiset rivit
                    continue
    except FileNotFoundError:
        pass
    return records


def update_jsonl_db(db_path: str, new_records: List[Dict]) -> None:
    """
    Päivittää JSONL-tietokannan:
    - lukee olemassa olevat rivit
    - deduplaa id-kentän perusteella
    - ylikirjoittaa tiedoston yhdistetyllä datalla
    """
    existing_by_id: Dict[str, Dict] = {}

    # Lue olemassa oleva tietokanta (jos on)
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    # ohita rikkinäinen rivi
                    continue
                rec_id = rec.get("id")
                if rec_id:
                    existing_by_id[rec_id] = rec
    except FileNotFoundError:
        # ei entuudestaan kantaa → aloitetaan tyhjästä
        pass

    # Päivitä/ lisää uudet
    for rec in new_records:
        rec_id = rec.get("id")
        if not rec_id:
            continue
        existing_by_id[rec_id] = rec

    # Kirjoita takaisin tiedostoon
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        for rec in existing_by_id.values():
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[utils.update_jsonl_db] Database now has {len(existing_by_id)} records.")