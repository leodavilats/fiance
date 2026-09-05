from __future__ import annotations

from app.core.money import quantize, to_float
from app.ledger.apuracao import ISENCAO_MENSAL, apurar
from app.ledger.entries import LedgerEntry, TransactionKind


def compra(ticker: str, dia: str, quantidade: float, preco: float, id_: int) -> LedgerEntry:
    return LedgerEntry(
        kind=TransactionKind.BUY,
        symbol=ticker,
        traded_on=dia,
        quantity=quantidade,
        price=preco,
        id=id_,
    )


def venda(
    ticker: str, dia: str, quantidade: float, preco: float, id_: int, fees: float = 0.0
) -> LedgerEntry:
    return LedgerEntry(
        kind=TransactionKind.SELL,
        symbol=ticker,
        traded_on=dia,
        quantity=quantidade,
        price=preco,
        fees=fees,
        id=id_,
    )


def ir(apuracao, mes: str, categoria: str = "acoes_br") -> float:
    apurado = apuracao.mes(mes, categoria)
    return to_float(quantize(apurado.ir_amount)) if apurado else 0.0


CATEGORIAS = {"PETR4": "acoes_br", "VALE3": "acoes_br", "HGLG11": "fiis", "BOVA11": "etfs"}


class TestLucroEPrejuizoSeCompensamNoMes:
    def _razao(self, dia_do_lucro: str, dia_do_prejuizo: str) -> list[LedgerEntry]:
        return [
            compra("PETR4", "2026-01-05", 1000, 30.0, 1),
            compra("VALE3", "2026-01-05", 1000, 60.0, 2),
            venda("PETR4", dia_do_lucro, 1000, 40.0, 3),
            venda("VALE3", dia_do_prejuizo, 1000, 50.0, 4),
        ]

    def test_lucro_antes_do_prejuizo_nao_gera_imposto(self):
        apuracao = apurar(self._razao("2026-03-05", "2026-03-20"), CATEGORIAS)

        assert ir(apuracao, "2026-03") == 0.0

    def test_prejuizo_antes_do_lucro_da_o_mesmo_numero(self):
        apuracao = apurar(self._razao("2026-03-20", "2026-03-05"), CATEGORIAS)

        assert ir(apuracao, "2026-03") == 0.0

    def test_o_resultado_do_mes_e_a_soma_e_nao_a_maior_parcela(self):
        apuracao = apurar(self._razao("2026-03-05", "2026-03-20"), CATEGORIAS)
        marco = apuracao.mes("2026-03", "acoes_br")

        assert to_float(quantize(marco.result)) == 0.0
        assert to_float(quantize(marco.gross_sales)) == 90_000.0


class TestIsencaoMensalDeVinteMil:
    def test_venda_pequena_de_acao_e_isenta(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-05", 100, 30.0, 1),
                venda("PETR4", "2026-02-10", 100, 40.0, 2),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br")

        assert fevereiro.exempt is True
        assert ir(apuracao, "2026-02") == 0.0

    def test_a_segunda_venda_do_mes_tira_a_primeira_da_isencao(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-05", 1000, 10.0, 1),
                venda("PETR4", "2026-02-10", 500, 30.0, 2),
                venda("PETR4", "2026-02-25", 500, 30.0, 3),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br")

        assert to_float(quantize(fevereiro.gross_sales)) == 30_000.0
        assert fevereiro.exempt is False
        assert ir(apuracao, "2026-02") == 3_000.0, (
            "15% sobre os R$ 20.000 de lucro do mês — isolada, nenhuma das duas vendas "
            "passaria do teto, e as duas ficariam isentas"
        )

    def test_exatamente_no_teto_ainda_e_isento(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-05", 1000, 10.0, 1),
                venda("PETR4", "2026-02-10", 1000, 20.0, 2),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br")

        assert to_float(quantize(fevereiro.gross_sales)) == float(ISENCAO_MENSAL)
        assert fevereiro.exempt is True

    def test_fii_nao_tem_isencao_por_menor_que_seja(self):
        apuracao = apurar(
            [
                compra("HGLG11", "2026-01-05", 10, 100.0, 1),
                venda("HGLG11", "2026-02-10", 10, 150.0, 2),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "fiis")

        assert fevereiro.exempt is False
        assert ir(apuracao, "2026-02", "fiis") == 100.0, "20% sobre R$ 500 de lucro"

    def test_etf_nao_tem_isencao(self):
        apuracao = apurar(
            [
                compra("BOVA11", "2026-01-05", 100, 100.0, 1),
                venda("BOVA11", "2026-02-10", 100, 110.0, 2),
            ],
            CATEGORIAS,
        )

        assert apuracao.mes("2026-02", "etfs").exempt is False
        assert ir(apuracao, "2026-02", "etfs") == 150.0


class TestPrejuizoAtravessaOsMeses:
    def test_prejuizo_de_um_mes_abate_o_ganho_do_seguinte(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 3000, 30.0, 1),
                venda("PETR4", "2026-02-10", 1500, 20.0, 2),
                venda("PETR4", "2026-03-10", 1500, 40.0, 3),
            ],
            CATEGORIAS,
        )
        marco = apuracao.mes("2026-03", "acoes_br")

        assert to_float(quantize(marco.loss_offset_used)) == 15_000.0
        assert to_float(quantize(marco.taxable_profit)) == 0.0
        assert ir(apuracao, "2026-03") == 0.0

    def test_o_prejuizo_nao_volta_no_tempo(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 3000, 30.0, 1),
                venda("PETR4", "2026-03-10", 1500, 40.0, 2),
                venda("PETR4", "2026-04-10", 1500, 20.0, 3),
            ],
            CATEGORIAS,
        )

        assert ir(apuracao, "2026-03") == 2_250.0
        assert apuracao.saldo_de_prejuizo["acoes_br"] == 15_000

    def test_prejuizo_de_fii_nao_abate_ganho_de_acao(self):
        apuracao = apurar(
            [
                compra("HGLG11", "2026-01-02", 100, 100.0, 1),
                compra("PETR4", "2026-01-02", 3000, 30.0, 2),
                venda("HGLG11", "2026-02-10", 100, 50.0, 3),
                venda("PETR4", "2026-03-10", 1500, 40.0, 4),
            ],
            CATEGORIAS,
        )

        assert ir(apuracao, "2026-03") == 2_250.0, "o ganho em ação paga cheio"
        assert apuracao.saldo_de_prejuizo["fiis"] == 5_000

    def test_prejuizo_de_mes_isento_nao_vira_credito(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 100, 100.0, 1),
                venda("PETR4", "2026-02-10", 100, 50.0, 2),
                compra("VALE3", "2026-01-02", 1000, 30.0, 3),
                venda("VALE3", "2026-03-10", 1000, 60.0, 4),
            ],
            CATEGORIAS,
        )

        assert apuracao.mes("2026-02", "acoes_br").exempt is True
        assert "acoes_br" not in apuracao.saldo_de_prejuizo
        assert ir(apuracao, "2026-03") == 4_500.0, "15% sobre R$ 30.000, sem abatimento"


class TestTodaVendaDoRazaoApura:
    def test_venda_lancada_direto_no_razao_conta(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 2000, 10.0, 1),
                venda("PETR4", "2026-02-10", 2000, 30.0, 2),
            ],
            CATEGORIAS,
        )

        assert len(apuracao.vendas) == 1
        assert ir(apuracao, "2026-02") == 6_000.0

    def test_custo_sai_pelo_preco_medio_do_momento(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 100, 10.0, 1),
                compra("PETR4", "2026-01-03", 100, 20.0, 2),
                venda("PETR4", "2026-02-10", 100, 30.0, 3),
                venda("PETR4", "2026-03-10", 100, 30.0, 4),
            ],
            CATEGORIAS,
        )

        assert [v.avg_price for v in apuracao.vendas] == [15.0, 15.0]

    def test_taxa_de_corretagem_reduz_o_resultado(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 3000, 10.0, 1),
                venda("PETR4", "2026-02-10", 3000, 20.0, 2, fees=100.0),
            ],
            CATEGORIAS,
        )
        fevereiro = apuracao.mes("2026-02", "acoes_br")

        assert to_float(quantize(fevereiro.result)) == 29_900.0

    def test_venda_sem_posicao_no_razao_e_ignorada_em_vez_de_derrubar_a_apuracao(self):
        apuracao = apurar([venda("PETR4", "2026-02-10", 100, 30.0, 1)], CATEGORIAS)

        assert apuracao.vendas == []

    def test_desdobramento_entre_compra_e_venda_ajusta_a_media(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 100, 40.0, 1),
                LedgerEntry(
                    kind=TransactionKind.SPLIT,
                    symbol="PETR4",
                    traded_on="2026-01-15",
                    ratio_from=1,
                    ratio_to=2,
                    id=2,
                ),
                venda("PETR4", "2026-02-10", 200, 25.0, 3),
            ],
            CATEGORIAS,
        )

        assert apuracao.vendas[0].avg_price == 20.0
        assert to_float(quantize(apuracao.mes("2026-02", "acoes_br").result)) == 1_000.0


class TestDeclaracaoDePosicaoAncoraAApuracao:
    def test_venda_posterior_a_declaracao_apura_pela_media_declarada(self):
        apuracao = apurar(
            [
                LedgerEntry(
                    kind=TransactionKind.ADJUST,
                    symbol="PETR4",
                    traded_on="2026-02-01",
                    quantity=1000,
                    price=25.0,
                    id=1,
                ),
                venda("PETR4", "2026-03-10", 1000, 35.0, 2),
            ],
            CATEGORIAS,
        )

        assert apuracao.vendas[0].avg_price == 25.0
        assert ir(apuracao, "2026-03") == 1_500.0

    def test_compra_anterior_a_declaracao_nao_dobra_o_custo(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-05", 1000, 10.0, 1),
                LedgerEntry(
                    kind=TransactionKind.ADJUST,
                    symbol="PETR4",
                    traded_on="2026-02-01",
                    quantity=1000,
                    price=25.0,
                    id=2,
                ),
                venda("PETR4", "2026-03-10", 1000, 35.0, 3),
            ],
            CATEGORIAS,
        )

        assert apuracao.vendas[0].avg_price == 25.0
        assert len(apuracao.vendas) == 1


class TestOImpostoDaLinhaERateio:
    def test_o_rateio_por_venda_soma_o_imposto_do_mes(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 2000, 10.0, 1),
                compra("VALE3", "2026-01-02", 1000, 10.0, 2),
                venda("PETR4", "2026-02-10", 2000, 20.0, 3),
                venda("VALE3", "2026-02-20", 1000, 30.0, 4),
            ],
            CATEGORIAS,
        )

        rateado = sum(apuracao.ir_da_venda(v) for v in apuracao.vendas)

        assert to_float(quantize(rateado)) == ir(apuracao, "2026-02")

    def test_venda_com_prejuizo_nao_recebe_imposto_no_rateio(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 3000, 10.0, 1),
                compra("VALE3", "2026-01-02", 1000, 30.0, 2),
                venda("PETR4", "2026-02-10", 3000, 20.0, 3),
                venda("VALE3", "2026-02-20", 1000, 20.0, 4),
            ],
            CATEGORIAS,
        )
        perdedora = next(v for v in apuracao.vendas if v.ticker == "VALE3")

        assert apuracao.ir_da_venda(perdedora) == 0


class TestOQueAApuracaoNaoEscondeu:
    def test_o_mes_diz_por_que_o_numero_e_aquele(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 3000, 10.0, 1),
                venda("PETR4", "2026-02-10", 3000, 20.0, 2),
            ],
            CATEGORIAS,
        )

        assert "15%" in apuracao.mes("2026-02", "acoes_br").observation

    def test_mes_isento_explica_a_isencao(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 100, 10.0, 1),
                venda("PETR4", "2026-02-10", 100, 20.0, 2),
            ],
            CATEGORIAS,
        )

        assert "isenção" in apuracao.mes("2026-02", "acoes_br").observation

    def test_mes_com_abatimento_diz_quanto_foi_abatido(self):
        apuracao = apurar(
            [
                compra("PETR4", "2026-01-02", 6000, 30.0, 1),
                venda("PETR4", "2026-02-10", 3000, 20.0, 2),
                venda("PETR4", "2026-03-10", 3000, 50.0, 3),
            ],
            CATEGORIAS,
        )

        assert "prejuízo acumulado" in apuracao.mes("2026-03", "acoes_br").observation
