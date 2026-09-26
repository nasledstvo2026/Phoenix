#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Схема пайплайна создания схем по ИП (роли + гейты). Светлый стиль."""
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
OUT = BASE / "Fedor_Пайплайн_схем.svg"
FS = "DejaVu Sans, Arial, sans-serif"
W = 1280; M = 40
CW = 760; CX = (W - CW) / 2
CH = 74; GAP = 34
INK = "#0f172a"; DIM = "#475569"

CARDS = [
    ("НОРМА — корпус", "law_chunks.json + laws.json · единственный источник содержания", "#64748b"),
    ("ЧЕК-ЛИСТ ИЗ НОРМЫ", "law-ingest/id_sources.json — позиции с цитатами (проверяются по корпусу)", "#0d9488"),
    ("ФЁДОР (fz425-agent)", "формирует содержание и СПЕКУ (JSON по schema_spec.schema.json)", "#2563eb"),
    ("fz425-verifier", "проверяет факты спеки: ПРИНЯТ / ТРЕБУЕТ ДОРАБОТКИ", "#7c3aed"),
    ("ОТРИСОВЩИК (schema-render-agent)", "генератор build_*.py → SVG → chrome → PNG. Без спеки — ОТКАЗ", "#d97706"),
    ("ГЕЙТ 1 — check_scheme_qa.py", "структура (нужные подписи) + геометрия (наложения/выход, chrome CDP)", "#dc2626"),
    ("ГЕЙТ 2 — check_scheme_completeness.py", "покрытие чек-листа + целостность цитат по корпусу", "#dc2626"),
    ("main (курьер) → пользователь", "отдача только при ✅ обоих гейтов", "#16a34a"),
]

TITLE_H = 96
H = TITLE_H + len(CARDS) * (CH + GAP) + 40


def txt(x, y, s, size=15, fill=INK, weight="400", anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FS}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>')


def main():
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FS}">',
         '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
         '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.08"/></filter>'
         '<marker id="a" markerWidth="10" markerHeight="10" refX="7" refY="3.2" orient="auto">'
         '<path d="M0,0 L8,3.2 L0,6.4 z" fill="#94a3b8"/></marker>'
         '<marker id="ar" markerWidth="10" markerHeight="10" refX="7" refY="3.2" orient="auto">'
         '<path d="M0,0 L8,3.2 L0,6.4 z" fill="#dc2626"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         txt(M, 46, "Пайплайн создания схем по ИП (исполнительному производству)", 24, INK, "700"),
         txt(M, 74, "Принцип: содержание — только из нормы и спеки; визуал — отдельный агент; отдача — только после гейтов.", 14, DIM)]

    y = TITLE_H
    centers = []
    for i, (title, sub, color) in enumerate(CARDS):
        s.append(f'<rect x="{CX}" y="{y}" width="{CW}" height="{CH}" rx="14" fill="#ffffff" stroke="#e2e8f0" '
                 f'stroke-width="1.5" filter="url(#sh)"/>')
        s.append(f'<rect x="{CX}" y="{y+14}" width="6" height="{CH-28}" rx="3" fill="{color}"/>')
        s.append(f'<circle cx="{CX+40}" cy="{y+CH/2}" r="20" fill="{color}" opacity="0.14"/>')
        s.append(txt(CX + 40, y + CH / 2 + 6, str(i + 1), 17, color, "700", "middle"))
        s.append(txt(CX + 76, y + 32, title, 17, INK, "700"))
        s.append(txt(CX + 76, y + 54, sub, 13, DIM))
        centers.append(y + CH / 2)
        if i < len(CARDS) - 1:
            s.append(f'<line x1="{CX+CW/2:.0f}" y1="{y+CH+2}" x2="{CX+CW/2:.0f}" y2="{y+CH+GAP-4}" '
                     f'stroke="#94a3b8" stroke-width="2" marker-end="url(#a)"/>')
        y += CH + GAP

    # обратные связи (правка)
    def loop(from_i, to_i, label):
        y1 = centers[from_i]; y2 = centers[to_i]
        x = CX - 34
        s.append(f'<polyline points="{CX},{y1:.0f} {x},{y1:.0f} {x},{y2:.0f} {CX-2},{y2:.0f}" '
                 f'fill="none" stroke="#dc2626" stroke-width="1.6" stroke-dasharray="6 4" marker-end="url(#ar)"/>')
        s.append(txt(x - 8, (y1 + y2) / 2, label, 12, "#dc2626", "700", "end"))

    loop(5, 4, "❌ правка")
    loop(6, 4, "❌ правка")
    loop(3, 2, "ТРЕБУЕТ")
    s.append(txt(M, H - 14, "Гейты обязательны: без ✅ обоих схема не отдаётся. Роли не смешиваются: контент ≠ визуал.", 12.5, DIM))
    s.append("</svg>")
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт), {W}x{H}")


if __name__ == "__main__":
    main()
