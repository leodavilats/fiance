from pydantic import BaseModel, Field


class Preferences(BaseModel):
    cash_available: float = 0.0
    updated_at: float | None = None


class PreferencesRequest(BaseModel):
    cash_available: float = Field(0, ge=0)
