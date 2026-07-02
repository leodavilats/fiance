from __future__ import annotations

from app.collectors.rates import get_rates
from app.models.enums import RendaFixaType, TaxType
from app.models.renda_fixa import (
    IrBreakdown,
    ReferenceRates,
    RendaFixaAnalysisResult,
    RendaFixaAsset,
    RendaFixaCompareRequest,
    RendaFixaCompareResponse,
)

DEFAULT_CDI_ANUAL = 14.40
DEFAULT_SELIC_ANUAL = 14.40
DEFAULT_IPCA_ANUAL = 5.0


ISENTOS_IR = {
    RendaFixaType.lci,
    RendaFixaType.lca,
    RendaFixaType.cri,
    RendaFixaType.cra,
}


def _aliquota_ir(prazo_dias: int) -> float:
    if prazo_dias <= 180:
        return 0.225
    elif prazo_dias <= 360:
        return 0.20
    elif prazo_dias <= 720:
        return 0.175
    else:
        return 0.15


def _taxa_equivalente_periodo(taxa_anual_pct: float, meses: int) -> float:
    taxa_anual = taxa_anual_pct / 100.0
    return (1 + taxa_anual) ** (meses / 12.0) - 1


def _taxa_cdi_periodo(cdi_anual: float, percentual_cdi: float, meses: int) -> float:
    taxa_cdi = (1 + cdi_anual / 100.0) ** (meses / 12.0) - 1
    return (1 + taxa_cdi) ** (percentual_cdi / 100.0) - 1


def analyze_one(
    ativo: RendaFixaAsset,
    cdi_anual: float = DEFAULT_CDI_ANUAL,
    selic_anual: float = DEFAULT_SELIC_ANUAL,
) -> RendaFixaAnalysisResult:
    prazo_dias = int(ativo.prazo_meses * 30.44)

    isento = ativo.isento_ir
    if isento is None:
        isento = ativo.tipo in ISENTOS_IR

    if ativo.tipo_taxa == TaxType.pos_fixado and ativo.percentual_cdi:
        taxa_periodo = _taxa_cdi_periodo(cdi_anual, ativo.percentual_cdi, ativo.prazo_meses)
    else:
        taxa_periodo = _taxa_equivalente_periodo(ativo.taxa, ativo.prazo_meses)

    valor_bruto = ativo.valor_investido * (1 + taxa_periodo)
    rendimento_bruto = valor_bruto - ativo.valor_investido

    if isento:
        aliquota = 0.0
        valor_ir = 0.0
    else:
        aliquota = _aliquota_ir(prazo_dias)
        valor_ir = rendimento_bruto * aliquota

    rendimento_liquido = rendimento_bruto - valor_ir
    valor_liquido = ativo.valor_investido + rendimento_liquido

    if ativo.prazo_meses > 0:
        taxa_liq_periodo = rendimento_liquido / ativo.valor_investido
        taxa_liq_aa = ((1 + taxa_liq_periodo) ** (12.0 / ativo.prazo_meses) - 1) * 100
    else:
        taxa_liq_aa = 0.0

    taxa_cdi_periodo = _taxa_equivalente_periodo(cdi_anual * 0.85, ativo.prazo_meses)
    equiv_cdi_pct: float | None = None
    if taxa_cdi_periodo > 0:
        equiv_cdi_pct = round((taxa_liq_periodo / taxa_cdi_periodo) * 100, 2)

    return RendaFixaAnalysisResult(
        tipo=ativo.tipo.value,
        nome=ativo.nome,
        valor_investido=round(ativo.valor_investido, 2),
        valor_bruto=round(valor_bruto, 2),
        rendimento_bruto=round(rendimento_bruto, 2),
        ir=IrBreakdown(
            aliquota_pct=round(aliquota * 100, 2),
            valor_ir=round(valor_ir, 2),
            prazo_dias=prazo_dias,
        ),
        valor_liquido=round(valor_liquido, 2),
        rendimento_liquido=round(rendimento_liquido, 2),
        taxa_liquida_aa=round(taxa_liq_aa, 2),
        taxa_equivalente_cdi_pct=equiv_cdi_pct,
        isento_ir=isento,
        liquidez=ativo.liquidez.value,
        prazo_meses=ativo.prazo_meses,
    )


def compare_options(req: RendaFixaCompareRequest) -> RendaFixaCompareResponse:
    cdi = req.cdi_anual if req.cdi_anual else DEFAULT_CDI_ANUAL
    selic = req.selic_anual if req.selic_anual else DEFAULT_SELIC_ANUAL

    resultados: list[RendaFixaAnalysisResult] = [
        analyze_one(ativo, cdi, selic) for ativo in req.ativos
    ]

    melhor_idx = max(range(len(resultados)), key=lambda i: resultados[i].taxa_liquida_aa)
    for i, r in enumerate(resultados):
        r.melhor_opcao = i == melhor_idx

    return RendaFixaCompareResponse(
        resultados=resultados,
        cdi_referencia=cdi,
        selic_referencia=selic,
        melhor_opcao_index=melhor_idx,
    )


def get_reference_rates() -> ReferenceRates:
    r = get_rates()
    return ReferenceRates(
        cdi_anual=r["cdi_anual"],
        selic_anual=r["selic_anual"],
        ipca_anual=r["ipca_anual"],
        source=r["source"],
    )
