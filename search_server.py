#!/usr/bin/env python3
"""FastAPI-сервер для embedding-поиска по 425-ФЗ и НК РФ.
Модель загружается один раз при старте и живёт в памяти.
Порт 8765."""

import json, sys
import numpy as np
from pathlib import Path
from contextlib import asynccontextmanager

import faiss
from fastapi import FastAPI, Query
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent

MODEL: SentenceTransformer = None
INDEX: faiss.Index = None
CHUNKS: list = None
META: list = None

SOURCE_NAMES = {"fz425": "425-ФЗ", "nk1": "НК ч.1", "nk2": "НК ч.2"}

# Словарь аббревиатур налогового права
ABBREV = {
    "пно": "поручение налогового органа",
    "пос": "поручение о списании",
    "смэв-3": "система межведомственного электронного взаимодействия",
    "смэв": "система межведомственного электронного взаимодействия",
    "енс": "единый налоговый счет",
    "енп": "единый налоговый платеж",
    "фнс": "федеральная налоговая служба",
    "инн": "идентификационный номер налогоплательщика",
}


def expand_query(q: str) -> str:
    """Раскрыть аббревиатуры в запросе."""
    q_expanded = q.lower()
    for abbr, full in ABBREV.items():
        q_expanded = q_expanded.replace(abbr, full)
    # Если изменился — добавить оригинал для контекста
    if q_expanded != q.lower():
        q_expanded = f"{q} ({q_expanded})"
    else:
        q_expanded = q
    return q_expanded

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL, INDEX, CHUNKS, META
    print("🧠 Загрузка модели intfloat/multilingual-e5-small...", file=sys.stderr)
    MODEL = SentenceTransformer("intfloat/multilingual-e5-small")
    print("📊 Загрузка FAISS индекса...", file=sys.stderr)
    INDEX = faiss.read_index(str(BASE / "fz425_index.faiss"))
    print("📦 Загрузка чанков и метаданных...", file=sys.stderr)
    with open(BASE / "chunks.json", "r", encoding="utf-8") as f:
        CHUNKS = json.load(f)
    with open(BASE / "fz425_meta.json", "r", encoding="utf-8") as f:
        META = json.load(f)
    print(f"✅ Готово: {INDEX.ntotal} чанков, порт 8765", file=sys.stderr)
    yield
    print("🛑 Сервер остановлен", file=sys.stderr)

app = FastAPI(lifespan=lifespan, title="Law Embedding Search")

@app.get("/search")
async def search(
    q: str = Query(..., description="Поисковый запрос"),
    k: int = Query(5, ge=1, le=50, description="Кол-во результатов"),
    threshold: float = Query(0.83, ge=0, le=1, description="Порог релевантности"),
):
    # Раскрыть аббревиатуры и закодировать
    q_expanded = expand_query(q)
    vec = MODEL.encode(f"query: {q_expanded}", normalize_embeddings=True).astype(np.float32)
    scores, ids = INDEX.search(np.array([vec]), k)

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(CHUNKS):
            continue
        chunk = CHUNKS[idx]
        meta = META[idx]
        snippet = chunk["text"][:300].replace("\n", " ").strip()
        results.append({
            "rank": len(results) + 1,
            "score": round(float(score), 4),
            "source": SOURCE_NAMES.get(chunk["source"], chunk["source"]),
            "article": chunk["article"],
            "title": chunk["title"],
            "snippet": snippet,
            "full_text": chunk["text"],
        })

    # Фильтр по порогу
    results = [r for r in results if r["score"] >= threshold]

    return {
        "query": q,
        "expanded": q_expanded if q_expanded != q else None,
        "total": len(results),
        "threshold": threshold,
        "results": results,
    }

@app.get("/health")
async def health():
    return {"status": "ok", "chunks": INDEX.ntotal}
