from pydantic import BaseModel, Field


class Preferences(BaseModel):
    cash_available: float = 0.0
    passive_income_goal: float | None = None
    updated_at: float | None = None


class PreferencesRequest(BaseModel):
    cash_available: float = Field(0, ge=0)
    passive_income_goal: float | None = Field(None, ge=0)
