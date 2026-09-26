#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Кросс-функциональная схема с дорожками (Swimlane) — путь ИД по участникам процесса.

Дорожки (строки) = участники: суд/орган, ФНС, взыскатель, пристав, БАНК, должник.
Столбцы = этапы ЖЦ ИД. Шаги — в дорожке ответственного, со ссылкой на норму.

Выход: Fedor_Swimlane_ИД.svg (+ PNG рендерит вызывающий chrome)
"""
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
OUT = BASE / "Fedor_Swimlane_ИД.svg"
FS = "DejaVu Sans, Arial, sans-serif"

M = 36
TITLE_H = 92
HDR_W = 250
COL_W = 300
STAGE_H = 66
ROW_H = 156

INK = "#0f172a"; DIM = "#475569"; MUT = "#94a3b8"

STAGES = [
    "1. Выдача ИД", "2. Предъявление", "3. Возбуждение ИП",
    "4. Добровольное", "5. Принудительное", "6. Окончание / возврат",
]
STAGE_SUB = ["ст. 12–13", "ст. 21–22", "ст. 30–31", "5 дней", "ст. 36, 64, 68", "ст. 47 / 46 / 43"]

LANES = [
    ("Суд / орган,\nвыдавший ИД", "#4f46e5"),
    ("ФНС\n(налоговый орган)", "#ea580c"),
    ("Взыскатель", "#0d9488"),
    ("Судебный пристав\n(ФССП)", "#2563eb"),
    ("БАНК ★\nзона ответственности", "#d97706"),
    ("Должник", "#64748b"),
]

# (дорожка, этап, норма, текст)
STEPS = [
    (0, 0, "229-ФЗ ст. 12–13", "Выдача ИД: исп. лист, судебный приказ, нотариальное соглашение"),
    (1, 0, "229-ФЗ п. 5.2 ст. 12", "Постановление ФНС о взыскании задолженности"),
    (2, 1, "229-ФЗ ст. 21–22", "Предъявление ИД к исполнению (сроки, перерыв)"),
    (4, 1, "229-ФЗ ст. 8", "ИД предъявлен напрямую в банк"),
    (3, 2, "229-ФЗ ст. 30–31", "Возбуждение ИП (3 дня); отказ"),
    (5, 3, "229-ФЗ ст. 30 ч. 11–12", "Добровольное исполнение (5 дней)"),
    (3, 4, "229-ФЗ ст. 36, 64, 68", "Принудительное взыскание приставом"),
    (1, 4, "НК ч.1 ст. 46/60", "Поручение ФНС в банк (реестр решений)"),
    (4, 4, "НК 46/60 · ГК ч.2 ст. 855", "Списание · очерёдность · ст. 60 · розыск счетов · ст. 135"),
    (3, 5, "229-ФЗ ст. 47/46/43", "Окончание ИП: исполнено / возврат / прекращение"),
    (2, 5, "229-ФЗ ст. 46 ч. 4", "Возврат ИД взыскателю / повторное предъявление"),
    (4, 5, "НК ст. 60", "Подтверждение исполнения / сообщение о неисполнении"),
]

# стрелки: (из индекса STEPS, в индекс STEPS)
ARROWS = [
    (0, 2), (1, 2), (2, 4), (4, 5), (5, 6), (6, 9), (9, 10),
    (7, 8), (8, 11), (3, 8), (11, 9), (10, 2),
]


def esc(s):
    return escape(s)


def txt(x, y, s, size=15, fill=INK, weight="400", anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FS}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')


def wrap(t, n):
    out, line = [], ""
    for w in t.split():
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    out.append(line)
    return out


def main():
    col_x0 = M + HDR_W
    W = col_x0 + COL_W * len(STAGES) + M
    grid_top = TITLE_H + STAGE_H
    H = grid_top + ROW_H * len(LANES) + 120

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{FS}">',
         '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
         '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.10"/></filter>'
         '<marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
         '<path d="M0,0 L7,3 L0,6 z" fill="#64748b"/></marker>'
         '<marker id="arb" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
         '<path d="M0,0 L7,3 L0,6 z" fill="#d97706"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         txt(M, 46, "Путь исполнительного документа — кросс-функциональная схема (дорожки участников)", 24, INK, "700"),
         txt(M, 72, "Столбцы — этапы ЖЦ ИД · строки — участники процесса · золотая дорожка — зона ответственности банка", 14, DIM)]

    # заголовки этапов
    for j, st in enumerate(STAGES):
        x = col_x0 + j * COL_W
        s.append(f'<rect x="{x}" y="{TITLE_H}" width="{COL_W}" height="{STAGE_H}" fill="#1e293b"/>')
        s.append(f'<line x1="{x}" y1="{TITLE_H}" x2="{x}" y2="{H-90}" stroke="#ffffff" opacity="0.08"/>')
        for i, ln in enumerate(wrap(st, 22)):
            s.append(txt(x + 16, TITLE_H + 30 + i * 21, ln, 16, "#f8fafc", "700"))
        s.append(txt(x + 16, TITLE_H + 56, STAGE_SUB[j], 13, "#a7b6d0"))

    # дорожки
    boxes = {}
    for li, (name, color) in enumerate(LANES):
        y = grid_top + li * ROW_H
        band = "#fff7e6" if li == 4 else ("#f8fafc" if li % 2 else "#ffffff")
        s.append(f'<rect x="{M}" y="{y}" width="{W-2*M}" height="{ROW_H}" fill="{band}"/>')
        s.append(f'<rect x="{M}" y="{y+ROW_H-1}" width="{W-2*M}" height="1" fill="#e6ebf3"/>')
        # заголовок дорожки
        s.append(f'<rect x="{M}" y="{y}" width="{HDR_W}" height="{ROW_H}" fill="{color}" opacity="0.12"/>')
        s.append(f'<rect x="{M}" y="{y}" width="6" height="{ROW_H}" fill="{color}"/>')
        for i, ln in enumerate(name.split("\n")):
            s.append(txt(M + 18, y + ROW_H / 2 - 6 + i * 20, ln, 15, color, "700"))

    # шаги
    percell = {}
    for k, (li, si, norm, label) in enumerate(STEPS):
        percell.setdefault((li, si), []).append(k)
    for k, (li, si, norm, label) in enumerate(STEPS):
        color = LANES[li][1]
        x = col_x0 + si * COL_W + 12
        w = COL_W - 24
        idxs = percell[(li, si)]
        n = len(idxs)
        bh = 64 if n == 1 else 84
        y = grid_top + li * ROW_H + (ROW_H - (bh * n + 10 * (n - 1))) / 2 + idxs.index(k) * (bh + 10)
        boxes[k] = (x, y, w, bh)
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{bh}" rx="10" fill="#ffffff" stroke="{color}" '
                 f'stroke-width="1.8" filter="url(#sh)"/>')
        s.append(f'<rect x="{x}" y="{y}" width="5" height="{bh}" rx="2.5" fill="{color}"/>')
        s.append(txt(x + 14, y + 22, norm, 13, color, "700"))
        for i, ln in enumerate(wrap(label, 34)[:2]):
            s.append(txt(x + 14, y + 40 + i * 15, ln, 11.5, DIM))

    # стрелки
    for a, b in ARROWS:
        x1, y1, w1, h1 = boxes[a]; x2, y2, w2, h2 = boxes[b]
        sx, sy = x1 + w1, y1 + h1 / 2
        ex, ey = x2, y2 + h2 / 2
        col = "#d97706" if (LANES[STEPS[a][0]][1] == "#d97706" or LANES[STEPS[b][0]][1] == "#d97706") else "#94a3b8"
        mk = "arb" if col == "#d97706" else "ar"
        if abs(sy - ey) < 6:
            s.append(f'<line x1="{sx+2:.0f}" y1="{sy:.0f}" x2="{ex-4:.0f}" y2="{ey:.0f}" stroke="{col}" '
                     f'stroke-width="1.8" marker-end="url(#{mk})"/>')
        else:
            mx = (sx + ex) / 2
            s.append(f'<polyline points="{sx+2:.0f},{sy:.0f} {mx:.0f},{sy:.0f} {mx:.0f},{ey:.0f} {ex-4:.0f},{ey:.0f}" '
                     f'fill="none" stroke="{col}" stroke-width="1.8" marker-end="url(#{mk})"/>')

    # легенда
    ly = H - 74
    s.append(txt(M, ly, "Легенда:", 13, INK, "700"))
    lx = M + 80
    for name, color in LANES:
        nm = name.replace("\n", " ")
        s.append(f'<rect x="{lx}" y="{ly-12}" width="16" height="14" rx="4" fill="{color}" opacity="0.14" stroke="{color}"/>')
        s.append(txt(lx + 24, ly, nm, 12.5, DIM))
        lx += 30 + len(nm) * 7.4
    s.append(txt(M, ly + 26, "Стрелки: серая — общий процесс; золотая — участие банка. "
                             "425-ФЗ меняет порядок взыскания (НК ст. 46/60) с 01.01.2027. Трактовки — draft.", 12, "#b91c1c"))
    s.append("</svg>")
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт), {W}x{H}")


if __name__ == "__main__":
    main()
