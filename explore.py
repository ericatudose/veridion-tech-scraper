import os, re
from collections import Counter

contor = Counter()
for fisier in os.listdir("pages"):
    if fisier.endswith(".html"):
        with open(f"pages/{fisier}", encoding="utf-8") as f:
            html = f.read().lower()
        domenii = set(re.findall(r'src="https?://([^/"]+)', html))
        contor.update(domenii)

for domeniu, nr in reversed(contor.most_common(40)):
    print(nr, domeniu)