from __future__ import annotations

import random
from decimal import Decimal

import pytest

from app.core.money import cents, from_cents, money, quantize, sum_money, to_float
from app.ledger import LedgerEntry, TransactionKind, project_position
from app.ledger.apuracao import apurar


class TestConversao:
    def test_float_vira_decimal_pelo_texto_e_nao_pelo_binario(self):
        assert money(0.1) == Decimal("0.1")
        assert Decimal(0.1) != Decimal("0.1")

    def test_decimal_passa_intacto(self):
        assert money(Decimal("1.005")) == Decimal("1.005")

    def test_arredondamento_e_meio_para_cima_nao_bancario(self):
        assert quantize("2.345") == Decimal("2.35")
        assert quantize("2.355") == Decimal("2.36")
        assert round(2.5) == 2, "o contraste: é este comportamento que não serve"

    def test_centavos_ida_e_volta(self):
        assert cents("19.90") == 1990
        assert from_cents(1990) == Decimal("19.90")


class TestErroAcumulado:
    def test_mil_operacoes_fecham_com_erro_zero(self):
        assert sum_money(["0.01"] * 1000) == Decimal("10.00")
        assert sum_money(["0.07"] * 100) == Decimal("7.00")

        assert sum(0.07 for _ in range(100)) != 7.0, "o contraste, em float"

    def test_carteira_de_mil_compras_tem_custo_exato(self):
        entradas = [
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="PETR4",
                traded_on="2024-01-10",
                quantity=1,
                price=0.07,
                id=i,
            )
            for i in range(1000)
        ]

        posicao = project_position(entradas)

        assert posicao.total_cost_exact == Decimal("70.00")
        assert posicao.avg_price_exact == Decimal("0.07")

    def test_taxas_de_mil_notas_somam_exatamente(self):
        entradas = [
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="PETR4",
                traded_on="2024-01-10",
                quantity=1,
                price=10.0,
                fees=2.90,
                id=i,
            )
            for i in range(1000)
        ]

        assert project_position(entradas).total_fees_exact == Decimal("2900.00")

    def test_compra_e_venda_alternadas_zeram_o_custo_sem_residuo(self):
        entradas = []
        for i in range(500):
            entradas.append(
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="PETR4",
                    traded_on="2024-01-10",
                    quantity=3,
                    price=10.10,
                    id=i * 2,
                )
            )
            entradas.append(
                LedgerEntry(
                    kind=TransactionKind.SELL,
                    symbol="PETR4",
                    traded_on="2024-01-10",
                    quantity=3,
                    price=10.10,
                    id=i * 2 + 1,
                )
            )

        posicao = project_position(entradas)

        assert posicao.quantity_exact == Decimal("0")
        assert posicao.total_cost_exact == Decimal("0")
        assert posicao.realized_pnl_exact == Decimal("0"), (
            "comprar e vender pelo mesmo preço não gera lucro nem prejuízo"
        )


class TestPropriedades:
    @staticmethod
    def _random_entries(seed: int, count: int) -> list[LedgerEntry]:
        rng = random.Random(seed)
        entries: list[LedgerEntry] = []
        held = 0
        for i in range(count):
            price = Decimal(rng.randrange(100, 10000)) / 100
            if held == 0 or rng.random() < 0.6:
                quantity = rng.randrange(1, 200)
                held += quantity
                entries.append(
                    LedgerEntry(
                        kind=TransactionKind.BUY,
                        symbol="PETR4",
                        traded_on="2024-01-10",
                        quantity=quantity,
                        price=float(price),
                        fees=float(Decimal(rng.randrange(0, 2000)) / 100),
                        id=i,
                    )
                )
            else:
                quantity = rng.randrange(1, held + 1)
                held -= quantity
                entries.append(
                    LedgerEntry(
                        kind=TransactionKind.SELL,
                        symbol="PETR4",
                        traded_on="2024-01-10",
                        quantity=quantity,
                        price=float(price),
                        id=i,
                    )
                )
        return entries

    @pytest.mark.parametrize("seed", range(8))
    def test_custo_nunca_fica_negativo(self, seed):
        posicao = project_position(self._random_entries(seed, 200))

        assert posicao.total_cost_exact >= 0
        assert posicao.quantity_exact >= 0

    @pytest.mark.parametrize("seed", range(8))
    def test_custo_e_sempre_quantidade_vezes_preco_medio(self, seed):
        posicao = project_position(self._random_entries(seed, 200))

        assert posicao.avg_price_exact * posicao.quantity_exact == pytest.approx(
            posicao.total_cost_exact
        )

    @pytest.mark.parametrize("seed", range(8))
    def test_zerar_a_posicao_zera_o_custo(self, seed):
        entradas = self._random_entries(seed, 200)
        posicao_parcial = project_position(entradas)

        if posicao_parcial.quantity_exact > 0:
            entradas.append(
                LedgerEntry(
                    kind=TransactionKind.SELL,
                    symbol="PETR4",
                    traded_on="2024-01-11",
                    quantity=float(posicao_parcial.quantity_exact),
                    price=10.0,
                    id=10_000,
                )
            )

        final = project_position(entradas)

        assert final.quantity_exact == 0
        assert final.total_cost_exact == 0


def _compra(ticker, dia, quantidade, preco, id_):
    return LedgerEntry(
        kind=TransactionKind.BUY,
        symbol=ticker,
        traded_on=dia,
        quantity=quantidade,
        price=preco,
        id=id_,
    )


def _venda(ticker, dia, quantidade, preco, id_):
    return LedgerEntry(
        kind=TransactionKind.SELL,
        symbol=ticker,
        traded_on=dia,
        quantity=quantidade,
        price=preco,
        id=id_,
    )


class TestApuracaoFiscal:
    def test_o_imposto_sai_dos_exatos_e_nao_dos_arredondados(self):
        apuracao = apurar(
            [
                _compra("PETR4", "2026-01-05", 333, 10.115, 1),
                _venda("PETR4", "2026-02-10", 333, 30.335, 2),
                _compra("VALE3", "2026-01-05", 1000, 20.0, 3),
                _venda("VALE3", "2026-02-11", 1000, 20.0, 4),
            ],
            {"PETR4": "acoes_br", "VALE3": "acoes_br"},
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br")

        bruto = Decimal("333") * Decimal("30.335") - Decimal("333") * Decimal("10.115")
        imposto = bruto * Decimal("0.15")

        assert fevereiro.exempt is False
        assert to_float(quantize(fevereiro.result)) == to_float(quantize(bruto))
        assert to_float(quantize(fevereiro.ir_amount)) == to_float(quantize(imposto))

    def test_a_isencao_mensal_e_comparada_com_valor_exato(self):
        def imposto_de(preco_de_venda: str) -> float:
            apuracao = apurar(
                [
                    _compra("PETR4", "2026-01-05", 1000, 5.0, 1),
                    _venda("PETR4", "2026-02-10", 1000, float(preco_de_venda), 2),
                ],
                {"PETR4": "acoes_br"},
            )
            return to_float(quantize(apuracao.mes("2026-02", "acoes_br").ir_amount))

        assert imposto_de("20.0") == 0.0, "exatamente R$ 20.000 ainda é isento"
        assert imposto_de("20.001") > 0.0, "um centésimo acima já tributa o mês inteiro"


class TestSemFloatOndeImporta:
    def test_a_projecao_guarda_o_valor_fiscal_em_decimal(self):
        posicao = project_position(
            [
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="PETR4",
                    traded_on="2024-01-10",
                    quantity=1,
                    price=1.0,
                )
            ]
        )

        for campo in (
            "quantity_exact",
            "total_cost_exact",
            "realized_pnl_exact",
            "total_fees_exact",
            "avg_price_exact",
        ):
            assert isinstance(getattr(posicao, campo), Decimal), campo

    def test_a_borda_da_api_continua_em_float(self):
        posicao = project_position(
            [
                LedgerEntry(
                    kind=TransactionKind.BUY,
                    symbol="PETR4",
                    traded_on="2024-01-10",
                    quantity=1,
                    price=1.0,
                )
            ]
        )

        for valor in posicao.as_dict().values():
            assert not isinstance(valor, Decimal)
