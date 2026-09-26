#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный генератор swimlane-схемы ИЗ СПЕКИ (JSON). v2 — динамические высоты.

Данные (дорожки/этапы/шаги) — только из спеки. Полнота — отдельным гейтом.

Использование: python3 build_from_spec.py SPEC.json [--out file.svg]
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
FS = "DejaVu Sans, Arial, sans-serif"
M = 36; TITLE_H = 92; HDR_W = 250; COL_W = 300
INK = "#0f172a"; DIM = "#475569"
PALETTE = ["#4f46e5", "#ea580c", "#0d9488", "#2563eb", "#d97706", "#64748b", "#7c3aed", "#db2777"]


def txt(x, y, s, size=15, fill=INK, weight="400", anchor="start"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FS}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(str(s))}</text>')


def wrap(t, n):
    out, line = [], ""
    for w in str(t).split():
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    out.append(line)
    return out


def main():
    spec_path = sys.argv[1]
    out = BASE / "Fedor_Схема_из_спеки.svg"
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))

    lanes = spec.get("lanes", []) or [{"id": "main", "title": "Процесс"}]
    stages = spec.get("stages", [])
    steps = spec.get("steps", [])
    lane_idx = {l["id"]: i for i, l in enumerate(lanes)}
    stage_idx = {s["id"]: i for i, s in enumerate(stages)}
    lane_color = {l["id"]: PALETTE[i % len(PALETTE)] for i, l in enumerate(lanes)}

    # --- предрасчёт высоты карточек и строк ---
    def step_lines(st):
        nl = wrap(st.get("norm", ""), 30)
        tl = wrap(st.get("text", ""), 34)[:3]
        return nl, tl

    def step_h(st):
        nl, tl = step_lines(st)
        return 16 + 14 * len(nl) + (4 + 14 * len(tl) if tl else 0) + 6

    # высоты заголовка этапа
    stage_h = 34
    for st in stages:
        n = len(wrap(st["title"], 22)) * 20 + len(wrap(st.get("norms", ""), 26)) * 16 + 22
        stage_h = max(stage_h, n)

    cells = {}
    lane_rows = []
    for li, l in enumerate(lanes):
        hmax = 78
        for st in steps:
            if st["lane"] == l["id"]:
                cells.setdefault((st["lane"], st["stage"]), []).append(st)
        for key, arr in cells.items():
            if key[0] == l["id"]:
                h = sum(step_h(x) for x in arr) + 10 * (len(arr) - 1) + 24
                hmax = max(hmax, h)
        lane_rows.append(hmax)

    col_x0 = M + HDR_W
    W = col_x0 + COL_W * max(1, len(stages)) + M
    grid_top = TITLE_H + stage_h
    grid_h = sum(lane_rows)

    cl_items = []
    cl_ref = spec.get("checklist_ref"); cl_src = None
    if cl_ref and (BASE / cl_ref).exists():
        cld = json.loads((BASE / cl_ref).read_text(encoding="utf-8"))
        cl_items = cld.get("items", []); cl_src = cld.get("source_norm", "")
    cl_rows = (len(cl_items) + 1) // 2 if cl_items else 0
    PANEL_H = (60 + cl_rows * 24) if cl_items else 0
    H = grid_top + grid_h + 24 + PANEL_H + 96

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FS}">',
         '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
         '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.10"/></filter>'
         '<marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
         '<path d="M0,0 L7,3 L0,6 z" fill="#94a3b8"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         txt(M, 44, spec.get("title", "Схема"), 23, INK, "700"),
         txt(M, 70, spec.get("subtitle", ""), 14, DIM)]

    # этапы
    for j, st in enumerate(stages):
        x = col_x0 + j * COL_W
        s.append(f'<rect x="{x}" y="{TITLE_H}" width="{COL_W}" height="{stage_h}" fill="#1e293b"/>')
        tl = wrap(st["title"], 22)
        for i, ln in enumerate(tl):
            s.append(txt(x + 16, TITLE_H + 28 + i * 20, ln, 16, "#f8fafc", "700"))
        ny = TITLE_H + 28 + len(tl) * 20 + 2
        for i, ln in enumerate(wrap(st.get("norms", ""), 26)):
            s.append(txt(x + 16, ny + i * 16, ln, 12.5, "#a7b6d0"))

    # дорожки
    y = grid_top
    for li, l in enumerate(lanes):
        rh = lane_rows[li]
        color = lane_color[l["id"]]
        band = "#fff7e6" if l.get("highlight") else ("#f8fafc" if li % 2 else "#ffffff")
        s.append(f'<rect x="{M}" y="{y}" width="{W-2*M}" height="{rh}" fill="{band}"/>')
        s.append(f'<rect x="{M}" y="{y+rh-1}" width="{W-2*M}" height="1" fill="#e6ebf3"/>')
        s.append(f'<rect x="{M}" y="{y}" width="{HDR_W}" height="{rh}" fill="{color}" opacity="0.12"/>')
        s.append(f'<rect x="{M}" y="{y}" width="6" height="{rh}" fill="{color}"/>')
        ll = wrap(l["title"], 24)
        for i, ln in enumerate(ll):
            s.append(txt(M + 18, y + rh / 2 - (len(ll) - 1) * 9 + i * 18, ln, 14.5, color, "700"))

        # карточки шагов этой дорожки
        for si in range(len(stages)):
            key = (l["id"], stages[si]["id"])
            arr = cells.get(key, [])
            if not arr:
                continue
            total = sum(step_h(x) for x in arr) + 10 * (len(arr) - 1)
            cy = y + (rh - total) / 2
            x = col_x0 + si * COL_W + 12; w = COL_W - 24
            for st in arr:
                bh = step_h(st)
                s.append(f'<rect x="{x}" y="{cy:.1f}" width="{w}" height="{bh:.1f}" rx="10" fill="#ffffff" '
                         f'stroke="{color}" stroke-width="1.8" filter="url(#sh)"/>')
                s.append(f'<rect x="{x}" y="{cy:.1f}" width="5" height="{bh:.1f}" rx="2.5" fill="{color}"/>')
                yy = cy + 16
                nl, tl = step_lines(st)
                for ln in nl:
                    s.append(txt(x + 14, yy, ln, 12.5, color, "700")); yy += 14
                yy += 4
                for ln in tl:
                    s.append(txt(x + 14, yy, ln, 11.5, DIM)); yy += 14
                cy += bh + 10
        y += rh

    # панель чек-листа
    if cl_items:
        py = grid_top + grid_h + 24
        s.append(f'<rect x="{M}" y="{py}" width="{W-2*M}" height="{PANEL_H}" rx="12" fill="#f8fafc" stroke="#e2e8f0"/>')
        s.append(txt(M + 16, py + 26, f"Контрольный список: {cl_src} — {len(cl_items)} позиций (полнота проверяется гейтом)", 13, INK, "700"))
        cw = (W - 2 * M - 32) // 2
        for i, it in enumerate(cl_items):
            cx = M + 16 + (i % 2) * (cw + 16); cy = py + 52 + (i // 2) * 24
            s.append(txt(cx, cy, f"п. {it.get('p','')} · {it.get('who','')} — {it.get('doc','')}", 12.5, DIM))

    ly = H - 66
    s.append(txt(M, ly, "Оговорка: приоритеты/коллизии — только curated; трактовки — draft. Содержание — из спеки (Фёдор + верификатор).", 12, "#b91c1c"))
    s.append(txt(M, ly + 22, f"Источник нормы: {spec.get('source_norm','—')}", 12, DIM))
    s.append("</svg>")
    out.write_text("\n".join(s), encoding="utf-8")
    print(f"OK: {out} ({out.stat().st_size} байт), {W}x{H}")


if __name__ == "__main__":
    main()
