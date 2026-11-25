import os, re, json, glob
import pandas as pd
from bs4 import BeautifulSoup

# ---------- 1. Regulile mele ----------
with open("signatures.json") as f:
    reguli_mele = json.load(f)

# ---------- 2. Regulile Wappalyzer ----------
def lista(x):
    return x if isinstance(x, list) else [x]

def compileaza(model):
    model = model.split("\\;")[0]          # taie "\;version:..." etc.
    try:
        return re.compile(model, re.I)
    except re.error:
        return None                         # unele regex-uri sunt scrise pentru JavaScript

wapp = {}
for cale in glob.glob("webappanalyzer/src/technologies/*.json"):
    with open(cale, encoding="utf-8") as f:
        wapp.update(json.load(f))

reguli_wapp = []
for nume, t in wapp.items():
    r = {"nume": nume,
         "implies": [i.split("\\;")[0] for i in lista(t.get("implies", []))],
         "html": [c for c in map(compileaza, lista(t.get("html", []))) if c],
         "scriptSrc": [c for c in map(compileaza, lista(t.get("scriptSrc", []))) if c]}
    for camp in ["headers", "cookies", "meta"]:
        r[camp] = {}
        for cheie, model in t.get(camp, {}).items():
            modele = [c for c in map(compileaza, lista(model)) if c]
            if modele:
                r[camp][cheie.lower()] = modele
    reguli_wapp.append(r)

print("Reguli Wappalyzer incarcate:", len(reguli_wapp))

# ---------- 3. Detectia ----------
df = pd.read_parquet("domains.parquet")
rezultate = []

for domeniu in df["root_domain"]:
    if not os.path.exists(f"pages/{domeniu}.html"):
        continue
    with open(f"pages/{domeniu}.html", encoding="utf-8") as f:
        html = f.read()[:300000]            # limităm, ca să nu dureze prea mult
    with open(f"pages/{domeniu}.json") as f:
        info = json.load(f)

    html_mic = html.lower()
    headere = {k.lower(): v for k, v in info["headers"].items()}
    cookies = {k.lower(): v for k, v in info["cookies"].items()}
    soup = BeautifulSoup(html, "html.parser")
    scripturi = [s["src"] for s in soup.find_all("script", src=True)]
    meta = {m["name"].lower(): m.get("content", "")
            for m in soup.find_all("meta") if m.get("name")}

    gasite = {}
    def adauga(nume, dovada):
        if nume not in gasite:
            gasite[nume] = dovada

    # a) regulile mele
    for regula in reguli_mele:
        if regula["unde"] == "html":
            poz = html_mic.find(regula["caut"])
            if poz != -1:
                adauga(regula["nume"], "html: ..." + html_mic[max(0, poz-30):poz+60] + "...")
        else:
            valoare = headere.get(regula["header"], "").lower()
            if regula["caut"] in valoare:
                adauga(regula["nume"], f"header {regula['header']}: {valoare}")

    # b) regulile Wappalyzer
    for r in reguli_wapp:
        dovada = None
        for c in r["scriptSrc"]:
            s = next((s for s in scripturi if c.search(s)), None)
            if s:
                dovada = f"script src: {s}"
                break
        if not dovada:
            for c in r["html"]:
                m = c.search(html)
                if m:
                    dovada = "html: " + m.group(0)[:100]
                    break
        if not dovada:
            for camp, valori, eticheta in [("headers", headere, "header"),
                                           ("cookies", cookies, "cookie"),
                                           ("meta", meta, "meta")]:
                for cheie, modele in r[camp].items():
                    if cheie in valori and any(c.search(valori[cheie]) for c in modele):
                        dovada = f"{eticheta} {cheie}: {valori[cheie][:100]}"
                        break
                if dovada:
                    break
        if dovada:
            adauga(r["nume"], dovada)

    # c) tehnologii deduse (implies)
    for nume in list(gasite):
        for dedus in next((r["implies"] for r in reguli_wapp if r["nume"] == nume), []):
            adauga(dedus, f"dedus din {nume}")

    rezultate.append({"domeniu": domeniu,
                      "tehnologii": [{"tehnologie": n, "dovada": d} for n, d in gasite.items()]})
    print(domeniu, len(gasite))

with open("results.json", "w") as f:
    json.dump(rezultate, f, indent=2, ensure_ascii=False)

total = sum(len(r["tehnologii"]) for r in rezultate)
distincte = {t["tehnologie"] for r in rezultate for t in r["tehnologii"]}
zero = [r["domeniu"] for r in rezultate if not r["tehnologii"]]
print("Site-uri:", len(rezultate), "| Detectii:", total,
      "| Tehnologii distincte:", len(distincte), "| Site-uri cu 0:", len(zero))
print("Fara tehnologii:", zero)