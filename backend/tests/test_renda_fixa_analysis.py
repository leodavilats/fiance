from app.analysis.renda_fixa_analysis import analyze_one
from app.models.enums import Liquidez, RendaFixaType, TaxType
from app.models.renda_fixa import RendaFixaAsset


def _asset(**overrides):
    defaults = {
        "tipo": RendaFixaType.cdb,
        "valor_investido": 10_000.0,
        "taxa": 12.0,
        "prazo_meses": 12,
        "tipo_taxa": TaxType.pre_fixado,
        "percentual_cdi": None,
        "liquidez": Liquidez.no_vencimento,
        "nome": "Teste",
        "isento_ir": None,
    }
    defaults.update(overrides)
    return RendaFixaAsset(**defaults)


def test_cdb_is_taxed():
    result = analyze_one(_asset())
    assert result.isento_ir is False
    assert result.ir.valor_ir > 0


def test_lci_is_tax_exempt():
    result = analyze_one(_asset(tipo=RendaFixaType.lci))
    assert result.isento_ir is True
    assert result.ir.valor_ir == 0.0
    assert result.rendimento_liquido == result.rendimento_bruto


def test_ir_rate_tiers_by_prazo():
    curto = analyze_one(_asset(prazo_meses=5))
    medio = analyze_one(_asset(prazo_meses=10))
    longo = analyze_one(_asset(prazo_meses=20))
    muito_longo = analyze_one(_asset(prazo_meses=30))

    assert curto.ir.aliquota_pct == 22.5
    assert medio.ir.aliquota_pct == 20.0
    assert longo.ir.aliquota_pct == 17.5
    assert muito_longo.ir.aliquota_pct == 15.0


def test_pos_fixado_uses_cdi_percentual():
    result = analyze_one(
        _asset(tipo_taxa=TaxType.pos_fixado, percentual_cdi=110.0, taxa=1.0),
        cdi_anual=14.4,
    )
    assert result.rendimento_bruto > 0


def test_explicit_isento_ir_overrides_tipo():
    result = analyze_one(_asset(isento_ir=True))
    assert result.isento_ir is True
    assert result.ir.valor_ir == 0.0


def test_percentual_cdi_is_multiplicative_not_exponential():
    """ "110% do CDI" é 1,10 × CDI, não (1+CDI)^1,10."""
    cdi = 14.4
    result = analyze_one(
        _asset(tipo_taxa=TaxType.pos_fixado, percentual_cdi=110.0, taxa=1.0, prazo_meses=12),
        cdi_anual=cdi,
    )
    assert result.taxa_anual_efetiva_pct == round(cdi * 1.10, 2)


def test_hundred_percent_of_cdi_equals_the_cdi():
    cdi = 14.4
    result = analyze_one(
        _asset(tipo_taxa=TaxType.pos_fixado, percentual_cdi=100.0, taxa=1.0),
        cdi_anual=cdi,
    )
    assert result.taxa_anual_efetiva_pct == cdi


def test_double_cdi_does_not_explode_exponentially():
    cdi = 14.4
    result = analyze_one(
        _asset(tipo_taxa=TaxType.pos_fixado, percentual_cdi=200.0, taxa=1.0),
        cdi_anual=cdi,
    )
    assert result.taxa_anual_efetiva_pct == round(cdi * 2, 2)


def test_ipca_plus_composes_inflation_with_the_real_rate():
    """IPCA+6% rendia 6%, sem inflação — `tesouro_ipca` só existia no enum."""
    result = analyze_one(
        _asset(tipo=RendaFixaType.tesouro_ipca, taxa=6.0, tipo_taxa=TaxType.pre_fixado),
        ipca_anual=5.0,
    )
    esperado = round(((1.05 * 1.06) - 1) * 100, 2)
    assert result.taxa_anual_efetiva_pct == esperado
    assert result.taxa_anual_efetiva_pct > 6.0


def test_hibrido_also_composes_inflation():
    result = analyze_one(_asset(taxa=4.0, tipo_taxa=TaxType.hibrido), ipca_anual=5.0)
    assert result.taxa_anual_efetiva_pct == round(((1.05 * 1.04) - 1) * 100, 2)


def test_pct_of_cdi_is_not_inflated_by_a_hardcoded_benchmark():
    """Uma LCI a 100% do CDI era exibida como ~117% do CDI."""
    cdi = 14.4
    lci = analyze_one(
        _asset(
            tipo=RendaFixaType.lci,
            tipo_taxa=TaxType.pos_fixado,
            percentual_cdi=100.0,
            taxa=1.0,
            prazo_meses=12,
        ),
        cdi_anual=cdi,
    )

    assert 99.0 <= lci.taxa_equivalente_cdi_pct <= 101.0
    assert lci.pct_cdi_bruto_equivalente > 120.0


def test_twenty_four_month_term_lands_on_the_fifteen_percent_bracket():
    """O web usava meses × 30 (720 d -> 17,5%) e o backend × 30,44 (730 d -> 15%)."""
    result = analyze_one(_asset(prazo_meses=24))
    assert result.ir.prazo_dias > 720
    assert result.ir.aliquota_pct == 15.0


def test_mark_to_market_uses_the_elapsed_term():
    """`prazo_meses_override` é o que permite marcar a posição a mercado."""
    cinco_meses = analyze_one(_asset(prazo_meses=24), prazo_meses_override=5)
    doze_meses = analyze_one(_asset(prazo_meses=24), prazo_meses_override=12)

    assert cinco_meses.rendimento_liquido < doze_meses.rendimento_liquido
    assert cinco_meses.ir.aliquota_pct == 22.5
    assert analyze_one(_asset(prazo_meses=24)).ir.aliquota_pct == 15.0


def test_daily_liquidity_wins_when_the_rate_is_nearly_the_same():
    from app.analysis.renda_fixa_analysis import compare_options
    from app.models.renda_fixa import RendaFixaCompareRequest

    travado = _asset(nome="CDB 5 anos", taxa=13.1, prazo_meses=60)
    liquido = _asset(
        nome="CDB liquidez diária", taxa=13.0, prazo_meses=60, liquidez=Liquidez.diaria
    )

    resp = compare_options(
        RendaFixaCompareRequest(ativos=[travado, liquido], cdi_anual=14.4, ipca_anual=5.0)
    )

    assert resp.resultados[resp.melhor_opcao_index].nome == "CDB liquidez diária"
    assert "liquidez" in resp.melhor_opcao_motivo.lower()


def test_much_better_rate_still_wins_over_liquidity():
    from app.analysis.renda_fixa_analysis import compare_options
    from app.models.renda_fixa import RendaFixaCompareRequest

    travado = _asset(nome="CDB 5 anos", taxa=18.0, prazo_meses=60)
    liquido = _asset(
        nome="CDB liquidez diária", taxa=11.0, prazo_meses=60, liquidez=Liquidez.diaria
    )

    resp = compare_options(
        RendaFixaCompareRequest(ativos=[travado, liquido], cdi_anual=14.4, ipca_anual=5.0)
    )

    assert resp.resultados[resp.melhor_opcao_index].nome == "CDB 5 anos"
