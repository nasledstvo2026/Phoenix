#!/usr/bin/env python3
"""Скачивание каталога Пиранези из Rijksmuseum (Search API, без ключа)."""
import json
import time
import urllib.request

BASE = "https://data.rijksmuseum.nl"
SEARCH = BASE + "/search/collection"
HDRS = {"Accept": "application/json",
        "User-Agent": "Phoenix-catalog-builder/0.1 (personal non-commercial research)"}


def get(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def label_to_str(v):
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("en", "nl", "und", "value"):
            if v.get(k):
                return v[k]
        return "; ".join(str(x) for x in v.values())
    return None


def main():
    # 1) все страницы поиска -> ID объектов
    ids = []
    url = SEARCH + "?creator=Piranesi"
    page = 0
    while url and page < 100:
        d = get(url)
        for it in d.get("orderedItems", []) or []:
            iid = it.get("id")
            if iid and iid not in ids:
                ids.append(iid)
        nxt = d.get("next") or {}
        url = nxt.get("id")
        page += 1
        print(f"page {page}: {len(ids)} ids", flush=True)
        time.sleep(0.3)

    print("TOTAL_IDS", len(ids), flush=True)

    # 2) резолвим каждый объект
    records = []
    for i, iid in enumerate(ids):
        num = iid.rstrip("/").split("/")[-1]
        try:
            d = get(f"{BASE}/{num}")
            rec = {"id": iid, "number": num, "names": [],
                   "identifier": None, "date": None, "technique": None,
                   "type": d.get("type")}

            for idf in d.get("identified_by", []) or []:
                if idf.get("type") == "Name" and idf.get("content"):
                    rec["names"].append(idf["content"])
                elif idf.get("type") == "Identifier" and idf.get("content"):
                    rec["identifier"] = idf["content"]

            pb = d.get("produced_by") or {}
            ts = pb.get("timespan") or {}
            if ts:
                rec["date"] = (label_to_str(ts.get("label"))
                               or ts.get("begin_of_the_begin")
                               or ts.get("end_of_the_end"))
            techs = pb.get("technique") or []
            if techs:
                names = []
                for idf in techs[0].get("identified_by", []) or []:
                    if idf.get("type") == "Name" and idf.get("content"):
                        names.append(idf["content"])
                rec["technique"] = "; ".join(names) if names else None

            records.append(rec)
        except Exception as e:
            print("ERR", num, e, flush=True)
        if (i + 1) % 25 == 0:
            print(f"resolved {i + 1}/{len(ids)}", flush=True)
        time.sleep(0.25)

    with open("data/catalog_raw.json", "w", encoding="utf-8") as f:
        json.dump({"ids": ids, "records": records}, f,
                  ensure_ascii=False, indent=1)
    print("SAVED", len(records), flush=True)


if __name__ == "__main__":
    main()
