import os
import requests

def download_paperpile_bib(dest_path="data/paperpile.bib"):
    url = os.environ.get("PAPERPILE_BIB_URL")
    if not url:
        print("[download_paperpile_bib] No PAPERPILE_BIB_URL defined, skipping download.")
        return False

    print(f"[download_paperpile_bib] Downloading BibTeX from: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"[download_paperpile_bib] Saved to {dest_path}")
        return True
    except Exception as e:
        print(f"[download_paperpile_bib] Error downloading BibTeX: {e}")
        return False