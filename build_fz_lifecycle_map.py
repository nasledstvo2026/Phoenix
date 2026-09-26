#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта «ЖЦ ИД + ФЗ» v2 — чистая ручная вёрстка (SVG).

Сверху — таймлайн 7 этапов ЖЦ ИД (ядро: 229-ФЗ).
Под каждым этапом — акты, работающие на этом этапе (цветные плашки).
Ниже — легенда и ключевые межзаконные связи.

Выход: Fedor_Карта_ЖЦ_ИД.svg
"""
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
OUT = BASE / "Fedor_Карта_ЖЦ_ИД.svg"

W = 2600
M = 28
TITLEH = 92
BOXH = 118
PILLH = 272
LEGH = 96
LINKH = 120

FS = "DejaVu Sans, Arial, sans-serif"

STAGES = [
    ("1", "Выдача ИД", "ст. 12–13"),
    ("2", "Предъявление", "ст. 21–22"),
    ("3", "Возбуждение ИП", "ст. 30–31"),
    ("4", "Добровольное", "5 дней · ст. 30"),
    ("5", "Принудительное", "ст. 36, 64, 68"),
    ("6", "Окончание / возврат", "ст. 47 / 46 / 43"),
    ("7", "Повторное", "ст. 46 ч. 4"),
]

LAWS = {
    "229-ФЗ": ("#bae1ff", "#1d4ed8"),
    "425-ФЗ": ("#ffb3ba", "#dc2626"),
    "НК ч. 1": ("#fed7aa", "#ea580c"),
    "НК ч. 2": ("#fef08a", "#ca8a04"),
    "ГК ч. 2": ("#99f6e4", "#0d9488"),
    "УПК РФ": ("#c7d2fe", "#4f46e5"),
    "127-ФЗ": ("#ddd6fe", "#7c3aed"),
    "603-ФЗ": ("#fbcfe8", "#db2777"),
}

# этап -> [(акт, текст)]
PILLS = {
    0: [("229-ФЗ", "виды и требования к ИД (ст. 12–13)"),
        ("НК ч. 1", "ИД = постановление налогового органа (п. 5.2 ст. 12)"),
        ("НК ч. 2", "объект взыскания: налоги, пени, штрафы"),
        ("УПК РФ", "штраф как наказание (ст. 103 229-ФЗ)")],
    1: [("229-ФЗ", "сроки предъявления; перерыв срока (ст. 21–22)")],
    2: [("229-ФЗ", "возбуждение ИП; отказ (ст. 30–31)")],
    3: [("229-ФЗ", "добровольно — 5 дней (ст. 30 ч. 11–12)")],
    4: [("229-ФЗ", "2 месяца (ст. 36, 64, 68)"),
        ("425-ФЗ", "amends НК ст. 46/60 — реестр решений, 3 часа · с 01.01.2027"),
        ("НК ч. 1", "взыскание через банк (ст. 46/60); ЕНС (ст. 11.3)"),
        ("ГК ч. 2", "очерёдность списания со счетов (ст. 855)")],
    5: [("229-ФЗ", "окончание / возврат / прекращение (ст. 47/46/43)"),
        ("НК ч. 1", "списание безнадёжной задолженности (ст. 59)"),
        ("127-ФЗ", "приостановление ИП; внесудебное банкротство (ст. 223.2/223.4)"),
        ("603-ФЗ", "приостановление требований (СВО / мобилизация)")],
    6: [("229-ФЗ", "повторное предъявление (ст. 46 ч. 4)")],
}

LINKS = [
    ("этап 1", "НК ч.1 → 229-ФЗ", "постановление налогового органа — один из видов ИД"),
    ("этап 5", "425-ФЗ → НК ч.1", "amends: новая редакция ст. 46/60 НК (с 01.01.2027)"),
    ("этап 5", "229-ФЗ → ГК ч.2", "refers: очерёдность списания — по ст. 855 ГК"),
    ("этап 6", "127-ФЗ ↔ 229-ФЗ", "refers: приостановление ИП ↔ возврат ИД (ст. 46)"),
    ("этап 6", "603-ФЗ → 229-ФЗ", "amends: приостановление требований (мобилизация)"),
]


def txt(x, y, s, size=13, fill="#0f172a", weight="400", anchor="start", op=1.0):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FS}" font-size="{size}" '
            f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" opacity="{op}">{escape(s)}</text>')


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
    colw = (W - 2 * M) / len(STAGES)
    H = TITLEH + BOXH + PILLH + LEGH + LINKH + M
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{FS}">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         txt(M, 42, "Жизненный цикл исполнительного документа (ИД) и федеральные законы",
             26, "#0f172a", "700"),
         txt(M, 68, "На каждом этапе — акты, которые на нём работают. Ядро цикла — 229-ФЗ «Об исполнительном производстве».",
             14, "#475569")]

    # таймлайн этапов
    for j, (num, name, norms) in enumerate(STAGES):
        x = M + j * colw
        col = 24 + j * (colw - 24)
        s.append(f'<rect x="{x+6:.0f}" y="{TITLEH}" width="{colw-12:.0f}" height="{BOXH}" rx="12" '
                 f'fill="#1e293b" stroke="#0f172a"/>')
        s.append(f'<circle cx="{x+38:.0f}" cy="{TITLEH+40}" r="20" fill="#5eead4"/>')
        s.append(txt(x + 38, TITLEH + 47, num, 21, "#0f172a", "700", "middle"))
        for i, ln in enumerate(wrap(name, 18)):
            s.append(txt(x + 68, TITLEH + 36 + i * 22, ln, 17, "#f8fafc", "700"))
        for i, ln in enumerate(wrap(norms, 26)):
            s.append(txt(x + 20, TITLEH + 92 + i * 17, ln, 13, "#a7b6d0"))
        if j < len(STAGES) - 1:
            s.append(txt(x + colw - 6, TITLEH + 62, "→", 30, "#94a3b8", "700", "middle"))

    # подписи столбцов-разделителей
    py = TITLEH + BOXH + 10
    for j in range(len(STAGES)):
        x = M + j * colw
        if j > 0:
            s.append(f'<line x1="{x:.0f}" y1="{py}" x2="{x:.0f}" y2="{py+PILLH-30}" stroke="#e2e8f0" stroke-width="1.5" stroke-dasharray="4 6"/>')

    # плашки под каждым этапом
    for j in range(len(STAGES)):
        x = M + j * colw
        yy = py
        items = PILLS.get(j)
        if not items:
            continue
        for (law, text) in items:
            fill, stroke = LAWS[law]
            dash = ' stroke-dasharray="7 5"' if law.startswith("425") else ''
            lines = wrap(text, 44)
            h = 32 + 16 * len(lines)
            s.append(f'<rect x="{x+6:.0f}" y="{yy:.0f}" width="{colw-12:.0f}" height="{h:.0f}" rx="10" '
                     f'fill="#ffffff" stroke="{stroke}" stroke-width="2"{dash}/>')
            s.append(f'<rect x="{x+6:.0f}" y="{yy:.0f}" width="6" height="{h:.0f}" rx="3" fill="{fill}"/>')
            s.append(txt(x + 20, yy + 20, law, 13.5, stroke, "700"))
            ly = yy + 38
            for ln in lines:
                s.append(txt(x + 20, ly, ln, 12, "#334155")); ly += 16
            yy += h + 8

    # легенда
    ley = TITLEH + BOXH + PILLH + 24
    s.append(txt(M, ley, "Легенда:", 15, "#0f172a", "700"))
    lx = M + 90
    for law, (fill, stroke) in LAWS.items():
        s.append(f'<rect x="{lx}" y="{ley-14}" width="20" height="18" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        s.append(txt(lx + 26, ley + 1, law, 13, "#1e293b", "600"))
        lx += 26 + 8 * len(law) + 40
    s.append(txt(M, ley + 30, "Пунктир — эффект только с 01.01.2027 (425-ФЗ). "
                              "Ст. 855 ГК РФ в библиотеке отсутствует (узел-заглушка); трактовки связей — статус draft.",
             12, "#b91c1c"))

    # ключевые связи
    cy = ley + LEGH - 10
    s.append(txt(M, cy, "Ключевые межзаконные связи (поверх ЖЦ):", 15, "#0f172a", "700"))
    for i, (st, rel, note) in enumerate(LINKS):
        y = cy + 26 + i * 20
        s.append(txt(M + 16, y, "•", 13, "#64748b"))
        s.append(txt(M + 34, y, st, 13, "#0f172a", "700"))
        s.append(txt(M + 100, y, rel, 13, "#1d4ed8", "600"))
        s.append(txt(M + 300, y, "— " + note, 13, "#475569"))
    s.append("</svg>")
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт), {W}x{H}")


if __name__ == "__main__":
    main()
