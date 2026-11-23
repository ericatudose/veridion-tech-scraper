import os, json
import pandas as pd

with open("signatures.json") as f:
    reguli = json.load(f)

df = pd.read_parquet("domains.parquet")
rezultate = []

def fragment(text, poz):
    start = max(0, poz - 30)
    return text[start:poz + 60].replace("\n", " ")

for domeniu in df["root_domain"]:
    cale_html = f"pages/{domeniu}.html"
    if not os.path.exists(cale_html):
        continue

    with open(cale_html, encoding="utf-8") as f:
        html = f.read().lower()
    with open(f"pages/{domeniu}.json") as f:
        info = json.load(f)
    headere = {k.lower(): v.lower() for k, v in info["headers"].items()}

    gasite = []
    for regula in reguli:
        caut = regula["caut"]
        if regula["unde"] == "html":
            poz = html.find(caut)
            if poz != -1:
                gasite.append({"tehnologie": regula["nume"],
                               "dovada": "html: ..." + fragment(html, poz) + "..."})
        elif regula["unde"] == "header":
            valoare = headere.get(regula["header"], "")
            if caut in valoare:
                gasite.append({"tehnologie": regula["nume"],
                               "dovada": f"header {regula['header']}: {valoare}"})

    rezultate.append({"domeniu": domeniu, "tehnologii": gasite})
    print(domeniu, len(gasite))

with open("results.json", "w") as f:
    json.dump(rezultate, f, indent=2, ensure_ascii=False)

total = sum(len(r["tehnologii"]) for r in rezultate)
print("Site-uri analizate:", len(rezultate), "| Tehnologii gasite:", total)