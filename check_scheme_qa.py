#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA схемы (по образцу АСВ): структура + численная геометрия (chrome CDP).

Проверяет:
  1) СТРУКТУРА — в SVG присутствуют все ожидаемые подписи (--require).
  2) ГЕОМЕТРИЯ — через chrome CDP: bbox всех <text>; взаимные НАЛОЖЕНИЯ подписей
     и ВЫХОД за пределы холста.
Опционально запускает Qwen2.5-VL (см. qwen_review_scheme.py) — отдельно.

Использование:
  python3 check_scheme_qa.py SCHEMA.svg [--require "строка1;;строка2;..."]
Выход: 0 = ок, 1 = проблемы (структура/геометрия).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

try:
    import websocket  # websocket-client
except Exception:
    websocket = None

PORT = 9345
CHROME = "/usr/bin/google-chrome"


def load_svg(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def structural(svg, required):
    problems = []
    for s in required:
        if s and s not in svg:
            problems.append(f"нет подписи: «{s}»")
    return problems


def geometry(svg_path):
    """Возвращает (problems, stats) через CDP."""
    if websocket is None:
        return ["CDP недоступен (нет websocket-client)"], {}
    subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                      f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
                      "--window-size=1800,2400", "--user-data-dir=/tmp/cdp_scheme",
                      "about:blank"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws_url = None
    for _ in range(40):
        try:
            d = json.load(urllib.request.urlopen(f"http://localhost:{PORT}/json/version"))
            ws_url = d["webSocketDebuggerUrl"]
            break
        except Exception:
            time.sleep(0.5)
    if not ws_url:
        return ["CDP не поднялся"], {}
    ws = websocket.create_connection(ws_url, timeout=30)
    _id = [0]

    def cmd(method, params=None, sid=None):
        _id[0] += 1
        msg = {"id": _id[0], "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        ws.send(json.dumps(msg))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == _id[0]:
                return r

    url = "file://" + os.path.abspath(svg_path)
    t = cmd("Target.createTarget", {"url": url})["result"]["targetId"]
    s = cmd("Target.attachToTarget", {"targetId": t, "flatten": True})["result"]["sessionId"]
    cmd("Page.enable", sid=s)
    cmd("Runtime.enable", sid=s)
    time.sleep(2.0)

    js = r"""
(() => {
  const svg = document.querySelector('svg');
  if (!svg) return JSON.stringify({error:'нет <svg>'});
  const sr = svg.getBoundingClientRect();
  const W = sr.width, H = sr.height;
  const texts = [...svg.querySelectorAll('text')];
  const bx = [];
  for (const t of texts) {
    const s = (t.textContent||'').trim();
    if (!s) continue;
    const r = t.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    bx.push({t: s.slice(0,45), x: r.x - sr.x, y: r.y - sr.y, w: r.width, h: r.height});
  }
  const inter = (a,b) => {
    const x = Math.max(0, Math.min(a.x+a.w,b.x+b.w) - Math.max(a.x,b.x));
    const y = Math.max(0, Math.min(a.y+a.h,b.y+b.h) - Math.max(a.y,b.y));
    return x*y;
  };
  const overlaps = [];
  for (let i=0;i<bx.length;i++) for (let j=i+1;j<bx.length;j++) {
    const a=bx[i], b=bx[j];
    if (a.t===b.t) continue;
    const ov = inter(a,b);
    const minA = Math.min(a.w*a.h, b.w*b.h);
    if (minA>0 && ov/minA > 0.35) overlaps.push({a:a.t, b:b.t, frac:+(ov/minA).toFixed(2)});
  }
  const outside = bx.filter(b => b.x < -2 || b.y < -2 || b.x+b.w > W+2 || b.y+b.h > H+2)
                    .map(b => ({t:b.t, x:Math.round(b.x), y:Math.round(b.y)}));
  return JSON.stringify({W:Math.round(W), H:Math.round(H), texts:bx.length,
                         overlaps:overlaps.slice(0,40), n_overlaps:overlaps.length,
                         outside:outside.slice(0,20), n_outside:outside.length});
})()
"""
    r = cmd("Runtime.evaluate", {"expression": js, "returnByValue": True}, sid=s)
    val = r.get("result", {}).get("result", {}).get("value")
    ws.close()
    try:
        data = json.loads(val)
    except Exception:
        return ["не удалось разобрать CDP-ответ"], {}
    if data.get("error"):
        return [data["error"]], {}
    problems = []
    for o in data.get("overlaps", [])[:12]:
        problems.append(f"наложение подписей: «{o['a']}» ↔ «{o['b']}» ({o['frac']})")
    for o in data.get("outside", [])[:12]:
        problems.append(f"выход за холст: «{o['t']}» ({o['x']},{o['y']})")
    return problems, data


def main():
    svg_path = sys.argv[1]
    required = []
    if "--require" in sys.argv:
        required = [x for x in sys.argv[sys.argv.index("--require") + 1].split(";;") if x.strip()]

    svg = load_svg(svg_path)
    sp = structural(svg, required)
    gp, gstats = geometry(svg_path)

    print("═" * 60)
    print(f"QA схемы: {svg_path}")
    print(f"Холст: {gstats.get('W')}×{gstats.get('H')} · подписей: {gstats.get('texts')}")
    print(f"Структура: {'✅ все подписи на месте' if not sp else '❌ ' + str(len(sp)) + ' проблем'}")
    for p in sp:
        print("   -", p)
    print(f"Геометрия: {'✅ наложений/выходов нет' if not gp else '❌ ' + str(len(gp)) + ' проблем'}")
    for p in gp:
        print("   -", p)
    ok = not (sp or gp)
    print("ИТОГ:", "✅ ПРИНЯТО" if ok else "❌ ТРЕБУЕТ ПРАВКИ")
    print("═" * 60)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
