from typing import List, Optional
from pydantic import BaseModel


class WatchlistItem(BaseModel):
    ticker: str
    note: str = ""
    created_at: Optional[float] = None


class WatchlistRequest(BaseModel):
    items: List[WatchlistItem]
