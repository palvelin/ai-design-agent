import os
import json
from typing import List, Dict


def update_jsonl_db(path: str, new_records: List[Dict], id_key: str = "id") -> None:
    """
    Lukee olemassa olevan JSONL-tiedoston (jos on),
    päivittää/korvaa rivit `id_key`-kentän perusteella,
    ja kirjoittaa koko setin takaisin tiedostoon.

    Tämä pitää huolen, ettei sama arXiv-paperi mene moneen kertaan eri muodoissa.
    """
    existing: Dict[str, Dict] = {}

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rec_id = rec.get(id_key)
                if rec_id:
                    existing[rec_id] = rec

    for rec in new_records:
        rec_id = rec.get(id_key)
        if not rec_id:
            continue
        existing[rec_id] = rec

    # Järjestetään vaikka julkaisuajan mukaan, jos löytyy
    def sort_key(item):
        rec = item[1]
        return (rec.get("published", ""), rec.get("title", ""))

    sorted_records = [rec for _, rec in sorted(existing.items(), key=sort_key)]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in sorted_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[utils.update_jsonl_db] Database now has {len(sorted_records)} records.")

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
                records.append(json.loads(line))
    except FileNotFoundError:
        pass
    return records