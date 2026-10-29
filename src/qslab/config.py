"""Environment-backed settings. Secrets stay in the environment, never in git."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Load simple ``KEY=VALUE`` lines without adding a dependency."""
    dotenv = Path(path)
    if not dotenv.is_file():
        return
    for raw in dotenv.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    tushare_token: str = ""
    proxy: str = ""
    timeout: float = 15.0
    data_dir: str = "data"
    firecrawl_api_key: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            tushare_token=os.environ.get("TUSHARE_TOKEN", ""),
            proxy=os.environ.get("QSLAB_PROXY", ""),
            timeout=float(os.environ.get("QSLAB_TIMEOUT", "15")),
            data_dir=os.environ.get("QSLAB_DATA_DIR", "data"),
            firecrawl_api_key=os.environ.get("FIRECRAWL_API_KEY", ""),
        )
