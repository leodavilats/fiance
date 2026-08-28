"""A projeção do livro-razão, contra valores calculados à mão.

O módulo é puro de propósito: dá para conferir cinco anos de carteira sem banco,
sem rede e sem usuário. É caro de escrever uma vez e é o que impede a regressão
que ninguém vê — preço médio errado só aparece em março, na declaração.
"""

from __future__ import annotations

import pytest

from app.ledger import LedgerEntry, LedgerError, TransactionKind, project_position
from app.ledger.projection import project_positions


def entry(kind: str, day: str, **kwargs) -> LedgerEntry:
    return LedgerEntry(kind=TransactionKind(kind), symbol="PETR4", traded_on=day, **kwargs)


class TestPrecoMedio:
    def test_compras_sucessivas_fazem_media_ponderada(self):
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("buy", "2024-03-10", quantity=100, price=40.0),
            ]
        )

        assert posicao.quantity == 200
        assert posicao.avg_price == pytest.approx(35.0)
        assert posicao.total_cost == pytest.approx(7000.0)

    def test_corretagem_entra_no_custo_de_aquisicao(self):
        """Ignorar a taxa infla o lucro tributável — é IR pago a mais."""
        posicao = project_position([entry("buy", "2024-01-10", quantity=100, price=30.0, fees=9.9)])

        assert posicao.total_cost == pytest.approx(3009.9)
        assert posicao.avg_price == pytest.approx(30.099)

    def test_venda_nao_altera_o_preco_medio(self):
        """Convenção brasileira: vender reduz quantidade e custo, não a média."""
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("buy", "2024-03-10", quantity=100, price=40.0),
                entry("sell", "2024-06-10", quantity=50, price=50.0),
            ]
        )

        assert posicao.quantity == 150
        assert posicao.avg_price == pytest.approx(35.0)
        assert posicao.realized_pnl == pytest.approx(50 * (50.0 - 35.0))

    def test_venda_total_zera_quantidade_e_custo(self):
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("sell", "2024-06-10", quantity=100, price=35.0),
            ]
        )

        assert posicao.quantity == 0
        assert posicao.total_cost == 0
        assert posicao.avg_price == 0
        assert posicao.is_open is False
        assert posicao.realized_pnl == pytest.approx(500.0)

    def test_venda_sem_posicao_e_recusada_com_o_numero_a_vista(self):
        with pytest.raises(LedgerError, match="sem posição"):
            project_position(
                [
                    entry("buy", "2024-01-10", quantity=10, price=30.0),
                    entry("sell", "2024-02-10", quantity=11, price=30.0),
                ]
            )


class TestEventosCorporativos:
    def test_desdobramento_1_para_2_dobra_quantidade_sem_mudar_custo(self):
        """O critério de aceite, literal: custo total intacto, média pela metade."""
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("split", "2024-05-02", ratio_from=1, ratio_to=2),
            ]
        )

        assert posicao.quantity == 200
        assert posicao.total_cost == pytest.approx(3000.0)
        assert posicao.avg_price == pytest.approx(15.0)

    def test_grupamento_10_para_1_reduz_quantidade_e_sobe_a_media(self):
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=1000, price=1.20),
                entry("split", "2024-05-02", ratio_from=10, ratio_to=1),
            ]
        )

        assert posicao.quantity == pytest.approx(100)
        assert posicao.total_cost == pytest.approx(1200.0)
        assert posicao.avg_price == pytest.approx(12.0)

    def test_desdobramento_nao_ajustado_seria_ir_errado(self):
        """Prova por contraste do porquê de o evento ser lançamento de razão."""
        com_ajuste = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("split", "2024-05-02", ratio_from=1, ratio_to=2),
                entry("sell", "2024-09-10", quantity=200, price=20.0),
            ]
        )

        # Sem o ajuste, a mesma venda pareceria prejuízo de 1000 em vez de
        # lucro de 1000 — e o usuário declararia o número errado.
        assert com_ajuste.realized_pnl == pytest.approx(1000.0)

    def test_bonificacao_soma_quantidade_pelo_custo_declarado(self):
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("bonus", "2024-04-10", quantity=10, price=12.0),
            ]
        )

        assert posicao.quantity == 110
        assert posicao.total_cost == pytest.approx(3120.0)

    def test_amortizacao_reduz_custo_sem_reduzir_quantidade(self):
        posicao = project_position(
            [
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="MXRF11",
                    traded_on="2024-01-10",
                    quantity=100,
                    price=10.0,
                ),
                LedgerEntry(
                    kind=TransactionKind.AMORTIZATION,
                    symbol="MXRF11",
                    traded_on="2024-07-10",
                    amount=150.0,
                ),
            ]
        )

        assert posicao.quantity == 100
        assert posicao.total_cost == pytest.approx(850.0)
        assert posicao.avg_price == pytest.approx(8.5)

    def test_amortizacao_nao_leva_o_custo_abaixo_de_zero(self):
        posicao = project_position(
            [
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="MXRF11",
                    traded_on="2024-01-10",
                    quantity=10,
                    price=1.0,
                ),
                LedgerEntry(
                    kind=TransactionKind.AMORTIZATION,
                    symbol="MXRF11",
                    traded_on="2024-07-10",
                    amount=999.0,
                ),
            ]
        )

        assert posicao.total_cost == 0.0

    def test_transferencia_entre_corretoras_nao_cria_nem_destroi_custo(self):
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("transfer_out", "2024-02-10", quantity=40, price=0.0),
                entry("transfer_in", "2024-02-11", quantity=40, price=30.0),
            ]
        )

        assert posicao.quantity == 100
        assert posicao.total_cost == pytest.approx(3000.0)


class TestOrdemEValidacao:
    def test_a_ordem_e_por_dia_e_desempatada_pelo_id(self):
        """Vender antes de comprar no mesmo dia daria posição negativa."""
        compra = LedgerEntry(
            kind=TransactionKind.BUY,
            symbol="PETR4",
            traded_on="2024-01-10",
            quantity=100,
            price=30.0,
            id=1,
        )
        venda = LedgerEntry(
            kind=TransactionKind.SELL,
            symbol="PETR4",
            traded_on="2024-01-10",
            quantity=100,
            price=32.0,
            id=2,
        )

        assert project_position([venda, compra]).realized_pnl == pytest.approx(200.0)

    def test_data_fora_do_formato_do_dia_brasileiro_e_recusada(self):
        with pytest.raises(LedgerError, match="YYYY-MM-DD"):
            entry("buy", "10/01/2024", quantity=1, price=1.0)

    def test_desdobramento_1_para_1_nao_e_lancamento(self):
        with pytest.raises(LedgerError, match="1:1"):
            entry("split", "2024-01-10", ratio_from=1, ratio_to=1)

    def test_compra_sem_preco_e_recusada(self):
        with pytest.raises(LedgerError, match="preço positivo"):
            entry("buy", "2024-01-10", quantity=100, price=0.0)

    def test_ajuste_declarado_substitui_em_vez_de_somar(self):
        posicao = project_position(
            [
                entry("buy", "2024-01-10", quantity=100, price=30.0),
                entry("adjust", "2024-02-10", quantity=250, price=28.0),
            ]
        )

        assert posicao.quantity == 250
        assert posicao.total_cost == pytest.approx(7000.0)
        assert posicao.avg_price == pytest.approx(28.0)


class TestCarteiraSinteticaDeCincoAnos:
    """Cinco anos de operações com o resultado conferido à mão.

    Caro de escrever uma vez; é o que impede a regressão invisível.
    """

    ENTRIES = [
        # 2021 — montagem
        entry("buy", "2021-02-15", quantity=100, price=20.00, fees=10.00, id=1),
        entry("buy", "2021-08-20", quantity=200, price=25.00, fees=10.00, id=2),
        # 2022 — desdobramento 1:2 e realização parcial
        entry("split", "2022-04-01", ratio_from=1, ratio_to=2, id=3),
        entry("sell", "2022-09-15", quantity=200, price=18.00, fees=10.00, id=4),
        # 2023 — bonificação e novo aporte
        entry("bonus", "2023-03-10", quantity=40, price=9.00, id=5),
        entry("buy", "2023-11-05", quantity=100, price=22.00, fees=10.00, id=6),
        # 2024 — grupamento 2:1
        entry("split", "2024-06-03", ratio_from=2, ratio_to=1, id=7),
        # 2025 — realização final parcial
        entry("sell", "2025-10-20", quantity=100, price=45.00, fees=10.00, id=8),
    ]

    # Conta feita à mão, passo a passo:
    #  1. +100 @ 20 + 10        → qty 100, custo 2.010,00
    #  2. +200 @ 25 + 10        → qty 300, custo 7.020,00   (média 23,40)
    #  3. split 1:2             → qty 600, custo 7.020,00   (média 11,70)
    #  4. -200 @ 18, taxa 10    → custo baixa 200 × 11,70 = 2.340,00
    #                             qty 400, custo 4.680,00
    #                             lucro 200 × 18 − 2.340 − 10 = 1.250,00
    #  5. +40 bonificadas @ 9   → qty 440, custo 5.040,00   (média ≈ 11,4545)
    #  6. +100 @ 22 + 10        → qty 540, custo 7.250,00   (média ≈ 13,4259)
    #  7. grupamento 2:1        → qty 270, custo 7.250,00   (média ≈ 26,8518)
    #  8. -100 @ 45, taxa 10    → custo baixa 100 × 26,851851… = 2.685,185…
    #                             qty 170, custo 4.564,814…
    #                             lucro += 100 × 45 − 2.685,185… − 10 = 1.804,814…
    EXPECTED_QUANTITY = 170.0
    EXPECTED_TOTAL_COST = 7250.0 - (7250.0 / 270.0) * 100.0
    EXPECTED_REALIZED = 1250.0 + (4500.0 - (7250.0 / 270.0) * 100.0 - 10.0)

    def test_quantidade_final(self):
        assert project_position(self.ENTRIES).quantity == pytest.approx(self.EXPECTED_QUANTITY)

    def test_custo_e_preco_medio_finais(self):
        posicao = project_position(self.ENTRIES)

        assert posicao.total_cost == pytest.approx(self.EXPECTED_TOTAL_COST)
        assert posicao.avg_price == pytest.approx(self.EXPECTED_TOTAL_COST / 170.0)

    def test_lucro_realizado_acumulado(self):
        assert project_position(self.ENTRIES).realized_pnl == pytest.approx(self.EXPECTED_REALIZED)

    def test_taxas_somadas_batem_com_as_notas(self):
        assert project_position(self.ENTRIES).total_fees == pytest.approx(50.0)

    def test_a_ordem_de_entrada_nao_altera_o_resultado(self):
        """Reordenar a lista não pode mudar o número: a ordem é do razão."""
        embaralhado = list(reversed(self.ENTRIES))

        assert project_position(embaralhado).total_cost == pytest.approx(
            project_position(self.ENTRIES).total_cost
        )

    def test_a_janela_de_negociacao_e_registrada(self):
        posicao = project_position(self.ENTRIES)

        assert posicao.first_traded_on == "2021-02-15"
        assert posicao.last_traded_on == "2025-10-20"
        assert posicao.entries_applied == len(self.ENTRIES)


class TestCarteiraInteira:
    def test_projeta_cada_ativo_isoladamente(self):
        posicoes = project_positions(
            [
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="PETR4",
                    traded_on="2024-01-10",
                    quantity=100,
                    price=30.0,
                ),
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="VALE3",
                    traded_on="2024-01-10",
                    quantity=50,
                    price=60.0,
                ),
                LedgerEntry(
                    kind=TransactionKind.SPLIT,
                    symbol="PETR4",
                    traded_on="2024-05-01",
                    ratio_from=1,
                    ratio_to=2,
                ),
            ]
        )

        assert posicoes["PETR4"].quantity == 200
        assert posicoes["VALE3"].quantity == 50

    def test_posicao_encerrada_continua_na_projecao_com_o_lucro(self):
        """A apuração de IR consome exatamente isto."""
        posicoes = project_positions(
            [
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="PETR4",
                    traded_on="2024-01-10",
                    quantity=100,
                    price=30.0,
                ),
                LedgerEntry(
                    kind=TransactionKind.SELL,
                    symbol="PETR4",
                    traded_on="2024-02-10",
                    quantity=100,
                    price=35.0,
                    id=2,
                ),
            ]
        )

        assert posicoes["PETR4"].is_open is False
        assert posicoes["PETR4"].realized_pnl == pytest.approx(500.0)
