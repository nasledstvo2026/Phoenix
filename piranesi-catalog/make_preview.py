#!/usr/bin/env python3
"""Сборка preview.html — одностраничный предпросмотр каталога (всё inline)."""
import json
import re

INDEX = "index.html"
STYLE = "style.css"
APP = "app.js"
DATA = "data/catalog.json"
OUT = "preview.html"

html = open(INDEX, encoding="utf-8").read()
style = open(STYLE, encoding="utf-8").read()
app = open(APP, encoding="utf-8").read()
data = json.dumps(json.load(open(DATA, encoding="utf-8")), ensure_ascii=False)

html = html.replace('<link rel="stylesheet" href="style.css">',
                    "<style>\n" + style + "\n</style>")
html = html.replace('<script src="app.js"></script>',
                    "<script>window.__DATA__ = " + data + ";</script>\n"
                    "<script>" + app + "</script>")

open(OUT, "w", encoding="utf-8").write(html)
print(OUT, len(html), "bytes")
