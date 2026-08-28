"""O funil, calculado — porque funil que ninguém vê não é consultado.

Seis perguntas, uma métrica cada, com a meta do ano 1 ao lado. As metas vivem
aqui e não numa planilha para que a distância entre o real e o alvo apareça na
mesma resposta que o número.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

from app.core import events
from app.storage import event_store

DAY = 86400.0


@dataclass
class FunnelMetric:
    question: str
    metric: str
    value: float | None
    target: float | None
    unit: str
    numerator: int
    denominator: int
    detail: str

    def as_dict(self) -> dict:
        return asdict(self)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _retention(
    first_seen: dict[str, float],
    active_days: dict[str, set[str]],
    window_days: int,
    now: float,
) -> tuple[int, int]:
    """Quantos dos que entraram há ao menos `window_days` voltaram depois disso.

    Só entra na coorte quem já teve tempo de bater a janela — do contrário a
    retenção de 30 dias mediria gente com três dias de conta.
    """
    from app.core.brt import to_brt

    eligible = 0
    retained = 0
    for user_id, started in first_seen.items():
        if now - started < window_days * DAY:
            continue
        eligible += 1
        threshold = started + window_days * DAY
        days = active_days.get(user_id, set())
        if any(day >= to_brt(threshold).strftime("%Y-%m-%d") for day in days):
            retained += 1
    return retained, eligible


def build_funnel(days: int = 90, now: float | None = None) -> dict:
    moment = now if now is not None else time.time()
    since = moment - days * DAY

    first_seen = event_store.first_seen_by_user()
    active_days = event_store.active_days_by_user(since=since)

    signups = event_store.users_with("signup_completed")
    onboarded = event_store.users_with("onboarding_completed")
    first_position = event_store.users_with("portfolio_first_position_added")
    four_assets = event_store.users_with("portfolio_reached_4_assets")
    base = signups or set(first_seen)

    aha_in_week = set()
    for name in events.AHA_EVENTS:
        for user_id, at in event_store.first_by_user(name).items():
            started = first_seen.get(user_id)
            if started is not None and at - started <= 7 * DAY:
                aha_in_week.add(user_id)

    paywall = event_store.users_with("paywall_viewed")
    trials = event_store.users_with("trial_started")
    upgrades = event_store.users_with("upgrade_started")
    subscribers = event_store.users_with("subscription_started")
    cancelled = event_store.users_with("subscription_cancelled")

    d7_num, d7_den = _retention(first_seen, active_days, 7, moment)
    d30_num, d30_den = _retention(first_seen, active_days, 30, moment)

    weekly = {u for u, ds in event_store.active_days_by_user(moment - 7 * DAY).items() if ds}
    monthly = {u for u, ds in event_store.active_days_by_user(moment - 30 * DAY).items() if ds}

    metrics = [
        FunnelMetric(
            question=events.QUESTION_ENTRY,
            metric="Conclusão do onboarding",
            value=_rate(len(onboarded), len(base)),
            target=0.60,
            unit="ratio",
            numerator=len(onboarded),
            denominator=len(base),
            detail="onboarding_completed sobre quem criou conta.",
        ),
        FunnelMetric(
            question=events.QUESTION_PORTFOLIO,
            metric="Ativação — primeira posição",
            value=_rate(len(first_position), len(base)),
            target=0.55,
            unit="ratio",
            numerator=len(first_position),
            denominator=len(base),
            detail="portfolio_first_position_added sobre quem criou conta.",
        ),
        FunnelMetric(
            question=events.QUESTION_PORTFOLIO,
            metric="Carteira legível — 4 ativos",
            value=_rate(len(four_assets), len(base)),
            target=0.35,
            unit="ratio",
            numerator=len(four_assets),
            denominator=len(base),
            detail="Mínimo para o veredito de risco ser emitido.",
        ),
        FunnelMetric(
            question=events.QUESTION_VALUE,
            metric="Primeiro aha na 1ª semana",
            value=_rate(len(aha_in_week), len(base)),
            target=0.40,
            unit="ratio",
            numerator=len(aha_in_week),
            denominator=len(base),
            detail="Qualquer um dos quatro eventos de aha em até 7 dias.",
        ),
        FunnelMetric(
            question=events.QUESTION_RETURN,
            metric="D7",
            value=_rate(d7_num, d7_den),
            target=0.40,
            unit="ratio",
            numerator=d7_num,
            denominator=d7_den,
            detail="Coorte com ao menos 7 dias de conta.",
        ),
        FunnelMetric(
            question=events.QUESTION_RETURN,
            metric="D30",
            value=_rate(d30_num, d30_den),
            target=0.25,
            unit="ratio",
            numerator=d30_num,
            denominator=d30_den,
            detail="Métrica-farol: é o portão G2.",
        ),
        FunnelMetric(
            question=events.QUESTION_RETURN,
            metric="WAU/MAU",
            value=_rate(len(weekly), len(monthly)),
            target=0.35,
            unit="ratio",
            numerator=len(weekly),
            denominator=len(monthly),
            detail="Frequência de uso dentro do mês.",
        ),
        FunnelMetric(
            question=events.QUESTION_LIMIT,
            metric="Prévia → trial",
            value=_rate(len(trials & paywall), len(paywall)),
            target=None,
            unit="ratio",
            numerator=len(trials & paywall),
            denominator=len(paywall),
            detail="Quem viu o gate e começou o trial. Meta: medir antes de fixar.",
        ),
        FunnelMetric(
            question=events.QUESTION_PAY,
            metric="Trial → pago",
            value=_rate(len(subscribers & trials), len(trials)),
            target=0.30,
            unit="ratio",
            numerator=len(subscribers & trials),
            denominator=len(trials),
            detail="Conversão do trial de 14 dias.",
        ),
        FunnelMetric(
            question=events.QUESTION_PAY,
            metric="Free → Premium",
            value=_rate(len(subscribers), len(base)),
            target=0.03,
            unit="ratio",
            numerator=len(subscribers),
            denominator=len(base),
            detail="Premissa do modelo financeiro: 3%.",
        ),
        FunnelMetric(
            question=events.QUESTION_PAY,
            metric="Churn acumulado",
            value=_rate(len(cancelled), len(subscribers)),
            target=0.06,
            unit="ratio",
            numerator=len(cancelled),
            denominator=len(subscribers),
            detail="Cancelamentos sobre assinaturas iniciadas. Alvo: abaixo de 6%.",
        ),
    ]

    return {
        "window_days": days,
        "generated_at": moment,
        "cohort_size": len(base),
        "metrics": [m.as_dict() for m in metrics],
        "upgrade_started": len(upgrades),
        "paywall_by_origin": event_store.counts_by_prop("paywall_viewed", "origin", since=since),
        "limit_by_feature": event_store.counts_by_prop("limit_reached", "feature", since=since),
        "event_counts": event_store.counts_by_name(since=since),
    }


def aha_correlation(now: float | None = None) -> list[dict]:
    """Cada evento de aha contra D30 — qual deles é o momento de valor de fato.

    Não é uma regressão: é a comparação de retenção entre quem bateu o evento na
    primeira semana e quem não bateu. Com 60 dias de coorte, é o suficiente para
    escolher em torno de qual evento montar o onboarding.
    """
    moment = now if now is not None else time.time()
    first_seen = event_store.first_seen_by_user()
    active_days = event_store.active_days_by_user(moment - 400 * DAY)

    from app.core.brt import to_brt

    def retained_d30(user_id: str, started: float) -> bool:
        threshold = to_brt(started + 30 * DAY).strftime("%Y-%m-%d")
        return any(day >= threshold for day in active_days.get(user_id, set()))

    eligible = {u: s for u, s in first_seen.items() if moment - s >= 30 * DAY}

    out = []
    for name in events.AHA_EVENTS:
        by_user = event_store.first_by_user(name)
        hit, hit_ret, miss, miss_ret = 0, 0, 0, 0
        for user_id, started in eligible.items():
            at = by_user.get(user_id)
            reached = at is not None and at - started <= 7 * DAY
            if reached:
                hit += 1
                hit_ret += 1 if retained_d30(user_id, started) else 0
            else:
                miss += 1
                miss_ret += 1 if retained_d30(user_id, started) else 0

        with_rate = _rate(hit_ret, hit)
        without_rate = _rate(miss_ret, miss)
        out.append(
            {
                "event": name,
                "cohort_with": hit,
                "cohort_without": miss,
                "d30_with": with_rate,
                "d30_without": without_rate,
                "lift": (
                    round(with_rate - without_rate, 4)
                    if with_rate is not None and without_rate is not None
                    else None
                ),
            }
        )

    return sorted(out, key=lambda row: (row["lift"] is None, -(row["lift"] or 0)))
