from __future__ import annotations

import time

import pytest

from app.core.brt import to_brt
from app.core.money import quantize, to_float
from app.ledger import project_position
from app.ledger.apuracao import ALIQUOTA_DAY_TRADE, apurar
from app.ledger.entries import LedgerEntry, LedgerError, TransactionKind
from tests.conftest import make_auth_headers

CATEGORIAS = {"PETR4": "acoes_br", "VALE3": "acoes_br", "HGLG11": "fiis"}


def compra(dia: str, quantidade: float, preco: float, id_: int, **kw) -> LedgerEntry:
    return LedgerEntry(
        kind=TransactionKind.BUY,
        symbol=kw.pop("ticker", "PETR4"),
        traded_on=dia,
        quantity=quantidade,
        price=preco,
        id=id_,
        **kw,
    )


def venda(dia: str, quantidade: float, preco: float, id_: int, **kw) -> LedgerEntry:
    return LedgerEntry(
        kind=TransactionKind.SELL,
        symbol=kw.pop("ticker", "PETR4"),
        traded_on=dia,
        quantity=quantidade,
        price=preco,
        id=id_,
        **kw,
    )


def reais(valor) -> float:
    return to_float(quantize(valor))


class TestCompraEVendaNoMesmoDia:
    def test_vira_day_trade_e_nao_venda_comum(self):
        apuracao = apurar(
            [compra("2026-03-10", 100, 10.0, 1), venda("2026-03-10", 100, 12.0, 2)],
            CATEGORIAS,
        )

        assert [v.day_trade for v in apuracao.vendas] == [True]
        assert reais(apuracao.vendas[0].result) == 200.0
        assert apuracao.mes("2026-03", "acoes_br") is None, "nada sobra para o swing"
        assert apuracao.mes("2026-03", "acoes_br", day_trade=True).ir_rate == ALIQUOTA_DAY_TRADE

    def test_a_ordem_de_registro_dentro_do_dia_nao_muda_nada(self):
        antes = apurar(
            [compra("2026-03-10", 100, 10.0, 1), venda("2026-03-10", 100, 12.0, 2)],
            CATEGORIAS,
        )
        depois = apurar(
            [venda("2026-03-10", 100, 12.0, 1), compra("2026-03-10", 100, 10.0, 2)],
            CATEGORIAS,
        )

        assert reais(depois.vendas[0].result) == reais(antes.vendas[0].result) == 200.0

    def test_vender_antes_de_comprar_no_mesmo_dia_nao_e_venda_sem_posicao(self):
        estado = project_position(
            [venda("2026-03-10", 100, 12.0, 1), compra("2026-03-10", 100, 10.0, 2)]
        )

        assert estado.quantity == 0
        assert reais(estado.realized_pnl_exact) == 200.0

    def test_resultado_usa_os_precos_medios_do_dia(self):
        apuracao = apurar(
            [
                compra("2026-03-10", 100, 10.0, 1),
                compra("2026-03-10", 100, 12.0, 2),
                venda("2026-03-10", 50, 13.0, 3),
                venda("2026-03-10", 150, 11.0, 4),
            ],
            CATEGORIAS,
        )
        day_trade = apuracao.vendas[0]

        assert day_trade.quantity == 200
        assert day_trade.avg_price == 11.0
        assert day_trade.sell_price == 11.5
        assert reais(day_trade.result) == 100.0, "200 × (11,50 − 11,00)"
        assert day_trade.entry_id == 4, "a linha leva o id da última venda do dia"

    def test_taxas_entram_na_proporcao_do_que_casou(self):
        apuracao = apurar(
            [
                compra("2026-03-10", 100, 10.0, 1, fees=10.0),
                venda("2026-03-10", 60, 12.0, 2, fees=6.0),
            ],
            CATEGORIAS,
        )
        estado = project_position(
            [
                compra("2026-03-10", 100, 10.0, 1, fees=10.0),
                venda("2026-03-10", 60, 12.0, 2, fees=6.0),
            ]
        )

        assert reais(apuracao.vendas[0].fees) == 12.0, "60% da taxa de compra e toda a de venda"
        assert reais(apuracao.vendas[0].result) == 108.0
        assert reais(estado.total_cost_exact) == 404.0, "40 × 10 mais 40% da taxa de compra"


class TestDayTradeParcialComPosicaoAnterior:
    RAZAO = [
        compra("2026-01-05", 100, 10.0, 1),
        compra("2026-03-10", 100, 12.0, 2),
        venda("2026-03-10", 60, 13.0, 3),
    ]

    def test_so_a_quantidade_casada_e_day_trade(self):
        apuracao = apurar(self.RAZAO, CATEGORIAS)

        assert len(apuracao.vendas) == 1
        assert apuracao.vendas[0].day_trade is True
        assert apuracao.vendas[0].quantity == 60
        assert reais(apuracao.vendas[0].result) == 60.0, "60 × (13 − 12), não contra a média"

    def test_o_preco_medio_do_swing_nao_absorve_o_day_trade(self):
        estado = project_position(self.RAZAO)

        assert estado.quantity == 140
        assert estado.avg_price == pytest.approx((100 * 10.0 + 40 * 12.0) / 140), (
            "a sobra da compra (40 a 12) entra na média; as 60 casadas ficam de fora"
        )

    def test_a_venda_comum_seguinte_sai_pela_media_do_swing(self):
        apuracao = apurar([*self.RAZAO, venda("2026-04-10", 140, 15.0, 4)], CATEGORIAS)
        swing = apuracao.vendas[-1]

        assert swing.day_trade is False
        assert reais(swing.cost_basis) == 1_480.0
        assert reais(swing.result) == 620.0

    def test_sobra_de_venda_e_venda_comum_contra_a_media(self):
        apuracao = apurar(
            [
                compra("2026-01-05", 100, 10.0, 1),
                compra("2026-03-10", 60, 12.0, 2),
                venda("2026-03-10", 100, 13.0, 3),
            ],
            CATEGORIAS,
        )
        day_trade, swing = sorted(apuracao.vendas, key=lambda v: not v.day_trade)

        assert day_trade.quantity == 60
        assert reais(day_trade.result) == 60.0
        assert swing.quantity == 40
        assert swing.avg_price == 10.0
        assert reais(swing.result) == 120.0

    def test_sobra_de_venda_maior_que_a_posicao_recusa(self):
        with pytest.raises(LedgerError, match="day trade do dia casou 60"):
            project_position([compra("2026-03-10", 60, 12.0, 1), venda("2026-03-10", 100, 13.0, 2)])


class TestApuracaoMensalDoDayTrade:
    def test_isencao_de_vinte_mil_nao_vale_para_day_trade(self):
        apuracao = apurar(
            [compra("2026-03-10", 100, 10.0, 1), venda("2026-03-10", 100, 12.0, 2)],
            CATEGORIAS,
        )
        marco = apuracao.mes("2026-03", "acoes_br", day_trade=True)

        assert reais(marco.gross_sales) == 1_200.0
        assert marco.exempt is False
        assert reais(marco.ir_amount) == 40.0, "20% sobre R$ 200, mesmo com R$ 1.200 vendidos"

    def test_venda_de_day_trade_conta_no_volume_da_isencao_do_swing(self):
        apuracao = apurar(
            [
                compra("2026-01-05", 1000, 10.0, 1),
                venda("2026-03-05", 1000, 15.0, 2),
                compra("2026-03-10", 1000, 10.0, 3),
                venda("2026-03-10", 1000, 10.0, 4),
            ],
            CATEGORIAS,
        )
        swing = apuracao.mes("2026-03", "acoes_br")

        assert reais(swing.gross_sales) == 15_000.0
        assert swing.exempt is False, "R$ 15 mil comuns + R$ 10 mil de day trade passam do teto"
        assert reais(swing.ir_amount) == 750.0
        assert "day trade" in swing.observation

    def test_prejuizo_de_day_trade_compensa_no_mes_seguinte(self):
        apuracao = apurar(
            [
                compra("2026-02-10", 100, 20.0, 1),
                venda("2026-02-10", 100, 15.0, 2),
                compra("2026-03-10", 100, 10.0, 3),
                venda("2026-03-10", 100, 18.0, 4),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br", day_trade=True)
        marco = apuracao.mes("2026-03", "acoes_br", day_trade=True)

        assert reais(fevereiro.loss_generated) == 500.0
        assert reais(marco.loss_offset_used) == 500.0
        assert reais(marco.taxable_profit) == 300.0
        assert reais(marco.ir_amount) == 60.0
        assert apuracao.saldo_de_prejuizo_day_trade == {}

    def test_prejuizo_de_day_trade_nao_abate_ganho_comum(self):
        apuracao = apurar(
            [
                compra("2026-02-10", 100, 20.0, 1),
                venda("2026-02-10", 100, 15.0, 2),
                compra("2026-01-05", 3000, 10.0, 3),
                venda("2026-03-20", 3000, 20.0, 4),
            ],
            CATEGORIAS,
        )
        marco = apuracao.mes("2026-03", "acoes_br")

        assert reais(marco.loss_offset_used) == 0.0
        assert reais(marco.ir_amount) == 4_500.0
        assert reais(apuracao.saldo_de_prejuizo_day_trade["acoes_br"]) == 500.0
        assert "acoes_br" not in apuracao.saldo_de_prejuizo

    def test_prejuizo_comum_nao_abate_ganho_de_day_trade(self):
        apuracao = apurar(
            [
                compra("2026-01-05", 3000, 20.0, 1),
                venda("2026-02-05", 3000, 10.0, 2),
                compra("2026-03-10", 100, 10.0, 3),
                venda("2026-03-10", 100, 18.0, 4),
            ],
            CATEGORIAS,
        )
        marco = apuracao.mes("2026-03", "acoes_br", day_trade=True)

        assert reais(marco.loss_offset_used) == 0.0
        assert reais(marco.ir_amount) == 160.0
        assert reais(apuracao.saldo_de_prejuizo["acoes_br"]) == 30_000.0

    def test_fii_em_day_trade_tambem_e_20_por_cento_e_apurado_a_parte(self):
        apuracao = apurar(
            [
                compra("2026-03-10", 10, 100.0, 1, ticker="HGLG11"),
                venda("2026-03-10", 10, 110.0, 2, ticker="HGLG11"),
            ],
            CATEGORIAS,
        )

        assert apuracao.mes("2026-03", "fiis") is None
        assert reais(apuracao.mes("2026-03", "fiis", day_trade=True).ir_amount) == 20.0


class TestIrrfDeUmPorCento:
    def test_a_corretora_retem_1_por_cento_do_ganho_e_ele_abate_o_imposto(self):
        apuracao = apurar(
            [compra("2026-03-10", 100, 10.0, 1), venda("2026-03-10", 100, 12.0, 2)],
            CATEGORIAS,
        )
        marco = apuracao.mes("2026-03", "acoes_br", day_trade=True)

        assert reais(marco.irrf_withheld) == 2.0
        assert reais(marco.irrf_deducted) == 2.0
        assert reais(marco.ir_payable) == 38.0
        assert reais(marco.ir_amount) == 40.0, "o imposto apurado não muda; muda o que se paga"
        assert "IRRF" in marco.observation

    def test_dia_com_prejuizo_nao_tem_retencao(self):
        apuracao = apurar(
            [compra("2026-03-10", 100, 12.0, 1), venda("2026-03-10", 100, 10.0, 2)],
            CATEGORIAS,
        )

        assert apuracao.mes("2026-03", "acoes_br", day_trade=True).irrf_withheld == 0

    def test_a_retencao_e_sobre_o_resultado_liquido_do_dia(self):
        apuracao = apurar(
            [
                compra("2026-03-10", 100, 10.0, 1),
                venda("2026-03-10", 100, 12.0, 2),
                compra("2026-03-10", 100, 20.0, 3, ticker="VALE3"),
                venda("2026-03-10", 100, 19.5, 4, ticker="VALE3"),
            ],
            CATEGORIAS,
        )

        assert reais(apuracao.mes("2026-03", "acoes_br", day_trade=True).irrf_withheld) == 1.5

    def test_retencao_de_mes_sem_imposto_fica_para_o_seguinte(self):
        apuracao = apurar(
            [
                compra("2026-02-10", 100, 10.0, 1),
                venda("2026-02-10", 100, 15.0, 2),
                compra("2026-02-20", 100, 20.0, 3),
                venda("2026-02-20", 100, 10.0, 4),
                compra("2026-03-10", 100, 10.0, 5),
                venda("2026-03-10", 100, 20.0, 6),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br", day_trade=True)
        marco = apuracao.mes("2026-03", "acoes_br", day_trade=True)

        assert reais(fevereiro.irrf_withheld) == 5.0
        assert fevereiro.irrf_deducted == 0
        assert reais(marco.irrf_deducted) == 15.0, "R$ 5 de fevereiro + R$ 10 de março"
        assert reais(marco.ir_payable) == 85.0, "20% de (1.000 − 500 de prejuízo) − 15"
        assert apuracao.saldo_de_irrf == {}


class TestDayTradeNaRota:
    def _hoje(self) -> str:
        return to_brt(time.time()).strftime("%Y-%m-%d")

    def test_compra_e_venda_do_dia_chegam_como_day_trade(self, client):
        headers = make_auth_headers("day_trade_rota")
        hoje = self._hoje()
        resposta = client.post(
            "/api/transactions",
            headers=headers,
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "quantity": 100,
                "price": 10.0,
                "traded_on": hoje,
            },
        )
        assert resposta.status_code in (200, 201), resposta.text

        vendida = client.post(
            "/api/portfolio/sell",
            headers=headers,
            json={"ticker": "PETR4", "quantity": 100, "sell_price": 12.0},
        )
        assert vendida.status_code == 200, vendida.text
        assert vendida.json()["day_trade"] is True
        assert vendida.json()["gross_profit"] == 200.0

        corpo = client.get("/api/portfolio/trades", headers=headers).json()
        mes = next(m for m in corpo["months"] if m["day_trade"])

        assert mes["ir_amount"] == 40.0
        assert mes["irrf_withheld"] == 2.0
        assert mes["ir_payable"] == 38.0
        assert corpo["trades"][0]["day_trade"] is True
