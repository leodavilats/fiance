from __future__ import annotations

from decimal import Decimal

import pytest

from app.ledger import LedgerEntry, TransactionKind
from app.ledger.projection import project_position, project_positions
from app.services import ledger_service
from app.storage import ledger_store, portfolio_store


def entrada(indice, kind, symbol, traded_on, **campos) -> LedgerEntry:
    return LedgerEntry(
        kind=TransactionKind(kind), symbol=symbol, traded_on=traded_on, id=indice, **campos
    )


CINCO_ANOS = [
    entrada(1, "buy", "PETR4", "2021-01-15", quantity=100, price=20.00, fees=5.00),
    entrada(2, "buy", "HGLG11", "2021-03-01", quantity=50, price=160.00),
    entrada(3, "buy", "VALE3", "2021-02-01", quantity=80, price=90.00),
    entrada(4, "buy", "PETR4", "2021-07-08", quantity=150, price=24.00, fees=7.50),
    entrada(5, "split", "PETR4", "2022-03-10", ratio_from=1, ratio_to=2),
    entrada(6, "transfer_in", "HGLG11", "2022-08-15", quantity=50, price=140.00),
    entrada(7, "sell", "PETR4", "2022-09-22", quantity=200, price=15.00, fees=4.00),
    entrada(8, "sell", "VALE3", "2023-04-12", quantity=80, price=70.00, fees=2.00),
    entrada(9, "bonus", "PETR4", "2023-05-04", quantity=20, price=0.00),
    entrada(10, "amortization", "PETR4", "2024-02-14", amount=367.50),
    entrada(11, "transfer_out", "HGLG11", "2024-06-20", quantity=40),
    entrada(12, "sell", "HGLG11", "2025-01-10", quantity=10, price=170.00, fees=1.00),
    entrada(13, "sell", "PETR4", "2025-11-03", quantity=120, price=12.00, fees=3.00),
]


class TestPETR4ConferidaAMao:
    @pytest.fixture()
    def posicao(self):
        return project_position([e for e in CINCO_ANOS if e.symbol == "PETR4"], "PETR4")

    def test_quantidade_final(self, posicao):
        assert posicao.quantity_exact == Decimal("200")

    def test_preco_medio_final(self, posicao):
        assert posicao.avg_price_exact == Decimal("9.375")

    def test_custo_total_final(self, posicao):
        assert posicao.total_cost_exact == Decimal("1875.00")

    def test_lucro_realizado_acumulado(self, posicao):
        assert posicao.realized_pnl_exact == Decimal("1063.00")

    def test_corretagem_acumulada(self, posicao):
        assert posicao.total_fees_exact == Decimal("19.50")

    def test_o_desdobramento_dobrou_a_quantidade_sem_mexer_no_custo(self):
        ate_o_desdobramento = [e for e in CINCO_ANOS if e.symbol == "PETR4" and e.id <= 5]

        posicao = project_position(ate_o_desdobramento, "PETR4")

        assert posicao.quantity_exact == Decimal("500")
        assert posicao.total_cost_exact == Decimal("5612.50")
        assert posicao.avg_price_exact == Decimal("11.225")

    def test_a_venda_nao_mexeu_no_preco_medio(self):
        ate_a_venda = [e for e in CINCO_ANOS if e.symbol == "PETR4" and e.id <= 7]

        posicao = project_position(ate_a_venda, "PETR4")

        assert posicao.avg_price_exact == Decimal("11.225")
        assert posicao.quantity_exact == Decimal("300")
        assert posicao.realized_pnl_exact == Decimal("751.00")

    def test_a_bonificacao_diluiu_o_preco_medio(self):
        ate_a_bonificacao = [e for e in CINCO_ANOS if e.symbol == "PETR4" and e.id <= 9]

        posicao = project_position(ate_a_bonificacao, "PETR4")

        assert posicao.quantity_exact == Decimal("320")
        assert posicao.total_cost_exact == Decimal("3367.50")
        assert posicao.avg_price_exact == Decimal("10.5234375")

    def test_a_amortizacao_baixou_o_custo_sem_mexer_na_quantidade(self):
        ate_a_amortizacao = [e for e in CINCO_ANOS if e.symbol == "PETR4" and e.id <= 10]

        posicao = project_position(ate_a_amortizacao, "PETR4")

        assert posicao.quantity_exact == Decimal("320")
        assert posicao.total_cost_exact == Decimal("3000.00")


class TestHGLG11ConferidaAMao:
    @pytest.fixture()
    def posicao(self):
        return project_position([e for e in CINCO_ANOS if e.symbol == "HGLG11"], "HGLG11")

    def test_quantidade_final(self, posicao):
        assert posicao.quantity_exact == Decimal("50")

    def test_preco_medio_final(self, posicao):
        assert posicao.avg_price_exact == Decimal("150")

    def test_custo_total_final(self, posicao):
        assert posicao.total_cost_exact == Decimal("7500")

    def test_lucro_realizado(self, posicao):
        assert posicao.realized_pnl_exact == Decimal("199.00")

    def test_transferencia_de_saida_nao_gera_lucro(self):
        ate_a_transferencia = [e for e in CINCO_ANOS if e.symbol == "HGLG11" and e.id <= 11]

        posicao = project_position(ate_a_transferencia, "HGLG11")

        assert posicao.realized_pnl_exact == Decimal("0")
        assert posicao.quantity_exact == Decimal("60")
        assert posicao.avg_price_exact == Decimal("150")


class TestVALE3ZeradaComPrejuizo:
    @pytest.fixture()
    def posicao(self):
        return project_position([e for e in CINCO_ANOS if e.symbol == "VALE3"], "VALE3")

    def test_a_posicao_fecha_zerada(self, posicao):
        assert posicao.quantity_exact == Decimal("0")
        assert posicao.total_cost_exact == Decimal("0")
        assert posicao.is_open is False

    def test_o_prejuizo_fica_registrado(self, posicao):
        assert posicao.realized_pnl_exact == Decimal("-1602.00")


class TestACarteiraInteira:
    def test_o_resultado_realizado_da_carteira_fecha(self):
        posicoes = project_positions(CINCO_ANOS)

        total = sum(p.realized_pnl_exact for p in posicoes.values())

        assert total == Decimal("-340.00")

    def test_so_o_que_ainda_esta_aberto_conta_como_posicao(self):
        posicoes = project_positions(CINCO_ANOS)

        abertas = {s for s, p in posicoes.items() if p.is_open}

        assert abertas == {"PETR4", "HGLG11"}

    def test_o_custo_total_investido_fecha(self):
        posicoes = project_positions(CINCO_ANOS)

        total = sum(p.total_cost_exact for p in posicoes.values())

        assert total == Decimal("9375.00")


class TestOsMesmosNumerosPassandoPeloBanco:
    def test_gravar_cinco_anos_e_projetar_da_o_mesmo_resultado(self, client):
        uid = "u_sintetica_banco"
        for e in CINCO_ANOS:
            ledger_store.record(
                LedgerEntry(
                    kind=e.kind,
                    symbol=e.symbol,
                    traded_on=e.traded_on,
                    quantity=e.quantity,
                    price=e.price,
                    fees=e.fees,
                    ratio_from=e.ratio_from,
                    ratio_to=e.ratio_to,
                    amount=e.amount,
                ),
                source="teste",
                user_id=uid,
            )

        projetado = ledger_service.project(uid)

        assert projetado["PETR4"].avg_price_exact == Decimal("9.375")
        assert projetado["PETR4"].quantity_exact == Decimal("200")
        assert projetado["HGLG11"].total_cost_exact == Decimal("7500")
        assert projetado["VALE3"].is_open is False

    def test_a_projecao_gravada_bate_com_a_conta_a_mao(self, client):
        uid = "u_sintetica_projecao"
        for e in CINCO_ANOS:
            ledger_store.record(
                LedgerEntry(
                    kind=e.kind,
                    symbol=e.symbol,
                    traded_on=e.traded_on,
                    quantity=e.quantity,
                    price=e.price,
                    fees=e.fees,
                    ratio_from=e.ratio_from,
                    ratio_to=e.ratio_to,
                    amount=e.amount,
                ),
                source="teste",
                user_id=uid,
            )
        ledger_service.rebuild_projection(user_id=uid)

        posicoes = {p["ticker"]: p for p in portfolio_store.list_positions(uid)}

        assert set(posicoes) == {"PETR4", "HGLG11"}
        assert posicoes["PETR4"]["quantity"] == 200.0
        assert posicoes["PETR4"]["avg_price"] == 9.375
        assert posicoes["HGLG11"]["avg_price"] == 150.0

    def test_a_reconciliacao_fecha_verde(self, client):
        uid = "u_sintetica_reconcilia"
        for e in CINCO_ANOS:
            ledger_store.record(
                LedgerEntry(
                    kind=e.kind,
                    symbol=e.symbol,
                    traded_on=e.traded_on,
                    quantity=e.quantity,
                    price=e.price,
                    fees=e.fees,
                    ratio_from=e.ratio_from,
                    ratio_to=e.ratio_to,
                    amount=e.amount,
                ),
                source="teste",
                user_id=uid,
            )
        ledger_service.rebuild_projection(user_id=uid)

        assert ledger_service.reconcile(uid)["in_sync"]
