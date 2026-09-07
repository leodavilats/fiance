from __future__ import annotations

from decimal import Decimal

import pytest

from app.cashflow.entries import CashEntry, CashError, CashKind
from app.cashflow.month import estimar_variavel, projetar_mes


def entrada(categoria: str, valor: float, dia: str, pago: str | None = None, **kw) -> CashEntry:
    return CashEntry(
        kind=CashKind.INCOME,
        category=categoria,
        description=categoria,
        amount=valor,
        due_on=dia,
        paid_on=pago if pago is not None else dia,
        **kw,
    )


def saida(categoria: str, valor: float, dia: str, pago: str | None = "mesmo") -> CashEntry:
    return CashEntry(
        kind=CashKind.EXPENSE,
        category=categoria,
        description=categoria,
        amount=valor,
        due_on=dia,
        paid_on=dia if pago == "mesmo" else pago,
    )


def mes_do_wireframe() -> list[CashEntry]:
    """O mês de exemplo do wireframe da ponte, no dia 20."""
    return [
        entrada("salario", 6418.73, "2026-09-05"),
        saida("moradia", 2150.00, "2026-09-05"),
        saida("mercado", 804.15, "2026-09-14"),
        saida("divida", 1099.92, "2026-09-12"),
        saida("contas_da_casa", 187.44, "2026-09-22", pago=None),
        saida("contas_da_casa", 129.90, "2026-09-25", pago=None),
    ]


def historico_variavel() -> list[CashEntry]:
    """Três meses fechados de gasto variável, para a estimativa existir."""
    return [
        saida("mercado", 1204.15, "2026-06-20"),
        saida("mercado", 1140.60, "2026-07-20"),
        saida("mercado", 1063.28, "2026-08-20"),
    ]


class TestOMesSeparaFatoDeProjecao:
    def test_livre_agora_e_fato_e_nao_desconta_estimativa(self):
        p = projetar_mes(mes_do_wireframe(), "2026-09")

        assert p.entrou == Decimal("6418.73")
        assert p.saiu == Decimal("4054.07")
        assert p.comprometido == Decimal("317.34")
        assert p.livre_agora == Decimal("2047.32")

    def test_sem_mes_fechado_nao_ha_faixa_e_a_sobra_e_o_livre(self):
        p = projetar_mes(mes_do_wireframe(), "2026-09")

        assert p.tem_faixa is False
        assert p.sobra_piso == p.livre_agora, (
            "sem historico a estimativa nao existe, e ausencia de estimativa nao vira zero "
            "otimista: a sobra e o proprio livre, e a tela diz que nao ha faixa"
        )

    def test_com_historico_a_sobra_e_o_livre_menos_o_que_ainda_deve_sair(self):
        p = projetar_mes(mes_do_wireframe() + historico_variavel(), "2026-09")

        assert p.tem_faixa is True
        assert p.estimativa.meses_de_base == ("2026-06", "2026-07", "2026-08")
        assert p.estimativa.ja_gasto == Decimal("804.15")

        # O maior dos tres meses fechados manda no piso; o menor, no teto.
        assert p.estimativa.restante_alto == Decimal("400.00")
        assert p.estimativa.restante_baixo == Decimal("259.13")

        assert p.sobra_piso == Decimal("1647.32")
        assert p.sobra_teto == Decimal("1788.19")

    def test_a_diferenca_entre_as_duas_telas_e_exatamente_a_estimativa(self):
        p = projetar_mes(mes_do_wireframe() + historico_variavel(), "2026-09")

        assert p.livre_agora - p.sobra_piso == p.estimativa.restante_alto, (
            "e a frase que liga /mes a /sobra: livre agora menos o que ainda deve sair"
        )

    def test_o_mes_fecha_na_conta(self):
        p = projetar_mes(mes_do_wireframe() + historico_variavel(), "2026-09")

        divida = Decimal("890.00")
        ordens = Decimal("464.40") + Decimal("197.00")
        resto = Decimal("95.92")

        assert divida + ordens + resto == p.sobra_piso, (
            "o exemplo do wireframe fecha: divida + ordens em cota inteira + o resto que fica "
            "abaixo da ordem minima somam o piso"
        )


class TestOQueEntraNaBaseDeRenda:
    def test_provento_e_reembolso_nao_inflam_a_renda_de_base(self):
        entries = mes_do_wireframe() + [
            entrada("provento", 340.00, "2026-09-15", derived=True),
            entrada("reembolso", 212.80, "2026-09-16"),
        ]
        p = projetar_mes(entries, "2026-09")

        assert p.entrou == Decimal("6971.53"), "as duas entram no caixa"
        assert p.renda_de_base == Decimal("6418.73"), (
            "mas nenhuma das duas e renda recorrente: provento nao se repete por contrato e "
            "reembolso e dinheiro que voltou, nao dinheiro que se ganhou"
        )

    def test_provento_lancado_a_mao_e_recusado(self):
        with pytest.raises(CashError, match="derivado do razão"):
            CashEntry(
                kind=CashKind.INCOME,
                category="provento",
                description="PETR4",
                amount=340.00,
                due_on="2026-09-15",
            )

    def test_provento_derivado_do_razao_e_aceito(self):
        e = entrada("provento", 340.00, "2026-09-15", derived=True)

        assert e.derived is True
        assert e.kind is CashKind.INCOME


class TestPagamentoDeDividaNaoEConsumo:
    def test_divida_sai_do_caixa_mas_nao_entra_na_estimativa(self):
        entries = [
            saida("divida", 1099.92, "2026-06-12"),
            saida("divida", 1099.92, "2026-07-12"),
            saida("divida", 1099.92, "2026-08-12"),
        ]
        est = estimar_variavel(entries, "2026-09")

        assert est.existe is False, (
            "pagamento de divida nao e custo de vida; se entrasse na base, a estimativa de "
            "gasto variavel diria que a rotina custa o que a divida custa"
        )

    def test_mas_o_pagamento_reduz_o_livre_do_mes(self):
        p = projetar_mes(mes_do_wireframe(), "2026-09")

        assert Decimal("1099.92") <= p.saiu


class TestSobraNegativa:
    def test_mes_que_fecha_negativo_e_marcado(self):
        entries = [
            entrada("salario", 2000.00, "2026-09-05"),
            saida("moradia", 2150.00, "2026-09-05"),
        ]
        p = projetar_mes(entries, "2026-09")

        assert p.livre_agora == Decimal("-150.00")
        assert p.negativa is True

    def test_conta_a_vencer_entra_no_comprometido_e_no_a_vencer(self):
        p = projetar_mes(mes_do_wireframe(), "2026-09")

        assert len(p.a_vencer) == 2
        assert [e.due_on for e in p.a_vencer] == ["2026-09-22", "2026-09-25"]


class TestACompetenciaEODiaDoPagamento:
    def test_conta_paga_com_atraso_conta_no_mes_do_pagamento(self):
        e = saida("contas_da_casa", 187.44, "2026-08-25", pago="2026-09-03")

        assert e.mes == "2026-09", (
            "o caixa mede quando o dinheiro se moveu, nao quando a conta venceu"
        )

    def test_conta_nao_paga_conta_no_mes_do_vencimento(self):
        e = saida("contas_da_casa", 187.44, "2026-09-22", pago=None)

        assert e.mes == "2026-09"
        assert e.comprometido is True
