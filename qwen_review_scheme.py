#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qwen2.5-VL: проверка СХЕМЫ по чек-листу (по образцу qwen_review_report.py).

Использование: python3 qwen_review_scheme.py IMAGE.png [7b]
Запускать интерпретатором с llama_cpp: /home/user1/llama-venv/bin/python
"""
import os
import sys
import time

sys.path.insert(0, "/home/user1/llama-venv/lib/python3.12/site-packages")
import cv2
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Qwen25VLChatHandler

MODEL_3B = "/home/user1/models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
MODEL_7B = "/home/user1/models/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf"
MMPROJ = "/home/user1/models/mmproj-F16.gguf"
MMPROJ_7B = "/home/user1/models/7b/mmproj-F16.gguf"

SRC = sys.argv[1]
USE_7B = len(sys.argv) > 2 and sys.argv[2] == "7b"
MODEL = MODEL_7B if USE_7B else MODEL_3B
MMPROJ_PATH = MMPROJ_7B if USE_7B else MMPROJ
N_CTX = 2048 if USE_7B else 4096
SCALE_PX = 1000 if USE_7B else 1200

img = cv2.imread(SRC)
h, w = img.shape[:2]
scale = SCALE_PX / max(w, h)
img = cv2.resize(img, (int(w * scale), int(h * scale)))
resized = f"/tmp/qwen_scheme_{os.getpid()}.jpg"
cv2.imwrite(resized, img)
print(f"Resized: {w}x{h} -> {img.shape[1]}x{img.shape[0]}", flush=True)

handler = Qwen25VLChatHandler(clip_model_path=MMPROJ_PATH, verbose=False)
llm = Llama(model_path=MODEL, chat_handler=handler, n_ctx=N_CTX, n_threads=4, verbose=False)

PROMPT = """Перед тобой блок-схема: путь исполнительного документа (ИД) — от источников
до завершения, с выделенной зоной ответственности банка. Проверь строго и по пунктам:

1. ЛЕГЕНДА СВЕРХУ: есть ли компактная полоса-легенда с цветными квадратиками и подписями?
2. ПОЛНОТА: есть ли блоки «источники ИД», этапы пути (выдача, предъявление, возбуждение,
   добровольное, принудительное, окончание), финал (исполнено / возврат ИД / прекращение / повторное)?
3. ЗОНА БАНКА: выделены ли цветом блоки ответственности банка (НК ст. 46/60, ГК ст. 855,
   обязанности, розыск счетов, ответственность ст. 135)?
4. ДЕФЕКТЫ: есть ли наложение текста, обрезка, наезжающие блоки, нечитаемый шрифт?
   Если да — перечисли конкретные надписи.
5. ВЕРДИКТ: одной строкой — «ГОДИТСЯ» или «ТРЕБУЕТ ПРАВКИ» + что именно.

Отвечай на русском, кратко, без домыслов. Если что-то неразборчиво — помечай [неразборчиво]."""

messages = [{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": f"file://{resized}"}},
    {"type": "text", "text": PROMPT},
]}]

print("Analyzing (Qwen2.5-VL)...", flush=True)
t0 = time.time()
resp = llm.create_chat_completion(messages=messages, max_tokens=1024)
print(f"\n[Готово за {time.time()-t0:.0f} сек, модель {'7B' if USE_7B else '3B'}]\n", flush=True)
print(resp["choices"][0]["message"]["content"])
os.unlink(resized)
