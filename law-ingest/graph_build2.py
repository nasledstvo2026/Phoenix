#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Этап 3 v2: типизированный граф взаимосвязей ФЗ с обогащением.

Отличия от graph_build.py:
  • рёбра получают confidence, origin (auto|curated), direction, law_from/law_to, cross;
  • у рёбер — пункт цели (paragraph), если в контексте указан «пункт N статьи M»;
  • расширены типы: amends, supersedes, delegates, defines, refers, procedure;
  • улучшено разрешение ссылок: имя закона из контекста → иначе «свой» закон
    (stub-узел, если статья не в корпусе) → иначе разрешено по уникальности;
  • очевиден «хвост» неразрешённых ссылок (unresolved.json).

Выход:
  law-ingest/graph_v2.json          — полный граф
  law-ingest/graph_cross_v2.json    — только межзаконные рёбра
  law-ingest/unresolved.json        — очередь неразрешённых ссылок
"""
import collections
import json
import re
import sys
from pathlib import Path

BASE = Path("/home/user1/phoenix")
DATA = BASE / "law-ingest"

REF = re.compile(r"стать[яиюей]{1,3}\s+(\d+(?:\.\d+)?)")
PAR = re.compile(r"пункт\w*\s+(\d+(?:\.\d+)?)")

# имя «чужого» закона в контексте
LAWTALK = {
    "NK-2": r"части\s+второй\s+настоящего\s+Кодекса|Налогового\s+кодекса\s*\(часть\s+вторая\)|часть\s+вторая\s+Кодекса",
    "NK-1": r"части\s+первой\s+настоящего\s+Кодекса|Налогового\s+кодекса\s*\(часть\s+первая\)|часть\s+первая\s+Кодекса",
    "GK-2": r"Гражданского\s+кодекса",
    "UPK": r"Уголовно-процессуального\s+кодекса",
    "FZ-229": r"об\s+исполнительном\s+производстве",
    "FZ-127": r"о\s+несостоятельности\s*\(банкротстве\)",
    "FZ-425": r"\b425-ФЗ\b",
    "FZ-603": r"\b603-ФЗ\b",
}
NK_GENERIC = re.compile(r"Налогового\s+кодекса(?!\s*\()", re.I)
SAME = re.compile(r"настоящего\s+(Кодекса|Федерального\s+закона)", re.I)

AMEND = re.compile(r"внести|изложить\s+в\s+следующей\s+редакции|дополнить|признать\s+утратив")
SUPER = re.compile(r"применяется\s+с|до\s+дня\s+вступления\s+в\s+силу|переходн\w+|утрачивает\s+силу\s+с")
DELEG = re.compile(r"Правительств|федеральн\w+\s+орган\w+\s+исполнительной\s+власти|уполномоченн\w+\s+орган")
DEFINE = re.compile(r"по\s+смыслу|применительно\s+к|определяется\s+в\s+порядке|понимается")
REFERS = re.compile(r"в\s+соответствии|порядке,\s+установленном|во\s+исполнение|с\s+учётом")

CORE = {
    "NK-1:46", "NK-1:60", "NK-1:135", "FZ-229:46", "FZ-229:47",
    "GK-2:855", "FZ-425:1", "FZ-425:20",
}


def classify(ctx: str) -> str:
    if AMEND.search(ctx):
        return "amends"
    if SUPER.search(ctx):
        return "supersedes"
    if DELEG.search(ctx):
        return "delegates"
    if DEFINE.search(ctx):
        return "defines"
    if REFERS.search(ctx):
        return "refers"
    if re.search(r"настоящего\s+(Кодекса|Федерального\s+закона)", ctx, re.I):
        return "procedure"
    return "refers"


def target_law(ctx: str, full_text: str, src_law: str, num: str, arts: dict):
    """Закон-цель ссылки: (закон|None, confidence, неоднозначна ли)."""
    # 1) явное имя чужого закона
    for lay, pat in LAWTALK.items():
        if re.search(pat, ctx, re.I):
            return lay, 0.90, False
    # 2) «Налогового кодекса» без части
    if NK_GENERIC.search(ctx):
        cands = [l for l in ("NK-1", "NK-2") if num in arts[l]]
        if len(cands) == 1:
            return cands[0], 0.80, False
        return "NK-2", 0.60, False
    # 3) статья есть в «своём» законе — это внутризаконная ссылка
    if num in arts[src_law]:
        return src_law, 0.85, False
    # 4) статья есть ровно в одном другом законе — межазаконная ссылка
    cands = [l for l in arts if num in arts[l]]
    if len(cands) == 1:
        return cands[0], 0.80, False
    # 5) несколько кандидатов — пробуем имя закона во всём тексте чанка
    if len(cands) > 1:
        for lay, pat in LAWTALK.items():
            if lay in cands and re.search(pat, full_text, re.I):
                return lay, 0.65, False
        return None, 0.50, True
    # 6) статьи нет ни в одном корпусе — stub в «своём» законе
    return src_law, 0.60, False


def main() -> int:
    cross_only = "--cross-only" in sys.argv
    chunks = json.loads((DATA / "law_chunks.json").read_text(encoding="utf-8"))["chunks"]

    arts = collections.defaultdict(set)
    node_title = {}
    node_chunks = collections.Counter()
    for c in chunks:
        arts[c["law"]].add(c["article"])
        node_title.setdefault(f'{c["law"]}:{c["article"]}', c["title"])
        node_chunks[f'{c["law"]}:{c["article"]}'] += 1

    edges = collections.Counter()
    meta = {}
    unresolved = []
    stubs = set()

    for c in chunks:
        src = f'{c["law"]}:{c["article"]}'
        text = c["text"]
        for m in REF.finditer(text):
            num = m.group(1)
            ctx = text[max(0, m.start() - 180):m.start() + 40]
            t = classify(ctx)
            lay, conf, amb = target_law(ctx, text, c["law"], num, arts)
            if lay is None:
                unresolved.append({"from": src, "article": num, "reasons": "ambiguous",
                                   "evidence": re.sub(r"\s+", " ", ctx).strip()[-160:]})
                continue
            tgt = f"{lay}:{num}"
            if num not in arts[lay]:
                stubs.add(tgt)
                conf = max(0.55, conf - 0.20)
            if tgt == src:
                continue
            pm = PAR.search(ctx)
            par = pm.group(1) if pm else None
            key = (src, tgt, t)
            edges[key] += 1
            meta.setdefault(key, {
                "type": t, "confidence": round(conf, 2), "origin": "auto",
                "direction": "directed", "paragraph": par,
                "evidence": re.sub(r"\s+", " ", ctx).strip()[-180:],
            })

    edge_list = []
    for (a, b, t), w in edges.items():
        mt = meta[(a, b, t)]
        la, lb = a.split(":")[0], b.split(":")[0]
        edge_list.append({
            "from": a, "to": b, "type": t, "weight": w,
            "confidence": mt["confidence"], "origin": mt["origin"],
            "direction": mt["direction"], "paragraph": mt["paragraph"],
            "cross": la != lb, "evidence": mt["evidence"],
        })

    if cross_only:
        edge_list = [e for e in edge_list if e["cross"]]

    node_ids = sorted({n for e in edge_list for n in (e["from"], e["to"])})
    by_type = collections.Counter(e["type"] for e in edge_list)
    cross = sum(1 for e in edge_list if e["cross"])
    conf_vals = [e["confidence"] for e in edge_list]
    deg_out = collections.Counter(e["from"] for e in edge_list)
    deg_in = collections.Counter(e["to"] for e in edge_list)

    nodes = []
    for n in node_ids:
        law, art = n.split(":", 1)
        nodes.append({
            "id": n, "law": law, "article": art,
            "title": node_title.get(n, "")[:140],
            "in_corpus": n not in stubs,
            "chunks": node_chunks.get(n, 0),
            "in_core": n in CORE,
            "deg_out": deg_out.get(n, 0), "deg_in": deg_in.get(n, 0),
        })

    graph = {
        "version": "2.0",
        "stats": {
            "nodes": len(nodes), "edges": len(edge_list),
            "by_type": dict(by_type), "cross_law_edges": cross,
            "unresolved_refs": len(unresolved), "stub_nodes": len(stubs),
            "confidence_mean": round(sum(conf_vals) / max(len(conf_vals), 1), 3),
            "conf_ge_0_9": sum(1 for c in conf_vals if c >= 0.9),
        },
        "nodes": nodes, "edges": edge_list,
    }

    out = DATA / ("graph_cross_v2.json" if cross_only else "graph_v2.json")
    out.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "unresolved.json").write_text(
        json.dumps({"count": len(unresolved), "items": unresolved[:500]},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{'cross' if cross_only else 'full'}] узлов: {len(nodes)} | рёбер: {len(edge_list)} | "
          f"межзаконных: {cross} | stub-узлов: {len(stubs)}")
    print("по типам:", dict(by_type))
    print("confidence: mean=%.3f  >=0.9: %d" % (
        sum(conf_vals) / max(len(conf_vals), 1), sum(1 for c in conf_vals if c >= 0.9)))
    print("узлов по законам:", dict(collections.Counter(n.split(':')[0] for n in node_ids)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
