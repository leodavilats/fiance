from pydantic import BaseModel, Field


class Preferences(BaseModel):
    passive_income_goal: float | None = None
    desired_yield_stock: float = 0.06
    desired_yield_fii: float = 0.10
    desired_yield_bdr: float = 0.04
    desired_yield_etf: float = 0.04
    notify_price_alerts: bool = True
    notify_new_opportunities: bool = True
    updated_at: float | None = None


class PreferencesRequest(BaseModel):
    passive_income_goal: float | None = Field(None, ge=0)
    desired_yield_stock: float | None = Field(None, gt=0, le=1)
    desired_yield_fii: float | None = Field(None, gt=0, le=1)
    desired_yield_bdr: float | None = Field(None, gt=0, le=1)
    desired_yield_etf: float | None = Field(None, gt=0, le=1)
    notify_price_alerts: bool | None = None
    notify_new_opportunities: bool | None = None
