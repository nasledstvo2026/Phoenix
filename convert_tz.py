#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Конвертер TZ.md (социальный исследователь) → socissledtz.html в стиле сайта Phoenix."""
import re, html

SRC = 'social-research-agent/TZ.md'
OUT = 'socissledtz.html'

# --- извлекаем CSS из старой страницы ---
old = open(OUT, encoding='utf-8').read()
m = re.search(r'<style>.*?</style>', old, re.S)
css = m.group(0) if m else ''

# --- парсер markdown-подмножества ---
def inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t

def md_to_html(md_text):
    out = []
    in_code = False
    in_ul = False
    in_table = False
    first_h2 = True
    skip_until_close = False
    lines = md_text.split('\n')
    i = 0
    skip_tags = {'<section', '</section>', '<context>', '</context>', '<requirements>', '</requirements>',
                 '<constraints>', '</constraints>', '<validation>', '</validation>', '<changelog>', '</changelog>'}
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        # пропуск meta-блока <section id=...> до </section>
        if skip_until_close:
            if stripped.startswith('</section>'):
                skip_until_close = False
            i += 1; continue
        if stripped.startswith('<section id'):
            skip_until_close = True
            i += 1; continue
        # пропуск служебных тегов и пустых
        if any(stripped.startswith(t) for t in skip_tags):
            i += 1; continue
        if in_code:
            if stripped.startswith('```'):
                out.append('</code></pre>'); in_code = False
            else:
                out.append(html.escape(line))
            i += 1; continue
        if stripped.startswith('```'):
            if in_ul: out.append('</ul>'); in_ul = False
            if in_table: out.append('</table>'); in_table = False
            out.append('<pre><code>'); in_code = True
            i += 1; continue
        if not stripped:
            if in_ul: out.append('</ul>'); in_ul = False
            if in_table: out.append('</table>'); in_table = False
            i += 1; continue
        # таблица
        if stripped.startswith('|'):
            if not in_table:
                out.append('<table>'); in_table = True
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                i += 1; continue  # разделитель
            tag = 'th' if not in_table else 'td'
            # первая строка после открытия = заголовок
            if out[-1] == '<table>':
                tag = 'th'
            out.append('<tr>' + ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells) + '</tr>')
            i += 1; continue
        if in_table:
            out.append('</table>'); in_table = False
        # заголовки
        hm = re.match(r'^(#{2,4})\s+(.*)$', stripped)
        if hm:
            lvl = len(hm.group(1))
            txt = inline(hm.group(2))
            if lvl == 2:
                if in_ul: out.append('</ul>'); in_ul = False
                if not first_h2:
                    out.append('</section>')
                first_h2 = False
                out.append(f'\n\n<section>\n<h2>{txt}</h2>')
            elif lvl == 3:
                out.append(f'<h3>{txt}</h3>')
            else:
                out.append(f'<h4>{txt}</h4>')
            i += 1; continue
        # список
        lm = re.match(r'^\s*[-*]\s+(.*)$', stripped)
        if lm:
            if not in_ul:
                out.append('<ul>'); in_ul = True
            out.append(f'<li>{inline(lm.group(1))}</li>')
            i += 1; continue
        if in_ul:
            out.append('</ul>'); in_ul = False
        # нумерованный список
        nm = re.match(r'^\s*\d+\.\s+(.*)$', stripped)
        if nm:
            out.append(f'<p>{inline(nm.group(1))}</p>')
            i += 1; continue
        # обычный параграф (собираем соседние)
        buf = [inline(stripped)]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            ns = nxt.strip()
            if not ns or ns.startswith(('|', '```', '#', '- ', '* ', '1.')) or any(ns.startswith(t) for t in skip_tags):
                break
            buf.append(inline(ns))
            i += 1
        out.append('<p>' + ' '.join(buf) + '</p>')
    if in_ul: out.append('</ul>')
    if in_table: out.append('</table>')
    if in_code: out.append('</code></pre>')
    out.append('</section>')
    return '\n'.join(out)

# --- читаем TZ.md, отрезаем первый заголовок ---
md = open(SRC, encoding='utf-8').read()
md = re.sub(r'^# .*\n', '', md, count=1)
body = md_to_html(md)

# --- секция 0: статус реализации ---
status = '''<section>
  <h2>0. Статус реализации — 20.08.2026</h2>
  <p><strong>ТЗ обновлено 19.08.2026 (v1.11)</strong> — доступ по триггеру только Кирилл; полный сбор выполнен (273 файла, 16–18.08.2026); проведён анализ стоимости (~7 000 ₽, корневая причина — раздутый контекст оркестратора) и сформирован подход к удешевлению; зафиксирована карта моделей.</p>
  <table>
    <tr><th>Этап</th><th>Статус</th><th>Комментарий</th></tr>
    <tr><td>1. Подготовка инфраструктуры</td><td>✅ Готово</td><td>workspace, каталоги, <code>categories.json</code>, промпты <code>invalidy/vbd/svo</code>, SKILL.md, AGENTS.md, <code>build_summary.py</code></td></tr>
    <tr><td>2. Конфигурация агентов</td><td>✅ Готово</td><td><code>social-research-agent</code> + <code>irina-router</code>; карта моделей: flash везде, pro — только fallback</td></tr>
    <tr><td>3. Маршрутизация</td><td>✅ Готово (изменено 19.08)</td><td>Binding Ирины (739016616) → irina-router снят; запуск по триггеру — ТОЛЬКО Кирилл; «Федор» не затронут</td></tr>
    <tr><td>6. Тестирование</td><td>🧪 Частично</td><td>Тест 1/3/4 ✅; Тест 2/5/6 ❌; Тест 7 🚫; полный сбор (89×3) выполнен 16–18.08: 273 файла</td></tr>
    <tr><td>7. Приёмка</td><td>🧪 Частично</td><td>Инструкция для Ирины ✅, сводные Excel ✅; системные проверки 80% полей ❌</td></tr>
  </table>

  <h3>Ключевые изменения v1.9–v1.11 (19.08.2026)</h3>
  <ul>
    <li><strong>Запуск по триггеру — только Кирилл</strong> (346428630): binding Ирины на irina-router снят, остальным на триггеры сбора — отказ «Эта функция доступна только владельцу»; «Федор» доступен всем, как раньше</li>
    <li><strong>Квартальный пересбор — штатный режим:</strong> меры «скип готовых» и «запрет повторов» отклонены, полный пересбор всех 89×3 при каждом квартальном прогоне (накопительный Excel 🆕/❌/✏️/▬)</li>
    <li><strong>Анализ стоимости (раздел 4.1):</strong> ~7 000 ₽ за полный сбор; корневая причина — раздутый контекст оркестратора (1.2 млрд токенов, 80% расходов); план удешевления: контекст оркестратора 1M→32K, краткие announce субагентов, thinking medium, кэш DeepSeek → ~1 000–1 500 ₽ за прогон</li>
    <li><strong>Карта моделей:</strong> flash везде (оркестратору — жёстко), pro — только fallback, локальные модели не используются</li>
  </ul>
</section>'''

# --- сборка страницы ---
page = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ТЗ: Социальный исследователь на Фениксе</title>
{css}
</head>
<body>

<header>
  <div class="container">
    <h1>📋 ТЗ: Социальный исследователь на Фениксе</h1>
    <div class="meta-card">
      <span>👤 <strong>Автор:</strong> Лунтик 🦞</span>
      <span class="status-badge accepted">✅ Согласовано</span>
      <span>📅 <strong>Дата:</strong> 2026-08-20</span>
      <span>🏷️ <strong>Версия:</strong> 1.12</span>
    </div>
    <br>
    <a class="back" href="social.html">← Назад к «Социальный консультант»</a>
    <span style="color:var(--text-secondary); margin: 0 0.6rem;">·</span>
    <a class="back" href="https://github.com/nasledstvo2026/Phoenix/blob/main/social-research-agent/TZ.md" target="_blank" rel="noopener">📄 Исходное ТЗ (Markdown)</a>
  </div>
</header>

<div class="container">

{status}

{body}

</div>

<footer>
  ТЗ v1.12 · ред. 2026-08-20 · Феникс 🔥 · <a href="https://nasledstvo2026.github.io/Phoenix/social.html">Социальный консультант</a>
</footer>

</body>
</html>'''

open(OUT, 'w', encoding='utf-8').write(page)
print('OK:', OUT, len(page), 'bytes')
