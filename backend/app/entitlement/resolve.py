"""De assinatura + trial + flag para direitos.

Um lugar só decide o que a pessoa pode. A checagem é **do servidor** porque
cliente adulterado não pode virar assinante, e é centralizada porque a régua vai
mudar: a composição do plano é a decisão mais provável de ser revista depois dos
primeiros experimentos.

**Enquanto a flag estiver desligada, todo mundo tem tudo.** É o que permite o
código de cobrança viver em produção antes de a cobrança existir — ligar passa a
ser decisão, não entrega. E é a razão de `entitlements_enabled` existir em vez
de o módulo ser adicionado depois: adicionar depois significa descobrir todos os
pontos de gate durante o lançamento.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.database import db_session
from app.models.db_models import SubscriptionDb

from . import meter
from .plans import Feature, Plan, allows, limit_for, rule_for

#: Duração do trial. Começa na **primeira posição salva**, não no cadastro:
#: trial que expira antes de a pessoa ter uma carteira é trial desperdiçado.
TRIAL_DAYS = 14

#: Situações em que a **assinatura** dá direito.
#:
#: `trialing` fica de fora de propósito. O status é carimbado quando o trial
#: começa e ninguém o reescreve quando ele acaba — se ele concedesse direito,
#: todo mundo viraria Premium permanente no dia 15. Quem decide o trial é
#: `trial_ends_at`, que tem data.
#:
#: `past_due` concede porque cobrança falhada é problema de cartão, não de
#: intenção: cortar o acesso na primeira falha é como se perde o cliente que
#: só precisava atualizar o cartão.
ACTIVE_STATUSES = frozenset({"active", "past_due"})


@dataclass
class Entitlements:
    plan: Plan
    #: `True` quando a régua está desligada — todo mundo tem tudo.
    unrestricted: bool = False
    trial_ends_at: float | None = None
    in_trial: bool = False
    #: Fim do Premium concedido sem pagamento (crédito de indicação).
    credited_until: float | None = None
    price_cents: int = 0
    locked_price: bool = False
    features: dict[str, bool] = field(default_factory=dict)
    limits: dict[str, int | None] = field(default_factory=dict)

    @property
    def days_left_in_trial(self) -> int | None:
        if not self.in_trial or self.trial_ends_at is None:
            return None
        return max(0, int((self.trial_ends_at - time.time()) // 86400))

    def as_dict(self) -> dict:
        return {
            "plan": self.plan.value,
            "unrestricted": self.unrestricted,
            "in_trial": self.in_trial,
            "trial_ends_at": self.trial_ends_at,
            "trial_days_left": self.days_left_in_trial,
            "credited_until": self.credited_until,
            "price_cents": self.price_cents,
            "locked_price": self.locked_price,
            "features": dict(self.features),
            "limits": dict(self.limits),
        }


@dataclass(frozen=True)
class _Snapshot:
    """Os campos da assinatura, já fora da sessão.

    Devolver a linha do ORM daqui a deixaria destacada assim que o `with`
    fechasse, e o primeiro acesso a atributo estouraria `DetachedInstanceError`
    — em produção, no meio da resolução de direitos.
    """

    status: str
    trial_ends_at: float | None
    credited_until: float | None
    current_period_end: float | None
    price_cents: int
    locked: bool


def _subscription(user_id: str) -> _Snapshot | None:
    with db_session() as session:
        row = session.get(SubscriptionDb, user_id)
        if row is None:
            return None
        return _Snapshot(
            status=row.status,
            trial_ends_at=row.trial_ends_at,
            credited_until=row.credited_until,
            current_period_end=row.current_period_end,
            price_cents=row.price_cents,
            locked=bool(row.locked),
        )


def resolve(user_id: str, now: float | None = None) -> Entitlements:
    """Os direitos correntes do usuário."""
    moment = now if now is not None else time.time()
    settings = get_settings()

    if not settings.entitlements_enabled:
        # Régua desligada: o produto inteiro é livre, e é assim que ele está
        # hoje. Nada de gate aparece, nada de contador roda.
        return Entitlements(
            plan=Plan.PREMIUM,
            unrestricted=True,
            features={f.value: True for f in Feature},
            limits={f.value: None for f in Feature},
        )

    row = _subscription(user_id)
    plan = Plan.FREE
    in_trial = False
    trial_ends_at = None
    credited_until = None
    price_cents = 0
    locked = False

    if row is not None:
        trial_ends_at = row.trial_ends_at
        credited_until = row.credited_until
        price_cents = row.price_cents
        locked = row.locked

        in_trial = trial_ends_at is not None and moment < trial_ends_at

        # Assinatura vencida **degrada**, não apaga: cancelar Premium não é
        # cancelar conta, e manter a carteira acessível evita pedido de
        # exclusão em massa no primeiro churn.
        assinatura_vale = row.status in ACTIVE_STATUSES and (
            row.current_period_end is None or moment < row.current_period_end
        )

        # Crédito de indicação concede como assinatura concede. Fica separado
        # do trial porque são coisas diferentes: o trial é uma vez na vida e o
        # crédito acumula — somá-los reabriria o trial de quem já o gastou.
        com_credito = row.credited_until is not None and moment < row.credited_until

        if assinatura_vale or in_trial or com_credito:
            plan = Plan.PREMIUM

    features = {f.value: allows(f, plan) for f in Feature}
    limits = {f.value: limit_for(f, plan) for f in Feature}

    return Entitlements(
        plan=plan,
        trial_ends_at=trial_ends_at,
        in_trial=in_trial,
        credited_until=credited_until,
        price_cents=price_cents,
        locked_price=locked,
        features=features,
        limits=limits,
    )


@dataclass
class Decision:
    """Resposta a 'esta pessoa pode usar isto agora?'."""

    allowed: bool
    feature: Feature
    plan: Plan
    reason: str = ""
    limit: int | None = None
    used: int = 0
    #: `True` quando o bloqueio é de teto e não de plano — a mensagem muda:
    #: "acabou este mês" pede espera ou upgrade; "não está no seu plano" só
    #: pede upgrade.
    limit_reached: bool = False

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "feature": self.feature.value,
            "plan": self.plan.value,
            "required_plan": rule_for(self.feature).min_plan.value,
            "reason": self.reason,
            "limit": self.limit,
            "used": self.used,
            "limit_reached": self.limit_reached,
        }


def check(feature: Feature, user_id: str, cost: int = 0) -> Decision:
    """Avalia sem consumir. `cost=1` consome quando permitido.

    Separar avaliar de consumir importa: a tela pergunta "posso?" para decidir
    se mostra o gate, e perguntar não pode gastar a cota de quem só passou por
    ali.
    """
    direitos = resolve(user_id)

    if direitos.unrestricted:
        return Decision(True, feature, direitos.plan)

    regra = rule_for(feature)

    if not allows(feature, direitos.plan):
        return Decision(
            allowed=False,
            feature=feature,
            plan=direitos.plan,
            reason=regra.rationale or "Disponível no plano Premium.",
        )

    limite = limit_for(feature, direitos.plan)
    if limite is None:
        if cost:
            meter.consume(user_id, feature, amount=cost, monthly=regra.monthly)
        return Decision(True, feature, direitos.plan, limit=None)

    usado = meter.used(user_id, feature, monthly=regra.monthly)

    if usado + cost > limite:
        return Decision(
            allowed=False,
            feature=feature,
            plan=direitos.plan,
            reason=(f"Você usou {usado} de {limite} {regra.unit} do plano {direitos.plan.value}."),
            limit=limite,
            used=usado,
            limit_reached=True,
        )

    if cost:
        meter.consume(user_id, feature, amount=cost, monthly=regra.monthly)

    return Decision(True, feature, direitos.plan, limit=limite, used=usado + cost)
