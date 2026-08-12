from __future__ import annotations

from app.models import CategoryAllocation, PortfolioHealth, PortfolioPosition

_WEIGHTS = {
    "concentration": 0.30,
    "sector_concentration": 0.20,
    "diversification": 0.20,
    "risk": 0.30,
}


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def compute_portfolio_health(
    positions: list[PortfolioPosition],
    allocations: list[CategoryAllocation],
) -> PortfolioHealth | None:
    real_positions = [p for p in positions if not p.ticker.startswith("RF_")]
    if not real_positions:
        return None

    values = [(p.ticker, p.current_value or p.invested) for p in real_positions]
    total = sum(v for _, v in values) or 1.0

    top_ticker, top_value = max(values, key=lambda x: x[1])
    top_pct = top_value / total * 100
    # acima de 40% num único ativo já é considerado risco alto (score 0);
    # abaixo de 10% é considerado bem diluído (score 100).
    concentration_score = _clip(100 - (top_pct - 10) * (100 / 30))

    sector_totals: dict[str, float] = {}
    for p in real_positions:
        if p.sector:
            sector_totals[p.sector] = sector_totals.get(p.sector, 0.0) + (
                p.current_value or p.invested
            )

    top_sector = None
    top_sector_pct = None
    sector_concentration_score = 100.0
    if sector_totals:
        top_sector, top_sector_value = max(sector_totals.items(), key=lambda x: x[1])
        top_sector_pct = top_sector_value / total * 100
        # mesma régua da concentração por ativo, só que com teto mais alto
        # (é normal um setor pesar mais que um ativo isolado).
        sector_concentration_score = _clip(100 - (top_sector_pct - 20) * (100 / 40))

    categories_present = {a.category for a in allocations if a.current_value > 0}
    diversification_score = _clip(len(categories_present) / 5 * 100)

    at_risk_value = sum(
        (p.current_value or p.invested)
        for p in real_positions
        if p.verdict in ("SELL", "STRONG_SELL")
    )
    risk_score = _clip(100 - (at_risk_value / total * 100) * 1.5)

    overall = (
        _WEIGHTS["concentration"] * concentration_score
        + _WEIGHTS["sector_concentration"] * sector_concentration_score
        + _WEIGHTS["diversification"] * diversification_score
        + _WEIGHTS["risk"] * risk_score
    )

    warnings: list[str] = []
    if top_pct >= 30:
        warnings.append(f"{top_ticker} representa {top_pct:.0f}% da carteira — risco concentrado.")
    if top_sector_pct and top_sector_pct >= 40:
        warnings.append(f"Setor {top_sector} representa {top_sector_pct:.0f}% da carteira.")
    if len(categories_present) <= 2:
        warnings.append("Carteira concentrada em poucas categorias de ativo.")
    if at_risk_value > 0:
        at_risk_pct = at_risk_value / total * 100
        warnings.append(f"{at_risk_pct:.0f}% da carteira está em ativos com sinal de venda.")

    return PortfolioHealth(
        score=round(overall, 1),
        concentration_score=round(concentration_score, 1),
        sector_concentration_score=round(sector_concentration_score, 1),
        diversification_score=round(diversification_score, 1),
        risk_score=round(risk_score, 1),
        top_position_ticker=top_ticker,
        top_position_pct=round(top_pct, 1),
        top_sector=top_sector,
        top_sector_pct=round(top_sector_pct, 1) if top_sector_pct is not None else None,
        warnings=warnings,
    )
