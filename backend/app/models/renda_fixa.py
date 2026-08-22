from datetime import date

from pydantic import BaseModel, Field, field_validator

from .enums import Liquidez, RendaFixaType, TaxType


class RendaFixaAsset(BaseModel):
    tipo: RendaFixaType
    valor_investido: float = Field(..., gt=0, le=1e11, description="Valor a investir em R$")
    taxa: float = Field(
        ...,
        gt=0,
        le=100,
        description="Taxa anual em % (pré-fixado) ou taxa real a.a. (IPCA+/híbrido)",
    )
    prazo_meses: int = Field(..., gt=0, le=600, description="Prazo em meses")
    tipo_taxa: TaxType = TaxType.pre_fixado
    percentual_cdi: float | None = Field(
        None, gt=0, le=500, description="% do CDI para pós-fixados (ex.: 110 para 110% CDI)"
    )
    liquidez: Liquidez = Liquidez.no_vencimento
    nome: str | None = Field(None, max_length=120, description="Nome / banco emissor (opcional)")
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
    taxa_anual_efetiva_pct: float = 0.0
    taxa_equivalente_cdi_pct: float | None = None
    pct_cdi_bruto_equivalente: float | None = None
    isento_ir: bool
    liquidez: str
    prazo_meses: float
    melhor_opcao: bool = False


class RendaFixaCompareRequest(BaseModel):
    ativos: list[RendaFixaAsset] = Field(..., min_length=1, max_length=20)
    cdi_anual: float | None = Field(
        None, gt=0, le=100, description="CDI anual atual em % (se None usa a taxa do BCB)"
    )
    selic_anual: float | None = Field(
        None, gt=0, le=100, description="Selic anual atual em % (se None usa a taxa do BCB)"
    )
    ipca_anual: float | None = Field(
        None, gt=-50, le=100, description="IPCA anual em % (se None usa a taxa do BCB)"
    )


class RendaFixaCompareResponse(BaseModel):
    resultados: list[RendaFixaAnalysisResult]
    cdi_referencia: float
    selic_referencia: float
    ipca_referencia: float = 0.0
    melhor_opcao_index: int
    melhor_opcao_motivo: str = ""
    fonte_taxas: str = "estimativa"


class ReferenceRates(BaseModel):
    cdi_anual: float
    selic_anual: float
    ipca_anual: float
    source: str = "estimativa"


class FixedIncomeBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120, description="Nome / banco emissor")
    tipo: RendaFixaType
    valor_investido: float = Field(..., gt=0, le=1e11)
    taxa: float = Field(..., gt=0, le=100, description="% a.a. (pré) ou taxa real a.a. (IPCA+)")
    tipo_taxa: TaxType = TaxType.pre_fixado
    percentual_cdi: float | None = Field(None, gt=0, le=500)
    data_aplicacao: date
    vencimento: date | None = None
    liquidez: Liquidez = Liquidez.no_vencimento
    isento_ir: bool | None = None
    oculto: bool = Field(False, description="Exclui da soma da carteira sem apagar o registro")

    @field_validator("vencimento")
    @classmethod
    def _vencimento_depois_da_aplicacao(cls, v: date | None, info) -> date | None:
        aplicacao = info.data.get("data_aplicacao")
        if v is not None and aplicacao is not None and v <= aplicacao:
            raise ValueError("O vencimento precisa ser depois da data de aplicação.")
        return v


class FixedIncomeCreateRequest(FixedIncomeBase):
    pass


class FixedIncomeUpdateRequest(BaseModel):
    """Atualização parcial: só os campos enviados são gravados."""

    nome: str | None = Field(None, min_length=1, max_length=120)
    tipo: RendaFixaType | None = None
    valor_investido: float | None = Field(None, gt=0, le=1e11)
    taxa: float | None = Field(None, gt=0, le=100)
    tipo_taxa: TaxType | None = None
    percentual_cdi: float | None = Field(None, gt=0, le=500)
    data_aplicacao: date | None = None
    vencimento: date | None = None
    liquidez: Liquidez | None = None
    isento_ir: bool | None = None
    oculto: bool | None = None


class FixedIncomePosition(FixedIncomeBase):
    """Posição de renda fixa marcada a mercado pelo backend."""

    id: int

    valor_atual: float
    rendimento_acumulado: float
    rendimento_pct: float
    meses_decorridos: float
    taxa_anual_efetiva_pct: float
    yield_equivalente_pct: float

    valor_no_vencimento: float | None = None
    rendimento_no_vencimento: float | None = None
    dias_para_vencimento: int | None = None
    vencimento_proximo: bool = False


class FixedIncomeListResponse(BaseModel):
    items: list[FixedIncomePosition]
    total_investido: float
    total_atual: float
    total_rendimento: float
    rendimento_pct: float
    taxa_media_aa: float
    cdi_referencia: float
    fonte_taxas: str = "estimativa"
