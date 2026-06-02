from pydantic import BaseModel, Field

from .enums import Liquidez, RendaFixaType, TaxType


class RendaFixaAsset(BaseModel):
    tipo: RendaFixaType
    valor_investido: float = Field(..., gt=0, description="Valor a investir em R$")
    taxa: float = Field(..., gt=0, description="Taxa anual em % (ex.: 12.5 para 12.5% a.a.)")
    prazo_meses: int = Field(..., gt=0, description="Prazo em meses")
    tipo_taxa: TaxType = TaxType.pre_fixado
    percentual_cdi: float | None = Field(
        None, gt=0, description="% do CDI para pós-fixados (ex.: 110 para 110% CDI)"
    )
    liquidez: Liquidez = Liquidez.no_vencimento
    nome: str | None = Field(None, description="Nome / banco emissor (opcional)")
    isento_ir: bool | None = Field(None, description="Se None, detecta automaticamente pelo tipo")


class IrBreakdown(BaseModel):
    aliquota_pct: float
    valor_ir: float
    prazo_dias: int


class RendaFixaAnalysisResult(BaseModel):
    tipo: str
    nome: str | None
    valor_investido: float
    valor_bruto: float
    rendimento_bruto: float
    ir: IrBreakdown
    valor_liquido: float
    rendimento_liquido: float
    taxa_liquida_aa: float
    taxa_equivalente_cdi_pct: float | None
    isento_ir: bool
    liquidez: str
    prazo_meses: int
    melhor_opcao: bool = False


class RendaFixaCompareRequest(BaseModel):
    ativos: list[RendaFixaAsset] = Field(..., min_length=1)
    cdi_anual: float | None = Field(
        None, description="CDI anual atual em % (se None usa valor padrão)"
    )
    selic_anual: float | None = Field(
        None, description="Selic anual atual em % (se None usa valor padrão)"
    )


class RendaFixaCompareResponse(BaseModel):
    resultados: list[RendaFixaAnalysisResult]
    cdi_referencia: float
    selic_referencia: float
    melhor_opcao_index: int


class ReferenceRates(BaseModel):
    cdi_anual: float
    selic_anual: float
    ipca_anual: float
    source: str = "estimativa"
