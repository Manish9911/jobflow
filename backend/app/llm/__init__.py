"""Swappable LLM provider interface.

Every caller goes through ``get_llm()`` and ``llm.complete(system, user)``.
Phase 3 ships the OpenAI provider (default ``gpt-4o-mini``, per user config);
``none`` (or a missing API key) returns a provider whose ``is_available()`` is
False so the rest of the app can fall back to deterministic behaviour.

OpenRouter free tier (2026-11-18): the configured model pool
(``llm_models``, comma-separated) is used round-robin so two ``:free`` models
share the daily token budget; a model that 429s/quota-exhausts is benched for
15 min and traffic shifts to the other. When every model in the pool is
exhausted, ``LLMUnavailable`` tells the operator to switch to the local
qwen-3.8-27b endpoint.
"""
from __future__ import annotations

import time

import httpx

from .base import LLM, LLMUnavailable

# OpenRouter/edge conditions that mean "try the next model in the pool".
_RETRYABLE_STATUS = {401, 402, 408, 429, 500, 502, 503, 504}
_BENCH_SECONDS = 15 * 60


class OpenAIProvider(LLM):
    """OpenAI-compatible chat completions over httpx (no SDK dependency).

    Works with api.openai.com or any OpenAI-compatible server via
    ``openai_base_url``.
    """

    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1",
                 extra_headers: dict | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.extra_headers = extra_headers or {}

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, user: str, temperature: float = 0.2,
                 timeout: float = 90.0) -> str:
        if not self.is_available():
            raise LLMUnavailable("OPENAI_API_KEY is not set — put it in .env to enable LLM tailoring")
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", **self.extra_headers},
            json={
                "model": self.model,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter (openrouter.ai) — OpenAI-compatible gateway to many models.

    Sends the optional attribution headers OpenRouter uses for its app
    ranking (HTTP-Referer / X-Title); harmless if ignored.

    With ``models`` (a pool of >=1 model ids), requests go round-robin across
    the pool and any model that returns a retryable/quota error is benched for
    15 minutes so the other model(s) carry the traffic.
    """

    name = "openrouter"

    def __init__(self, api_key: str, model: str,
                 base_url: str = "https://openrouter.ai/api/v1",
                 models: list[str] | None = None):
        super().__init__(api_key, model, base_url,
                         extra_headers={"HTTP-Referer": "http://127.0.0.1:8000",
                                        "X-Title": "Jobflow"})
        self.models = [m for m in (models or [model]) if m]
        self._idx = 0
        self._bench_until: dict[str, float] = {}

    def _next_model(self) -> str:
        now = time.time()
        for i in range(len(self.models)):
            m = self.models[(self._idx + i) % len(self.models)]
            if self._bench_until.get(m, 0.0) <= now:
                self._idx = (self._idx + i + 1) % len(self.models)
                return m
        # all benched: use the one that frees up soonest
        return min(self.models, key=lambda m: self._bench_until.get(m, 0.0))

    def complete(self, system: str, user: str, temperature: float = 0.2,
                 timeout: float = 90.0) -> str:
        if not self.is_available():
            raise LLMUnavailable("OPENROUTER_API_KEY is not set — put it in .env to enable LLM tailoring")
        tried: list[str] = []
        while len(tried) < len(self.models):
            model = self._next_model()
            if model in tried:
                break
            tried.append(model)
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", **self.extra_headers},
                json={
                    "model": model,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=timeout,
            )
            status = getattr(resp, "status_code", 200)
            if status < 400:
                data = resp.json()
                content = (data["choices"][0]["message"].get("content") or "").strip()
                if content:
                    return content
                # reasoning-only response (some free models) — treat as retryable
                resp = httpx.Response(502, request=resp.request,
                                      content=b"null content (reasoning only)")
                status = 502
            if status in _RETRYABLE_STATUS:
                self._bench_until[model] = time.time() + _BENCH_SECONDS
                continue
            resp.raise_for_status()
        raise LLMUnavailable(
            "all OpenRouter free models exhausted or unreachable "
            f"({', '.join(tried)}) — switch to the local qwen-3.8-27b endpoint")

    def bench_status(self) -> dict[str, str]:
        """Human-readable per-model state (for ops/UI)."""
        now = time.time()
        return {m: ("bench until " + time.strftime("%H:%M", time.localtime(self._bench_until[m]))
                    if self._bench_until.get(m, 0.0) > now else "ok")
                for m in self.models}


def get_llm(settings) -> LLM:
    """Build the configured provider. Never raises for a missing key —
    callers check ``is_available()`` and fall back."""
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.llm_model,
                              settings.openai_base_url)
    if settings.llm_provider == "openrouter":
        model = settings.llm_model
        # OpenRouter model ids are namespaced (openai/gpt-4o-mini); keep a
        # plain model name working by defaulting to the openai namespace.
        if "/" not in model:
            model = f"openai/{model}"
        pool = [m.strip() for m in (settings.llm_models or "").split(",") if m.strip()]
        if not pool or pool == [model]:
            pool = [model]
        return OpenRouterProvider(settings.openrouter_api_key, model,
                                  settings.openrouter_base_url, models=pool)
    # anthropic/ollama: same interface, not implemented yet (Phase 3 scope
    # is openai + deterministic fallback per the confirmed preference).
    return OpenAIProvider("", settings.llm_model)
