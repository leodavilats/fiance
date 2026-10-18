from pydantic import BaseModel, Field


class InboxItem(BaseModel):
    id: int
    kind: str = Field(
        description=(
            "patrimony | verdict_change | allocation | maturity | new_opportunity | tax | "
            "price_alert | digest"
        )
    )
    severity: str = Field(description="info | warning | critical | positive")
    title: str
    detail: str
    ticker: str | None = None
    action: str | None = None
    action_label: str | None = None
    created_at: float = Field(description="Quando o aviso entrou na caixa, em segundos.")
    read_at: float | None = None


class InboxPage(BaseModel):
    items: list[InboxItem] = Field(default_factory=list)
    unread: int = 0
    next_cursor: str | None = None
    has_more: bool = False


class InboxUnread(BaseModel):
    unread: int


class InboxReadRequest(BaseModel):
    ids: list[int] | None = Field(
        default=None,
        max_length=500,
        description="Avisos a marcar como lidos. Omitido, marca todos.",
    )
