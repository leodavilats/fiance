from __future__ import annotations

import time

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    picture: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    onboarded_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Lápide da exclusão. A linha sobrevive anonimizada porque é ela que guarda
    # o corte de sessão: apagá-la faria um token ainda vivo ressuscitar a conta
    # na primeira escrita.
    deleted_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class PortfolioPosition(Base):
    __tablename__ = "portfolio"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    quantity: Mapped[float] = mapped_column(Float)
    avg_price: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String, default="auto")
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshot"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    captured_at: Mapped[float] = mapped_column(Float, primary_key=True)
    total_invested: Mapped[float] = mapped_column(Float)
    total_current: Mapped[float] = mapped_column(Float)
    total_pnl: Mapped[float] = mapped_column(Float)
    total_pnl_pct: Mapped[float] = mapped_column(Float)


class WatchlistItemDb(Base):
    __tablename__ = "watchlist"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    note: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[float] = mapped_column(Float)


class GoalDb(Base):
    __tablename__ = "goals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    category: Mapped[str] = mapped_column(String, primary_key=True)
    target_pct: Mapped[float] = mapped_column(Float)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    deadline: Mapped[str | None] = mapped_column(String, nullable=True)


class SectorGoalDb(Base):
    __tablename__ = "sector_goals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    sector: Mapped[str] = mapped_column(String, primary_key=True)
    target_pct: Mapped[float] = mapped_column(Float)


class PreferencesDb(Base):
    __tablename__ = "preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    cash_available: Mapped[float] = mapped_column(Float, default=0)
    passive_income_goal: Mapped[float | None] = mapped_column(Float, nullable=True)
    desired_yield_stock: Mapped[float] = mapped_column(Float, default=0.06)
    desired_yield_fii: Mapped[float] = mapped_column(Float, default=0.10)
    desired_yield_bdr: Mapped[float] = mapped_column(Float, default=0.04)
    desired_yield_etf: Mapped[float] = mapped_column(Float, default=0.04)
    notify_price_alerts: Mapped[bool] = mapped_column(default=True)
    opportunities_frequency: Mapped[str] = mapped_column(String, default="weekly")
    risk_profile: Mapped[str] = mapped_column(String, default="moderate")
    #: Apetite por informação na tela, não acessibilidade de contraste.
    #: Fica na conta e não no navegador porque acompanha a pessoa, não o
    #: aparelho — quem lê tabela densa lê densa em qualquer tela.
    density: Mapped[str] = mapped_column(String, default="comfortable")
    preferred_categories: Mapped[str] = mapped_column(String, default="")
    preferred_sectors: Mapped[str] = mapped_column(String, default="")
    excluded_tickers: Mapped[str] = mapped_column(String, default="")
    last_digest_sent_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)


class ClosedTradeDb(Base):
    __tablename__ = "closed_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    quantity: Mapped[float] = mapped_column(Float)
    avg_price: Mapped[float] = mapped_column(Float)
    sell_price: Mapped[float] = mapped_column(Float)
    gross_profit: Mapped[float] = mapped_column(Float)
    ir_rate: Mapped[float] = mapped_column(Float)
    ir_amount: Mapped[float] = mapped_column(Float)
    net_profit: Mapped[float] = mapped_column(Float)
    loss_offset_used: Mapped[float] = mapped_column(Float, default=0.0)
    taxable_profit: Mapped[float] = mapped_column(Float, default=0.0)
    loss_compensable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sold_at: Mapped[float] = mapped_column(Float)
    created_at: Mapped[float] = mapped_column(Float)


class NotifiedOpportunityDb(Base):
    __tablename__ = "notified_opportunities"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    notified_at: Mapped[float] = mapped_column(Float)


class DeviceTokenDb(Base):
    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    platform: Mapped[str] = mapped_column(String, default="android")
    created_at: Mapped[float] = mapped_column(Float)


class PriceAlertDb(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String)
    condition: Mapped[str] = mapped_column(String)
    target_price: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    triggered_at: Mapped[float | None] = mapped_column(Float, nullable=True)


class FixedIncomePositionDb(Base):
    """Renda fixa como entidade de primeira classe."""

    __tablename__ = "fixed_income_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    nome: Mapped[str] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)
    valor_investido: Mapped[float] = mapped_column(Float)
    taxa: Mapped[float] = mapped_column(Float)
    tipo_taxa: Mapped[str] = mapped_column(String, default="pre_fixado")
    percentual_cdi: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_aplicacao: Mapped[str] = mapped_column(String)
    vencimento: Mapped[str | None] = mapped_column(String, nullable=True)
    liquidez: Mapped[str] = mapped_column(String, default="no_vencimento")
    isento_ir: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    oculto: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class JobLockDb(Base):
    """Lock cooperativo para jobs de background."""

    __tablename__ = "job_locks"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    holder: Mapped[str] = mapped_column(String)
    acquired_at: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[float] = mapped_column(Float)


class DividendReceivedDb(Base):
    """Provento efetivamente creditado."""

    __tablename__ = "dividends_received"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String, index=True)
    paid_at: Mapped[str] = mapped_column(String, index=True)
    amount: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String, default="dividendo")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[float] = mapped_column(Float)


class FollowedSuggestionDb(Base):
    """Sugestão que o usuário declarou ter seguido."""

    __tablename__ = "followed_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, default="opportunities")
    action: Mapped[str] = mapped_column(String, default="comprar")
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    followed_on: Mapped[str] = mapped_column(String, index=True)
    score_at_suggestion: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict_at_suggestion: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)


class RevokedTokenDb(Base):
    """Denylist de sessão por `jti`.

    Guarda só o identificador do token, nunca o token. `expires_at` é o `exp`
    do próprio token: passado ele, a entrada não tem mais função e é varrida.
    """

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    revoked_at: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[float] = mapped_column(Float, index=True)


class SessionCutDb(Base):
    """Corte de revogação em bloco: token emitido antes disto não vale mais.

    Tabela própria, e não coluna em `users`, porque o corte precisa existir para
    quem ainda não tem linha de titular — conta criada implicitamente por escrita
    — e precisa sobreviver à anonimização da conta.
    """

    __tablename__ = "session_cuts"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    cut_at: Mapped[float] = mapped_column(Float, nullable=False)


class UsageCounterDb(Base):
    """Contador por usuário, recurso e janela.

    Uma primitiva só para dois usos que sempre foram o mesmo problema: teto de
    abuso (rate limiting por rota e minuto) e teto de plano (5 páginas de ativo
    por mês). A granularidade mora em `window_key` — `2026-08-27T14:35` para o
    minuto, `2026-08` para o mês calendário brasileiro.
    """

    __tablename__ = "usage_counters"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    resource: Mapped[str] = mapped_column(String, primary_key=True)
    window_key: Mapped[str] = mapped_column(String, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, index=True)
    updated_at: Mapped[float] = mapped_column(Float)


class ProductEventDb(Base):
    """Evento de produto — funil, ativação e retenção.

    Nenhum valor monetário, ticker ou posição entra aqui: o dicionário de
    eventos é fechado e as propriedades passam por uma lista de chaves
    permitidas antes de gravar.
    """

    __tablename__ = "product_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    occurred_at: Mapped[float] = mapped_column(Float, index=True)
    day: Mapped[str] = mapped_column(String, index=True)
    platform: Mapped[str] = mapped_column(String, default="web")
    props: Mapped[str] = mapped_column(String, default="{}")


Index("ix_product_events_user_name", ProductEventDb.user_id, ProductEventDb.name)


class InstrumentDb(Base):
    """Identidade interna do ativo, separada do ticker.

    A B3 reaproveita código: um ticker aposentado pode voltar em outra empresa
    anos depois. Somar os dois históricos daria preço médio de duas companhias
    diferentes — e preço médio errado é IR errado. Por isso o símbolo tem
    janela de validade e o lançamento aponta para o instrumento, não para o
    texto do ticker.
    """

    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String, index=True)
    asset_type: Mapped[str] = mapped_column(String, default="br_stock")
    name: Mapped[str] = mapped_column(String, default="")
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    #: Janela em que este símbolo pertenceu a este instrumento, em dia BRT.
    #: `valid_to` nulo significa "é o dono atual do código".
    valid_from: Mapped[str] = mapped_column(String, default="1900-01-01")
    valid_to: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


class TransactionDb(Base):
    """Um lançamento do livro-razão. É a fonte de verdade da carteira."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    instrument_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    #: Denormalizado para leitura e para o caso de o instrumento não ter sido
    #: resolvido ainda. A identidade que vale é `instrument_id`.
    symbol: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    fees: Mapped[float] = mapped_column(Float, default=0.0)
    ratio_from: Mapped[float] = mapped_column(Float, default=1.0)
    ratio_to: Mapped[float] = mapped_column(Float, default=1.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    #: Dia da operação no fuso brasileiro. É data, não instante: nota de
    #: corretagem tem dia, não hora.
    traded_on: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, default="manual")
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[float] = mapped_column(Float)


Index("ix_transactions_user_symbol", TransactionDb.user_id, TransactionDb.symbol)
Index("ix_transactions_user_traded_on", TransactionDb.user_id, TransactionDb.traded_on)


class AuditLogDb(Base):
    """Registro append-only do que aconteceu na conta.

    Responde ao usuário e ao auditor com a mesma frase. Não tem update nem
    delete na camada de escrita — só a exclusão de conta o remove.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    entity: Mapped[str] = mapped_column(String, default="")
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String, default="")
    detail: Mapped[str] = mapped_column(String, default="{}")
    occurred_at: Mapped[float] = mapped_column(Float, index=True)


class SubscriptionDb(Base):
    """A assinatura, com **preço e plano versionados**.

    Preço travado de fundador é promessa pública, então tem que ser dado e não
    convenção: `price_cents` guarda o que a pessoa contratou e `locked` diz que
    um reajuste da tabela não a alcança. Sem isso, a única forma de cumprir a
    promessa seria lembrar dela — e reajuste é exatamente o momento em que
    ninguém lembra.

    `provider` e `external_id` existem desde já porque o direito mora aqui e o
    canal é detalhe: trocar de gateway não pode exigir migrar assinante.
    """

    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)

    plan_code: Mapped[str] = mapped_column(String, default="free")
    status: Mapped[str] = mapped_column(String, default="none", index=True)

    #: O que a pessoa paga, em centavos. Nunca derivado da tabela vigente.
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String, default="BRL")
    interval: Mapped[str] = mapped_column(String, default="monthly")

    #: Reajuste da tabela não alcança quem está travado.
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_at: Mapped[float | None] = mapped_column(Float, nullable=True)

    trial_started_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    trial_ends_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_period_end: Mapped[float | None] = mapped_column(Float, nullable=True)
    cancelled_at: Mapped[float | None] = mapped_column(Float, nullable=True)

    provider: Mapped[str] = mapped_column(String, default="none")
    external_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)


class ProcessedWebhookDb(Base):
    """Eventos de gateway já processados, por id do provedor.

    Webhook chega mais de uma vez por desenho — o provedor reenvia até receber
    200. Conceder direito duas vezes é o modo de falha óbvio; a tabela é o que
    torna o processamento idempotente sem depender de o gateway se comportar.
    """

    __tablename__ = "processed_webhooks"

    provider: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    processed_at: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(String, default="")
