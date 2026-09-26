#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта «Путь ИД: источники → этапы → завершение» — светлая ручная инфографика (SVG).

Никаких «чёрных квадратов»: только светлые карточки, мягкие тени, цветные акценты.
Выход: Fedor_Путь_ИД_карта.svg  (+ PNG рендерит вызывающий через chrome)
"""
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
OUT = BASE / "Fedor_Путь_ИД_карта.svg"

FS = "DejaVu Sans, Arial, sans-serif"
W = 1500
M = 40
HEAD = 168
LEG = 62
CARD_W = 900
CARD_X = M
GAP = 16

INK = "#0f172a"; DIM = "#475569"; MUT = "#94a3b8"
BLUE = "#2563eb"; GOLD = "#d97706"; GREEN = "#16a34a"; PINK = "#db2777"; VIOLET = "#7c3aed"; TEAL = "#0d9488"

BANK_ZONE = "#fff7e6"

STEPS = [
    ("src", "ИСТОЧНИКИ ИД", "кто выдаёт документ", TEAL, None,
     ["Суды (ОЮ, арбитраж) — исполнительный лист",
      "Мировой судья — судебный приказ",
      "ФНС (налоговый орган) — постановление о взыскании",
      "Нотариус — соглашение об алиментах / медиативное",
      "ФССП, контрольные и гос. органы — акты, постановления"]),
    ("1", "ВЫДАЧА ИД", "229-ФЗ: ст. 12 (виды) · ст. 13 (требования)", BLUE, None, []),
    ("2", "ПРЕДЪЯВЛЕНИЕ К ИСПОЛНЕНИЮ", "229-ФЗ: ст. 21 (сроки) · ст. 22 (перерыв)", BLUE, None, []),
    ("2б", "НАПРЯМУЮ В БАНК (минуя приставов)", "229-ФЗ: ст. 8", BLUE, "БАНК", []),
    ("3", "ВОЗБУЖДЕНИЕ ИП", "229-ФЗ: ст. 30 (3 дня); отказ — ст. 31", BLUE, None, []),
    ("4", "ДОБРОВОЛЬНОЕ ИСПОЛНЕНИЕ", "229-ФЗ: ст. 30 ч. 11–12 (5 дней)", BLUE, None, []),
    ("5", "ПРИНУДИТЕЛЬНОЕ ИСПОЛНЕНИЕ", "229-ФЗ: ст. 36 (2 мес.), ст. 64, 68", BLUE, None, []),
    ("5б", "ИСПОЛНЕНИЕ ПОРУЧЕНИЙ ФНС", "НК РФ ч.1: ст. 46, 60 · 3 часа (с 01.01.2027) / 1 опер. день", GOLD, "БАНК",
     ["Очерёдность списания — ГК РФ ч.2 ст. 855",
      "Обязанности банка (НК ст. 60): исполнить · не задерживать · сообщить",
      "Розыск счетов — ПНО только по ИНН (с 01.01.2027)",
      "Ответственность банка (НК ст. 135): 1/150 ставки, ≤0,2%/день; 30%"]),
    ("6", "ОКОНЧАНИЕ ИП", "229-ФЗ: ст. 47 (исполнено) / ст. 46 (возврат) / ст. 43 (прекращение)", BLUE, None, []),
]

OUTCOMES = [
    ("ЗАВЕРШЕНО", "требования исполнены", GREEN),
    ("ВОЗВРАТ ИД взыскателю", "229-ФЗ ст. 46 — взыскание невозможно", GOLD),
    ("ПРЕКРАЩЕНИЕ ИП", "229-ФЗ ст. 43", MUT),
]
AGAIN = "ПОВТОРНОЕ ПРЕДЪЯВЛЕНИЕ — 229-ФЗ ст. 46 ч. 4 (сроки ст. 21) → новый цикл"


def txt(x, y, s, size=16, fill=INK, weight="400", anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FS}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>')


def wrap(t, n):
    out, line = [], ""
    for w in t.split():
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    out.append(line)
    return out


def card(x, y, w, h, fill="#ffffff", stroke="#e2e8f0", accent=None, badge=None, badge_color=None):
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" '
         f'stroke-width="1.5" filter="url(#sh)"/>']
    if accent:
        s.append(f'<rect x="{x}" y="{y+14}" width="6" height="{h-28}" rx="3" fill="{accent}"/>')
    if badge:
        bw = 16 + len(badge) * 9
        s.append(f'<rect x="{x+w-bw-16}" y="{y+14}" width="{bw}" height="24" rx="12" '
                 f'fill="{badge_color}" opacity="0.14"/>')
        s.append(txt(x + w - bw / 2 - 16, y + 31, badge, 13, badge_color, "700", "middle"))
    return "".join(s)


def main():
    # расчёт высот
    heights = []
    for kind, title, sub, color, badge, extra in STEPS:
        h = 84
        if extra:
            h += 26 * len(extra)
        heights.append(h)
    total = HEAD + LEG + sum(heights) + GAP * (len(STEPS) - 1) + 24 + 96 + 50 + M
    H = total

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{FS}">',
         '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
         '<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.08"/>'
         '</filter></defs>',
         f'<rect width="{W}" height="{H}" fill="#f7f9fc"/>']

    # заголовок
    s.append(txt(M, 56, "Путь исполнительного документа: от возникновения до завершения", 28, INK, "700"))
    s.append(txt(M, 86, "Каждый этап — через свой ФЗ. Золотым выделена зона ответственности банка.", 16, DIM))

    # легенда (верх, компактно)
    ly = 118
    items = [("старт (источники)", TEAL), ("229-ФЗ — этапы", BLUE), ("425-ФЗ — изменяющий", PINK),
             ("зона ответственности банка", GOLD), ("завершение", GREEN), ("возврат / прекращение", "#eab308")]
    lx = M
    for lab, col in items:
        wid = 30 + len(lab) * 8.4
        s.append(f'<rect x="{lx}" y="{ly}" width="{wid}" height="26" rx="13" fill="{col}" opacity="0.12"/>')
        s.append(f'<circle cx="{lx+14}" cy="{ly+13}" r="6" fill="{col}"/>')
        s.append(txt(lx + 26, ly + 18, lab, 13.5, DIM, "600"))
        lx += wid + 12
    s.append(f'<line x1="{M}" y1="{HEAD-14}" x2="{W-M}" y2="{HEAD-14}" stroke="#e6ebf3" stroke-width="1.5"/>')

    # карточки этапов
    y = HEAD + LEG - 20
    for i, (kind, title, sub, color, badge, extra) in enumerate(STEPS):
        h = heights[i]
        gold = (color == GOLD)
        fill = BANK_ZONE if gold else "#ffffff"
        s.append(card(CARD_X, y, CARD_W, h, fill=fill, accent=color, badge=badge, badge_color=GOLD))
        # номер/кружок
        cyc = y + 34
        s.append(f'<circle cx="{CARD_X+38}" cy="{cyc}" r="20" fill="{color}" opacity="0.14"/>')
        s.append(txt(CARD_X + 38, cyc + 7, kind, 17, color, "700", "middle"))
        s.append(txt(CARD_X + 72, y + 40, title, 18, INK, "700"))
        s.append(txt(CARD_X + 72, y + 64, sub, 14, DIM))
        if extra:
            yy = y + 88
            for e in extra:
                s.append(f'<circle cx="{CARD_X+80}" cy="{yy-5}" r="3.5" fill="{color}"/>')
                s.append(txt(CARD_X + 92, yy, e, 13.5, DIM))
                yy += 26
        # коннектор
        if i < len(STEPS) - 1:
            s.append(f'<line x1="{CARD_X+38}" y1="{y+h}" x2="{CARD_X+38}" y2="{y+h+GAP}" '
                     f'stroke="#cbd5e1" stroke-width="2.5"/>')
        y += h + GAP

    # завершение
    y += 6
    s.append(txt(M, y, "ЗАВЕРШЕНИЕ", 16, INK, "700"))
    y += 18
    ow = (CARD_W - 2 * 14) / 3
    for j, (t, sub, col) in enumerate(OUTCOMES):
        ox = CARD_X + j * (ow + 14)
        s.append(card(ox, y, ow, 76, accent=col))
        s.append(txt(ox + 18, y + 32, t, 14.5, col, "700"))
        for k, ln in enumerate(wrap(sub, 30)):
            s.append(txt(ox + 18, y + 52 + k * 16, ln, 12.5, DIM))
    y += 96
    s.append(f'<rect x="{CARD_X}" y="{y}" width="{CARD_W}" height="40" rx="10" fill="#eef4ff" stroke="#dbe6ff"/>')
    s.append(txt(CARD_X + 16, y + 25, AGAIN, 13.5, BLUE, "600"))

    # дисклеймер
    y += 70
    s.append(txt(M, y, "Оговорка: 425-ФЗ меняет порядок взыскания (НК ст. 46/60) с 01.01.2027; "
                       "ст. 855 ГК РФ в библиотеке отсутствует (узел-заглушка).", 12, "#b91c1c"))
    s.append("</svg>")
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт), {W}x{H}")


if __name__ == "__main__":
    main()
