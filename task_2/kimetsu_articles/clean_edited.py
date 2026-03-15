#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Удаляет из edited_*.txt иероглифы, романизированный японский и английские надписи."""

import re
import os

DIR = os.path.dirname(os.path.abspath(__file__))

# Скобки с иероглифами/каной/романи: ( 鬼 , Oni ? ) или ( 水 の 呼 吸 , Mizu no kokyū ? )
def remove_japanese_parens(text):
    # Удаляем блоки вида ( ... , ... ? ) где внутри есть CJK или кана
    def repl(m):
        s = m.group(1)
        if re.search(r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', s) or re.search(r'[A-Za-z]{2,}\s+no\s+', s):
            return ' '
        return m.group(0)
    return re.sub(r'\s*\(\s*([^)]+)\s*\)', repl, text)

# Удалить строки-заголовки только на английском (секции типа "### On Japanese", "### Romaji")
def remove_english_headers(text):
    lines = text.split('\n')
    out = []
    for line in lines:
        stripped = line.strip()
        # Пропускаем строки, которые целиком на латинице (заголовки)
        if re.match(r'^###\s*[A-Za-z\s]+$', stripped):
            continue
        if stripped in ('On Japanese', 'Romaji', 'English', 'Anime', 'Manga') and not re.search(r'[а-яА-ЯёЁ]', line):
            continue
        out.append(line)
    return '\n'.join(out)

# Удалить упоминания актёров на английском, например "Джессика Ди Чикко (ребёнок)"
def remove_english_va(text):
    return re.sub(r'\n[А-Яа-яёЁ\s]+\([^)]*[A-Za-z][^)]*\)\s*\n', '\n', text)

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    orig = text
    text = remove_japanese_parens(text)
    text = remove_english_headers(text)
    # Удалить эмодзи (например информационный символ)
    text = text.replace('\U0001f50a', '')
    text = re.sub(r'  +', ' ', text)
    if text != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    return False

def main():
    count = 0
    for name in os.listdir(DIR):
        if name.startswith('edited_') and name.endswith('.txt'):
            if clean_file(os.path.join(DIR, name)):
                count += 1
                print('Cleaned:', name)
    print('Done. Cleaned', count, 'files.')

if __name__ == '__main__':
    main()
