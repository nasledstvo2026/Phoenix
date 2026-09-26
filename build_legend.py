#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Добавляет компактную легенду по всем цветам СВЕРХУ схемы (постобработка SVG).

Вход:  Fedor_Путь_ИД_банк_raw.svg (вывод mermaid-cli)
Выход: Fedor_Путь_ИД_банк.svg (со легендой сверху)
Затем рендер PNG делает вызывающий скрипт.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
SRC = BASE / "Fedor_Путь_ИД_банк_raw.svg"
OUT = BASE / "Fedor_Путь_ИД_банк.svg"

FS = "DejaVu Sans, Arial, sans-serif"
LEGH = 74
M = 20

# (fill, stroke, label, dashed)
ITEMS = [
    ("#5eead4", "#0f172a", "старт (источники ИД)", False),
    ("#f1f5f9", "#334155", "источник", False),
    ("#fed7aa", "#ea580c", "ФНС (источник)", False),
    ("#bae1ff", "#1d4ed8", "229-ФЗ (этапы ИД)", False),
    ("#ffb3ba", "#dc2626", "425-ФЗ (изменяющий)", False),
    ("#fde68a", "#b45309", "зона ответственности банка", False),
    ("#86efac", "#0f172a", "завершено", False),
    ("none", "#334155", "пунктир — эффект с 01.01.2027", True),
]


def main():
    txt = SRC.read_text(encoding="utf-8")
    m = re.search(r'<svg[^>]*viewBox="([\d\.\-\s]+)"[^>]*>', txt)
    vb = [float(x) for x in m.group(1).split()]
    minx, miny, W, H = vb[0], vb[1], vb[2], vb[3]
    inner = txt[m.end(): txt.rfind("</svg>")]

    # геометрия легенды
    x = M
    parts, total = [], x
    for fill, stroke, label, dashed in ITEMS:
        sw = 22
        dash = ' stroke-dasharray="6 4"' if dashed else ''
        parts.append(f'<rect x="{x}" y="26" width="{sw}" height="22" rx="5" fill="{fill if fill!="none" else "#ffffff"}" '
                     f'stroke="{stroke}" stroke-width="2"{dash}/>')
        lx = x + sw + 8
        parts.append(f'<text x="{lx}" y="43" font-family="{FS}" font-size="15" fill="#0f172a">{escape(label)}</text>')
        x = lx + len(label) * 8.6 + 34
    total = max(x + M, W + 2 * M)

    outer_w = total
    outer_h = LEGH + H
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{outer_w:.0f}" height="{outer_h:.0f}" '
           f'viewBox="0 0 {outer_w:.0f} {outer_h:.0f}" font-family="{FS}">',
           f'<rect width="{outer_w:.0f}" height="{outer_h:.0f}" fill="#ffffff"/>',
           f'<rect x="0" y="0" width="{outer_w:.0f}" height="{LEGH}" fill="#f8fafc"/>',
           f'<line x1="0" y1="{LEGH}" x2="{outer_w:.0f}" y2="{LEGH}" stroke="#e2e8f0" stroke-width="2"/>',
           f'<text x="{M}" y="16" font-family="{FS}" font-size="12" fill="#64748b" font-weight="700">ЛЕГЕНДА</text>']
    svg += parts
    svg.append(f'<g transform="translate({-minx:.1f},{LEGH - miny:.1f})">')
    svg.append(inner)
    svg.append("</g></svg>")
    OUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт), {outer_w:.0f}x{outer_h:.0f}")


if __name__ == "__main__":
    main()
