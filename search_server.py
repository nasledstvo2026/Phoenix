#!/usr/bin/env python3
"""FastAPI-сервер embedding-поиска и графа взаимосвязей по библиотеке ФЗ (мульти-ФЗ).

Данные:
  law-ingest/law_index.faiss + law_chunks.json + laws.json  — поиск (RAG)
  law-ingest/graph_v2.json                                  — граф взаимосвязей

Эндпоинты:
  GET /search        — семантический поиск по нормам (q, k, law, threshold)
  GET /laws          — реестр актов
  GET /health        — живость (+by_law)
  GET /graph/stats   — статистика графа
  GET /graph/search  — поиск узлов графа (q, law)
  GET /graph/node    — узел + связи (node)
  GET /refs          — связи узла (node, direction, types, min_confidence, cross_only)
  GET /graph         — подграф (node|law|topic, depth, min_confidence, cross_only)
  GET /graph/path    — путь между нормами (from, to, max_depth, min_confidence, bidir)

Порт 8765, только localhost.
"""
import json
import sys
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

import faiss
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
DATA = BASE / "law-ingest"

MODEL: SentenceTransformer = None
INDEX: faiss.Index = None
CHUNKS: list = None
LAWS: dict = None
NAMES: dict = None
GRAPH: dict = None  # {"nodes","out","in","stats","alias"}

ABBREV = {
    "пно": "поручение налогового органа",
    "пос": "поручение о списании",
    "смэв-3": "система межведомственного электронного взаимодействия",
    "смэв": "система межведомственного электронного взаимодействия",
    "енс": "единый налоговый счет",
    "енп": "единый налоговый платеж",
    "фнс": "федеральная налоговая служба",
    "инн": "идентификационный номер налогоплательщика",
    "нк": "налоговый кодекс",
    "гк": "гражданский кодекс",
    "упк": "уголовно-процессуальный кодекс",
    "ип": "исполнительное производство",
    "фз": "федеральный закон",
}


def expand_query(q: str) -> str:
    qx = q.lower()
    for abbr, full in ABBREV.items():
        qx = qx.replace(abbr, full)
    return f"{q} ({qx})" if qx != q.lower() else q


def _load_graph() -> dict:
    path = DATA / "graph_v2.json"
    if not path.exists():
        path = DATA / "graph.json"
    g = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    out, inn = defaultdict(list), defaultdict(list)
    for e in g["edges"]:
        out[e["from"]].append(e)
        inn[e["to"]].append(e)
    # алиасы: «229-ФЗ:46», «229:46» → канонический «FZ-229:46»
    alias = {}
    num2code = {}
    for code, l in (LAWS or {}).items():
        num2code[str(l.get("number", "")).replace("-ФЗ", "").strip()] = code
    for nid in nodes:
        law, art = nid.split(":", 1)
        alias[nid.lower()] = nid
        num = str((LAWS or {}).get(law, {}).get("number", "")).replace("-ФЗ", "")
        if num:
            alias[f"{num}:{art}".lower()] = nid
    return {"path": str(path), "nodes": nodes, "out": out, "in": inn,
            "stats": g.get("stats", {}), "alias": alias, "edges_all": g["edges"]}


def resolve_node(nid: str) -> str:
    if GRAPH is None:
        raise HTTPException(503, "граф не загружен")
    if nid in GRAPH["nodes"]:
        return nid
    hit = GRAPH["alias"].get(nid.strip().lower())
    if hit:
        return hit
    raise HTTPException(404, f"узел '{nid}' не найден; формат LAW:ART, напр. FZ-229:46")


def edge_view(e: dict, other_key: str) -> dict:
    other = e[other_key]
    n = GRAPH["nodes"].get(other, {})
    return {"node": other, "law": n.get("law"), "article": n.get("article"),
            "title": n.get("title", ""), "type": e["type"], "weight": e.get("weight"),
            "confidence": e.get("confidence"), "paragraph": e.get("paragraph"),
            "cross": e.get("cross"), "evidence": e.get("evidence")}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL, INDEX, CHUNKS, LAWS, NAMES, GRAPH
    print("🧠 Загрузка модели intfloat/multilingual-e5-small...", file=sys.stderr)
    MODEL = SentenceTransformer("intfloat/multilingual-e5-small")
    INDEX = faiss.read_index(str(DATA / "law_index.faiss"))
    CHUNKS = json.loads((DATA / "law_chunks.json").read_text(encoding="utf-8"))["chunks"]
    reg = json.loads((DATA / "laws.json").read_text(encoding="utf-8"))
    LAWS = {l["code"]: l for l in reg["laws"]}
    NAMES = {l["code"]: (l["number"] if l["kind"] != "codex" else l["title"]) for l in reg["laws"]}
    GRAPH = _load_graph()
    print(f"✅ Готово: {INDEX.ntotal} чанков, {len(LAWS)} актов, "
          f"граф {GRAPH['stats'].get('nodes')} узлов / {GRAPH['stats'].get('edges')} рёбер",
          file=sys.stderr)
    yield
    print("🛑 Сервер остановлен", file=sys.stderr)


app = FastAPI(lifespan=lifespan, title="Law Search + Graph API (multi-FZ)")


# ─────────────────────────────── ПОИСК (RAG) ───────────────────────────────
@app.get("/search")
async def search(
    q: str = Query(..., description="Поисковый запрос"),
    k: int = Query(5, ge=1, le=50),
    threshold: float = Query(0.85, ge=0, le=1, description="Порог релевантности"),
    law: str = Query(None, description="Фильтр по коду закона, напр. FZ-229"),
):
    q_expanded = expand_query(q)
    vec = MODEL.encode(f"query: {q_expanded}", normalize_embeddings=True).astype(np.float32)
    fetch = k if not law else min(len(CHUNKS), max(k * 40, 400))
    scores, ids = INDEX.search(np.array([vec]), fetch)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(CHUNKS):
            continue
        c = CHUNKS[idx]
        if law and c["law"] != law:
            continue
        results.append({
            "rank": len(results) + 1, "score": round(float(score), 4),
            "law": c["law"], "source": NAMES.get(c["law"], c["law"]),
            "article": c["article"], "title": c["title"],
            "revision": c.get("revision"), "in_force_from": c.get("in_force_from"),
            "snippet": c["text"][:300].replace("\n", " ").strip(),
            "full_text": c["text"],
        })
        if len(results) >= k:
            break
    results = [r for r in results if r["score"] >= threshold]
    return {"query": q, "expanded": q_expanded if q_expanded != q else None,
            "law_filter": law, "total": len(results), "threshold": threshold,
            "results": results}


@app.get("/laws")
async def laws():
    out = []
    for code, l in LAWS.items():
        n = sum(1 for c in CHUNKS if c["law"] == code)
        out.append({"code": code, "number": l["number"], "title": l["title"],
                    "revision": l["revision"], "in_force_from": l["in_force_from"],
                    "kind": l["kind"], "chunks": n, "editions": len(l.get("editions", []))})
    return {"laws": out}


@app.get("/health")
async def health():
    by_law = {}
    for c in CHUNKS:
        by_law[c["law"]] = by_law.get(c["law"], 0) + 1
    return {"status": "ok", "chunks": INDEX.ntotal, "laws": len(LAWS),
            "graph_edges": GRAPH["stats"].get("edges") if GRAPH else 0,
            "by_law": by_law}


# ─────────────────────────────── ГРАФ ───────────────────────────────
@app.get("/graph/stats")
async def graph_stats():
    return {"graph_file": GRAPH["path"], **GRAPH["stats"]}


@app.get("/graph/search")
async def graph_search(
    q: str = Query(None, description="подстрока по id или заголовку узла"),
    law: str = Query(None, description="фильтр по коду закона"),
    limit: int = Query(25, ge=1, le=200),
):
    res = []
    ql = (q or "").strip().lower()
    for n in GRAPH["nodes"].values():
        if law and n["law"] != law:
            continue
        if ql and ql not in n["id"].lower() and ql not in n.get("title", "").lower():
            continue
        res.append({"id": n["id"], "law": n["law"], "article": n["article"],
                    "title": n.get("title", ""), "in_core": n.get("in_core"),
                    "deg_out": n.get("deg_out"), "deg_in": n.get("deg_in")})
    res.sort(key=lambda x: -((x["deg_out"] or 0) + (x["deg_in"] or 0)))
    return {"total": len(res), "results": res[:limit]}


@app.get("/refs")
async def refs(
    node: str = Query(..., description="узел LAW:ART"),
    direction: str = Query("both", pattern="^(out|in|both)$"),
    types: str = Query(None, description="через запятую: refers,amends,procedure,..."),
    min_confidence: float = Query(0.0, ge=0, le=1),
    cross_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
):
    nid = resolve_node(node)
    tset = {t.strip() for t in types.split(",")} if types else None
    out, inn = [], []
    if direction in ("out", "both"):
        for e in GRAPH["out"].get(nid, []):
            if tset and e["type"] not in tset:
                continue
            if e.get("confidence", 1) < min_confidence or (cross_only and not e.get("cross")):
                continue
            out.append(edge_view(e, "to"))
    if direction in ("in", "both"):
        for e in GRAPH["in"].get(nid, []):
            if tset and e["type"] not in tset:
                continue
            if e.get("confidence", 1) < min_confidence or (cross_only and not e.get("cross")):
                continue
            inn.append(edge_view(e, "from"))
    out.sort(key=lambda x: -(x["weight"] or 0))
    inn.sort(key=lambda x: -(x["weight"] or 0))
    node_info = GRAPH["nodes"].get(nid, {})
    return {"node": nid, "title": node_info.get("title", ""),
            "in_core": node_info.get("in_core"), "out": out[:limit], "in": inn[:limit],
            "counts": {"out": len(out), "in": len(inn)}}


@app.get("/graph")
async def graph(
    node: str = Query(None, description="затравочный узел LAW:ART"),
    law: str = Query(None, description="затравочные узлы — все статьи закона"),
    topic: str = Query(None, description="подстрока темы (по заголовкам узлов)"),
    depth: int = Query(1, ge=1, le=3),
    min_confidence: float = Query(0.0, ge=0, le=1),
    cross_only: bool = Query(False),
    max_nodes: int = Query(300, ge=1, le=3000),
):
    if node:
        seeds = [resolve_node(node)]
    elif law:
        seeds = [n["id"] for n in GRAPH["nodes"].values() if n["law"] == law]
    elif topic:
        tl = topic.lower()
        seeds = [n["id"] for n in GRAPH["nodes"].values()
                 if tl in n.get("title", "").lower() or tl in n["id"].lower()]
    else:
        raise HTTPException(400, "укажите node, law или topic")
    if not seeds:
        return {"seeds": [], "nodes": [], "edges": [], "truncated": False}

    seen = set(seeds)
    frontier = list(seeds)
    used = set()
    for _ in range(depth):
        nxt = []
        for u in frontier:
            for e in GRAPH["out"].get(u, []) + GRAPH["in"].get(u, []):
                if e.get("confidence", 1) < min_confidence or (cross_only and not e.get("cross")):
                    continue
                key = (e["from"], e["to"], e["type"], e["paragraph"])
                used.add(key)
                for v in (e["from"], e["to"]):
                    if v not in seen:
                        seen.add(v)
                        nxt.append(v)
        frontier = nxt
        if len(seen) > max_nodes * 3:
            break
    edges = [e for e in GRAPH["edges_all"]
             if (e["from"], e["to"], e["type"], e.get("paragraph")) in used]
    nodes = [{**{k: GRAPH["nodes"][i].get(k) for k in ("id", "law", "article", "title", "in_core")}}
             for i in list(seen)[:max_nodes]]
    keep = {n["id"] for n in nodes}
    edges = [e for e in edges if e["from"] in keep and e["to"] in keep]
    return {"seeds": seeds[:50], "nodes": nodes, "edges": edges,
            "truncated": len(seen) > max_nodes, "stats": {"nodes": len(nodes), "edges": len(edges)}}


@app.get("/graph/node")
async def graph_node(node: str = Query(..., description="узел LAW:ART")):
    nid = resolve_node(node)
    n = GRAPH["nodes"].get(nid, {})
    return {"node": nid, **n,
            "refs_out": len(GRAPH["out"].get(nid, [])),
            "refs_in": len(GRAPH["in"].get(nid, []))}


@app.get("/graph/path")
async def graph_path(
    from_: str = Query(..., alias="from", description="начальный узел LAW:ART"),
    to: str = Query(..., description="конечный узел LAW:ART"),
    max_depth: int = Query(5, ge=1, le=8),
    min_confidence: float = Query(0.0, ge=0, le=1),
    bidir: bool = Query(True, description="учитывать рёбра в обе стороны"),
):
    src, dst = resolve_node(from_), resolve_node(to)
    if src == dst:
        return {"from": src, "to": dst, "length": 0, "path": [src], "edges": []}
    prev = {src: None}
    q = deque([(src, 0)])
    found = False
    while q:
        u, d = q.popleft()
        if d >= max_depth:
            continue
        cand = list(GRAPH["out"].get(u, []))
        if bidir:
            cand += list(GRAPH["in"].get(u, []))
        for e in cand:
            if e.get("confidence", 1) < min_confidence:
                continue
            v = e["to"] if e["from"] == u else e["from"]
            if v in prev:
                continue
            prev[v] = (u, e)
            if v == dst:
                found = True
                q.clear()
                break
            q.append((v, d + 1))
    if not found:
        return {"from": src, "to": dst, "length": None, "path": [], "edges": [],
                "note": "путь не найден в пределах max_depth"}
    path, path_edges = [], []
    cur = dst
    while cur is not None:
        path.append(cur)
        step = prev[cur]
        if step is None:
            break
        u, e = step
        path_edges.append({"from": e["from"], "to": e["to"], "type": e["type"],
                           "confidence": e.get("confidence"), "evidence": e.get("evidence")})
        cur = u
    path.reverse()
    path_edges.reverse()
    return {"from": src, "to": dst, "length": len(path_edges), "path": path, "edges": path_edges}
