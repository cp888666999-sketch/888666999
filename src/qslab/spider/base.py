"""A small, polite HTTP client for research crawlers.

It does not bypass logins, CAPTCHAs, paywalls, or rate limits. Keep the default
interval and respect each site's robots.txt / terms of service.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

DEFAULT_UA = "qslab/0.1 (+https://github.com/cp888666999-sketch/888666999)"


@dataclass
class HttpClient:
    timeout: float = 15.0
    min_interval: float = 1.0
    retries: int = 2
    proxy: str | None = None
    user_agent: str = DEFAULT_UA
    session: requests.Session = field(default_factory=requests.Session)
    _last_request: float = 0.0

    def __post_init__(self) -> None:
        self.proxy = self.proxy or os.environ.get("QSLAB_PROXY") or None
        self.timeout = float(os.environ.get("QSLAB_TIMEOUT", self.timeout))
        self.session.headers.update({"User-Agent": self.user_agent})

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            self._wait()
            try:
                response = self.session.get(url, timeout=self.timeout, proxies=proxies, **kwargs)
                if response.status_code in (429, 500, 502, 503, 504):
                    last = requests.HTTPError(f"HTTP {response.status_code}", response=response)
                    time.sleep(1.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last = exc
                if attempt < self.retries:
                    time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"GET {url} failed: {last}") from last

    def get_text(self, url: str, **kwargs: Any) -> str:
        return self.get(url, **kwargs).text

    def get_json(self, url: str, **kwargs: Any) -> Any:
        return json.loads(self.get_text(url, **kwargs))
