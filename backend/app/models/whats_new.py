from pydantic import BaseModel, Field


class WhatsNewItem(BaseModel):
    """Uma linha de "o que mudou desde a sua última visita".

    O produto calculava saúde de carteira, gaps de alocação, vereditos, IR
    realizado e sugestões de redução — e nenhuma tela respondia a pergunta que
    o usuário tem ao abrir o app. Cada item aqui carrega a ação que fecha o
    ciclo, em vez de só informar.
    """

    kind: str = Field(
        ...,
        description=(
            "patrimony | verdict_change | allocation | maturity | new_opportunity | tax | empty"
        ),
    )
    severity: str = Field("info", description="info | warning | critical | positive")
    title: str
    detail: str
    ticker: str | None = None
    # Ação sugerida, no vocabulário da UI: analyze | sell | rebalance |
    # fixed_income | market | goals
    action: str | None = None
    action_label: str | None = None


class WhatsNewResponse(BaseModel):
    items: list[WhatsNewItem] = Field(default_factory=list)
    since: float | None = Field(
        None, description="Timestamp do estado anterior usado na comparação"
    )
    days_since: float | None = Field(None, description="Dias entre o estado anterior e agora")
    generated_at: float = 0.0
