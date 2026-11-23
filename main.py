import os, json
import requests
import pandas as pd

df = pd.read_parquet("domains.parquet")
os.makedirs("pages", exist_ok=True)
erori = []

for domeniu in df["root_domain"]:
    if os.path.exists(f"pages/{domeniu}.html"):
        continue  # l-am descărcat deja

    r = None
    for schema in ["https", "http"]:
        try:
            r = requests.get(f"{schema}://{domeniu}", timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
            break
        except Exception as e:
            ultima_eroare = str(e)

    if r is None:
        erori.append({"domeniu": domeniu, "eroare": ultima_eroare})
        print("EROARE", domeniu)
        continue

    with open(f"pages/{domeniu}.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    with open(f"pages/{domeniu}.json", "w") as f:
        json.dump({"status": r.status_code,
                   "url_final": r.url,
                   "headers": dict(r.headers),
                   "cookies": r.cookies.get_dict()}, f, indent=2)
    print("OK", domeniu)

with open("erori.json", "w") as f:
    json.dump(erori, f, indent=2)
print("Gata. Erori:", len(erori))