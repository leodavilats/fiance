from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.collectors.news import NewsItem


W_VALUE = 30 
W_QUALITY = 25     
W_TECHNICAL = 25   
W_DIVIDEND = 10    
W_NEWS = 10        


@dataclass
class DipScoreBreakdown:
    value_score: float = 0.0
    quality_score: float = 0.0
    technical_score: float = 0.0
    dividend_score: float = 0.0
    news_score: float = 0.0


@dataclass
class DipResult:
    dip_score: float
    breakdown: DipScoreBreakdown
    verdict: str        
    verdict_label: str
    confidence: float 
    reasons: List[str]
    drop_from_52w_high_pct: Optional[float]
    drop_from_fair_price_pct: Optional[float]
    news_sentiment_summary: str


def _value_score(margin_of_safety: Optional[float]) -> tuple[float, List[str]]:
    """MOS = (fair_price - current_price) / fair_price. Positivo = barato."""
    reasons: List[str] = []
    if margin_of_safety is None:
        reasons.append("Preço justo não calculado (sem EPS/dividendos — ex.: cripto ou growth sem histórico). Pontuação neutra aplicada.")
        return round(W_VALUE * 0.35, 2), reasons

    mos_pct = margin_of_safety * 100

    if mos_pct >= 40:
        pts = W_VALUE
        reasons.append(f"Excelente margem de segurança: {mos_pct:.1f}% abaixo do preço justo.")
    elif mos_pct >= 25:
        pts = W_VALUE * 0.8
        reasons.append(f"Boa margem de segurança: {mos_pct:.1f}% abaixo do preço justo.")
    elif mos_pct >= 10:
        pts = W_VALUE * 0.5
        reasons.append(f"Margem de segurança razoável: {mos_pct:.1f}% abaixo do preço justo.")
    elif mos_pct >= 0:
        pts = W_VALUE * 0.2
        reasons.append(f"Próximo do preço justo ({mos_pct:.1f}% de margem).")
    else:
        pts = 0.0
        reasons.append(f"Ativo acima do preço justo ({abs(mos_pct):.1f}% de prêmio) — risco de pagar caro.")

    return round(pts, 2), reasons


def _quality_score(
    roe: Optional[float],
    profit_margin: Optional[float],
    debt_to_equity: Optional[float],
) -> tuple[float, List[str]]:
    reasons: List[str] = []
    pts = 0.0

    if roe is not None:
        if roe >= 20:
            pts += 10
            reasons.append(f"ROE excelente: {roe:.1f}%.")
        elif roe >= 15:
            pts += 7
            reasons.append(f"ROE saudável: {roe:.1f}%.")
        elif roe >= 10:
            pts += 4
            reasons.append(f"ROE aceitável: {roe:.1f}%.")
        else:
            reasons.append(f"ROE baixo ({roe:.1f}%): rentabilidade preocupante.")
    else:
        reasons.append("ROE indisponível.")

    # Margem de lucro (até 8 pts)
    if profit_margin is not None:
        if profit_margin >= 15:
            pts += 8
            reasons.append(f"Margem líquida forte: {profit_margin:.1f}%.")
        elif profit_margin >= 8:
            pts += 5
            reasons.append(f"Margem líquida satisfatória: {profit_margin:.1f}%.")
        elif profit_margin >= 3:
            pts += 2
            reasons.append(f"Margem líquida apertada: {profit_margin:.1f}%.")
        else:
            reasons.append(f"Margem líquida muito baixa ({profit_margin:.1f}%) — empresa com dificuldade de gerar lucro.")
    else:
        reasons.append("Margem de lucro indisponível.")

    if debt_to_equity is not None:
        if debt_to_equity <= 0.3:
            pts += 7
            reasons.append(f"Dívida muito baixa (D/E: {debt_to_equity:.2f}) — empresa sólida.")
        elif debt_to_equity <= 0.7:
            pts += 5
            reasons.append(f"Endividamento controlado (D/E: {debt_to_equity:.2f}).")
        elif debt_to_equity <= 1.5:
            pts += 2
            reasons.append(f"Alavancagem moderada (D/E: {debt_to_equity:.2f}).")
        else:
            reasons.append(f"Alto endividamento (D/E: {debt_to_equity:.2f}) — risco elevado em crises.")
    else:
        reasons.append("Índice de endividamento indisponível.")

    return round(min(pts, W_QUALITY), 2), reasons


def _technical_score(
    rsi_14: Optional[float],
    trend: Optional[str],
    distance_from_52w_high_pct: Optional[float],
    sma_200: Optional[float],
    last_price: Optional[float],
) -> tuple[float, List[str]]:
    reasons: List[str] = []
    pts = 0.0

    if rsi_14 is not None:
        if rsi_14 <= 25:
            pts += 10
            reasons.append(f"RSI fortemente sobrevendido ({rsi_14:.0f}) — alta probabilidade de reversão técnica.")
        elif rsi_14 <= 35:
            pts += 7
            reasons.append(f"RSI sobrevendido ({rsi_14:.0f}) — sinal de possível fundo técnico.")
        elif rsi_14 <= 45:
            pts += 4
            reasons.append(f"RSI próximo a zona de sobrevendido ({rsi_14:.0f}).")
        elif rsi_14 >= 65:
            reasons.append(f"RSI elevado ({rsi_14:.0f}) — ativo não está em baixa técnica.")
        else:
            pts += 1
    else:
        reasons.append("RSI indisponível.")

    if distance_from_52w_high_pct is not None:
        drop_from_top = abs(distance_from_52w_high_pct)
        if drop_from_top >= 35:
            pts += 10
            reasons.append(f"Queda de {drop_from_top:.1f}% em relação ao topo de 52 semanas — dip pronunciado.")
        elif drop_from_top >= 20:
            pts += 7
            reasons.append(f"Queda de {drop_from_top:.1f}% em relação ao topo de 52 semanas.")
        elif drop_from_top >= 10:
            pts += 4
            reasons.append(f"Queda moderada de {drop_from_top:.1f}% em relação ao topo.")
        else:
            pts += 1
            reasons.append(f"Ativo próximo ao topo de 52 semanas (queda de apenas {drop_from_top:.1f}%) — não é um dip evidente.")
    else:
        reasons.append("Histórico de 52 semanas indisponível.")

    if sma_200 is not None and last_price is not None:
        if last_price < sma_200:
            pts += 5
            reasons.append(f"Preço abaixo da SMA200 ({sma_200:.2f}) — zona historicamente de valor.")
        else:
            dist_pct = ((last_price - sma_200) / sma_200) * 100
            if dist_pct < 5:
                pts += 2
                reasons.append("Preço levemente acima da SMA200.")

    return round(min(pts, W_TECHNICAL), 2), reasons


def _dividend_score(
    dividend_yield: Optional[float],
    avg_dividend_5y: Optional[float],
) -> tuple[float, List[str]]:
    reasons: List[str] = []
    pts = 0.0

    if dividend_yield is None and avg_dividend_5y is None:
        reasons.append("Dados de dividendos indisponíveis — pontuação neutra aplicada.")
        return round(W_DIVIDEND * 0.3, 2), reasons

    if dividend_yield is not None and dividend_yield > 0:
        if dividend_yield >= 8:
            pts += 7
            reasons.append(f"DY atrativo: {dividend_yield:.1f}% — remuneração sólida enquanto espera valorização.")
        elif dividend_yield >= 5:
            pts += 5
            reasons.append(f"DY razoável: {dividend_yield:.1f}%.")
        elif dividend_yield >= 2:
            pts += 2
            reasons.append(f"DY baixo ({dividend_yield:.1f}%) — foco de crescimento, não dividendos.")
        else:
            reasons.append(f"DY muito baixo ({dividend_yield:.1f}%).")
    elif dividend_yield == 0:
        reasons.append("Sem dividendos recentes registrados.")

    if avg_dividend_5y is not None and avg_dividend_5y > 0:
        pts += 3
        reasons.append(f"Histórico de dividendos (média 5a: {avg_dividend_5y:.2f}).")

    return round(min(pts, W_DIVIDEND), 2), reasons


def _news_score(items: list) -> tuple[float, List[str]]:
    reasons: List[str] = []
    if not items:
        return 5.0, ["Sem notícias recentes — nem positivo nem negativo."]

    pos = sum(1 for i in items if i.sentiment == "positive")
    neg = sum(1 for i in items if i.sentiment == "negative")
    total = len(items)

    ratio = (pos - neg) / total if total > 0 else 0

    if ratio >= 0.5:
        pts = W_NEWS
        reasons.append(f"Maioria das notícias recentes é positiva ({pos}/{total}).")
    elif ratio >= 0.1:
        pts = W_NEWS * 0.7
        reasons.append(f"Notícias recentes levemente positivas ({pos} positivas, {neg} negativas).")
    elif ratio > -0.2:
        pts = W_NEWS * 0.5
        reasons.append("Notícias recentes mistas ou neutras.")
    else:
        pts = W_NEWS * 0.1
        reasons.append(f"Maioria das notícias recentes é negativa ({neg}/{total}) — verifique os motivos da queda.")

    return round(pts, 2), reasons


def compute_dip_analysis(
    margin_of_safety: Optional[float],
    roe: Optional[float],
    profit_margin: Optional[float],
    debt_to_equity: Optional[float],
    rsi_14: Optional[float],
    trend: Optional[str],
    distance_from_52w_high_pct: Optional[float],
    sma_200: Optional[float],
    last_price: Optional[float],
    dividend_yield: Optional[float],
    avg_dividend_5y: Optional[float],
    fair_price_consensus: Optional[float],
    current_price: Optional[float],
    news_items: List[NewsItem],
    news_sentiment_summary: str,
) -> DipResult:
    all_reasons: List[str] = []

    v_pts, v_reasons = _value_score(margin_of_safety)
    q_pts, q_reasons = _quality_score(roe, profit_margin, debt_to_equity)
    t_pts, t_reasons = _technical_score(rsi_14, trend, distance_from_52w_high_pct, sma_200, last_price)
    d_pts, d_reasons = _dividend_score(dividend_yield, avg_dividend_5y)
    n_pts, n_reasons = _news_score(news_items)

    all_reasons.extend(v_reasons)
    all_reasons.extend(q_reasons)
    all_reasons.extend(t_reasons)
    all_reasons.extend(d_reasons)
    all_reasons.extend(n_reasons)

    total = round(v_pts + q_pts + t_pts + d_pts + n_pts, 2)

    if total >= 68:
        verdict = "OPORTUNIDADE"
        verdict_label = "Oportunidade na baixa"
        confidence = min(1.0, total / 100)
    elif total >= 42:
        verdict = "NEUTRO"
        verdict_label = "Posição neutra — aguardar"
        confidence = 0.5
    else:
        verdict = "ARMADILHA"
        verdict_label = "Armadilha — cuidado com o value trap"
        confidence = min(1.0, (100 - total) / 100)

    drop_52w: Optional[float] = None
    if distance_from_52w_high_pct is not None:
        drop_52w = round(abs(distance_from_52w_high_pct), 2)

    drop_fair: Optional[float] = None
    if fair_price_consensus and current_price and fair_price_consensus > 0:
        drop_fair = round((fair_price_consensus - current_price) / fair_price_consensus * 100, 2)

    breakdown = DipScoreBreakdown(
        value_score=v_pts,
        quality_score=q_pts,
        technical_score=t_pts,
        dividend_score=d_pts,
        news_score=n_pts,
    )

    return DipResult(
        dip_score=total,
        breakdown=breakdown,
        verdict=verdict,
        verdict_label=verdict_label,
        confidence=round(confidence, 3),
        reasons=all_reasons,
        drop_from_52w_high_pct=drop_52w,
        drop_from_fair_price_pct=drop_fair,
        news_sentiment_summary=news_sentiment_summary,
    )
