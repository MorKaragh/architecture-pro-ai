#!/usr/bin/env python3
"""
Проверка доступности Yandex Foundation Models API.

Что проверяет:
- textEmbedding endpoint
- completion endpoint

И для каждого endpoint пробует:
- Bearer YANDEX_IAM_TOKEN
- Api-Key YANDEX_CLOUD_API_KEY

Это помогает быстро понять, каким способом авторизации можно пользоваться
прямо сейчас и не истёк ли IAM-токен.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests


EMBED_URL = "https://ai.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
LLM_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


@dataclass(frozen=True)
class CheckResult:
    auth_mode: str
    endpoint: str
    ok: bool
    status_code: int | None
    details: str


def _build_auth_headers(folder_id: str, auth_value: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": auth_value,
        "x-folder-id": folder_id,
    }


def _check_embedding(headers: dict[str, str], folder_id: str, timeout: float) -> CheckResult:
    payload = {
        "modelUri": f"emb://{folder_id}/text-search-query/latest",
        "text": "проверка подключения",
    }
    try:
        resp = requests.post(EMBED_URL, headers=headers, json=payload, timeout=timeout)
        if resp.ok:
            data = resp.json()
            return CheckResult(
                auth_mode=headers["Authorization"].split(" ", 1)[0],
                endpoint="embedding",
                ok=True,
                status_code=resp.status_code,
                details=f"embedding_len={len(data.get('embedding', []))}",
            )
        return CheckResult(
            auth_mode=headers["Authorization"].split(" ", 1)[0],
            endpoint="embedding",
            ok=False,
            status_code=resp.status_code,
            details=resp.text[:300],
        )
    except Exception as e:  # noqa: BLE001
        return CheckResult(
            auth_mode=headers["Authorization"].split(" ", 1)[0],
            endpoint="embedding",
            ok=False,
            status_code=None,
            details=repr(e),
        )


def _check_llm(headers: dict[str, str], folder_id: str, timeout: float) -> CheckResult:
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite/latest",
        "completionOptions": {"stream": False, "temperature": 0.1, "maxTokens": "64"},
        "messages": [{"role": "user", "text": "Ответь одним словом: ок"}],
    }
    try:
        resp = requests.post(LLM_URL, headers=headers, json=payload, timeout=timeout)
        if resp.ok:
            data = resp.json()
            text = (
                data.get("result", {})
                .get("alternatives", [{}])[0]
                .get("message", {})
                .get("text", "")
                .strip()
            )
            return CheckResult(
                auth_mode=headers["Authorization"].split(" ", 1)[0],
                endpoint="llm",
                ok=True,
                status_code=resp.status_code,
                details=f"answer={text[:120]}",
            )
        return CheckResult(
            auth_mode=headers["Authorization"].split(" ", 1)[0],
            endpoint="llm",
            ok=False,
            status_code=resp.status_code,
            details=resp.text[:300],
        )
    except Exception as e:  # noqa: BLE001
        return CheckResult(
            auth_mode=headers["Authorization"].split(" ", 1)[0],
            endpoint="llm",
            ok=False,
            status_code=None,
            details=repr(e),
        )


def _print_env_status(folder: str | None, iam: str | None, api_key: str | None) -> None:
    print("Environment:")
    print(f"  YANDEX_CLOUD_FOLDER: {'set' if folder else 'missing'}")
    print(f"  YANDEX_IAM_TOKEN: {'set' if iam else 'missing'}")
    print(f"  YANDEX_CLOUD_API_KEY: {'set' if api_key else 'missing'}")
    print()


def _print_result(result: CheckResult) -> None:
    status = "OK" if result.ok else "FAIL"
    print(
        json.dumps(
            {
                "auth_mode": result.auth_mode,
                "endpoint": result.endpoint,
                "status": status,
                "http_status": result.status_code,
                "details": result.details,
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    folder_id = os.getenv("YANDEX_CLOUD_FOLDER")
    iam_token = os.getenv("YANDEX_IAM_TOKEN")
    api_key = os.getenv("YANDEX_CLOUD_API_KEY")
    timeout = float(os.getenv("YANDEX_CHECK_TIMEOUT_SEC", "20"))

    _print_env_status(folder_id, iam_token, api_key)

    if not folder_id:
        print("ERROR: YANDEX_CLOUD_FOLDER is required.")
        return 2

    checks: list[CheckResult] = []

    if iam_token:
        h = _build_auth_headers(folder_id, f"Bearer {iam_token}")
        checks.append(_check_embedding(h, folder_id, timeout))
        checks.append(_check_llm(h, folder_id, timeout))

    if api_key:
        h = _build_auth_headers(folder_id, f"Api-Key {api_key}")
        checks.append(_check_embedding(h, folder_id, timeout))
        checks.append(_check_llm(h, folder_id, timeout))

    if not checks:
        print("ERROR: no auth credentials found (need YANDEX_IAM_TOKEN and/or YANDEX_CLOUD_API_KEY).")
        return 2

    print("Checks:")
    for item in checks:
        _print_result(item)

    # Скрипт считается успешным, если есть хотя бы одна валидная пара проверок:
    # embedding OK + llm OK для одного типа авторизации.
    auth_groups: dict[str, dict[str, bool]] = {}
    for item in checks:
        auth_groups.setdefault(item.auth_mode, {})
        auth_groups[item.auth_mode][item.endpoint] = item.ok

    healthy_modes = [
        mode
        for mode, res in auth_groups.items()
        if res.get("embedding") is True and res.get("llm") is True
    ]
    if healthy_modes:
        print()
        print(f"Healthy auth modes: {', '.join(healthy_modes)}")
        return 0

    print()
    print("No fully healthy auth mode found.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
