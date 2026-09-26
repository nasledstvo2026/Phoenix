#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Слой-схема «ЖЦ ИД + ФЗ» на vis-network с ВРУЧНУЮ заданными координатами.

Снизу — рельс жизненного цикла (229-ФЗ). Сверху — законы; стрелки с подписями
показывают, на каком этапе акт работает. Пунктир — эффект с 01.01.2027.

Собирает HTML → рендер PNG через headless Chrome.
Выход: Fedor_Слой_Карта.html / Fedor_Слой_Карта.png
"""
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).parent

C = {
    "FZ-425": "#ffb3ba", "NK-1": "#fed7aa", "NK-2": "#fef08a", "GK-2": "#99f6e4",
    "UPK": "#c7d2fe", "FZ-127": "#ddd6fe", "FZ-603": "#fbcfe8", "FZ-229": "#bae1ff",
    "LIFE": "#e2e8f0",
}

nodes = [
    # этапы (рельс, снизу)
    {"id": "L1", "label": "① Выдача ИД\nст. 12–13", "x": 200, "y": 760, "grp": "LIFE"},
    {"id": "L2", "label": "② Предъявление\nст. 21–22", "x": 420, "y": 760, "grp": "LIFE"},
    {"id": "L3", "label": "③ Возбуждение ИП\nст. 30–31", "x": 640, "y": 760, "grp": "LIFE"},
    {"id": "L4", "label": "④ Добровольное\n5 дней · ст. 30", "x": 860, "y": 760, "grp": "LIFE"},
    {"id": "L5", "label": "⑤ Принудительное\nст. 36, 64, 68", "x": 1080, "y": 760, "grp": "LIFE"},
    {"id": "L6", "label": "⑥ Окончание / возврат\nст. 47 / 46 / 43", "x": 1300, "y": 760, "grp": "LIFE"},
    {"id": "L7", "label": "⑦ Повторное\nст. 46 ч. 4", "x": 1520, "y": 760, "grp": "LIFE"},
    # законы (сверху)
    {"id": "UPK", "label": "УПК РФ\nштраф за преступление", "x": 200, "y": 470, "grp": "UPK"},
    {"id": "NK2", "label": "НК РФ ч. 2\nналоги, пени, штрафы", "x": 430, "y": 470, "grp": "NK-2"},
    {"id": "NK1", "label": "НК РФ ч. 1\nЕНС · взыскание ст. 46/60", "x": 760, "y": 250, "grp": "NK-1"},
    {"id": "FZ425", "label": "425-ФЗ — изменяющий", "x": 760, "y": 60, "grp": "FZ-425"},
    {"id": "GK2", "label": "ГК РФ ч. 2\nочерёдность (ст. 855)", "x": 1080, "y": 470, "grp": "GK-2"},
    {"id": "FZ127", "label": "127-ФЗ\nбанкротство", "x": 1320, "y": 470, "grp": "FZ-127"},
    {"id": "FZ603", "label": "603-ФЗ\nСВО / мобилизация", "x": 1540, "y": 470, "grp": "FZ-603"},
    {"id": "CORE", "label": "229-ФЗ — Об исполнительном производстве\n(ядро жизненного цикла)", "x": 860, "y": 940, "grp": "FZ-229"},
]

edges = [
    # рельс
    {"from": "L1", "to": "L2", "color": "#334155", "width": 3},
    {"from": "L2", "to": "L3", "color": "#334155", "width": 3},
    {"from": "L3", "to": "L4", "color": "#334155", "width": 3},
    {"from": "L4", "to": "L5", "color": "#334155", "width": 3},
    {"from": "L5", "to": "L6", "color": "#334155", "width": 3},
    {"from": "L6", "to": "L7", "color": "#334155", "width": 3},
    {"from": "L7", "to": "L2", "label": "цикл повторяется", "color": "#334155", "dashes": True},
    # ядро
    {"from": "CORE", "to": "L3", "label": "регламентирует этапы ①–⑦", "color": "#1d4ed8", "dashes": True},
    # налоговый контур
    {"from": "NK2", "to": "NK1", "label": "объект взыскания", "color": "#ca8a04"},
    {"from": "FZ425", "to": "NK1", "label": "amends: реестр решений, 3 часа — с 01.01.2027",
     "color": "#dc2626", "dashes": True, "width": 2},
    {"from": "NK1", "to": "L1", "label": "ИД = постановление налогового органа", "color": "#ea580c"},
    {"from": "NK1", "to": "L5", "label": "взыскание через банк (ст. 46/60)", "color": "#ea580c"},
    {"from": "NK1", "to": "L6", "label": "списание безнадёжной (ст. 59)", "color": "#ea580c"},
    # прочие акты
    {"from": "UPK", "to": "L1", "label": "штраф-наказание", "color": "#4f46e5"},
    {"from": "GK2", "to": "L5", "label": "очерёдность списания", "color": "#0d9488"},
    {"from": "FZ127", "to": "L6", "label": "приостановление ИП / банкротство", "color": "#7c3aed"},
    {"from": "FZ603", "to": "L6", "label": "приостановление (СВО)", "color": "#db2777", "dashes": True},
]

# JSON для фронтенда
vis_nodes = [{
    "id": n["id"], "label": n["label"], "x": n["x"] * 1.4, "y": n["y"] * 1.4,
    "shape": "box", "font": {"color": "#0f172a", "size": 15, "face": "DejaVu Sans", "multi": False},
    "color": {"background": C[n["grp"]], "border": "#334155",
              "highlight": {"background": C[n["grp"]], "border": "#111"}},
    "borderWidth": 3 if n["grp"] in ("FZ-229", "FZ-425") else 1.6,
    "margin": 12, "widthConstraint": {"minimum": 120, "maximum": 230},
} for n in nodes]

vis_edges = [{
    "from": e["from"], "to": e["to"], "label": e.get("label", ""),
    "color": {"color": e.get("color", "#64748b"), "highlight": "#111"},
    "font": {"size": 13, "color": "#334155", "face": "DejaVu Sans", "background": "#ffffff",
             "strokeWidth": 4, "strokeColor": "#ffffff", "align": "middle"},
    "width": e.get("width", 1.6), "dashes": e.get("dashes", False),
    "smooth": {"type": "curvedCW", "roundness": 0.25},
    "arrows": {"to": {"enabled": True, "scaleFactor": 0.7}},
} for e in edges]

data = {"nodes": vis_nodes, "edges": vis_edges}

html = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:#fff;font-family:"DejaVu Sans",Arial,sans-serif}
#h{position:absolute;left:28px;top:18px} h2{margin:0;font-size:24px}
p{margin:6px 0 0;color:#475569;font-size:14px}</style></head>
<body>
<div id="h"><h2>Жизненный цикл исполнительного документа (ИД) и федеральные законы</h2>
<p>Рельс снизу — этапы ЖЦ ИД (ядро: 229-ФЗ). Стрелки — вклад законов в этапы; пунктир — эффект с 01.01.2027.</p></div>
<div id="net" style="position:absolute;left:0;top:96px;width:100%;height:1250px"></div>
<script src="assets/vis-network.min.js"></script>
<script>
const D = __DATA__;
const nodes = new vis.DataSet(D.nodes.map(n=>({...n, fixed:true, physics:false})));
const edges = new vis.DataSet(D.edges);
const net = new vis.Network(document.getElementById('net'), {nodes,edges}, {
  physics:false, layout:{improvedLayout:false}, interaction:{zoomView:false, dragView:false},
  nodes:{shape:'box'}, edges:{selectionWidth:0}
});
</script></body></html>"""

html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
out_html = BASE / "Fedor_Слой_Карта.html"
out_html.write_text(html, encoding="utf-8")

CMD = ["google-chrome-stable", "--headless=new", "--disable-gpu", "--no-sandbox",
       "--hide-scrollbars", "--force-device-scale-factor=1.7", "--window-size=2360,1400",
       f"--screenshot={BASE/'Fedor_Слой_Карта.png'}", f"file://{out_html}"]
print(" ".join(CMD[:3]), "...")
r = subprocess.run(CMD, capture_output=True, text=True, timeout=120)
print((r.stderr or "")[-300:])
print("html:", out_html, "| png:", (BASE/'Fedor_Слой_Карта.png').exists())
