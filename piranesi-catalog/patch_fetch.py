#!/usr/bin/env python3
"""Докачка пропущенных объектов (устойчивость к timespan-списку)."""
import json
import time
import urllib.request

BASE = "https://data.rijksmuseum.nl"
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


def resolve(iid):
    num = iid.rstrip("/").split("/")[-1]
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
    if isinstance(ts, list):
        ts = ts[0] if ts else {}
    if isinstance(ts, dict) and ts:
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
    return rec


def main():
    with open("data/catalog_raw.json", encoding="utf-8") as f:
        raw = json.load(f)
    have = {r["id"] for r in raw["records"]}
    missing = [i for i in raw["ids"] if i not in have]
    print("MISSING", len(missing), flush=True)
    ok = 0
    for iid in missing:
        try:
            raw["records"].append(resolve(iid))
            ok += 1
        except Exception as e:
            print("ERR", iid, e, flush=True)
        time.sleep(0.3)
    with open("data/catalog_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)
    print("ADDED", ok, "TOTAL", len(raw["records"]), flush=True)


if __name__ == "__main__":
    main()
