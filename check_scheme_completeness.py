#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ГЕЙТ ПОЛНОТЫ схемы: оракул берётся ИЗ НОРМЫ, а не из головы.

Проверки:
  1) ЦЕЛОСТНОСТЬ — каждая позиция чек-листа (id_sources.json) подтверждена
     цитатой в корпусе (law_chunks). Ловит выдуманные/устаревшие позиции.
  2) ПОКРЫТИЕ — каждая позиция чек-листа присутствует в схеме (SVG).
     Ловит ПРОПУСКИ (именно то, что пропустило ФССП).

Использование:
  python3 check_scheme_completeness.py SCHEMA.svg [--checklist law-ingest/id_sources.json]
Выход: 0 = ок, 1 = неполнота.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
CHUNKS = BASE / "law-ingest/law_chunks.json"


def corpus_text():
    ch = json.loads(CHUNKS.read_text(encoding="utf-8"))["chunks"]
    txt = " ".join(c["text"] for c in ch)
    return re.sub(r"\[([^\]]+)\]\(#[^)]+\)", r"\1", txt)  # снять md-ссылки


def main():
    svg_path = sys.argv[1]
    cl_path = BASE / "law-ingest/id_sources.json"
    if "--checklist" in sys.argv:
        cl_path = Path(sys.argv[sys.argv.index("--checklist") + 1])
    cl = json.loads(cl_path.read_text(encoding="utf-8"))
    items = cl["items"]
    svg = Path(svg_path).read_text(encoding="utf-8")
    cor = corpus_text()

    integrity, coverage = [], []
    for it in items:
        q = re.sub(r"\s+", " ", it["quote"]).strip()
        if q not in cor:
            integrity.append(it)
        if it["doc"] not in svg:
            coverage.append(it)

    print("═" * 64)
    print(f"ГЕЙТ ПОЛНОТЫ: {svg_path}")
    print(f"Источник списка: {cl['source_norm']}")
    print(f"Позиций в чек-листе: {len(items)}")
    print(f"1) Целостность (цитаты в корпусе): "
          f"{'✅ все подтверждены' if not integrity else '❌ ' + str(len(integrity)) + ' не найдено'}")
    for it in integrity:
        print(f"   - п.{it['p']}: цитата не найдена в корпусе")
    print(f"2) Покрытие схемы: {'✅ все позиции отражены' if not coverage else '❌ не отражено: ' + str(len(coverage))}")
    for it in coverage:
        print(f"   - п.{it['p']} «{it['doc']}» ({it['who']}) — НЕТ на схеме")
    ok = not (integrity or coverage)
    print("ИТОГ:", "✅ ПОЛНОТА ПОДТВЕРЖДЕНА" if ok else "❌ СХЕМА НЕПОЛНА")
    print("═" * 64)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
