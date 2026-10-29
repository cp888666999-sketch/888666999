"""Command line entry point for qslab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__
from .config import load_dotenv
from .quant.indicators import add_indicators


def _demo_frame(rows: int = 120, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0005, 0.02, rows)
    close = 100.0 * np.cumprod(1.0 + returns)
    high = close * (1.0 + rng.uniform(0.0, 0.01, rows))
    low = close * (1.0 - rng.uniform(0.0, 0.01, rows))
    open_ = np.concatenate([[close[0]], close[:-1]])
    volume = rng.integers(1_000, 10_000, rows)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def _cmd_demo(args: argparse.Namespace) -> int:
    df = add_indicators(_demo_frame(args.rows))
    cols = [
        "close",
        "DIF",
        "DEA",
        "MACD",
        "K",
        "D",
        "J",
        "ATR",
        "BOLL_MID",
        "BOLL_UPPER",
        "BOLL_LOWER",
    ]
    print(df[cols].tail(args.tail).to_string())
    return 0


def _cmd_indicators(args: argparse.Namespace) -> int:
    path = Path(args.csv)
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 2
    df = pd.read_csv(path)
    out = add_indicators(df)
    if args.out:
        out.to_csv(args.out, index=False)
        print(f"written: {args.out} ({len(out)} rows)")
    else:
        print(out.tail(args.tail).to_string())
    return 0


def _cmd_scrape(args: argparse.Namespace) -> int:
    from .spider.firecrawl import FirecrawlClient, FirecrawlError

    try:
        client = FirecrawlClient()
        payload = client.scrape(args.url)
    except FirecrawlError as exc:
        print(f"firecrawl error: {exc}", file=sys.stderr)
        return 2

    data = payload.get("data") or {}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2)[: args.chars])
        return 0

    markdown = data.get("markdown") or ""
    if args.out:
        Path(args.out).write_text(markdown, encoding="utf-8")
        title = (data.get("metadata") or {}).get("title") or ""
        print(f"written: {args.out} ({len(markdown)} chars) {title}".strip())
    else:
        print(markdown[: args.chars])
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    from .spider.firecrawl import FirecrawlClient, FirecrawlError

    try:
        client = FirecrawlClient()
        payload = client.search(args.query, limit=args.limit)
    except FirecrawlError as exc:
        print(f"firecrawl error: {exc}", file=sys.stderr)
        return 2

    items = payload.get("data") or []
    if isinstance(items, dict):
        items = items.get("web") or []
    for index, item in enumerate(items, start=1):
        title = item.get("title") or "(no title)"
        url = item.get("url") or ""
        description = (item.get("description") or "").replace("\n", " ")[:160]
        print(f"{index}. {title}\n   {url}\n   {description}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qslab",
        description="Quant indicators + polite crawling toolkit",
    )
    parser.add_argument("--version", action="version", version=f"qslab {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="generate synthetic OHLC and print indicators")
    demo.add_argument("--rows", type=int, default=120)
    demo.add_argument("--tail", type=int, default=5)
    demo.set_defaults(func=_cmd_demo)

    ind = sub.add_parser("indicators", help="add MACD/KDJ/ATR/BOLL to a CSV")
    ind.add_argument("--csv", required=True, help="input CSV with high/low/close columns")
    ind.add_argument("--out", default="", help="output CSV path")
    ind.add_argument("--tail", type=int, default=5)
    ind.set_defaults(func=_cmd_indicators)

    scrape = sub.add_parser("scrape", help="scrape one page with Firecrawl")
    scrape.add_argument("--url", required=True)
    scrape.add_argument("--out", default="", help="write markdown to this file")
    scrape.add_argument("--chars", type=int, default=2000, help="max chars to print")
    scrape.add_argument("--json", action="store_true", help="print raw JSON instead")
    scrape.set_defaults(func=_cmd_scrape)

    search = sub.add_parser("search", help="search the web with Firecrawl")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=5)
    search.set_defaults(func=_cmd_search)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
