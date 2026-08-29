from __future__ import annotations

from app.collectors.rates import get_rates
from app.models.enums import Liquidez, RendaFixaType, TaxType
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

DIAS_POR_MES = 30.4375

LIQUIDEZ_TOLERANCIA_PP = 0.5

ISENTOS_IR = {
    RendaFixaType.lci,
    RendaFixaType.lca,
    RendaFixaType.cri,
    RendaFixaType.cra,
}

INDEXADOS_IPCA = {RendaFixaType.tesouro_ipca}


def _aliquota_ir(prazo_dias: int) -> float:
    if prazo_dias <= 180:
        return 0.225
    elif prazo_dias <= 360:
        return 0.20
    elif prazo_dias <= 720:
        return 0.175
    else:
        return 0.15


def _compor(taxa_anual_pct: float, meses: float) -> float:
    return (1 + taxa_anual_pct / 100.0) ** (meses / 12.0) - 1


def taxa_anual_efetiva(
    ativo: RendaFixaAsset,
    cdi_anual: float,
    ipca_anual: float,
) -> float:
    if ativo.tipo_taxa == TaxType.pos_fixado and ativo.percentual_cdi:
        return cdi_anual * (ativo.percentual_cdi / 100.0)

    indexado_ipca = ativo.tipo in INDEXADOS_IPCA or ativo.tipo_taxa == TaxType.hibrido
    if indexado_ipca:
        return ((1 + ipca_anual / 100.0) * (1 + ativo.taxa / 100.0) - 1) * 100.0

    return ativo.taxa


def analyze_one(
    ativo: RendaFixaAsset,
    cdi_anual: float = DEFAULT_CDI_ANUAL,
    selic_anual: float = DEFAULT_SELIC_ANUAL,
    ipca_anual: float = DEFAULT_IPCA_ANUAL,
    prazo_meses_override: float | None = None,
) -> RendaFixaAnalysisResult:
    prazo_meses = ativo.prazo_meses if prazo_meses_override is None else prazo_meses_override
    prazo_dias = int(round(prazo_meses * DIAS_POR_MES))

    isento = ativo.isento_ir
    if isento is None:
        isento = ativo.tipo in ISENTOS_IR

    taxa_anual_pct = taxa_anual_efetiva(ativo, cdi_anual, ipca_anual)
    taxa_periodo = _compor(taxa_anual_pct, prazo_meses)

    valor_bruto = ativo.valor_investido * (1 + taxa_periodo)
    rendimento_bruto = valor_bruto - ativo.valor_investido

    if isento:
        aliquota = 0.0
        valor_ir = 0.0
    else:
        aliquota = _aliquota_ir(prazo_dias)
        valor_ir = max(rendimento_bruto, 0.0) * aliquota

    rendimento_liquido = rendimento_bruto - valor_ir
    valor_liquido = ativo.valor_investido + rendimento_liquido

    taxa_liq_periodo = rendimento_liquido / ativo.valor_investido
    if prazo_meses > 0:
        taxa_liq_aa = ((1 + taxa_liq_periodo) ** (12.0 / prazo_meses) - 1) * 100
    else:
        taxa_liq_aa = 0.0

    pct_cdi_liquido: float | None = None
    pct_cdi_bruto_equivalente: float | None = None
    if cdi_anual > 0:
        pct_cdi_liquido = round(taxa_liq_aa / cdi_anual * 100, 2)
        aliquota_referencia = _aliquota_ir(prazo_dias)
        cdi_liquido_tributado = cdi_anual * (1 - aliquota_referencia)
        if cdi_liquido_tributado > 0:
            pct_cdi_bruto_equivalente = round(taxa_liq_aa / cdi_liquido_tributado * 100, 2)

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
        taxa_anual_efetiva_pct=round(taxa_anual_pct, 2),
        taxa_equivalente_cdi_pct=pct_cdi_liquido,
        pct_cdi_bruto_equivalente=pct_cdi_bruto_equivalente,
        isento_ir=isento,
        liquidez=ativo.liquidez.value,
        prazo_meses=prazo_meses,
    )


def _escolher_melhor(resultados: list[RendaFixaAnalysisResult]) -> tuple[int, str]:
    melhor_taxa_idx = max(range(len(resultados)), key=lambda i: resultados[i].taxa_liquida_aa)
    melhor_taxa = resultados[melhor_taxa_idx].taxa_liquida_aa

    if resultados[melhor_taxa_idx].liquidez == Liquidez.diaria.value:
        return melhor_taxa_idx, "Melhor taxa líquida, com liquidez diária."

    liquidos = [
        i
        for i, r in enumerate(resultados)
        if r.liquidez == Liquidez.diaria.value
        and (melhor_taxa - r.taxa_liquida_aa) <= LIQUIDEZ_TOLERANCIA_PP
    ]
    if liquidos:
        idx = max(liquidos, key=lambda i: resultados[i].taxa_liquida_aa)
        diff = melhor_taxa - resultados[idx].taxa_liquida_aa
        return idx, (
            f"Liquidez diária por apenas {diff:.2f} p.p. a.a. menos que a melhor "
            "taxa — resgatar quando precisar vale a diferença."
        )

    return melhor_taxa_idx, "Melhor taxa líquida entre as opções sem liquidez diária."


def compare_options(req: RendaFixaCompareRequest) -> RendaFixaCompareResponse:
    rates = get_rates()
    cdi = req.cdi_anual if req.cdi_anual else rates["cdi_anual"]
    selic = req.selic_anual if req.selic_anual else rates["selic_anual"]
    ipca = req.ipca_anual if req.ipca_anual else rates["ipca_anual"]

    resultados: list[RendaFixaAnalysisResult] = [
        analyze_one(ativo, cdi, selic, ipca) for ativo in req.ativos
    ]

    melhor_idx, motivo = _escolher_melhor(resultados)
    for i, r in enumerate(resultados):
        r.melhor_opcao = i == melhor_idx

    return RendaFixaCompareResponse(
        resultados=resultados,
        cdi_referencia=cdi,
        selic_referencia=selic,
        ipca_referencia=ipca,
        melhor_opcao_index=melhor_idx,
        melhor_opcao_motivo=motivo,
        fonte_taxas=rates["source"],
    )


def get_reference_rates() -> ReferenceRates:
    r = get_rates()
    return ReferenceRates(
        cdi_anual=r["cdi_anual"],
        selic_anual=r["selic_anual"],
        ipca_anual=r["ipca_anual"],
        source=r["source"],
    )
