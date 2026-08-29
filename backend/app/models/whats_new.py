from pydantic import BaseModel, Field


class WhatsNewItem(BaseModel):
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
    action: str | None = None
    action_label: str | None = None


class WhatsNewResponse(BaseModel):
    items: list[WhatsNewItem] = Field(default_factory=list)
    since: float | None = Field(
        None, description="Timestamp do estado anterior usado na comparação"
    )
    days_since: float | None = Field(None, description="Dias entre o estado anterior e agora")
    generated_at: float = 0.0
