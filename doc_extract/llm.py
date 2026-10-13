"""One thin seam to an OpenAI-compatible chat endpoint (local Ollama by default).

Every LLM call in this project goes through `chat()`. Configure it with env only;
never hardcode a key. If the endpoint is unreachable we raise `LLMError` with a
clear message rather than crashing the whole run or hanging a batch.
"""
from __future__ import annotations

import json
import os
import re

import requests

BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
MODEL = os.getenv("LLM_MODEL", "qwen3:30b-a3b-instruct-2507-q4_K_M")
API_KEY = os.getenv("LLM_API_KEY", "ollama")


class LLMError(RuntimeError):
    """Raised when the LLM endpoint can't be reached or returns garbage."""


def chat(messages, *, temperature=0.0, timeout=120, json_mode=True) -> str:
    """POST a chat completion and return the assistant message text."""
    url = BASE_URL.rstrip("/") + "/chat/completions"
    payload = {"model": MODEL, "messages": messages, "temperature": temperature}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise LLMError(
            f"LLM call to {url} (model {MODEL}) failed: {e}. "
            "Is Ollama running? See README for LLM_BASE_URL/LLM_MODEL."
        ) from e


def parse_json_block(text: str) -> dict:
    """Pull a JSON object out of a model reply.

    Handles a clean object, a ```json fenced block, or an object embedded in
    prose. Raises LLMError if nothing parseable is found.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # strip code fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    # last resort: first {...last } span
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise LLMError("Model reply did not contain valid JSON.")
