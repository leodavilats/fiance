from typing import Optional
from pydantic import BaseModel, Field


class Preferences(BaseModel):
    cash_available: float = 0.0
    desired_yield: float = 0.06
    updated_at: Optional[float] = None


class PreferencesRequest(BaseModel):
    cash_available: float = Field(0, ge=0)
    desired_yield: float = Field(0.06, gt=0, le=0.30)
