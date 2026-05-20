from __future__ import annotations

import logging

from typing import Dict, List, Literal, Optional, Tuple

import numpy as np

import pandas as pd

from scipy.cluster.hierarchy import linkage

from scipy.optimize import minimize

from scipy.spatial.distance import squareform

from app.models.recommendation import Allocation
from app.models.company import ScoredCompany

logger = logging.getLogger(__name__)

Strategy = Literal["max_sharpe", "min_volatility", "hrp"]

RISK_FREE = 0.105

TRADING_DAYS = 252

MAX_WEIGHT = 0.40

def _build_price_frame(history: Dict[str, Dict[str, float]], tickers: List[str]) -> pd.DataFrame:

    series = {tk: pd.Series(history[tk]) for tk in tickers if tk in history and history[tk]}

    if not series:

        return pd.DataFrame()

    df = pd.DataFrame(series)

    df.index = pd.to_datetime(df.index)

    df = df.sort_index().ffill().dropna(how="all")

    threshold = int(len(df) * 0.6)

    df = df.dropna(axis=1, thresh=threshold).ffill().bfill()

    return df

def _annualize(returns: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:

    mu = returns.mean().values * TRADING_DAYS

    cov = returns.cov().values * TRADING_DAYS

    return mu, cov

def _max_sharpe(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:

    n = len(mu)

    x0 = np.full(n, 1 / n)

    bounds = [(0.0, MAX_WEIGHT)] * n

    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)

    def neg_sharpe(w: np.ndarray) -> float:

        ret = float(w @ mu)

        vol = float(np.sqrt(w @ cov @ w))

        return -(ret - RISK_FREE) / vol if vol > 0 else 1e9

    res = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=cons)

    return res.x if res.success else x0

def _min_vol(cov: np.ndarray) -> np.ndarray:

    n = cov.shape[0]

    x0 = np.full(n, 1 / n)

    bounds = [(0.0, MAX_WEIGHT)] * n

    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)

    res = minimize(lambda w: float(w @ cov @ w), x0, method="SLSQP", bounds=bounds, constraints=cons)

    return res.x if res.success else x0

def _correl_dist(corr: pd.DataFrame) -> pd.DataFrame:

    return ((1 - corr) / 2.0) ** 0.5

def _get_quasi_diag(link: np.ndarray) -> List[int]:

    link = link.astype(int)

    sort_ix = pd.Series([link[-1, 0], link[-1, 1]])

    num_items = link[-1, 3]

    while sort_ix.max() >= num_items:

        sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)

        df0 = sort_ix[sort_ix >= num_items]

        i = df0.index

        j = df0.values - num_items

        sort_ix[i] = link[j, 0]

        df0 = pd.Series(link[j, 1], index=i + 1)

        sort_ix = pd.concat([sort_ix, df0]).sort_index()

        sort_ix.index = range(sort_ix.shape[0])

    return sort_ix.tolist()

def _ivp(cov: pd.DataFrame) -> np.ndarray:

    ivp = 1.0 / np.diag(cov.values)

    return ivp / ivp.sum()

def _cluster_var(cov: pd.DataFrame, items: List[int]) -> float:

    cov_ = cov.iloc[items, items]

    w = _ivp(cov_).reshape(-1, 1)

    return float((w.T @ cov_.values @ w)[0, 0])

def _hrp_weights(cov: pd.DataFrame, sort_ix: List[int]) -> pd.Series:

    w = pd.Series(1.0, index=sort_ix)

    clusters = [sort_ix]

    while clusters:

        clusters = [

            c[i:j]

            for c in clusters

            for i, j in ((0, len(c) // 2), (len(c) // 2, len(c)))

            if len(c) > 1

        ]

        for i in range(0, len(clusters), 2):

            c0, c1 = clusters[i], clusters[i + 1]

            v0, v1 = _cluster_var(cov, c0), _cluster_var(cov, c1)

            alpha = 1 - v0 / (v0 + v1)

            w[c0] *= alpha

            w[c1] *= 1 - alpha

    return w

def _hrp(returns: pd.DataFrame) -> np.ndarray:

    cov = returns.cov() * TRADING_DAYS

    corr = returns.corr()

    dist = _correl_dist(corr)

    link = linkage(squareform(dist.values, checks=False), method="single")

    sort_ix = _get_quasi_diag(link)

    weights = _hrp_weights(cov, sort_ix)

    weights = weights.reindex(range(len(returns.columns))).fillna(0)

    return weights.values

def _optimize_weights(prices: pd.DataFrame, strategy: Strategy) -> Dict[str, float]:

    returns = prices.pct_change().dropna()

    cols = list(returns.columns)

    if strategy == "hrp":

        w = _hrp(returns)

    elif strategy == "min_volatility":

        _, cov = _annualize(returns)

        w = _min_vol(cov)

    else:

        mu, cov = _annualize(returns)

        w = _max_sharpe(mu, cov)

    w = np.clip(w, 0, None)

    if w.sum() <= 0:

        return {}

    w = w / w.sum()

    return {cols[i]: float(w[i]) for i in range(len(cols)) if w[i] > 1e-4}

def _allocate_discrete(

    weights: Dict[str, float],

    latest_prices: Dict[str, float],

    cash: float,

) -> Dict[str, int]:

    qty: Dict[str, int] = {}

    remaining = cash

    items = sorted(weights.items(), key=lambda x: -x[1])

    for tk, w in items:

        price = latest_prices.get(tk)

        if not price or price <= 0:

            continue

        n = int((w * cash) // price)

        if n > 0:

            qty[tk] = n

            remaining -= n * price

    changed = True

    while changed and remaining > 0:

        changed = False

        for tk, _ in items:

            price = latest_prices.get(tk, 0)

            if 0 < price <= remaining:

                qty[tk] = qty.get(tk, 0) + 1

                remaining -= price

                changed = True

                break

    return qty

def optimize_portfolio(

    ranked: List[ScoredCompany],

    history: Dict[str, Dict[str, float]],

    cash: float,

    max_positions: int,

    strategy: Strategy = "max_sharpe",

) -> Optional[List[Allocation]]:

    candidates = [s for s in ranked if s.score > 0][:max_positions]

    tickers = [c.fundamentals.ticker for c in candidates]

    prices = _build_price_frame(history, tickers)

    if prices.empty or prices.shape[1] < 2 or len(prices) < 60:

        logger.warning("histórico insuficiente para otimização (%s).", prices.shape)

        return None

    try:

        weights = _optimize_weights(prices, strategy)

    except Exception as e:

        logger.exception("falha na otimização: %s", e)

        return None

    if not weights:

        return None

    by_ticker = {c.fundamentals.ticker: c for c in candidates}

    latest = {tk: float(prices[tk].iloc[-1]) for tk in prices.columns}

    qty_map = _allocate_discrete(weights, latest, cash)

    if not qty_map:

        return None

    allocations: List[Allocation] = []

    invested_total = 0.0

    for tk, qty in qty_map.items():

        if qty <= 0 or tk not in by_ticker:

            continue

        sc = by_ticker[tk]

        price = sc.fundamentals.price or latest[tk]

        invested = qty * price

        invested_total += invested

        allocations.append(

            Allocation(

                ticker=tk,

                name=sc.fundamentals.name,

                sector=sc.fundamentals.sector,

                price=round(price, 2),

                quantity=int(qty),

                invested=round(invested, 2),

                weight=0.0,

                score=sc.score,

                rationale=sc.rationale,

            )

        )

    if invested_total > 0:

        for a in allocations:

            a.weight = round(a.invested / invested_total, 4)

    return allocations

def portfolio_metrics(

    allocations: List[Allocation],

    history: Dict[str, Dict[str, float]],

) -> Dict[str, float]:

    tickers = [a.ticker for a in allocations]

    prices = _build_price_frame(history, tickers)

    if prices.empty or len(prices) < 60:

        return {}

    returns = prices.pct_change().dropna()

    cols = [a.ticker for a in allocations if a.ticker in returns.columns]

    weights = np.array([a.weight for a in allocations if a.ticker in returns.columns])

    if len(weights) == 0 or weights.sum() == 0:

        return {}

    weights = weights / weights.sum()

    mean = returns[cols].mean().values * TRADING_DAYS

    cov = returns[cols].cov().values * TRADING_DAYS

    exp_ret = float(weights @ mean)

    vol = float(np.sqrt(weights @ cov @ weights))

    sharpe = (exp_ret - RISK_FREE) / vol if vol > 0 else 0.0

    return {

        "expected_return": round(exp_ret, 4),

        "volatility": round(vol, 4),

        "sharpe": round(sharpe, 3),

    }

