from pydantic import BaseModel, Field

from .enums import AssetType


class DipScanItem(BaseModel):
    symbol: str
    name: str | None = None
    asset_type: AssetType
    sector: str | None = None
    price: float | None = None
    as_of: float | None = Field(
        default=None, description="Momento da cotação, em segundos desde a época."
    )
    drop_from_52w_high_pct: float = Field(
        ..., description="Queda do preço desde a máxima de 52 semanas, em percentual positivo."
    )
    verdict: str = Field(..., description="O mesmo veredito da leitura de valor do ativo.")
    label: str = Field(..., description="A etiqueta da leitura de valor, que descreve posição.")
    basis: str = "none"
    confidence_label: str = "baixa"
    band_quality: str = "sem_faixa"
    fair_low: float | None = None
    fair_high: float | None = None
    principal_value: float | None = None
    margin_of_safety: float | None = None
    dividend_yield: float | None = None
    top_reason: str = Field(
        "", description="A primeira razão da leitura de valor: onde o preço está contra a faixa."
    )


class DipScannerResponse(BaseModel):
    items: list[DipScanItem]
    scanned: int
    universe_used: list[str]
    min_drop_pct: float = Field(
        ..., description="Queda mínima desde a máxima de 52 semanas para entrar no recorte."
    )
    disclaimer: str = "Conteúdo educativo. Não constitui recomendação formal de investimento."
