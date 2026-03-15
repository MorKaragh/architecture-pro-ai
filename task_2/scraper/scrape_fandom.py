#!/usr/bin/env python3
"""
Скрипт для скачивания статей с сайта fandom.com в текстовом виде.

Использование:
  python scrape_fandom.py <URL> [--output FILE]
  python scrape_fandom.py --list urls.txt [--output-dir DIR]
  python scrape_fandom.py --list urls.txt   # сохраняет в папку output/

Примеры URL:
  https://minecraft.fandom.com/wiki/Diamond
  https://starwars.fandom.com/wiki/Luke_Skywalker
"""

import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    print(
        "Не установлены зависимости. В папке scraper выполните:\n"
        "  source venv/bin/activate   # или venv\\Scripts\\activate на Windows\n"
        "  pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import cloudscraper
    USE_CLOUDSCRAPER = True
except ModuleNotFoundError:
    USE_CLOUDSCRAPER = False

# Задержка между запросами (секунды), чтобы не перегружать сервер
REQUEST_DELAY = 1.5

# Заголовки как у браузера — иначе Fandom может вернуть 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


def is_fandom_wiki_url(url: str) -> bool:
    """Проверяет, что URL ведёт на вики fandom.com."""
    return ".fandom.com" in url and "/wiki/" in url


def slug_from_url(url: str) -> str:
    """Извлекает slug статьи из URL для имени файла (безопасное имя)."""
    match = re.search(r"/wiki/([^/?&#]+)", url)
    if not match:
        return "article"
    raw = unquote(match.group(1))
    # Оставляем буквы, цифры, дефис и подчёркивание; остальное — подчёркивание
    safe = re.sub(r"[^\w\-.]", "_", raw)
    return safe.strip("_") or "article"


def extract_article_text(html: str, url: str) -> tuple[str, str]:
    """
    Извлекает заголовок и основной текст статьи из HTML.
    Возвращает (заголовок, текст).
    """
    soup = BeautifulSoup(html, "lxml")
    title = ""
    main = soup.select_one("#content .mw-parser-output") or soup.select_one(
        ".mw-parser-output"
    )
    if not main:
        main = soup.select_one("#mw-content-text") or soup.find("main")
    if not main:
        return "", ""

    # Заголовок страницы
    title_el = soup.select_one("#firstHeading") or soup.select_one("h1.page-header__title")
    if title_el:
        title = title_el.get_text(strip=True)

    lines = []
    for node in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "caption"]):
        tag = node.name
        text = node.get_text(separator=" ", strip=True)
        if not text:
            continue
        if tag == "h1":
            lines.append(f"\n# {text}\n")
        elif tag == "h2":
            lines.append(f"\n## {text}\n")
        elif tag == "h3":
            lines.append(f"\n### {text}\n")
        elif tag == "h4":
            lines.append(f"\n#### {text}\n")
        elif tag in ("td", "th"):
            lines.append(text)
        elif tag == "caption":
            lines.append(f"\n**{text}**\n")
        elif tag == "li":
            lines.append(f"  - {text}")
        else:
            lines.append(text)

    # Если структурированный обход дал мало — берём весь текст блока
    raw_text = main.get_text(separator="\n", strip=True)
    if raw_text and len(" ".join(lines).strip()) < 0.3 * len(raw_text):
        lines = [raw_text]

    body = "\n".join(lines)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    header = f"# {title}\n\nИсточник: {url}\n\n"
    return title, header + body


def fetch_article(url: str, session: requests.Session) -> tuple[str, str] | None:
    """Загружает страницу и возвращает (заголовок, текст) или None при ошибке."""
    if not is_fandom_wiki_url(url):
        print(f"Пропуск (не вики fandom): {url}", file=sys.stderr)
        return None
    try:
        # Referer с того же домена — иногда без этого 403
        parsed = url.split("/wiki/")[0]
        headers = {**HEADERS, "Referer": f"{parsed}/"}
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return extract_article_text(resp.text, url)
    except requests.RequestException as e:
        print(f"Ошибка запроса {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Ошибка обработки {url}: {e}", file=sys.stderr)
        return None


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Сохранено: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Скачивание статей с fandom.com в текстовом виде"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL одной статьи (например https://minecraft.fandom.com/wiki/Diamond)",
    )
    parser.add_argument(
        "--list",
        "-l",
        metavar="FILE",
        help="Файл со списком URL (по одному на строку)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Файл для сохранения (для одного URL)",
    )
    parser.add_argument(
        "--output-dir",
        "-d",
        default="output",
        metavar="DIR",
        help="Папка для сохранения при --list (по умолчанию: output)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"Задержка между запросами в секундах (по умолчанию {REQUEST_DELAY})",
    )
    args = parser.parse_args()

    urls: list[str] = []
    if args.list:
        list_path = Path(args.list)
        if not list_path.exists():
            print(f"Файл не найден: {list_path}", file=sys.stderr)
            sys.exit(1)
        urls = [
            line.strip()
            for line in list_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not urls:
            print("В файле нет URL.", file=sys.stderr)
            sys.exit(1)
    elif args.url:
        urls = [args.url]
    else:
        parser.print_help()
        sys.exit(1)

    out_dir = Path(args.output_dir)
    # cloudscraper обходит защиту Cloudflare (403), если установлен
    if USE_CLOUDSCRAPER:
        session = cloudscraper.create_scraper()
    else:
        session = requests.Session()
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(args.delay)
        result = fetch_article(url, session)
        if result is None:
            continue
        title, text = result
        if not text.strip():
            print(f"Пустой контент: {url}", file=sys.stderr)
            continue
        if len(urls) == 1 and args.output:
            path = Path(args.output)
        else:
            slug = slug_from_url(url)
            path = out_dir / f"{slug}.txt"
        save_text(path, text)

    print("Готово.")


if __name__ == "__main__":
    main()
