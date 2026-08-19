from typing import Any

from ..models.goal import Goal
from ..models.opportunity import Opportunity
from ..models.portfolio import PortfolioItem


def _analyze_investor_profile(goals: list[Goal]) -> dict[str, Any]:
    total_pct = sum(g.target_pct for g in goals)

    normalized_goals = {}
    for g in goals:
        normalized_goals[g.category] = (g.target_pct / total_pct * 100) if total_pct > 0 else 0

    renda_pct = normalized_goals.get("renda", 0)
    trade_pct = normalized_goals.get("trade", 0)

    if renda_pct >= 60:
        profile_type = "Conservador"
        description = "Foco em renda passiva e preservação de capital."
    elif trade_pct >= 50:
        profile_type = "Agressivo"
        description = "Foco em crescimento e valorização de capital."
    else:
        profile_type = "Moderado"
        description = "Equilíbrio entre renda e crescimento."

    return {
        "type": profile_type,
        "description": description,
        "goals": normalized_goals,
        "risk_tolerance": _assess_risk_tolerance(trade_pct),
    }


def _assess_risk_tolerance(trade_pct: float) -> str:
    risk_score = trade_pct * 0.5

    if risk_score >= 40:
        return "Alto"
    elif risk_score >= 20:
        return "Médio"
    else:
        return "Baixo"


def _calculate_current_allocation(
    portfolio: list[PortfolioItem],
    evaluation: dict[str, Any] | None,
    total_capital: float,
) -> list[dict[str, Any]]:
    if not evaluation or not evaluation.get("positions"):
        return []

    allocation = {}
    for pos in evaluation["positions"]:
        cat = pos.get("category_resolved", "trade")
        current_value = pos.get("current_price", 0) * pos.get("quantity", 0)

        if cat not in allocation:
            allocation[cat] = {"category": cat, "value": 0, "count": 0}

        allocation[cat]["value"] += current_value
        allocation[cat]["count"] += 1

    result = []
    for cat, data in allocation.items():
        pct = (data["value"] / total_capital * 100) if total_capital > 0 else 0
        result.append(
            {
                "category": cat,
                "current_value": data["value"],
                "current_pct": pct,
                "assets_count": data["count"],
            }
        )

    return result


def _identify_allocation_gaps(
    goals: list[Goal],
    current_allocation: list[dict[str, Any]],
    total_capital: float,
) -> list[dict[str, Any]]:
    gaps = []

    current_by_cat = {item["category"]: item for item in current_allocation}

    for goal in goals:
        cat = goal.category
        target_value = total_capital * (goal.target_pct / 100)
        current_item = current_by_cat.get(cat, {})
        current_value = current_item.get("current_value", 0)
        gap_value = target_value - current_value

        if abs(gap_value) > 100:
            gaps.append(
                {
                    "category": cat,
                    "target_pct": goal.target_pct,
                    "current_pct": current_item.get("current_pct", 0),
                    "gap_pct": goal.target_pct - current_item.get("current_pct", 0),
                    "target_value": target_value,
                    "current_value": current_value,
                    "gap_value": gap_value,
                    "action": "Comprar" if gap_value > 0 else "Reduzir",
                }
            )

    gaps.sort(key=lambda x: abs(x["gap_value"]), reverse=True)

    return gaps


def _rank_category_opportunities(
    category: str,
    budget: float,
    category_opps: list[Opportunity],
) -> tuple[list[Opportunity], dict[str, str]]:
    """Ordena as oportunidades candidatas de um gap por score (determinístico —
    sem dependência de IA externa)."""
    by_score = sorted(category_opps, key=lambda x: x.score, reverse=True)
    return by_score, {}


def _generate_investment_suggestions(
    allocation_gaps: list[dict[str, Any]],
    opportunities: list[Opportunity],
    cash_available: float,
    current_portfolio: list[PortfolioItem],
) -> list[dict[str, Any]]:
    suggestions = []
    remaining_cash = cash_available

    held_tickers = {item.ticker.upper() for item in current_portfolio}

    for gap in allocation_gaps:
        if gap["gap_value"] <= 0 or remaining_cash < 100:
            continue

        category = gap["category"]
        budget_for_category = min(gap["gap_value"], remaining_cash)

        category_opps = [
            opp
            for opp in opportunities
            if opp.category_resolved == category
            and opp.verdict in ["BUY", "STRONG_BUY"]
            and opp.price > 0
        ]

        category_opps, _ = _rank_category_opportunities(
            category, budget_for_category, category_opps
        )

        allocated = 0
        for opp in category_opps[:3]:
            if allocated >= budget_for_category:
                break

            amount_to_invest = min(budget_for_category - allocated, remaining_cash * 0.3)
            quantity = int(amount_to_invest / opp.price)

            if quantity < 1:
                continue

            actual_invest = quantity * opp.price

            objective = _generate_investment_objective(opp, category)
            reasons = _generate_suggestion_reasons(opp, category, gap)

            suggestions.append(
                {
                    "ticker": opp.ticker,
                    "name": opp.name,
                    "asset_type": opp.asset_type,
                    "category": category,
                    "objective": objective,
                    "price": opp.price,
                    "quantity": quantity,
                    "invest_amount": actual_invest,
                    "score": opp.score,
                    "dividend_yield": opp.dividend_yield,
                    "margin_of_safety": opp.margin_of_safety,
                    "verdict": opp.verdict,
                    "already_held": opp.ticker in held_tickers,
                    "reasons": reasons,
                    "rationale": None,
                }
            )

            allocated += actual_invest
            remaining_cash -= actual_invest

    if remaining_cash > cash_available * 0.5 and len(suggestions) < 3:
        top_opps = [
            opp
            for opp in opportunities
            if opp.verdict in ["BUY", "STRONG_BUY"] and opp.ticker not in held_tickers
        ]
        top_opps.sort(key=lambda x: x.score, reverse=True)

        for opp in top_opps[:2]:
            if remaining_cash < 100:
                break

            amount = min(remaining_cash * 0.2, remaining_cash)
            quantity = int(amount / opp.price)

            if quantity >= 1:
                actual = quantity * opp.price
                suggestions.append(
                    {
                        "ticker": opp.ticker,
                        "name": opp.name,
                        "asset_type": opp.asset_type,
                        "category": opp.category_resolved,
                        "objective": _generate_investment_objective(opp, opp.category_resolved),
                        "price": opp.price,
                        "quantity": quantity,
                        "invest_amount": actual,
                        "score": opp.score,
                        "dividend_yield": opp.dividend_yield,
                        "margin_of_safety": opp.margin_of_safety,
                        "verdict": opp.verdict,
                        "already_held": False,
                        "reasons": [
                            "Excelente oportunidade de entrada",
                            f"Score elevado: {opp.score:.0f}",
                        ],
                        "rationale": None,
                    }
                )
                remaining_cash -= actual

    return suggestions


def _generate_investment_objective(opp: Opportunity, category: str) -> str:
    objectives = {
        "renda": "Geração de renda passiva através de dividendos",
        "trade": "Crescimento de capital através de valorização",
        "etfs": "Diversificação de baixo custo via ETF",
        "caixa": "Preservação de capital e liquidez",
    }

    base = objectives.get(category, "Diversificação de portfólio")

    if opp.dividend_yield and opp.dividend_yield >= 6:
        return f"{base} — DY atrativo de {opp.dividend_yield:.1f}%"
    elif opp.margin_of_safety and opp.margin_of_safety >= 0.15:
        return f"{base} — Preço com desconto de {opp.margin_of_safety * 100:.0f}%"
    else:
        return base


def _generate_suggestion_reasons(
    opp: Opportunity,
    category: str,
    gap: dict[str, Any],
) -> list[str]:
    reasons = []

    if gap["gap_value"] > 0:
        reasons.append(
            f"Ajusta alocação de {category}: falta {gap['gap_pct']:.1f}% para atingir meta"
        )

    if opp.score >= 70:
        reasons.append(f"Score elevado ({opp.score:.0f}) indica forte potencial")

    if opp.margin_of_safety and opp.margin_of_safety >= 0.1:
        reasons.append(f"Margem de segurança de {opp.margin_of_safety * 100:.0f}%")

    if opp.dividend_yield and opp.dividend_yield >= 6:
        reasons.append(f"Dividend Yield atrativo de {opp.dividend_yield:.1f}%")

    if opp.verdict == "STRONG_BUY":
        reasons.append("Sinal forte de compra baseado em análise fundamentalista")

    return reasons[:3]


def _calculate_projected_allocation(
    current_allocation: list[dict[str, Any]],
    suggestions: list[dict[str, Any]],
    total_capital: float,
) -> list[dict[str, Any]]:
    projected = {item["category"]: item.copy() for item in current_allocation}

    for sug in suggestions:
        cat = sug["category"]
        if cat not in projected:
            projected[cat] = {
                "category": cat,
                "current_value": 0,
                "current_pct": 0,
                "assets_count": 0,
            }

        projected[cat]["current_value"] += sug["invest_amount"]
        if not sug["already_held"]:
            projected[cat]["assets_count"] += 1

    result = []
    new_total = total_capital + sum(s["invest_amount"] for s in suggestions)

    for cat, data in projected.items():
        new_pct = (data["current_value"] / new_total * 100) if new_total > 0 else 0
        result.append(
            {
                "category": cat,
                "projected_value": data["current_value"],
                "projected_pct": new_pct,
                "assets_count": data["assets_count"],
            }
        )

    return result


def _generate_strategy_summary(
    profile: dict[str, Any],
    suggestions: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
) -> str:
    if not suggestions:
        return "Seu portfólio está bem balanceado. Considere aguardar novas oportunidades."

    total_to_invest = sum(s["invest_amount"] for s in suggestions)
    n_suggestions = len(suggestions)

    summary = f"Com base no seu perfil {profile['type']}, sugerimos investir "
    summary += f"R$ {total_to_invest:,.2f} em {n_suggestions} "
    summary += "ativo" if n_suggestions == 1 else "ativos"
    summary += ". "

    categories = {}
    for sug in suggestions:
        cat = sug["category"]
        categories[cat] = categories.get(cat, 0) + sug["invest_amount"]

    if categories:
        main_cat = max(categories.items(), key=lambda x: x[1])
        summary += f"Maior alocação em {main_cat[0]} (R$ {main_cat[1]:,.2f}). "

    if gaps:
        critical_gap = gaps[0]
        if critical_gap["gap_value"] > 0:
            summary += f"Prioridade: ajustar {critical_gap['category']} "
            summary += f"(faltam {critical_gap['gap_pct']:.1f}% para meta)."

    return summary


def build_investment_strategy(
    cash_available: float,
    current_portfolio: list[PortfolioItem],
    goals: list[Goal],
    opportunities: list[Opportunity],
    portfolio_evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:

    total_invested = sum(item.quantity * item.avg_price for item in current_portfolio)
    total_capital = total_invested + cash_available

    profile = _analyze_investor_profile(goals)

    current_allocation = _calculate_current_allocation(
        current_portfolio, portfolio_evaluation, total_capital
    )

    allocation_gaps = _identify_allocation_gaps(goals, current_allocation, total_capital)

    suggestions = _generate_investment_suggestions(
        allocation_gaps, opportunities, cash_available, current_portfolio
    )

    projected_allocation = _calculate_projected_allocation(
        current_allocation, suggestions, total_capital
    )

    return {
        "profile": profile,
        "total_capital": total_capital,
        "cash_available": cash_available,
        "total_invested": total_invested,
        "current_allocation": current_allocation,
        "allocation_gaps": allocation_gaps,
        "suggestions": suggestions,
        "projected_allocation": projected_allocation,
        "summary": _generate_strategy_summary(profile, suggestions, allocation_gaps),
    }
