"""Construit la liste des publications de Gregory Faraut (pre-render Quarto).

Sources, dans l'ordre :
1. HAL (source principale : PDF en accès libre, lien HAL) ;
2. OpenAlex (base bibliographique ouverte, sans clé d'accès, interrogée par l'ORCID) :
   complète avec les articles pas encore déposés sur HAL ;
3. data/publications-manual.yml, saisi à la main et lu directement par Quarto
   (article accepté, pas encore référencé ailleurs).

Les articles de revue reçoivent les badges « JCR » et « SJR Qx » d'après data/journals.csv.
Les variantes du nom (Grégory, G. Faraut…) sont ramenées à « Gregory Faraut ».

Écrit data/publications.yml, lu par la liste de publications.qmd. Si une source ne répond
pas, le fichier existant est conservé : le site se construit toujours, avec la dernière
liste connue. Le journal de construction liste les articles à déposer sur HAL.

En local, les requêtes ne sont refaites que si le fichier a plus de 12 h
(forcer avec PUBS_REFRESH=1). Sur GitHub Actions (CI=true), elles sont toujours refaites.
Bibliothèque standard uniquement : rien à installer.
"""

import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HAL_ID = "gfaraut"
ORCID = "0000-0003-0388-932X"
OUT = Path(__file__).resolve().parent.parent / "data" / "publications.yml"
MAX_AGE = 12 * 3600

# Dépôts HAL où l'idHal « gfaraut » n'est pas rattaché à l'auteur : ajoutés à la main
# en attendant leur revendication dans HAL (après quoi on peut vider cette liste).
EXTRA_HAL_IDS = ["hal-02557589", "hal-04213244", "hal-01378583"]

# Travaux OpenAlex à ne jamais afficher (attribution erronée, doublon…) : DOI en minuscules.
EXCLUDE_DOIS: set[str] = set()

JOURNALS_CSV = OUT.parent / "journals.csv"

# Variantes de « Gregory Faraut » rencontrées dans HAL et OpenAlex.
ME_PATTERN = re.compile(r"(gr[ée]gory|g\.?)\s+faraut", re.I)
ME = "Gregory Faraut"

HAL_TYPES = {
    "ART": "Journal articles",
    "COMM": "Conference papers",
    "COUV": "Book chapters",
    "OUV": "Books",
    "DOUV": "Edited books",
    "POSTER": "Posters",
    "THESE": "Theses & HDR",
    "HDR": "Theses & HDR",
    "REPORT": "Reports",
    "PATENT": "Patents",
}
HAL_FIELDS = [
    "halId_s", "uri_s", "docType_s", "producedDateY_i", "title_s", "authFullName_s",
    "citationRef_s", "doiId_s", "fileMain_s", "journalTitle_s", "journalIssn_s", "journalEissn_s",
]
# Types OpenAlex retenus (éditoriaux, dépôts d'archives… sont ignorés).
OPENALEX_TYPES = {
    "article": "Journal articles",
    "conference-paper": "Conference papers",
    "proceedings-article": "Conference papers",
    "book-chapter": "Book chapters",
    "book": "Books",
}


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "quarto-site-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def norm(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def bare_doi(doi: str) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (doi or "").strip().lower())


def canon_authors(names: list[str]) -> list[str]:
    return [ME if ME_PATTERN.fullmatch(n.strip()) else n for n in names]


def load_journals() -> list[dict]:
    """data/journals.csv → liste de revues {issn, journal, jcr, sjr} (lignes « # » ignorées)."""
    if not JOURNALS_CSV.exists():
        return []
    import csv
    lines = [l for l in JOURNALS_CSV.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.lstrip().startswith("#")]
    return [{k: (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(lines, delimiter=";")]


def tag_journal(item: dict, issns: list[str], journals: list[dict], missing: set) -> None:
    """Ajoute jcr / sjr à un article de revue, d'après son ISSN ou, à défaut, son titre."""
    if item["categories"][0] != "Journal articles":
        return
    issns = {i.strip() for i in issns if i}
    for j in journals:
        if j["issn"] in issns or norm(j["journal"]) == norm(item["venue"]):
            if j.get("jcr", "").lower() in ("yes", "oui", "y", "1", "true"):
                item["jcr"] = True
            if re.fullmatch(r"Q[1-4]", j.get("sjr", "").upper()):
                item["sjr"] = j["sjr"].upper()
            return
    missing.add(f"{item['venue']} (ISSN {', '.join(sorted(issns)) or '?'})")


# ---------------------------------------------------------------- HAL

def fetch_hal() -> list[dict]:
    q = f"authIdHal_s:{HAL_ID}"
    if EXTRA_HAL_IDS:
        q += " OR halId_s:(" + " OR ".join(EXTRA_HAL_IDS) + ")"
    params = {"q": q, "rows": 1000, "wt": "json", "fl": ",".join(HAL_FIELDS)}
    return get_json("https://api.archives-ouvertes.fr/search/?" + urllib.parse.urlencode(params))[
        "response"]["docs"]


def split_venue(ref: str) -> tuple[str, str]:
    """citationRef_s → (revue ou conférence, reste de la référence), en texte brut.

    Le lien DOI est retiré (bouton séparé). Le modèle EJS met la revue en italique et le
    nom de Greg en gras : Quarto échappe le HTML contenu dans les données d'une liste.
    """
    ref = re.sub(r",?\s*<a [^>]*>&#x27E8;.*?&#x27E9;</a>", "", ref)
    m = re.match(r"\s*<i>(.*?)</i>\s*,?\s*(.*)", ref, re.S)
    name, rest = (m.group(1), m.group(2)) if m else ("", ref)

    def strip(t: str) -> str:
        return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()

    rest = strip(rest).rstrip(",. ")
    return strip(name), (rest + ".") if rest else ""


def hal_item(d: dict, journals: list[dict], missing: set) -> dict:
    year = d.get("producedDateY_i", 0)
    venue, venue_rest = split_venue(d.get("citationRef_s", ""))
    title = d["title_s"][0] if isinstance(d.get("title_s"), list) else d.get("title_s", "")
    item = {
        "title": title,
        "date": f"{year}-01-01",
        "year": str(year),
        "categories": [HAL_TYPES.get(d.get("docType_s"), "Other")],
        "authors": canon_authors(d.get("authFullName_s", [])),
        "venue": venue,
        "venue_rest": venue_rest,
        "hal": d.get("uri_s", ""),
        "source": "HAL",
    }
    if d.get("doiId_s"):
        item["doi"] = "https://doi.org/" + d["doiId_s"]
    if d.get("fileMain_s"):
        item["pdf"] = d["fileMain_s"]
    tag_journal(item, [d.get("journalIssn_s"), d.get("journalEissn_s")], journals, missing)
    return item


def dedupe_hal(docs: list[dict]) -> list[dict]:
    """Un même document déposé deux fois sur HAL : on garde le dépôt avec PDF.

    Le type fait partie de la clé : un article de revue et une communication de même
    titre (même année) sont deux publications distinctes.
    """
    seen: dict[tuple, dict] = {}
    for d in docs:
        title = d["title_s"][0] if isinstance(d.get("title_s"), list) else d.get("title_s", "")
        key = (norm(title), d.get("producedDateY_i"), d.get("docType_s"))
        if key not in seen or (d.get("fileMain_s") and not seen[key].get("fileMain_s")):
            seen[key] = d
    return list(seen.values())


# ---------------------------------------------------------------- OpenAlex

def fetch_openalex() -> list[dict]:
    params = {
        "filter": f"author.orcid:{ORCID}",
        "per-page": 200,
        "select": "doi,title,publication_year,type,primary_location,authorships,biblio",
    }
    return get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params))["results"]


def openalex_item(w: dict, journals: list[dict], missing: set) -> dict | None:
    source = (w.get("primary_location") or {}).get("source") or {}
    category = OPENALEX_TYPES.get(w.get("type"))
    if not category or source.get("type") == "repository" or not w.get("title"):
        return None
    venue = source.get("display_name", "")
    if "PapersOnLine" in venue:  # actes de congrès IFAC publiés comme une revue
        category = "Conference papers"
    year = w.get("publication_year", 0)
    b = w.get("biblio") or {}
    rest = [f"vol. {b['volume']}" if b.get("volume") else "",
            f"no. {b['issue']}" if b.get("issue") else "",
            f"pp. {b['first_page']}–{b['last_page']}" if b.get("first_page") and b.get("last_page") else "",
            str(year)]
    item = {
        "title": html.unescape(w["title"]),
        "date": f"{year}-01-01",
        "year": str(year),
        "categories": [category],
        "authors": canon_authors([a["author"]["display_name"] for a in w.get("authorships", [])]),
        "venue": venue,
        "venue_rest": ", ".join(r for r in rest if r) + ".",
        "source": "OpenAlex",
    }
    if w.get("doi"):
        item["doi"] = "https://doi.org/" + bare_doi(w["doi"])
    tag_journal(item, (source.get("issn") or []) + [source.get("issn_l")], journals, missing)
    return item


# ---------------------------------------------------------------- assemblage

def fresh_enough() -> bool:
    if os.environ.get("CI") or os.environ.get("PUBS_REFRESH") or os.environ.get("HAL_REFRESH"):
        return False
    return OUT.exists() and time.time() - OUT.stat().st_mtime < MAX_AGE


def main() -> None:
    if fresh_enough():
        print(f"Publications : {OUT.name} récent, sources non interrogées (PUBS_REFRESH=1 pour forcer).")
        return
    try:
        hal_docs = fetch_hal()
        oa_works = fetch_openalex()
    except Exception as e:  # réseau absent, service indisponible…
        print(f"Publications : requête impossible ({e}) ; liste existante conservée.", file=sys.stderr)
        return

    journals, missing = load_journals(), set()
    items = [hal_item(d, journals, missing) for d in dedupe_hal(hal_docs)]
    known_dois = {bare_doi(i["doi"]) for i in items if i.get("doi")}
    known_titles = {norm(i["title"]) for i in items}
    added = []
    for w in oa_works:
        it = openalex_item(w, journals, missing)
        if not it:
            continue
        doi = bare_doi(it.get("doi", ""))
        if doi in EXCLUDE_DOIS or (doi and doi in known_dois) or norm(it["title"]) in known_titles:
            continue
        items.append(it)
        added.append(it)
        known_dois.add(doi)
        known_titles.add(norm(it["title"]))

    items.sort(key=lambda i: i["year"], reverse=True)
    OUT.parent.mkdir(exist_ok=True)
    # Le JSON est du YAML valide : pas de dépendance à PyYAML.
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Publications : {len(items) - len(added)} depuis HAL, {len(added)} depuis OpenAlex.")
    for it in added:
        print(f"  À déposer sur HAL : {it['year']} — {it['title']} ({it.get('doi', 'sans DOI')})")
    for m in sorted(missing):
        print(f"  Revue absente de data/journals.csv : {m}")


if __name__ == "__main__":
    main()
