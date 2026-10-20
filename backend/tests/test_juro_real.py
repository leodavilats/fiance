from __future__ import annotations

from app.collectors import juro_real


def _titulo(titulo: str, vencimento: str, compra: float | None, venda: float | None) -> dict:
    return {"titulo": titulo, "vencimento": vencimento, "data": "2026-10-16",
            "taxa_compra": compra, "taxa_venda": venda}  # fmt: skip


def test_referencia_e_o_ipca_sem_cupom_mais_longo_a_venda():
    titulos = [
        _titulo("Tesouro IPCA+", "2035-05-15", 6.9, 7.0),
        _titulo("Tesouro IPCA+", "2045-05-15", 6.7, 6.8),
        _titulo("Tesouro IPCA+", "2050-08-15", None, 6.6),
        _titulo("Tesouro IPCA+ com Juros Semestrais", "2060-08-15", 6.5, 6.6),
    ]

    escolhido = juro_real.mais_longo_a_venda(titulos)

    assert escolhido["vencimento"] == "2045-05-15", (
        "fora de venda não é referência, e o título com cupom é outro título (ADR-028)"
    )


def test_sem_titulo_a_venda_nao_ha_referencia():
    assert juro_real.mais_longo_a_venda([_titulo("Tesouro IPCA+", "2045-05-15", None, 6.8)]) is None
    assert juro_real.mais_longo_a_venda([]) is None


def test_taxa_absurda_fica_fora_da_faixa():
    assert juro_real.FAIXA.accepts(6.5)
    assert not juro_real.FAIXA.accepts(650.0), "taxa em pontos-base lida como percentual"
