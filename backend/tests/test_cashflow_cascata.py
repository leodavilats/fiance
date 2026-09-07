from __future__ import annotations

from decimal import Decimal

import pytest

from app.cashflow import cascata
from app.cashflow.cascata import TipoDePasso
from app.cashflow.debt import ClasseDaDivida, Debt, DebtError, classificar, classificar_todas
from app.cashflow.entries import CashEntry, CashKind

PISO = Decimal("1647.32")


def divida(taxa: float | None, saldo: float = 890.00, kind: str = "rotativo_cartao") -> Debt:
    return Debt(kind=kind, description="Rotativo do cartão", balance=saldo, monthly_rate=taxa)


class TestAClasseSaiDoCustoNaoDoTipo:
    def test_o_mesmo_instrumento_muda_de_classe_com_a_taxa(self):
        caro = classificar(divida(3.5, kind="credito_pessoal"), retorno_mensal_da_carteira=0.9)
        barato = classificar(divida(0.4, kind="credito_pessoal"), retorno_mensal_da_carteira=0.9)

        assert caro.classe is ClasseDaDivida.CARA
        assert barato.classe is ClasseDaDivida.ADMINISTRAVEL, (
            "consignado a 0,4% e consignado a 3,5% nao sao a mesma decisao; se o tipo "
            "decidisse, os dois sairiam iguais"
        )

    def test_financiamento_de_imovel_a_taxa_alta_e_caro(self):
        lido = classificar(
            divida(2.1, saldo=180000.0, kind="financiamento_imovel"),
            retorno_mensal_da_carteira=0.9,
        )

        assert lido.classe is ClasseDaDivida.CARA, (
            "o produto nao tem lista de instrumentos bons e ruins — tem uma conta"
        )

    def test_sem_taxa_informada_nao_ha_classe(self):
        lido = classificar(divida(None), retorno_mensal_da_carteira=0.9)

        assert lido.classe is ClasseDaDivida.SEM_TAXA
        assert lido.taxa_de_virada is None, (
            "o produto nao estima taxa de rotativo: varia por banco e por dia"
        )

    def test_sem_carteira_a_referencia_e_o_cdi(self):
        lido = classificar(divida(1.2), retorno_mensal_da_carteira=None, cdi_mensal=0.88)

        assert lido.fonte_da_referencia == "cdi"
        assert lido.classe is ClasseDaDivida.CARA

    def test_sem_carteira_e_sem_cdi_nao_ha_leitura(self):
        lido = classificar(divida(1.2), retorno_mensal_da_carteira=None, cdi_mensal=None)

        assert lido.classe is ClasseDaDivida.SEM_TAXA
        assert lido.fonte_da_referencia == "sem_referencia"

    def test_a_taxa_de_virada_e_a_propria_referencia(self):
        lido = classificar(divida(14.9), retorno_mensal_da_carteira=0.9)

        assert lido.taxa_de_virada == Decimal("0.9"), (
            "julgamento vem com a condicao conferivel que o desfaz, e ela sai por algebra"
        )

    def test_taxa_igual_a_referencia_nao_e_cara(self):
        lido = classificar(divida(0.9), retorno_mensal_da_carteira=0.9)

        assert lido.classe is ClasseDaDivida.ADMINISTRAVEL, (
            "empatar nao justifica antecipar quitacao; isso e decisao de fluxo de caixa"
        )

    def test_taxa_negativa_e_recusada(self):
        with pytest.raises(DebtError, match="rendimento"):
            divida(-0.5)

    def test_as_caras_vem_primeiro_e_a_de_maior_taxa_na_frente(self):
        lidas = classificar_todas(
            [
                Debt(
                    kind="financiamento_imovel",
                    description="Casa",
                    balance=180000,
                    monthly_rate=0.7,
                ),
                Debt(kind="rotativo_cartao", description="Cartão", balance=890, monthly_rate=14.9),
                Debt(
                    kind="cheque_especial", description="Especial", balance=1200, monthly_rate=8.2
                ),
                Debt(kind="parcelamento", description="Sem taxa", balance=400, monthly_rate=None),
            ],
            retorno_mensal_da_carteira=0.9,
        )

        assert [d.divida.description for d in lidas] == ["Cartão", "Especial", "Sem taxa", "Casa"]


class TestAOrdemPodeDizerNaoAporte:
    def test_divida_cara_maior_que_a_sobra_consome_tudo(self):
        lidas = classificar_todas([divida(14.9, saldo=4000.0)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(PISO, lidas)

        assert len(c.passos) == 1
        assert c.passos[0].tipo is TipoDePasso.DIVIDA
        assert c.passos[0].valor == PISO
        assert c.tem_aporte is False, (
            "terminar sem aporte e sucesso da tela, nao falha: com divida cara consumindo a "
            "sobra inteira, a resposta certa e nao aportar"
        )
        assert c.sobrou_para_aporte == Decimal("0")

    def test_o_exemplo_do_wireframe_fecha(self):
        lidas = classificar_todas([divida(14.9)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(PISO, lidas, desvio_de_meta="FIIs, 4,1 p.p. atrás")

        assert [p.tipo for p in c.passos] == [TipoDePasso.DIVIDA, TipoDePasso.APORTE]
        assert c.passos[0].valor == Decimal("890.00")
        assert c.passos[1].valor == Decimal("757.32")
        assert c.sobrou_para_aporte == Decimal("757.32")

    def test_divida_administravel_nao_vira_passo(self):
        lidas = classificar_todas([divida(0.5)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(PISO, lidas)

        assert [p.tipo for p in c.passos] == [TipoDePasso.APORTE]
        assert c.passos[0].valor == PISO, (
            "o produto nao pede quitacao antecipada de divida barata: isso e decisao de fluxo "
            "de caixa da pessoa, nao regua financeira"
        )

    def test_divida_sem_taxa_nao_vira_passo(self):
        lidas = classificar_todas([divida(None)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(PISO, lidas)

        assert [p.tipo for p in c.passos] == [TipoDePasso.APORTE]

    def test_sobra_negativa_nao_produz_passo_nenhum(self):
        lidas = classificar_todas([divida(14.9)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(Decimal("-150.00"), lidas)

        assert c.passos == ()
        assert c.tem_aporte is False

    def test_o_passo_de_divida_carrega_o_que_o_derrubaria(self):
        lidas = classificar_todas([divida(14.9)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(PISO, lidas)

        assert "0.90% ao mês" in c.passos[0].falsificador
        assert "14.90% ao mês" in c.passos[0].motivo

    def test_sem_meta_o_aporte_diz_que_ordenou_por_score(self):
        c = cascata.montar(PISO, [])

        assert c.passos[0].referencia == "score"
        assert "score" in c.passos[0].motivo


class TestAReservaVemDepoisDaDividaCara:
    def gasto_fixo_de_tres_meses(self) -> list[CashEntry]:
        return [
            CashEntry(
                kind=CashKind.EXPENSE,
                category="moradia",
                description="Aluguel",
                amount=2150.00,
                due_on=f"2026-0{m}-05",
                paid_on=f"2026-0{m}-05",
            )
            for m in (6, 7, 8)
        ]

    def test_a_base_da_reserva_e_o_gasto_fixo_da_propria_pessoa(self):
        base = cascata.gasto_fixo_mensal(self.gasto_fixo_de_tres_meses())

        assert base == Decimal("2150.00")

    def test_sem_mes_fechado_nao_ha_base_e_nao_ha_passo(self):
        c = cascata.montar(
            PISO,
            [],
            reserva_meses_alvo=6,
            reserva_atual=Decimal("0"),
            gasto_fixo=cascata.gasto_fixo_mensal([]),
        )

        assert [p.tipo for p in c.passos] == [TipoDePasso.APORTE]

    def test_a_divida_cara_come_a_sobra_antes_da_reserva(self):
        lidas = classificar_todas([divida(14.9, saldo=4000.0)], retorno_mensal_da_carteira=0.9)
        c = cascata.montar(
            PISO,
            lidas,
            reserva_meses_alvo=6,
            reserva_atual=Decimal("0"),
            gasto_fixo=Decimal("2150.00"),
        )

        assert [p.tipo for p in c.passos] == [TipoDePasso.DIVIDA], (
            "a reserva existe para nao precisar tomar divida cara; quem ja a tem nao precisa se "
            "proteger do risco de contrai-la, e poupar a juros de poupanca enquanto paga 14,9% "
            "ao mes e perder nas duas pontas"
        )

    def test_sem_divida_cara_a_reserva_vem_antes_do_aporte(self):
        # Alvo de 6 meses a 2.150 = 12.900. Com 12.000 guardados, faltam 900 -- menos que o
        # piso, entao os dois passos cabem.
        c = cascata.montar(
            PISO,
            [],
            reserva_meses_alvo=6,
            reserva_atual=Decimal("12000.00"),
            gasto_fixo=Decimal("2150.00"),
        )

        assert [p.tipo for p in c.passos] == [TipoDePasso.RESERVA, TipoDePasso.APORTE]
        assert c.passos[0].valor == Decimal("900.00")
        assert c.sobrou_para_aporte == Decimal("747.32")

    def test_reserva_que_falta_mais_que_a_sobra_consome_a_sobra_inteira(self):
        # Faltam 1.900 e o piso e 1.647,32: nenhum passo pode gastar dinheiro que nao existe.
        c = cascata.montar(
            PISO,
            [],
            reserva_meses_alvo=6,
            reserva_atual=Decimal("11000.00"),
            gasto_fixo=Decimal("2150.00"),
        )

        assert [p.tipo for p in c.passos] == [TipoDePasso.RESERVA]
        assert c.passos[0].valor == PISO
        assert c.tem_aporte is False

    def test_reserva_completa_nao_vira_passo(self):
        c = cascata.montar(
            PISO,
            [],
            reserva_meses_alvo=6,
            reserva_atual=Decimal("13000.00"),
            gasto_fixo=Decimal("2150.00"),
        )

        assert [p.tipo for p in c.passos] == [TipoDePasso.APORTE]

    def test_sem_alvo_declarado_nao_ha_passo_de_reserva(self):
        c = cascata.montar(
            PISO,
            [],
            reserva_meses_alvo=None,
            reserva_atual=Decimal("0"),
            gasto_fixo=Decimal("2150"),
        )

        assert [p.tipo for p in c.passos] == [TipoDePasso.APORTE], (
            "o produto nao inventa um alvo de seis meses: numero de mercado solto e "
            "exatamente o que a regua de divida proibe"
        )
