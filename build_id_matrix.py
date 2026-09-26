#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта «Жизненный цикл ИД × федеральные законы» (swimlane-матрица) → SVG.

Выход: Fedor_ЖЦ_ИД_матрица.svg
"""
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
OUT = BASE / "Fedor_ЖЦ_ИД_матрица.svg"

STAGES = [
    ("1. Выдача ИД", "ст. 12–13 229-ФЗ"),
    ("2. Предъявление", "сроки ст. 21; перерыв ст. 22"),
    ("3. Возбуждение ИП", "ст. 30; отказ — ст. 31"),
    ("4. Добровольное", "5 дней (ст. 30 ч. 11–12)"),
    ("5. Принудительное", "ст. 36 (2 мес.), 64, 68"),
    ("6. Окончание / возврат", "ст. 47 / 46 / 43"),
    ("7. Повторное", "ст. 46 ч. 4"),
]

# (закон, цвет, {индекс этапа: [строки]}, узел-цвет обводки)
ACTS = [
    ("229-ФЗ — Об исполнительном\nпроизводстве", "#bae1ff", {
        0: ["ст. 12 — виды ИД", "ст. 13 — требования к ИД"],
        1: ["ст. 21 — сроки (3 года и др.)", "ст. 22 — перерыв срока"],
        2: ["ст. 30 — возбуждение", "ст. 31 — отказ"],
        3: ["ст. 30 ч. 11–12 — 5 дней"],
        4: ["ст. 36 — 2 месяца", "ст. 64 — исп. действия", "ст. 68 — меры принуждения"],
        5: ["ст. 47 — окончание", "ст. 46 — возврат ИД", "ст. 43 — прекращение"],
        6: ["ст. 46 ч. 4 — повторно"],
    }, "#2563eb"),
    ("425-ФЗ — изменяющий\n(правит НК РФ)", "#ffb3ba", {
        4: ["правит НК ст. 46/60 —\nвзыскание через банк", "ОТЛОЖЕНО: ядро\nс 01.01.2027"],
    }, "#dc2626"),
    ("НК РФ ч. 1 — ЕНС /\nвзыскание задолженности", "#fed7aa", {
        0: ["постановление налог. органа —\nвид ИД (п. 5.2 ст. 12 229-ФЗ)"],
        4: ["ст. 46 — взыскание за счёт ДС", "ст. 60 — обязанности банка", "ст. 11.3 — ЕНС"],
        5: ["ст. 59 — списание безнадёжной"],
    }, "#ea580c"),
    ("НК РФ ч. 2 — налоги,\nпени, штрафы", "#fef08a", {
        0: ["объект взыскания: налоги,\nпени, штрафы"],
        4: ["состав задолженности"],
    }, "#ca8a04"),
    ("ГК РФ ч. 2 — очерёдность", "#99f6e4", {
        4: ["ст. 855 — очерёдность\nсписания со счетов (в библ. — заглушка)"],
    }, "#0d9488"),
    ("УПК РФ — штраф как наказание", "#c7d2fe", {
        0: ["взыскание штрафа за преступление\n(ст. 103 229-ФЗ → УПК: 27)"],
    }, "#4f46e5"),
    ("127-ФЗ — банкротство", "#ddd6fe", {
        5: ["приостановление ИП\n(ст. 223.4 / 223.6)",
            "внесудебное банкротство\n(ст. 223.2)"],
    }, "#7c3aed"),
    ("603-ФЗ — изменяющий (СВО)", "#fbcfe8", {
        5: ["приостановление требований\n(мобилизация / СВО)"],
    }, "#db2777"),
]

LINKS = {
    0: ["425-ФЗ → НК ч.1 (amends)"],
    4: ["425-ФЗ → НК ч.1 (amends) [2027]", "НК ч.1:60 → НК ч.1:46 (procedure)",
        "229-ФЗ:111 → ГК ч.2:855 (refers)"],
    5: ["127-ФЗ → 229-ФЗ:46 (refers)", "603-ФЗ → 229-ФЗ (amends)"],
}

# ── layout ──
M = 24
LABW, COLW = 320, 310
HEADH = 96
ROWH = 150
TITLEH = 64
W = M + LABW + COLW * len(STAGES) + M
H = TITLEH + HEADH + ROWH * (len(ACTS) + 1) + M + 70
FS = "DejaVu Sans, Arial, sans-serif"


def wrap(t, n):
    out = []
    for raw in t.split("\n"):
        words, line = raw.split(), ""
        for w in words:
            if len(line) + len(w) + 1 > n:
                out.append(line); line = w
            else:
                line = (line + " " + w).strip()
        out.append(line)
    return out


def txt(x, y, s, size=13, fill="#0f172a", weight="400", anchor="start", opacity=1):
    return (f'<text x="{x}" y="{y}" font-family="{FS}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" opacity="{opacity}">{escape(s)}</text>')


def cell_items(x, y, w, items, color):
    s, yy = [], y + 24
    for it in items:
        for i, ln in enumerate(wrap(it, 34)):
            s.append(txt(x + 10, yy, ln, 12.5,
                         "#0f172a" if i == 0 else "#475569", "600" if i == 0 else "400"))
            yy += 16
        yy += 8
    return "".join(s)


def main():
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{FS}">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         txt(M, 40, "Жизненный цикл исполнительного документа (ИД) и федеральные законы",
             24, "#0f172a", "700"),
         txt(M, 62, "Строки — акты библиотеки; столбцы — этапы ЖЦ ИД; в клетках — нормы, "
                    "работающие на этапе. Трактовки — проект (draft).", 13, "#475569")]

    y0 = TITLEH
    # header row
    s.append(f'<rect x="{M}" y="{y0}" width="{LABW}" height="{HEADH}" fill="#0f172a"/>')
    s.append(txt(M + 14, y0 + 34, "Этап ЖЦ ИД", 15, "#e2e8f0", "700"))
    s.append(txt(M + 14, y0 + 56, "↓ законы", 12, "#94a3b8"))
    for j, (t1, t2) in enumerate(STAGES):
        x = M + LABW + j * COLW
        s.append(f'<rect x="{x}" y="{y0}" width="{COLW}" height="{HEADH}" fill="#1e293b" '
                 f'stroke="#0f172a"/>')
        for i, ln in enumerate(wrap(t1, 26)):
            s.append(txt(x + 12, y0 + 30 + i * 20, ln, 15, "#e2e8f0", "700"))
        for i, ln in enumerate(wrap(t2, 30)):
            s.append(txt(x + 12, y0 + 62 + i * 17, ln, 12, "#94a3b8"))

    # act rows
    yy = y0 + HEADH
    for k, (name, color, cells, stroke) in enumerate(ACTS):
        s.append(f'<rect x="{M}" y="{yy}" width="{LABW}" height="{ROWH}" fill="{color}" '
                 f'stroke="{stroke}" stroke-width="2"/>')
        for i, ln in enumerate(wrap(name, 30)):
            s.append(txt(M + 14, yy + 34 + i * 21, ln, 15, "#1e293b", "700"))
        for j in range(len(STAGES)):
            x = M + LABW + j * COLW
            s.append(f'<rect x="{x}" y="{yy}" width="{COLW}" height="{ROWH}" fill="#f8fafc" '
                     f'stroke="#e2e8f0"/>')
            if j in cells:
                s.append(cell_items(x + 4, yy + 6, COLW, cells[j], color))
        yy += ROWH

    # links row
    s.append(f'<rect x="{M}" y="{yy}" width="{LABW}" height="{ROWH}" fill="#0f172a"/>')
    for i, ln in enumerate(wrap("Межзаконные связи (на этапе)", 26)):
        s.append(txt(M + 14, yy + 34 + i * 20, ln, 14, "#e2e8f0", "700"))
    for j in range(len(STAGES)):
        x = M + LABW + j * COLW
        s.append(f'<rect x="{x}" y="{yy}" width="{COLW}" height="{ROWH}" fill="#eef2f7" '
                 f'stroke="#cbd5e1"/>')
        if j in LINKS:
            s.append(cell_items(x + 4, yy + 6, COLW, LINKS[j], "#eef2f7"))
    yy += ROWH

    # legend
    ly = yy + 34
    s.append(txt(M, ly, "Легенда:", 13, "#0f172a", "700"))
    for i, (col, lab) in enumerate([("#ffb3ba", "425-ФЗ — профильный (отложенный эффект с 01.01.2027)"),
                                    ("#bae1ff", "229-ФЗ — ядро ЖЦ ИД"),
                                    ("#eef2f7", "связи между ФЗ"),
                                    ("#94a3b8", "прочерк — акт на этапе не задействован")]):
        x = M + 80 + i * 560
        s.append(f'<rect x="{x}" y="{ly - 12}" width="16" height="16" fill="{col}" stroke="#94a3b8"/>')
        s.append(txt(x + 22, ly, lab, 12.5, "#334155"))
    s.append(txt(M, ly + 30, "Оговорка: ст. 855 ГК РФ в библиотеке отсутствует (узел-заглушка); "
                             "трактовки связей — статус draft, приоритеты — только curated.",
                 12, "#b91c1c"))
    s.append("</svg>")
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"OK: {OUT} ({OUT.stat().st_size} байт), {W}x{H}")


if __name__ == "__main__":
    main()
