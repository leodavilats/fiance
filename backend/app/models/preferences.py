from pydantic import BaseModel, Field

from .enums import AssetCategory, RiskProfile

OpportunitiesFrequency = str  # "off" | "daily" | "weekly" | "monthly"


class Preferences(BaseModel):
    # Push depende de um token de dispositivo, que só o app registra. A tela de
    # Configurações do web oferecia opportunities_frequency e
    # notify_price_alerts sem efeito algum para quem usa só o navegador; agora o
    # backend informa se há dispositivo registrado e a UI pode dizer a verdade.
    push_enabled: bool = False
    registered_devices: int = 0

    cash_available: float = 0.0
    passive_income_goal: float | None = None
    desired_yield_stock: float = 0.06
    desired_yield_fii: float = 0.10
    desired_yield_bdr: float = 0.04
    desired_yield_etf: float = 0.04
    notify_price_alerts: bool = True
    opportunities_frequency: OpportunitiesFrequency = "weekly"
    risk_profile: RiskProfile = RiskProfile.moderate
    preferred_categories: list[AssetCategory] = Field(default_factory=list)
    preferred_sectors: list[str] = Field(default_factory=list)
    excluded_tickers: list[str] = Field(default_factory=list)
    updated_at: float | None = None


class PreferencesRequest(BaseModel):
    """Só os campos enviados são gravados (ver api/preferences.py).

    `cash_available` faltava aqui — o resultado é que todo PUT /preferences
    reescrevia o caixa disponível com 0.0, e o usuário redigitava o valor a
    cada visita a Estratégia/Quick Invest.
    """

    cash_available: float | None = Field(None, ge=0)
    passive_income_goal: float | None = Field(None, ge=0)
    desired_yield_stock: float | None = Field(None, gt=0, le=1)
    desired_yield_fii: float | None = Field(None, gt=0, le=1)
    desired_yield_bdr: float | None = Field(None, gt=0, le=1)
    desired_yield_etf: float | None = Field(None, gt=0, le=1)
    notify_price_alerts: bool | None = None
    opportunities_frequency: OpportunitiesFrequency | None = None
    risk_profile: RiskProfile | None = None
    preferred_categories: list[AssetCategory] | None = Field(None, max_length=10)
    preferred_sectors: list[str] | None = Field(None, max_length=50)
    excluded_tickers: list[str] | None = Field(None, max_length=500)
