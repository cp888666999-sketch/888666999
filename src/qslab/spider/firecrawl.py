"""Minimal Firecrawl client: scrape, search, map.

The API key is read from ``FIRECRAWL_API_KEY`` (environment or local ``.env``).
Never commit a real key.
"""

from __future__ import annotations

import os
from typing import Any

import requests

API_BASE = "https://api.firecrawl.dev/v1"


class FirecrawlError(RuntimeError):
    """Raised when Firecrawl is not configured or returns an error."""


class FirecrawlClient:
    def __init__(
        self,
        api_key: str | None = None,
        proxy: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY", "")
        if not self.api_key:
            raise FirecrawlError(
                "FIRECRAWL_API_KEY is not set (put it in .env or the environment)"
            )
        self.timeout = timeout
        proxy = proxy or os.environ.get("QSLAB_PROXY") or None
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.session.request(
            method,
            f"{API_BASE}{path}",
            timeout=self.timeout,
            proxies=self.proxies,
            **kwargs,
        )
        if response.status_code >= 400:
            raise FirecrawlError(f"HTTP {response.status_code}: {response.text[:200]}")
        payload = response.json()
        if isinstance(payload, dict) and payload.get("success") is False:
            raise FirecrawlError(str(payload.get("error") or payload)[:200])
        return payload

    def scrape(self, url: str, formats: list[str] | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            "/scrape",
            json={"url": url, "formats": formats or ["markdown"]},
        )

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        return self._request("POST", "/search", json={"query": query, "limit": limit})

    def map(self, url: str, limit: int = 50) -> dict[str, Any]:
        return self._request("POST", "/map", json={"url": url, "limit": limit})
