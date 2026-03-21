"""
Общие утилиты для логирования запросов к RAG (задание 7): время, эвристика «успешного» ответа.
"""

from __future__ import annotations

import datetime as dt


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def is_successful_answer(text: str, min_len: int) -> bool:
    if not text or len(text.strip()) < min_len:
        return False
    low = text.lower()
    deny_markers = (
        "я не знаю",
        "не найдено",
        "нет данных",
        "не могу ответить",
    )
    return not any(m in low for m in deny_markers)
