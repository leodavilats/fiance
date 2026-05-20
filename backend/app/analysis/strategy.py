"""
Módulo de análise de estratégia de investimentos personalizada.
"""
from typing import List, Dict, Any, Optional
from ..models.portfolio import PortfolioItem
from ..models.goal import Goal
from ..models.opportunity import Opportunity
from ..models.enums import AssetType


def build_investment_strategy(
    cash_available: float,
    current_portfolio: List[PortfolioItem],
    goals: List[Goal],
    opportunities: List[Opportunity],
    portfolio_evaluation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Constrói uma estratégia de investimento personalizada baseada no perfil do investidor.
    
    Args:
        cash_available: Caixa disponível para investir
        current_portfolio: Portfólio atual do investidor
        goals: Metas de alocação por categoria
        opportunities: Lista de oportunidades disponíveis
        portfolio_evaluation: Avaliação atual do portfólio (opcional)
    
    Returns:
        Estratégia completa com sugestões de investimento
    """
    # Calcular valor total da carteira
    total_invested = sum(item.quantity * item.avg_price for item in current_portfolio)
    total_capital = total_invested + cash_available
    
    # Analisar perfil com base nas metas
    profile = _analyze_investor_profile(goals)
    
    # Calcular alocação atual por categoria
    current_allocation = _calculate_current_allocation(
        current_portfolio, portfolio_evaluation, total_capital
    )
    
    # Identificar gaps de alocação
    allocation_gaps = _identify_allocation_gaps(goals, current_allocation, total_capital)
    
    # Gerar sugestões de investimento
    suggestions = _generate_investment_suggestions(
        allocation_gaps, opportunities, cash_available, current_portfolio
    )
    
    # Calcular nova alocação projetada
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


def _analyze_investor_profile(goals: List[Goal]) -> Dict[str, Any]:
    """Analisa o perfil do investidor com base nas metas."""
    total_pct = sum(g.target_pct for g in goals)
    
    # Normalizar se não somar 100%
    normalized_goals = {}
    for g in goals:
        normalized_goals[g.category] = (g.target_pct / total_pct * 100) if total_pct > 0 else 0
    
    # Definir perfil
    renda_pct = normalized_goals.get('renda', 0)
    trade_pct = normalized_goals.get('trade', 0)
    cripto_pct = normalized_goals.get('cripto', 0)
    
    if renda_pct >= 60:
        profile_type = 'Conservador'
        description = 'Foco em renda passiva e preservação de capital.'
    elif trade_pct >= 50:
        profile_type = 'Agressivo'
        description = 'Foco em crescimento e valorização de capital.'
    elif cripto_pct >= 30:
        profile_type = 'Arrojado'
        description = 'Alto risco com foco em criptomoedas e ativos voláteis.'
    else:
        profile_type = 'Moderado'
        description = 'Equilíbrio entre renda e crescimento.'
    
    return {
        "type": profile_type,
        "description": description,
        "goals": normalized_goals,
        "risk_tolerance": _assess_risk_tolerance(trade_pct, cripto_pct),
    }


def _assess_risk_tolerance(trade_pct: float, cripto_pct: float) -> str:
    """Avalia a tolerância ao risco."""
    risk_score = trade_pct * 0.5 + cripto_pct * 1.0
    
    if risk_score >= 40:
        return 'Alto'
    elif risk_score >= 20:
        return 'Médio'
    else:
        return 'Baixo'


def _calculate_current_allocation(
    portfolio: List[PortfolioItem],
    evaluation: Optional[Dict[str, Any]],
    total_capital: float,
) -> List[Dict[str, Any]]:
    """Calcula a alocação atual por categoria."""
    if not evaluation or not evaluation.get('positions'):
        return []
    
    allocation = {}
    for pos in evaluation['positions']:
        cat = pos.get('category_resolved', 'trade')
        current_value = pos.get('current_price', 0) * pos.get('quantity', 0)
        
        if cat not in allocation:
            allocation[cat] = {"category": cat, "value": 0, "count": 0}
        
        allocation[cat]['value'] += current_value
        allocation[cat]['count'] += 1
    
    # Converter para lista e calcular percentuais
    result = []
    for cat, data in allocation.items():
        pct = (data['value'] / total_capital * 100) if total_capital > 0 else 0
        result.append({
            "category": cat,
            "current_value": data['value'],
            "current_pct": pct,
            "assets_count": data['count'],
        })
    
    return result


def _identify_allocation_gaps(
    goals: List[Goal],
    current_allocation: List[Dict[str, Any]],
    total_capital: float,
) -> List[Dict[str, Any]]:
    """Identifica gaps entre alocação atual e metas."""
    gaps = []
    
    current_by_cat = {item['category']: item for item in current_allocation}
    
    for goal in goals:
        cat = goal.category
        target_value = total_capital * (goal.target_pct / 100)
        current_item = current_by_cat.get(cat, {})
        current_value = current_item.get('current_value', 0)
        gap_value = target_value - current_value
        
        if abs(gap_value) > 100:  # Apenas gaps significativos
            gaps.append({
                "category": cat,
                "target_pct": goal.target_pct,
                "current_pct": current_item.get('current_pct', 0),
                "gap_pct": goal.target_pct - current_item.get('current_pct', 0),
                "target_value": target_value,
                "current_value": current_value,
                "gap_value": gap_value,
                "action": "Comprar" if gap_value > 0 else "Reduzir",
            })
    
    # Ordenar por gap absoluto (maior primeiro)
    gaps.sort(key=lambda x: abs(x['gap_value']), reverse=True)
    
    return gaps


def _generate_investment_suggestions(
    allocation_gaps: List[Dict[str, Any]],
    opportunities: List[Opportunity],
    cash_available: float,
    current_portfolio: List[PortfolioItem],
) -> List[Dict[str, Any]]:
    """Gera sugestões de investimento baseadas nos gaps."""
    suggestions = []
    remaining_cash = cash_available
    
    # Tickers já em carteira
    held_tickers = {item.ticker.upper() for item in current_portfolio}
    
    # Processar gaps que precisam de compra
    for gap in allocation_gaps:
        if gap['gap_value'] <= 0 or remaining_cash < 100:
            continue
        
        category = gap['category']
        budget_for_category = min(gap['gap_value'], remaining_cash)
        
        # Filtrar oportunidades para essa categoria
        category_opps = [
            opp for opp in opportunities
            if opp.category_resolved == category
            and opp.verdict in ['BUY', 'STRONG_BUY']
            and opp.price > 0
        ]
        
        # Ordenar por score
        category_opps.sort(key=lambda x: x.score, reverse=True)
        
        # Selecionar até 3 melhores
        allocated = 0
        for opp in category_opps[:3]:
            if allocated >= budget_for_category:
                break
            
            # Calcular quantidade sugerida
            amount_to_invest = min(budget_for_category - allocated, remaining_cash * 0.3)
            quantity = int(amount_to_invest / opp.price)
            
            if quantity < 1:
                continue
            
            actual_invest = quantity * opp.price
            
            # Gerar objetivo da sugestão
            objective = _generate_investment_objective(opp, category)
            
            suggestions.append({
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
                "reasons": _generate_suggestion_reasons(opp, category, gap),
            })
            
            allocated += actual_invest
            remaining_cash -= actual_invest
    
    # Se sobrou muito caixa e não há gaps, sugerir top oportunidades
    if remaining_cash > cash_available * 0.5 and len(suggestions) < 3:
        top_opps = [
            opp for opp in opportunities
            if opp.verdict in ['BUY', 'STRONG_BUY']
            and opp.ticker not in held_tickers
        ]
        top_opps.sort(key=lambda x: x.score, reverse=True)
        
        for opp in top_opps[:2]:
            if remaining_cash < 100:
                break
            
            amount = min(remaining_cash * 0.2, remaining_cash)
            quantity = int(amount / opp.price)
            
            if quantity >= 1:
                actual = quantity * opp.price
                suggestions.append({
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
                    "reasons": ["Excelente oportunidade de entrada", f"Score elevado: {opp.score:.0f}"],
                })
                remaining_cash -= actual
    
    return suggestions


def _generate_investment_objective(opp: Opportunity, category: str) -> str:
    """Gera o objetivo do investimento."""
    objectives = {
        'renda': 'Geração de renda passiva através de dividendos',
        'trade': 'Crescimento de capital através de valorização',
        'cripto': 'Exposição a ativos digitais com alto potencial',
        'caixa': 'Preservação de capital e liquidez',
    }
    
    base = objectives.get(category, 'Diversificação de portfólio')
    
    # Adicionar contexto específico
    if opp.dividend_yield and opp.dividend_yield >= 6:
        return f"{base} — DY atrativo de {opp.dividend_yield:.1f}%"
    elif opp.margin_of_safety and opp.margin_of_safety >= 0.15:
        return f"{base} — Preço com desconto de {opp.margin_of_safety*100:.0f}%"
    else:
        return base


def _generate_suggestion_reasons(
    opp: Opportunity,
    category: str,
    gap: Dict[str, Any],
) -> List[str]:
    """Gera razões para a sugestão."""
    reasons = []
    
    # Razão de alocação
    if gap['gap_value'] > 0:
        reasons.append(
            f"Ajusta alocação de {category}: falta {gap['gap_pct']:.1f}% para atingir meta"
        )
    
    # Razões do ativo
    if opp.score >= 70:
        reasons.append(f"Score elevado ({opp.score:.0f}) indica forte potencial")
    
    if opp.margin_of_safety and opp.margin_of_safety >= 0.1:
        reasons.append(f"Margem de segurança de {opp.margin_of_safety*100:.0f}%")
    
    if opp.dividend_yield and opp.dividend_yield >= 6:
        reasons.append(f"Dividend Yield atrativo de {opp.dividend_yield:.1f}%")
    
    if opp.verdict == 'STRONG_BUY':
        reasons.append("Sinal forte de compra baseado em análise fundamentalista")
    
    return reasons[:3]  # Máximo 3 razões


def _calculate_projected_allocation(
    current_allocation: List[Dict[str, Any]],
    suggestions: List[Dict[str, Any]],
    total_capital: float,
) -> List[Dict[str, Any]]:
    """Calcula a alocação projetada após executar as sugestões."""
    projected = {item['category']: item.copy() for item in current_allocation}
    
    # Adicionar valores das sugestões
    for sug in suggestions:
        cat = sug['category']
        if cat not in projected:
            projected[cat] = {
                "category": cat,
                "current_value": 0,
                "current_pct": 0,
                "assets_count": 0,
            }
        
        projected[cat]['current_value'] += sug['invest_amount']
        if not sug['already_held']:
            projected[cat]['assets_count'] += 1
    
    # Recalcular percentuais
    result = []
    new_total = total_capital + sum(s['invest_amount'] for s in suggestions)
    
    for cat, data in projected.items():
        new_pct = (data['current_value'] / new_total * 100) if new_total > 0 else 0
        result.append({
            "category": cat,
            "projected_value": data['current_value'],
            "projected_pct": new_pct,
            "assets_count": data['assets_count'],
        })
    
    return result


def _generate_strategy_summary(
    profile: Dict[str, Any],
    suggestions: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
) -> str:
    """Gera um resumo textual da estratégia."""
    if not suggestions:
        return "Seu portfólio está bem balanceado. Considere aguardar novas oportunidades."
    
    total_to_invest = sum(s['invest_amount'] for s in suggestions)
    n_suggestions = len(suggestions)
    
    summary = f"Com base no seu perfil {profile['type']}, sugerimos investir "
    summary += f"R$ {total_to_invest:,.2f} em {n_suggestions} "
    summary += "ativo" if n_suggestions == 1 else "ativos"
    summary += ". "
    
    # Adicionar principais categorias
    categories = {}
    for sug in suggestions:
        cat = sug['category']
        categories[cat] = categories.get(cat, 0) + sug['invest_amount']
    
    if categories:
        main_cat = max(categories.items(), key=lambda x: x[1])
        summary += f"Maior alocação em {main_cat[0]} (R$ {main_cat[1]:,.2f}). "
    
    # Adicionar gap mais crítico
    if gaps:
        critical_gap = gaps[0]
        if critical_gap['gap_value'] > 0:
            summary += f"Prioridade: ajustar {critical_gap['category']} "
            summary += f"(faltam {critical_gap['gap_pct']:.1f}% para meta)."
    
    return summary
