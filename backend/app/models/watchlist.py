from pydantic import BaseModel


class WatchlistItem(BaseModel):
    ticker: str
    note: str = ""
    created_at: float | None = None


class WatchlistRequest(BaseModel):
    items: list[WatchlistItem]
