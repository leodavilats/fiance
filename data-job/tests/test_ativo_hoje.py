from __future__ import annotations

from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from tests.test_proventos import _coleta, _papel


def _hoje(engine) -> dict[str, sa.Row]:
    with engine.begin() as conn:
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.ativo_hoje"))
        return {r.codigo: r for r in conn.execute(sa.text("SELECT * FROM mercado.ativo_hoje"))}


def test_acao_traz_preco_faixa_acoes_e_proventos_de_doze_meses(engine):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRTESTACNOR1",
            "ON NM",
            {"2025-11-03": ("30", "30"), "2026-10-08": ("40", "39"), "2026-10-09": ("40", "41")},
        )
        coleta_id = _coleta(conn)
        conn.execute(
            sa.text(
                "INSERT INTO mercado.empresa (cnpj, razao_social, nome_comercial, setor, coleta_id) "
                "VALUES ('1', 'TESTE SA', 'Teste', 'Energia', :c)"
            ),
            {"c": coleta_id},
        )
        conn.execute(
            sa.text(
                "INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES ('TEST', '1', 'fca')"
            )
        )
        conn.execute(
            sa.text(
                "INSERT INTO mercado.capital_social (cnpj, data_referencia, versao, data_aprovacao, "
                "acoes_total, coleta_id) VALUES ('1', '2026-01-01', 1, '2026-03-01', 1000, :c)"
            ),
            {"c": coleta_id},
        )
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, origem, "
                "data_pagamento, coleta_id) VALUES "
                "('TEST', 'ON', '2026-03-01', 'DIVIDENDO', 1.5, 'b3_historico', NULL, :c), "
                "('TEST', 'ON', '2025-06-01', 'DIVIDENDO', 9, 'b3_historico', NULL, :c), "
                "('TEST', 'ON', '2026-09-30', 'DIVIDENDO', 0.5, 'b3_recente', '2026-11-30', :c)"
            ),
            {"c": coleta_id},
        )

    acao = _hoje(engine)["TEST3"]

    assert acao.tipo == "stock" and acao.classe == "ON"
    assert acao.preco == 41 and acao.preco_anterior == 39 and acao.data == date(2026, 10, 9)
    assert acao.maxima_52s == 40 and acao.minima_52s == 30
    assert (acao.nome, acao.setor, acao.acoes) == ("Teste", "Energia", 1000)
    assert acao.proventos_12m == Decimal("1.5"), (
        "fora da janela: o de jun/2025 e o que só paga em nov/2026"
    )


def test_fii_traz_valor_patrimonial_e_nao_soma_o_estimado(engine):
    with engine.begin() as conn:
        _papel(conn, "BRXPMLCTF000", "CI", {"2026-10-09": ("100", "100")}, codbdi="12")
        coleta_id = _coleta(conn)
        conn.execute(
            sa.text(
                "INSERT INTO mercado.fii_mensal (emissor, classe, referencia, cnpj, isin, nome, "
                "segmento, valor_patrimonial_cota, coleta_id) VALUES "
                "('XPML', 'CI', '2026-08-01', '9', 'BRXPMLCTF000', 'XP MALLS', 'Shoppings', 110, :c)"
            ),
            {"c": coleta_id},
        )
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, origem, "
                "coleta_id) VALUES "
                "('XPML', 'CI', '2026-08-31', 'RENDIMENTO', 0.9, 'b3_recente', :c), "
                "('XPML', 'CI', '2026-07-31', 'RENDIMENTO', 0.9, 'cvm_estimado', :c)"
            ),
            {"c": coleta_id},
        )

    fii = _hoje(engine)["TEST3"]

    assert fii.tipo == "fii"
    assert (fii.nome, fii.setor, fii.valor_patrimonial_cota) == ("XP MALLS", "Shoppings", 110)
    assert fii.proventos_12m == Decimal("0.9"), "o app não recebe rendimento estimado"
