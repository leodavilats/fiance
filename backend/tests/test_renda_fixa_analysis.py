from app.analysis.renda_fixa_analysis import analyze_one
from app.models.enums import Liquidez, RendaFixaType, TaxType
from app.models.renda_fixa import RendaFixaAsset


def _asset(**overrides):
    defaults = dict(
        tipo=RendaFixaType.cdb,
        valor_investido=10_000.0,
        taxa=12.0,
        prazo_meses=12,
        tipo_taxa=TaxType.pre_fixado,
        percentual_cdi=None,
        liquidez=Liquidez.no_vencimento,
        nome="Teste",
        isento_ir=None,
    )
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
    # prazo_dias = meses * 30.44, thresholds at 180/360/720 days
    curto = analyze_one(_asset(prazo_meses=5))  # ~152 dias -> 22.5%
    medio = analyze_one(_asset(prazo_meses=10))  # ~304 dias -> 20%
    longo = analyze_one(_asset(prazo_meses=20))  # ~609 dias -> 17.5%
    muito_longo = analyze_one(_asset(prazo_meses=30))  # ~913 dias -> 15%

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
    # a CDB explicitly marked isento_ir=True must not be taxed even though
    # its tipo is not in ISENTOS_IR
    result = analyze_one(_asset(isento_ir=True))
    assert result.isento_ir is True
    assert result.ir.valor_ir == 0.0
