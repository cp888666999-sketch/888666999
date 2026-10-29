"""Technical indicators with Chinese-market conventions.

Conventions:
- MACD histogram = 2 * (DIF - DEA)
- KDJ starts at K = D = 50
- ATR uses Wilder's RMA
- BOLL uses population std (ddof=0), including the unfinished bar

All functions are pure: they do not read files, call the network, or mutate input.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_series(values: pd.Series | np.ndarray | list[float], name: str) -> pd.Series:
    if isinstance(values, pd.Series):
        return values.astype(float)
    return pd.Series(values, dtype=float, name=name)


def macd(
    close: pd.Series | np.ndarray | list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD with the Chinese convention ``MACD = 2 * (DIF - DEA)``."""
    c = _as_series(close, "close")
    dif = c.ewm(span=fast, adjust=False).mean() - c.ewm(span=slow, adjust=False).mean()
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = 2.0 * (dif - dea)
    return pd.DataFrame({"DIF": dif, "DEA": dea, "MACD": hist})


def kdj(
    high: pd.Series | np.ndarray | list[float],
    low: pd.Series | np.ndarray | list[float],
    close: pd.Series | np.ndarray | list[float],
    n: int = 9,
    k_period: int = 3,
    d_period: int = 3,
) -> pd.DataFrame:
    """KDJ with initial ``K = D = 50`` and the classic smoothing factors."""
    if n <= 0 or k_period <= 0 or d_period <= 0:
        raise ValueError("n, k_period and d_period must be positive")

    h = _as_series(high, "high")
    low_s = _as_series(low, "low")
    c = _as_series(close, "close")

    lowest = low_s.rolling(n, min_periods=1).min()
    highest = h.rolling(n, min_periods=1).max()
    span = (highest - lowest).replace(0, np.nan)
    rsv = ((c - lowest) / span * 100.0).fillna(50.0)

    k = np.empty(len(c), dtype=float)
    d = np.empty(len(c), dtype=float)
    prev_k = 50.0
    prev_d = 50.0
    for i, value in enumerate(rsv.to_numpy(dtype=float)):
        prev_k = (k_period - 1) / k_period * prev_k + value / k_period
        prev_d = (d_period - 1) / d_period * prev_d + prev_k / d_period
        k[i] = prev_k
        d[i] = prev_d

    j = 3.0 * k - 2.0 * d
    return pd.DataFrame({"K": k, "D": d, "J": j}, index=c.index)


def true_range(
    high: pd.Series | np.ndarray | list[float],
    low: pd.Series | np.ndarray | list[float],
    close: pd.Series | np.ndarray | list[float],
) -> pd.Series:
    """True range; the first bar uses ``high - low``."""
    h = _as_series(high, "high")
    low_s = _as_series(low, "low")
    c = _as_series(close, "close")

    prev_close = c.shift(1)
    tr = pd.concat(
        [(h - low_s).abs(), (h - prev_close).abs(), (low_s - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    if len(tr):
        tr.iloc[0] = h.iloc[0] - low_s.iloc[0]
    return tr.rename("TR")


def atr(
    high: pd.Series | np.ndarray | list[float],
    low: pd.Series | np.ndarray | list[float],
    close: pd.Series | np.ndarray | list[float],
    n: int = 14,
) -> pd.Series:
    """ATR using Wilder's RMA, seeded with the mean of the first ``n`` TR values."""
    if n <= 0:
        raise ValueError("n must be positive")

    tr = true_range(high, low, close)
    values = tr.to_numpy(dtype=float)
    out = np.full(len(values), np.nan, dtype=float)
    if len(values) < n:
        return pd.Series(out, index=tr.index, name="ATR")

    out[n - 1] = float(np.nanmean(values[:n]))
    for i in range(n, len(values)):
        out[i] = (out[i - 1] * (n - 1) + values[i]) / n
    return pd.Series(out, index=tr.index, name="ATR")


def boll(
    close: pd.Series | np.ndarray | list[float],
    n: int = 20,
    k: float = 2.0,
    ddof: int = 0,
) -> pd.DataFrame:
    """Bollinger bands with population std by default (``ddof=0``)."""
    if n <= 0:
        raise ValueError("n must be positive")

    c = _as_series(close, "close")
    mid = c.rolling(n, min_periods=1).mean()
    std = c.rolling(n, min_periods=1).std(ddof=ddof)
    return pd.DataFrame(
        {
            "BOLL_MID": mid,
            "BOLL_UPPER": mid + k * std,
            "BOLL_LOWER": mid - k * std,
        }
    )


def add_indicators(
    df: pd.DataFrame,
    *,
    macd_params: tuple[int, int, int] = (12, 26, 9),
    kdj_params: tuple[int, int, int] = (9, 3, 3),
    atr_n: int = 14,
    boll_n: int = 20,
    boll_k: float = 2.0,
) -> pd.DataFrame:
    """Return a copy of ``df`` with MACD, KDJ, ATR and BOLL columns appended."""
    missing = {"high", "low", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")

    out = df.copy()
    macd_df = macd(out["close"], *macd_params)
    kdj_df = kdj(out["high"], out["low"], out["close"], *kdj_params)
    boll_df = boll(out["close"], boll_n, boll_k)
    out["ATR"] = atr(out["high"], out["low"], out["close"], atr_n)
    return pd.concat([out, macd_df, kdj_df, boll_df], axis=1)
