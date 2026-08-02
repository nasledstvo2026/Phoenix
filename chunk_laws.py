#!/usr/bin/env python3
"""Чанкинг законов: разбивка на статьи, очистка от мусора КонсультантПлюс."""

import re, json, sys
from pathlib import Path

BASE = Path(__file__).parent / "fz425-agent"
FILES = {
    "fz425": "Федеральныи_закон_от_28_11_2025_N_425_ФЗ_ред_от_26_06_2026---1e32d0b3-54d4-4260-bbfa-ad87c95c389d.md",
    "nk1":   "Налоговыи_кодекс_России_скои_Федерации_часть_первая_от_31---df4d6d1a-269a-4325-9334-538212601451.md",
    "nk2":   "Налоговыи_кодекс_России_скои_Федерации_часть_вторая_от_05---cbe04864-7a7e-4138-a2eb-c5127d122931.md",
}

MAX_CHUNK_CHARS = 3000  # ~750 токенов — с запасом под keywords (модель обрезает с 512 токенов)

# Ключевые слова для обогащения чанков 425-ФЗ
# Ключ = (source, article), значение = блок keywords в конец текста
KEYWORDS = {
    # art=1 425-ФЗ — ст.46 НК (ПНО)
    ("fz425", "1"): "КЛЮЧЕВЫЕ СЛОВА: розыск счетов, банк ищет счета должника, банк обязан найти счета, обязанность банка по розыску, ПНО поручение налогового органа, срок обработки ПНО 3 часа, взыскание задолженности через банк",
    # art=1 425-ФЗ — ст.60 НК (обязанности банка)
    ("fz425", "2"): "КЛЮЧЕВЫЕ СЛОВА: обязанности банка, банк обязан исполнить поручение, срок исполнения банком, ответственность банка за неисполнение",
    # art=20 425-ФЗ — переходные положения
    ("fz425", "20"): "КЛЮЧЕВЫЕ СЛОВА: переходный период, СМЭВ-3, система межведомственного электронного взаимодействия, реестр решений, неисполненные поручения, один операционный день",
}


def preprocess_425(text: str) -> str:
    """Предобработка 425-ФЗ: удалить КонсультантПлюс-разметку до парсинга статей."""
    lines = text.split('\n')
    cleaned = []

    for line in lines:
        # 1. Вырезать строки таблиц +---+
        if re.match(r'^\+\-+\+', line.strip()):
            continue
        # 2. Вырезать строки внутри таблиц | ... |
        if re.match(r'^\|.*\|$', line.strip()):
            continue
        # 3. Вырезать примечания КонсультантПлюс (в т.ч. оставшиеся после фильтрации таблиц)
        s = line.strip()
        if 'КонсультантПлюс' in s and ('примечан' in s.lower() or 'www.consultant' in s.lower()):
            continue
        # 4. Вырезать разделители ------
        if re.match(r'^-{10,}$', s):
            continue
        # 5. Вырезать картинки ![](media/...)
        if re.search(r'!\[.*?\]\(.*?media.*?\)', line):
            continue
        # 6. Дата сохранения
        if re.match(r'^Дата сохранения:', s):
            continue
        # 7. Пустые строки с картинками (остатки {width=...})
        if s.startswith('{width=') or s == '!':
            continue
        # 8. Ссылки [текст](url) → текст
        line = re.sub(r'\[([^\]]*?)\]\(https?://[^\)]+\)', r'\1', line)
        cleaned.append(line)

    return '\n'.join(cleaned)


def clean_line(line: str) -> str:
    """Удалить мусор КонсультантПлюс из строки (для НК)."""
    line = re.sub(r'!\[.*?\]\(.*?\)(\{.*?\})?', '', line)
    line = re.sub(r'\[([^\]]*?)\]\(https?://[^\)]+\)', r'\1', line)
    return line


def is_junk_line(line: str) -> bool:
    """Вернуть True если строка — мусор, который нужно пропустить (для НК)."""
    s = line.strip()
    if not s:
        return False
    if re.match(r'^-{10,}$', s):
        return True
    if re.match(r'^\+\-+\+', s):
        return True
    if re.match(r'^\|.*\|$', s):
        return True
    if 'КонсультантПлюс' in s and ('примечан' in s.lower() or 'www.consultant' in s.lower()):
        return True
    if re.match(r'^Дата сохранения:', s):
        return True
    if s.startswith('{width=') or s.startswith('!'):
        return True
    return False


def split_large_chunk(chunk: dict, max_chars: int = MAX_CHUNK_CHARS) -> list[dict]:
    """Разбить слишком большой чанк на подсмысловые куски по абзацам."""
    text = chunk['text']
    if len(text) <= max_chars:
        return [chunk]

    # Разбиваем по двойным переводам строк (границы абзацев)
    paragraphs = re.split(r'\n\s*\n', text)
    subchunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_len = len(para)

        if current and current_len + para_len > max_chars:
            # Сохраняем текущий подчанк
            sub_text = '\n\n'.join(current)
            subchunks.append({
                "article": chunk["article"],
                "title": chunk["title"],
                "text": sub_text,
                "source": chunk["source"]
            })
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len + 2  # +2 for \n\n

    if current:
        sub_text = '\n\n'.join(current)
        subchunks.append({
            "article": chunk["article"],
            "title": chunk["title"],
            "text": sub_text,
            "source": chunk["source"]
        })

    # Если разбился на 1 часть — вернуть как есть
    if len(subchunks) <= 1:
        return [chunk]

    # Добавить нумерацию к заголовкам
    for i, sc in enumerate(subchunks):
        sc["title"] = f"{sc['title']} (часть {i+1}/{len(subchunks)})"

    return subchunks


def extract_articles(text: str, source: str, use_preprocess: bool = False) -> list[dict]:
    """Разбить текст закона на статьи."""
    # Предобработка для 425-ФЗ
    if use_preprocess:
        text = preprocess_425(text)

    lines = text.split('\n')
    cleaned_lines = []

    # Очистка строк (для НК)
    for line in lines:
        line = clean_line(line)
        if is_junk_line(line):
            continue
        cleaned_lines.append(line)

    # Ищем границы статей
    article_pattern = re.compile(r'^Статья\s+(\d+(?:\.\d+)?)\.?\s*(.*)')
    chunks = []
    current_start = None
    current_num = ""
    current_title = ""
    current_lines = []
    in_header = True

    for i, line in enumerate(cleaned_lines):
        m = article_pattern.match(line.strip())
        if m:
            # Сохраняем предыдущую статью
            if current_start is not None and current_lines:
                text_chunk = '\n'.join(current_lines).strip()
                if text_chunk:  # не сохраняем пустые
                    chunks.append({
                        "article": current_num,
                        "title": current_title,
                        "text": text_chunk,
                        "source": source
                    })

            current_num = m.group(1)
            title_text = m.group(2).strip()
            if title_text:
                current_title = title_text
            else:
                current_title = f"Статья {current_num}"
            current_lines = [line]
            current_start = i
            in_header = False
        elif not in_header:
            current_lines.append(line)

    # Последняя статья
    if current_start is not None and current_lines:
        text_chunk = '\n'.join(current_lines).strip()
        if text_chunk:
            chunks.append({
                "article": current_num,
                "title": current_title,
                "text": text_chunk,
                "source": source
            })

    return chunks


def word_count(text: str) -> int:
    return len(text.split())


def merge_small_chunks(chunks: list[dict], min_words: int = 100) -> list[dict]:
    """Склеить мелкие статьи (< min_words) со следующей."""
    result = []
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        wc = word_count(chunk['text'])
        if wc < min_words and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            merged = {
                "article": f"{chunk['article']}+{next_chunk['article']}",
                "title": f"{chunk['title']} | {next_chunk['title']}",
                "text": chunk['text'] + '\n' + next_chunk['text'],
                "source": chunk['source']
            }
            result.append(merged)
            i += 2
        else:
            result.append(chunk)
            i += 1
    return result


def main():
    all_chunks = []
    stats = {}

    for source, fname in FILES.items():
        path = BASE / fname
        print(f"📄 {source}: {path.name}", file=sys.stderr)
        text = path.read_text(encoding='utf-8')

        # Для 425-ФЗ включаем предобработку
        use_preprocess = (source == "fz425")
        chunks = extract_articles(text, source, use_preprocess=use_preprocess)
        raw_count = len(chunks)
        chunks = merge_small_chunks(chunks)

        # Разбиваем большие чанки (до обогащения keywords, чтобы все подчанки получили keywords)
        split_chunks = []
        for c in chunks:
            split_chunks.extend(split_large_chunk(c))
        chunks = split_chunks

        # Обогащаем ключевыми словами (только 425-ФЗ) — добавляем В КОНЕЦ текста
        if source == "fz425":
            for c in chunks:
                kw = KEYWORDS.get((c["source"], c["article"]))
                if kw:
                    c["text"] = kw + "\n\n" + c["text"]

        total_words = sum(word_count(c['text']) for c in chunks)
        stats[source] = {"raw": raw_count, "merged": len(chunks), "words": total_words}
        all_chunks.extend(chunks)

        print(f"   Статей: {raw_count} → {len(chunks)} (после склейки/сплита), {total_words:,} слов", file=sys.stderr)

    # Добавляем ID
    for i, c in enumerate(all_chunks):
        c["id"] = i

    out_path = Path(__file__).parent / "chunks.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Всего чанков: {len(all_chunks)}", file=sys.stderr)
    print(f"💾 Сохранено: {out_path}", file=sys.stderr)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
