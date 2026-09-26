#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор интерактивной страницы «Карта взаимосвязей ФЗ» для сайта.

Данные:  law-ingest/graph_v2.json + law-ingest/legal_map.json
Выход:   fz-graph.html (самодостаточная страница, lib — assets/vis-network.min.js)

Запуск:  python3 build_graph_page.py
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "law-ingest"

LAW_COLORS = {
    "FZ-425": "#dc2626", "FZ-229": "#2563eb", "FZ-127": "#7c3aed", "GK-2": "#0d9488",
    "NK-1": "#ea580c", "NK-2": "#ca8a04", "UPK": "#4f46e5", "FZ-603": "#db2777",
}
TYPE_COLORS = {
    "amends": "#dc2626", "refers": "#64748b", "procedure": "#f59e0b",
    "delegates": "#0891b2", "defines": "#65a30d", "supersedes": "#be185d",
}
# Узлы/рёбра отложенного эффекта (ядро вступает в силу 01.01.2027 по ст. 25 425-ФЗ)
DELAYED_NODES = ["FZ-425:20", "NK-1:46", "NK-1:60"]


def main() -> int:
    g = json.loads((DATA / "graph_v2.json").read_text(encoding="utf-8"))
    reg = json.loads((DATA / "laws.json").read_text(encoding="utf-8"))
    legal_meta = json.loads((DATA / "legal_map.json").read_text(encoding="utf-8"))

    laws = {l["code"]: {"number": l["number"], "title": l["title"],
                        "revision": l["revision"], "in_force_from": l["in_force_from"],
                        "color": LAW_COLORS.get(l["code"], "#94a3b8")}
            for l in reg["laws"]}

    nodes = [[n["id"], n["law"], n["article"], (n.get("title") or "")[:90],
              1 if n.get("in_core") else 0, 1 if n.get("in_corpus") else 0]
             for n in g["nodes"]]
    edges = []
    for e in g["edges"]:
        par = e.get("paragraph")
        ev = (e.get("evidence") or "").replace("\n", " ").strip()[:120]
        edges.append([e["from"], e["to"], e["type"], e.get("confidence"),
                      1 if e.get("cross") else 0, par, ev])
    legal = [{"from": x["from"], "to": x["to"], "meaning": x.get("meaning"),
              "role_from": x.get("role_from"), "role_to": x.get("role_to"),
              "effect": x.get("effect"), "applies_when": x.get("applies_when"),
              "priority": x.get("priority"), "status": x.get("status")}
             for x in legal_meta.get("entries", [])]

    payload = {
        "stats": g["stats"], "laws": laws, "nodes": nodes, "edges": edges,
        "legal": legal, "delayed": DELAYED_NODES,
        "type_colors": TYPE_COLORS,
        "disclaimer": legal_meta.get("disclaimer", ""),
    }

    tpl = (BASE / "graph_page.template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__PAYLOAD__*/", json.dumps(payload, ensure_ascii=False))
    out = BASE / "fz-graph.html"
    out.write_text(html, encoding="utf-8")
    print(f"OK: {out} ({len(html)} байт); узлов {len(nodes)}, рёбер {len(edges)}, "
          f"курируемых трактовок {len(legal)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
