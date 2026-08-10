#!/usr/bin/env python3
"""Сборка data/catalog.json из сырых данных: группировка по сериям."""
import json
import re
import os

RAW = "data/catalog_raw.json"
OUT = "data/catalog.json"

# Правила определения серии: проверяются по порядку (первое совпадение)
RULES = [
    ("carceri", "Carceri d'Invenzione",
     ["carceri", "prison", "gevangenis", "kerker", "dungeon"]),
    ("grotteschi", "Grotteschi / Capricci",
     ["grottesco", "grotesque", "grotesk", "capriccio", "capricci", "caprice"]),
    ("prima_parte", "Prima Parte di Architetture e Prospettive",
     ["prima parte", "architetture", "prospettive", "eerste deel",
      "architectuur", "perspectieven"]),
    ("antichita_albano", "Antichità d'Albano e di Castel Gandolfo",
     ["antichità d'albano", "antichita d'albano", "castel gandolfo",
      "albano", "albaanse", "spelonca", "lago alban"]),
    ("antichita", "Antichità Romane",
     ["antichit", "antiqu", "oudheid", "avanzi", "avanzo",
      "bassorilievo", "bas-reliëf", "reliëf", "sarcofaag", "sarcophagus",
      "vondsten", "opgraving", "sepolcro", "sepolcri", "tomba", "tombe",
      "iscrizioni", "inscripties", "inscripti", "sepolcrali", "grafkelder",
      "grafkamers", "grafmonument", "pianta", "plattegrond", "sezione",
      "doorsnede", "dimostrazione", "sustruzion", "marcello", "marcellus",
      "piscina", "via appia", "appia", "muur", "muren", "marmerblokken",
      "constructie", "fragmenten", "vincibus", "teatro", "theater",
      "theatre", "spaccato", "hypocaustum", "trepidarium", "piramide"]),
    ("campus_martius", "Campus Martius",
     ["campus martius", "campus martii", "campus martis"]),
    ("lapides", "Lapides Capitolini",
     ["lapides", "capitolini"]),
    ("vasi", "Vasi, Candelabri, Cippi",
     ["vaso", "vase", "candelabro", "candelabrum", "candelaber",
      "cippo", "cippi", "urne", "urn", "lucerne", "lamp", "ambtszetel",
      "troon", "throne", "vaas", "kandelaber", "tripod", "altaar",
      "rhyton", "trireem", "bucrania", "voetstuk", "schaal"]),
    ("camini", "Diverse maniere d'adornare i cammini",
     ["chimney", "chimneypiece", "camino", "camini", "cammini", "mantelpiece",
      "cheminée", "schoorsteen", "schouw"]),
    ("trofei", "Trofei di Ottaviano Augusto",
     ["trofeo", "trofei", "trophy", "trofee", "trophaeum", "trophies"]),
    ("colonna", "Colonne Traiana e Antonina",
     ["colonna", "column", "zuil", "traian", "trajan", "antonine",
      "antonijn", "spiral column"]),
    ("paestum", "Paestum (Differentes vues de Pesto)",
     ["paestum", "pesto", "poseidonia"]),
    ("magnificenza", "Della Magnificenza ed Architettura de' Romani",
     ["magnificenza", "magnificence"]),
    ("vedute", "Vedute di Roma (виды Рима)",
     ["veduta", "vedute", "gezicht", "view of", "view in", "view at",
      "rome", "roma", "ruïne", "ruine", "ruin", "colosseum", "colosseo",
      "piazza", "foro", "forum", "campidoglio", "capitol", "palatino",
      "esquilino", "tivoli", "frescat", "castel", "s. pietro",
      "san pietro", "st. peter", "arco", "tempio", "temple", "tempel",
      "aquedotto", "acquedotto", "aquaduct", "anfiteatro", "amphitheater",
      "mausoleo", "mausoleum", "portico", "basilica", "terme", "thermen",
      "villa", "obelisco", "obelisk", "sibilla", "sibyl", "grot",
      "grotto", "ponte", "brug", "bridge", "kerk", "church",
      "campo", "santa", "stefano", "rotondo", "mecenate", "adriana",
      "neroniani", "claudia", "severo", "tito", "constant", "costantino",
      "sint-pieters", "vaticaan", "engelenburcht", "verlichting"]),
]

SERIES_ORDER = [r[0] for r in RULES]


def detect_series(title):
    t = (title or "").lower()
    for key, name, words in RULES:
        for w in words:
            if w in t:
                return key
    return "other"


def year_only(date_str):
    """ISO '1761-01-01T00:00:00Z' -> '1761'"""
    if not date_str:
        return None
    m = re.match(r"(\d{4})", str(date_str))
    return m.group(1) if m else None


def clean_title(names, number):
    """Лучшее название: полное, без дублей и чисто-датировочных строк."""
    cands = []
    for n in names or []:
        n = re.sub(r"\s+", " ", n).strip()
        if not n:
            continue
        if re.fullmatch(r"[\d\s\-–—./]+", n):  # только дата/цифры
            continue
        if n not in cands:
            cands.append(n)
    if cands:
        return cands[0]
    return f"Объект {number}"


def main():
    with open(RAW, encoding="utf-8") as f:
        raw = json.load(f)

    groups = {key: [] for key, name, words in RULES}
    groups["other"] = []
    total = 0

    for rec in raw["records"]:
        title = clean_title(rec.get("names"), rec.get("number"))
        key = detect_series(title)
        identifier = rec.get("identifier") or ""
        number = rec.get("number") or ""
        if identifier:
            url = f"https://www.rijksmuseum.nl/en/collection/{identifier}"
        else:
            url = f"https://id.rijksmuseum.nl/{number}"
        item = {
            "title": title,
            "date": year_only(rec.get("date")),
            "technique": rec.get("technique"),
            "identifier": identifier or None,
            "url": url,
        }
        groups[key].append(item)
        total += 1

    # сортировка внутри серий: по названию
    for key in groups:
        groups[key].sort(key=lambda x: x["title"].lower())

    series = []
    for key in SERIES_ORDER:
        if groups[key]:
            name = dict((r[0], r[1]) for r in RULES)[key]
            series.append({"key": key, "name": name, "items": groups[key]})
    if groups["other"]:
        series.append({"key": "other", "name": "Прочее / без серии",
                       "items": groups["other"]})

    out = {"source": "Rijksmuseum (data.rijksmuseum.nl, Search API)",
           "query": "creator=Piranesi", "total": total, "series": series}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("TOTAL", total)
    for s in series:
        print(f"  {s['key']}: {len(s['items'])}")


if __name__ == "__main__":
    main()
