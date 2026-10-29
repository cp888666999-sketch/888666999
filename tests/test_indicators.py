from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qslab.quant.indicators import add_indicators, atr, boll, kdj, macd, true_range
from qslab.spider.firecrawl import FirecrawlClient, FirecrawlError


def _frame(rows: int = 120, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.02, rows))
    high = close * (1.0 + rng.uniform(0.0, 0.01, rows))
    low = close * (1.0 - rng.uniform(0.0, 0.01, rows))
    return pd.DataFrame({"high": high, "low": low, "close": close})


def test_macd_identity() -> None:
    df = _frame()
    out = macd(df["close"])
    assert np.allclose(out["MACD"].to_numpy(), 2.0 * (out["DIF"] - out["DEA"]).to_numpy())


def test_kdj_constant_price_is_50() -> None:
    series = pd.Series([100.0] * 30)
    out = kdj(series, series, series)
    assert np.allclose(out["K"].to_numpy(), 50.0)
    assert np.allclose(out["D"].to_numpy(), 50.0)
    assert np.allclose(out["J"].to_numpy(), 50.0)


def test_kdj_range() -> None:
    df = _frame()
    out = kdj(df["high"], df["low"], df["close"])
    assert out["K"].between(0.0, 100.0).all()
    assert out["D"].between(0.0, 100.0).all()


def test_atr_wilder_recursion() -> None:
    df = _frame()
    out = atr(df["high"], df["low"], df["close"], n=14)
    assert out.iloc[:13].isna().all()
    assert out.iloc[13:].notna().all()
    assert (out.dropna() > 0).all()

    tr = true_range(df["high"], df["low"], df["close"]).to_numpy()
    values = out.to_numpy()
    assert np.isclose(values[14], (values[13] * 13.0 + tr[14]) / 14.0)


def test_boll_uses_population_std() -> None:
    df = _frame()
    out = boll(df["close"], n=20, k=2.0, ddof=0)
    mid = df["close"].rolling(20, min_periods=1).mean()
    std = df["close"].rolling(20, min_periods=1).std(ddof=0)
    assert np.allclose(out["BOLL_MID"].to_numpy(), mid.to_numpy())
    assert np.allclose(out["BOLL_UPPER"].to_numpy(), (mid + 2.0 * std).to_numpy())
    assert (out["BOLL_UPPER"] >= out["BOLL_MID"]).all()
    assert (out["BOLL_MID"] >= out["BOLL_LOWER"]).all()


def test_add_indicators_columns() -> None:
    df = _frame()
    out = add_indicators(df)
    for column in (
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
    ):
        assert column in out.columns
    assert len(out) == len(df)


def test_add_indicators_requires_ohlc() -> None:
    with pytest.raises(ValueError):
        add_indicators(pd.DataFrame({"close": [1.0, 2.0]}))


def test_firecrawl_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    with pytest.raises(FirecrawlError):
        FirecrawlClient(api_key="")
