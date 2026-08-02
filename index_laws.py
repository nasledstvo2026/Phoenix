#!/usr/bin/env python3
"""Индексация чанков в FAISS с multilingual-e5-small."""

import json, sys, time
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent

def main():
    # Грузим чанки
    chunks_path = BASE / "chunks.json"
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"📦 Загружено чанков: {len(chunks)}", file=sys.stderr)
    
    # Грузим модель
    print("🧠 Загрузка модели intfloat/multilingual-e5-small...", file=sys.stderr)
    t0 = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    print(f"   Загружена за {time.time() - t0:.1f}с", file=sys.stderr)
    
    # Подготавливаем тексты с префиксом "passage:"
    print("🔢 Эмбеддинг чанков...", file=sys.stderr)
    t0 = time.time()
    texts = ["passage: " + c["text"] for c in chunks]
    
    # Батчами
    batch_size = 32
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True  # для IndexFlatIP (cosine)
    )
    print(f"   {len(embeddings)} векторов за {time.time() - t0:.1f}с, dim={embeddings.shape[1]}", file=sys.stderr)
    
    # Строим FAISS индекс
    print("📊 Построение FAISS индекса...", file=sys.stderr)
    import faiss
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product на нормализованных = cosine
    index.add(embeddings.astype(np.float32))
    print(f"   Индекс: {index.ntotal} векторов", file=sys.stderr)
    
    # Сохраняем индекс
    index_path = BASE / "fz425_index.faiss"
    faiss.write_index(index, str(index_path))
    print(f"💾 Индекс: {index_path} ({index_path.stat().st_size / 1024:.0f} KB)", file=sys.stderr)
    
    # Сохраняем метаданные (без текстов — они в chunks.json)
    meta = []
    for c in chunks:
        meta.append({
            "id": c["id"],
            "source": c["source"],
            "article": c["article"],
            "title": c["title"],
            "text_len": len(c["text"])
        })
    
    meta_path = BASE / "fz425_meta.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Метаданные: {meta_path}", file=sys.stderr)
    print(f"\n✅ Готово: {len(chunks)} чанков, {dim}-мерные векторы", file=sys.stderr)

if __name__ == "__main__":
    main()
