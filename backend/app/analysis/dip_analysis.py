from __future__ import annotations

from dataclasses import dataclass

from app.collectors.news import NewsItem

W_VALUE = 30
W_QUALITY = 25
W_TECHNICAL = 25
W_DIVIDEND = 10
W_NEWS = 10

W_CRYPTO_TECHNICAL = 50
W_CRYPTO_NEWS = 25
W_CRYPTO_VALUE = 25


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
    reasons: list[str]
    drop_from_52w_high_pct: float | None
    drop_from_fair_price_pct: float | None
    news_sentiment_summary: str


def _value_score(margin_of_safety: float | None) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if margin_of_safety is None:
        reasons.append(
            "Preço justo não calculado (sem EPS/dividendos — ex.: cripto ou growth sem histórico). Pontuação neutra aplicada."
        )
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
        reasons.append(
            f"Ativo acima do preço justo ({abs(mos_pct):.1f}% de prêmio) — risco de pagar caro."
        )

    return round(pts, 2), reasons


def _quality_score(
    roe: float | None,
    profit_margin: float | None,
    debt_to_equity: float | None,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
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
            reasons.append(
                f"Margem líquida muito baixa ({profit_margin:.1f}%) — empresa com dificuldade de gerar lucro."
            )
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
            reasons.append(
                f"Alto endividamento (D/E: {debt_to_equity:.2f}) — risco elevado em crises."
            )
    else:
        reasons.append("Índice de endividamento indisponível.")

    return round(min(pts, W_QUALITY), 2), reasons


def _technical_score(
    rsi_14: float | None,
    trend: str | None,
    distance_from_52w_high_pct: float | None,
    sma_200: float | None,
    last_price: float | None,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    pts = 0.0

    if rsi_14 is not None:
        if rsi_14 <= 25:
            pts += 10
            reasons.append(
                f"RSI fortemente sobrevendido ({rsi_14:.0f}) — alta probabilidade de reversão técnica."
            )
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
            reasons.append(
                f"Queda de {drop_from_top:.1f}% em relação ao topo de 52 semanas — dip pronunciado."
            )
        elif drop_from_top >= 20:
            pts += 7
            reasons.append(f"Queda de {drop_from_top:.1f}% em relação ao topo de 52 semanas.")
        elif drop_from_top >= 10:
            pts += 4
            reasons.append(f"Queda moderada de {drop_from_top:.1f}% em relação ao topo.")
        else:
            pts += 1
            reasons.append(
                f"Ativo próximo ao topo de 52 semanas (queda de apenas {drop_from_top:.1f}%) — não é um dip evidente."
            )
    else:
        reasons.append("Histórico de 52 semanas indisponível.")

    if sma_200 is not None and last_price is not None:
        if last_price < sma_200:
            pts += 5
            reasons.append(
                f"Preço abaixo da SMA200 ({sma_200:.2f}) — zona historicamente de valor."
            )
        else:
            dist_pct = ((last_price - sma_200) / sma_200) * 100
            if dist_pct < 5:
                pts += 2
                reasons.append("Preço levemente acima da SMA200.")

    return round(min(pts, W_TECHNICAL), 2), reasons


def _dividend_score(
    dividend_yield: float | None,
    avg_dividend_5y: float | None,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    pts = 0.0

    if dividend_yield is None and avg_dividend_5y is None:
        reasons.append("Dados de dividendos indisponíveis — pontuação neutra aplicada.")
        return round(W_DIVIDEND * 0.3, 2), reasons

    if dividend_yield is not None and dividend_yield > 0:
        if dividend_yield >= 8:
            pts += 7
            reasons.append(
                f"DY atrativo: {dividend_yield:.1f}% — remuneração sólida enquanto espera valorização."
            )
        elif dividend_yield >= 5:
            pts += 5
            reasons.append(f"DY razoável: {dividend_yield:.1f}%.")
        elif dividend_yield >= 2:
            pts += 2
            reasons.append(
                f"DY baixo ({dividend_yield:.1f}%) — foco de crescimento, não dividendos."
            )
        else:
            reasons.append(f"DY muito baixo ({dividend_yield:.1f}%).")
    elif dividend_yield == 0:
        reasons.append("Sem dividendos recentes registrados.")

    if avg_dividend_5y is not None and avg_dividend_5y > 0:
        pts += 3
        reasons.append(f"Histórico de dividendos (média 5a: {avg_dividend_5y:.2f}).")

    return round(min(pts, W_DIVIDEND), 2), reasons


def _news_score(items: list) -> tuple[float, list[str]]:
    reasons: list[str] = []
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
        reasons.append(
            f"Maioria das notícias recentes é negativa ({neg}/{total}) — verifique os motivos da queda."
        )

    return round(pts, 2), reasons


def _crypto_score(
    rsi_14: float | None,
    distance_from_52w_high_pct: float | None,
    sma_200: float | None,
    last_price: float | None,
    news_items: list,
) -> tuple[float, float, float, list[str]]:
    """Scoring específico para cripto: foco em momentum técnico, distância do topo e sentimento.
    Retorna (technical_pts, news_pts, value_pts, reasons)."""
    reasons: list[str] = []

    tech_pts = 0.0
    if rsi_14 is not None:
        if rsi_14 <= 28:
            tech_pts += W_CRYPTO_TECHNICAL * 0.5
            reasons.append(f"RSI muito sobrevendido ({rsi_14:.0f}) — região de capitulação cripto.")
        elif rsi_14 <= 38:
            tech_pts += W_CRYPTO_TECHNICAL * 0.35
            reasons.append(f"RSI sobrevendido ({rsi_14:.0f}) — possível fundo de curto prazo.")
        elif rsi_14 <= 48:
            tech_pts += W_CRYPTO_TECHNICAL * 0.2
            reasons.append(f"RSI neutro-baixo ({rsi_14:.0f}).")
        elif rsi_14 >= 70:
            reasons.append(f"RSI sobrecomprado ({rsi_14:.0f}) — crypto não está em dip técnico.")
        else:
            tech_pts += W_CRYPTO_TECHNICAL * 0.1
    else:
        reasons.append("RSI indisponível para cripto.")

    if sma_200 is not None and last_price is not None:
        if last_price < sma_200 * 0.85:
            tech_pts += W_CRYPTO_TECHNICAL * 0.35
            reasons.append(
                "Preço significativamente abaixo da SMA200 — zona de desconto histórico em cripto."
            )
        elif last_price < sma_200:
            tech_pts += W_CRYPTO_TECHNICAL * 0.2
            reasons.append("Preço abaixo da SMA200 — zona de valor histórico.")
        else:
            reasons.append("Preço acima da SMA200 — não é um dip profundo.")

    tech_pts = round(min(tech_pts, W_CRYPTO_TECHNICAL), 2)

    news_pts = 0.0
    if not news_items:
        news_pts = W_CRYPTO_NEWS * 0.4
        reasons.append("Sem notícias recentes — sentimento neutro.")
    else:
        pos = sum(1 for i in news_items if i.sentiment == "positive")
        neg = sum(1 for i in news_items if i.sentiment == "negative")
        total = len(news_items)
        ratio = (pos - neg) / total if total > 0 else 0
        if ratio >= 0.4:
            news_pts = W_CRYPTO_NEWS
            reasons.append(f"Sentimento de mercado positivo ({pos}/{total} notícias positivas).")
        elif ratio >= 0:
            news_pts = W_CRYPTO_NEWS * 0.6
            reasons.append("Sentimento de mercado neutro a levemente positivo.")
        else:
            news_pts = W_CRYPTO_NEWS * 0.1
            reasons.append(f"Sentimento negativo ({neg}/{total}) — cautela elevada.")

    news_pts = round(min(news_pts, W_CRYPTO_NEWS), 2)

    value_pts = 0.0
    if distance_from_52w_high_pct is not None:
        drop = abs(distance_from_52w_high_pct)
        if drop >= 60:
            value_pts = W_CRYPTO_VALUE
            reasons.append(f"Queda de {drop:.0f}% do topo de 52 semanas — dip histórico cripto.")
        elif drop >= 40:
            value_pts = W_CRYPTO_VALUE * 0.75
            reasons.append(f"Queda de {drop:.0f}% do topo — dip pronunciado para cripto.")
        elif drop >= 25:
            value_pts = W_CRYPTO_VALUE * 0.5
            reasons.append(f"Queda de {drop:.0f}% do topo — correção moderada.")
        elif drop >= 10:
            value_pts = W_CRYPTO_VALUE * 0.2
            reasons.append(f"Queda de {drop:.0f}% — pequena correção.")
        else:
            reasons.append(f"Próximo do topo de 52 semanas (queda de {drop:.0f}%) — não é dip.")
    else:
        value_pts = W_CRYPTO_VALUE * 0.3
        reasons.append("Histórico de 52 semanas indisponível para cripto.")

    value_pts = round(min(value_pts, W_CRYPTO_VALUE), 2)

    return tech_pts, news_pts, value_pts, reasons


def compute_dip_analysis(
    margin_of_safety: float | None,
    roe: float | None,
    profit_margin: float | None,
    debt_to_equity: float | None,
    rsi_14: float | None,
    trend: str | None,
    distance_from_52w_high_pct: float | None,
    sma_200: float | None,
    last_price: float | None,
    dividend_yield: float | None,
    avg_dividend_5y: float | None,
    fair_price_consensus: float | None,
    current_price: float | None,
    news_items: list[NewsItem],
    news_sentiment_summary: str,
    asset_type: str = "stock",
) -> DipResult:
    all_reasons: list[str] = []

    is_crypto = asset_type == "crypto"

    if is_crypto:
        all_reasons.append(
            "Ativo classificado como cripto — análise usa perfil de momentum/sentimento (sem ROE, margem ou P/VP)."
        )
        t_pts, n_pts, v_pts, extra_reasons = _crypto_score(
            rsi_14, distance_from_52w_high_pct, sma_200, last_price, news_items
        )
        all_reasons.extend(extra_reasons)
        q_pts = 0.0
        d_pts = 0.0
        total = round(t_pts + n_pts + v_pts, 2)
        breakdown = DipScoreBreakdown(
            value_score=v_pts,
            quality_score=0.0,
            technical_score=t_pts,
            dividend_score=0.0,
            news_score=n_pts,
        )
    else:
        v_pts, v_reasons = _value_score(margin_of_safety)
        q_pts, q_reasons = _quality_score(roe, profit_margin, debt_to_equity)
        t_pts, t_reasons = _technical_score(
            rsi_14, trend, distance_from_52w_high_pct, sma_200, last_price
        )
        d_pts, d_reasons = _dividend_score(dividend_yield, avg_dividend_5y)
        n_pts, n_reasons = _news_score(news_items)

        all_reasons.extend(v_reasons)
        all_reasons.extend(q_reasons)
        all_reasons.extend(t_reasons)
        all_reasons.extend(d_reasons)
        all_reasons.extend(n_reasons)

        total = round(v_pts + q_pts + t_pts + d_pts + n_pts, 2)
        breakdown = DipScoreBreakdown(
            value_score=v_pts,
            quality_score=q_pts,
            technical_score=t_pts,
            dividend_score=d_pts,
            news_score=n_pts,
        )

    oportunidade_threshold = 55 if is_crypto else 68
    armadilha_threshold = 35 if is_crypto else 42

    if total >= oportunidade_threshold:
        verdict = "OPORTUNIDADE"
        verdict_label = "Oportunidade na baixa" if not is_crypto else "Zona de acumulação (cripto)"
        confidence = min(1.0, total / 100)
    elif total >= armadilha_threshold:
        verdict = "NEUTRO"
        verdict_label = "Posição neutra — aguardar"
        confidence = 0.5
    else:
        verdict = "ARMADILHA"
        verdict_label = (
            "Armadilha — cuidado com o value trap"
            if not is_crypto
            else "Possível queda adicional — cautela máxima"
        )
        confidence = min(1.0, (100 - total) / 100)

    drop_52w: float | None = None
    if distance_from_52w_high_pct is not None:
        drop_52w = round(abs(distance_from_52w_high_pct), 2)

    drop_fair: float | None = None
    if fair_price_consensus and current_price and fair_price_consensus > 0:
        drop_fair = round((fair_price_consensus - current_price) / fair_price_consensus * 100, 2)

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
