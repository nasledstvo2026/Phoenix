#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Карта «ЖЦ ИД × ФЗ» в СТИЛЕ ОТЧЁТА АСВ (переиспользован CSS/подход build_asv_report.py).

Шкала по горизонтали = этапы ЖЦ ИД. Строки = законы. На пересечениях — нормы.
Зона ответственности банка — отдельная выделенная строка.
Выход: Fedor_ЖЦ_гант.html (рендер PNG — через asv_shot.py)
"""
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "Fedor_ЖЦ_гант.html"

BLUE = "#2563eb"; PINK = "#db2777"; ORANGE = "#ea580c"; YELLOW = "#ca8a04"
TEAL = "#0d9488"; INDIGO = "#4f46e5"; VIOLET = "#7c3aed"; MAGENTA = "#db2777"; GOLD = "#d97706"

STAGES = [
    ("1", "Выдача ИД", "ст. 12–13"),
    ("2", "Предъявление", "ст. 21–22"),
    ("3", "Возбуждение", "ст. 30–31"),
    ("4", "Добровольно", "5 дней"),
    ("5", "Принудительно", "ст. 36, 64, 68"),
    ("6", "Окончание / возврат", "ст. 47 / 46 / 43"),
    ("7", "Повторно", "ст. 46 ч. 4"),
]

# (строка, цвет, {индекс этапа: [(норма, подпись)]}, is_bank)
ROWS = [
    ("229-ФЗ — ядро ЖЦ", BLUE, {
        0: [("ст. 12–13", "виды и требования к ИД")],
        1: [("ст. 21–22", "сроки; перерыв")],
        2: [("ст. 30–31", "возбуждение; отказ")],
        3: [("ст. 30 ч. 11–12", "5 дней")],
        4: [("ст. 36, 64, 68", "2 месяца; меры")],
        5: [("ст. 47 / 46 / 43", "окончание / возврат / прекращение")],
        6: [("ст. 46 ч. 4", "повторно")],
    }, False),
    ("425-ФЗ — изменяющий", PINK, {
        4: [("amends НК 46/60", "реестр решений, 3 часа · с 01.01.2027")],
    }, False),
    ("НК РФ ч. 1", ORANGE, {
        0: [("п. 5.2 ст. 12", "ИД = постановление ФНС")],
        4: [("ст. 46, 60", "взыскание через банк; ЕНС 11.3")],
        5: [("ст. 59", "списание безнадёжной")],
    }, False),
    ("НК РФ ч. 2", YELLOW, {
        0: [("—", "объект взыскания")],
        4: [("—", "состав задолженности")],
    }, False),
    ("ГК РФ ч. 2", TEAL, {
        4: [("ст. 855", "очерёдность списания со счетов")],
    }, False),
    ("УПК РФ", INDIGO, {
        0: [("ст. 103 229-ФЗ", "штраф за преступление")],
    }, False),
    ("127-ФЗ — банкротство", VIOLET, {
        5: [("ст. 223.4/223.6", "приостановление ИП; внесудебное (223.2)")],
    }, False),
    ("603-ФЗ — СВО", MAGENTA, {
        5: [("изменяющий", "приостановление требований")],
    }, False),
    ("★ ЗОНА ОТВЕТСТВЕННОСТИ БАНКА", GOLD, {
        1: [("229-ФЗ ст. 8", "предъявление напрямую в банк")],
        4: [("НК 46/60 · ГК 855", "сроки · очерёдность · обязанности (ст. 60)")],
        5: [("НК ст. 135", "ответственность: 1/150, ≤0,2%/день; 30% · розыск счетов")],
    }, True),
]

NAMEW = 300
COLW = 168
ROWH = 66
HEADH = 54
GX = NAMEW
GW = COLW * len(STAGES)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    H = HEADH + ROWH * len(ROWS)
    p = [f'<svg width="{NAMEW+GW}" height="{H}" viewBox="0 0 {NAMEW+GW} {H}">']
    # заголовки столбцов
    for j, (num, name, norms) in enumerate(STAGES):
        x = GX + j * COLW
        p.append(f'<rect x="{x}" y="0" width="{COLW}" height="{HEADH}" fill="#f8fafc"/>')
        p.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#eef2f7"/>')
        p.append(f'<text x="{x+14}" y="24" font-size="13" font-weight="700" fill="#0f172a">{esc(num)}. {esc(name)}</text>')
        p.append(f'<text x="{x+14}" y="42" font-size="11" fill="#64748b">{esc(norms)}</text>')
    # строки
    for i, (name, color, cells, is_bank) in enumerate(ROWS):
        y = HEADH + i * ROWH
        band = "#fff7e6" if is_bank else ("#f8fafc" if i % 2 else "#ffffff")
        p.append(f'<rect x="0" y="{y}" width="{NAMEW+GW}" height="{ROWH}" fill="{band}"/>')
        p.append(f'<rect x="0" y="{y+ROWH-1}" width="{NAMEW+GW}" height="1" fill="#eef2f7"/>')
        p.append(f'<rect x="0" y="{y}" width="5" height="{ROWH}" fill="{color}"/>')
        p.append(f'<text x="18" y="{y+ROWH/2+4}" font-size="13.5" font-weight="700" fill="{color}">{esc(name)}</text>')
        for j, items in cells.items():
            x = GX + j * COLW + 6
            h = 22 + 16 * len(items)
            cy = y + (ROWH - h) / 2
            dash = ' stroke-dasharray="6 4"' if name.startswith("425") else ''
            p.append(f'<rect x="{x}" y="{cy:.1f}" width="{COLW-12}" height="{h}" rx="8" fill="#ffffff" stroke="{color}" stroke-width="1.6"{dash}/>')
            yy = cy + 15
            for (norm, label) in items:
                p.append(f'<text x="{x+9}" y="{yy:.1f}" font-size="11" font-weight="700" fill="{color}">{esc(norm)}</text>')
                yy += 14
                p.append(f'<text x="{x+9}" y="{yy:.1f}" font-size="10.5" fill="#475569">{esc(label)}</text>')
                yy += 15
    p.append(f'<line x1="{GX}" y1="0" x2="{GX}" y2="{H}" stroke="#cbd5e1"/>')
    p.append("</svg>")
    return "".join(p), H


svg, SVGH = build_svg()

# CSS — как в отчёте АСВ
css = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
     background:#f1f5f9;color:#0f172a;padding:28px;-webkit-font-smoothing:antialiased}
.page{max-width:1460px;margin:0 auto;background:#fff;border-radius:16px;padding:32px;
      box-shadow:0 4px 24px rgba(15,23,42,.08)}
h1{font-size:22px;font-weight:700}
h1 .sub{display:block;font-size:13px;font-weight:500;color:#64748b;margin-top:4px}
.hdr{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px}
.chip{background:#eef2ff;color:#4338ca;font-size:12px;font-weight:600;padding:6px 12px;border-radius:999px;white-space:nowrap}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0 26px}
.kpi{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 18px}
.kpi .v{font-size:28px;font-weight:800}
.kpi .l{font-size:12px;color:#64748b;margin-top:4px}
.section{font-size:13px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.06em;margin:28px 0 12px}
.legend{display:flex;gap:18px;align-items:center;font-size:12.5px;color:#475569;margin-bottom:12px;flex-wrap:wrap}
.legend .it{display:flex;align-items:center;gap:6px}
.sw{width:14px;height:8px;border-radius:3px;display:inline-block}
.gantt{overflow-x:auto;border:1px solid #e2e8f0;border-radius:12px}
.gantt svg{display:block}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
th{background:#f8fafc;text-align:left;padding:10px 12px;font-size:11.5px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid #e2e8f0}
td{padding:9px 12px;border-bottom:1px solid #eef2f7;vertical-align:top}
.bank{background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:14px 20px;margin-top:14px}
.bank .bt{font-weight:800;color:#b45309;font-size:14px;margin-bottom:8px}
.bank ul{margin:0;padding-left:20px;font-size:13px;line-height:1.55;color:#1f2937}
.foot{margin-top:20px;font-size:11.5px;color:#94a3b8}
"""

html = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>ЖЦ ИД и федеральные законы</title><style>{css}</style></head>
<body><div class="page">

<div class="hdr">
  <h1>Жизненный цикл исполнительного документа и федеральные законы
    <span class="sub">Шкала — этапы ЖЦ ИД (ядро: 229-ФЗ). Строки — акты библиотеки; на пересечениях — нормы, работающие на этапе.</span>
  </h1>
  <div class="chip">ЖЦ ИД · зона ответственности банка</div>
</div>

<div class="kpis">
  <div class="kpi"><div class="v">5</div><div class="l">источников ИД</div></div>
  <div class="kpi"><div class="v">7</div><div class="l">этапов жизненного цикла</div></div>
  <div class="kpi"><div class="v">8</div><div class="l">актов в библиотеке</div></div>
  <div class="kpi"><div class="v">16</div><div class="l">курируемых трактовок (draft)</div></div>
</div>

<div class="section">Карта: этапы ЖЦ ИД × федеральные законы</div>
<div class="legend">
  <span class="it"><span class="sw" style="background:{BLUE}"></span>229-ФЗ — этапы ИД</span>
  <span class="it"><span class="sw" style="background:{PINK}"></span>425-ФЗ — изменяющий (2027)</span>
  <span class="it"><span class="sw" style="background:{GOLD}"></span>зона ответственности банка</span>
  <span class="it"><span class="sw" style="background:#fff;border:1.6px dashed {PINK}"></span>пунктир — эффект с 01.01.2027</span>
</div>
<div class="gantt">{svg}</div>

<div class="section">Зона ответственности банка</div>
<table>
  <tr><th>Что обязан</th><th>Норма</th><th>Срок / параметр</th></tr>
  <tr><td class="td-task">Исполнять поручение ФНС (налогового органа)</td><td class="mono">НК ч.1 ст. 46, 60</td><td>3 часа (с 01.01.2027) / 1 операционный день</td></tr>
  <tr><td class="td-task">Соблюдать очерёдность списания</td><td class="mono">ГК ч.2 ст. 855</td><td>очерёдность по гражданскому законодательству</td></tr>
  <tr><td class="td-task">Не задерживать при наличии средств; сообщить о неисполнении</td><td class="mono">НК ч.1 ст. 60</td><td>сообщить в течение следующего дня</td></tr>
  <tr><td class="td-task">Идентифицировать клиента и разыскать счета</td><td class="mono">ПНО по ИНН</td><td>с 01.01.2027</td></tr>
  <tr><td class="td-task">Исполнять ИД, предъявленный напрямую</td><td class="mono">229-ФЗ ст. 8</td><td>—</td></tr>
</table>

<div class="bank">
  <div class="bt">⚠️ Ответственность банка — НК РФ ч.1 ст. 135</div>
  <ul>
    <li>Неправомерное неисполнение поручения: штраф <b>1/150 ставки рефинансирования</b>, но не более <b>0,2%</b> за каждый календарный день просрочки.</li>
    <li>Действия по созданию ситуации отсутствия средств на счёте: штраф <b>30%</b> от непоступившей суммы.</li>
  </ul>
</div>

<div class="foot">Источники: 229-ФЗ ст. 8, 12–13, 21–22, 30–31, 36, 43, 46–47; НК РФ ч.1 ст. 46, 59, 60, 135; ГК РФ ч.2 ст. 855; 127-ФЗ ст. 223.2/223.4/223.6; УПК РФ; 425-ФЗ. Трактовки — статус draft.</div>

</div></body></html>"""

OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT} ({OUT.stat().st_size} байт), gantt SVG {NAMEW+GW}x{SVGH}")
