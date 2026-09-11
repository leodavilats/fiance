from __future__ import annotations

from decimal import Decimal

import pytest

from app.cashflow import CashEntry, CashError, CashKind, Debt
from app.services import cashflow_service
from app.storage import cash_store, portfolio_store


def saida(categoria: str, valor: float, dia: str, pago: str | None = "mesmo") -> CashEntry:
    return CashEntry(
        kind=CashKind.EXPENSE,
        category=categoria,
        description=categoria,
        amount=valor,
        due_on=dia,
        paid_on=dia if pago == "mesmo" else pago,
    )


def entrada(categoria: str, valor: float, dia: str) -> CashEntry:
    return CashEntry(
        kind=CashKind.INCOME,
        category=categoria,
        description=categoria,
        amount=valor,
        due_on=dia,
        paid_on=dia,
    )


@pytest.fixture
def uid(request) -> str:
    return f"u_caixa_{request.node.name}"[:60]


@pytest.fixture
def semeado(client, uid) -> str:
    cashflow_service.registrar(entrada("salario", 6418.73, "2026-09-05"), user_id=uid)
    cashflow_service.registrar(saida("moradia", 2150.00, "2026-09-05"), user_id=uid)
    cashflow_service.registrar(saida("mercado", 804.15, "2026-09-14"), user_id=uid)
    cashflow_service.registrar(saida("divida", 1099.92, "2026-09-12"), user_id=uid)
    cashflow_service.registrar(
        saida("contas_da_casa", 187.44, "2026-09-22", pago=None), user_id=uid
    )
    cashflow_service.registrar(
        saida("contas_da_casa", 129.90, "2026-09-25", pago=None), user_id=uid
    )
    return uid


def semear_provento(uid: str, valor: float = 340.00) -> dict:
    return portfolio_store.create_dividend_received(
        user_id=uid, ticker="PETR4", paid_at="2026-09-15", amount=valor
    )


def historico_de_mercado(uid: str) -> None:
    for dia, valor in [("2026-06-20", 1204.15), ("2026-07-20", 1140.60), ("2026-08-20", 1063.28)]:
        cashflow_service.registrar(saida("mercado", valor, dia), user_id=uid)


class TestOCaixaLeORazaoESemContarDuasVezes:
    def test_provento_recebido_entra_uma_vez_so(self, semeado):
        semear_provento(semeado)

        p = cashflow_service.mes(referencia="2026-09", user_id=semeado)

        assert p.entrou == Decimal("6758.73"), "6418,73 de salário + 340,00 de provento"
        assert p.renda_de_base == Decimal("6418.73"), (
            "provento entra no caixa e nao na base de renda: nao se repete por contrato"
        )

    def test_o_provento_nao_existe_na_tabela_de_caixa(self, semeado):
        semear_provento(semeado)

        na_tabela = cash_store.list_entries(user_id=semeado)
        no_caixa = cashflow_service.entradas(user_id=semeado)

        assert all(not e.derived for e in na_tabela), (
            "derivado nao se grava: duplicar fica impossivel por construcao, e nao possivel e "
            "evitado por disciplina"
        )
        assert len([e for e in no_caixa if e.derived]) == 1

    def test_ler_o_mes_muitas_vezes_nao_muda_nada(self, semeado):
        semear_provento(semeado)

        antes = len(cash_store.list_entries(user_id=semeado))
        for _ in range(3):
            p = cashflow_service.mes(referencia="2026-09", user_id=semeado)
        depois = len(cash_store.list_entries(user_id=semeado))

        assert antes == depois, "GET nao escreve"
        assert p.entrou == Decimal("6758.73")

    def test_provento_apagado_no_razao_desaparece_do_caixa(self, semeado):
        criada = semear_provento(semeado)
        assert cashflow_service.mes(referencia="2026-09", user_id=semeado).entrou == Decimal(
            "6758.73"
        )

        portfolio_store.delete_dividend_received(criada["id"], user_id=semeado)

        assert cashflow_service.mes(referencia="2026-09", user_id=semeado).entrou == Decimal(
            "6418.73"
        ), "o caixa le o razao, entao apagar la some aqui — sem lancamento orfao"

    def test_provento_corrigido_no_razao_corrige_o_caixa(self, semeado):
        criada = semear_provento(semeado)

        portfolio_store.update_dividend_received(criada["id"], user_id=semeado, amount=412.55)

        p = cashflow_service.mes(referencia="2026-09", user_id=semeado)
        assert p.entrou == Decimal("6831.28"), "6418,73 + 412,55"

    def test_entrada_derivada_nao_tem_id_para_apagar(self, semeado):
        semear_provento(semeado)
        derivada = next(e for e in cashflow_service.entradas(user_id=semeado) if e.derived)

        assert derivada.id is None, (
            "sem linha na tabela nao ha id, e sem id nao ha o que apagar — a guarda deixou de "
            "precisar existir"
        )

    def test_gravar_entrada_derivada_e_recusado(self, semeado):
        derivada = CashEntry(
            kind=CashKind.INCOME,
            category="provento",
            description="PETR4",
            amount=340.0,
            due_on="2026-09-15",
            paid_on="2026-09-15",
            derived=True,
        )

        with pytest.raises(CashError, match="não se grava"):
            cashflow_service.registrar(derivada, user_id=semeado)

    def test_so_provento_no_razao_nao_conta_como_caixa_lancado(self, client, uid):
        semear_provento(uid)

        assert cashflow_service.tem_caixa(user_id=uid) is False, (
            "quem so tem provento sincronizado nao lancou caixa nenhum; manda-lo para o Mes "
            "seria a tela vazia que a IA nova declarou como risco"
        )

    def test_um_lancamento_proprio_ja_conta_como_caixa(self, semeado):
        assert cashflow_service.tem_caixa(user_id=semeado) is True


class TestAPonteVindaDoBanco:
    def test_a_cascata_sai_do_piso_e_a_divida_cara_vem_primeiro(self, semeado):
        cash_store.add_debt(
            Debt(
                kind="rotativo_cartao",
                description="Rotativo do cartão",
                balance=890.00,
                monthly_rate=14.9,
            ),
            user_id=semeado,
        )
        historico_de_mercado(semeado)

        projecao, cascata = cashflow_service.sobra(
            referencia_mensal=0.9,
            tem_carteira=True,
            mes_referencia="2026-09",
            desvio_de_meta="FIIs, 4,1 p.p. atrás",
            user_id=semeado,
        )

        assert projecao.livre_agora == Decimal("2047.32")
        assert projecao.sobra_piso == Decimal("1647.32")
        assert [p.tipo.value for p in cascata.passos] == ["debt", "contribution"]
        assert cascata.passos[0].valor == Decimal("890.00")
        assert cascata.sobrou_para_aporte == Decimal("757.32")

    def test_divida_cara_grande_termina_sem_aporte(self, semeado):
        cash_store.add_debt(
            Debt(
                kind="cheque_especial",
                description="Cheque especial",
                balance=9000.00,
                monthly_rate=8.2,
            ),
            user_id=semeado,
        )
        historico_de_mercado(semeado)

        _, cascata = cashflow_service.sobra(
            referencia_mensal=0.9, tem_carteira=True, mes_referencia="2026-09", user_id=semeado
        )

        assert cascata.tem_aporte is False
        assert cascata.passos[0].valor == Decimal("1647.32")

    def test_sem_divida_a_cascata_tem_so_o_aporte(self, semeado):
        _, cascata = cashflow_service.sobra(
            referencia_mensal=0.9, tem_carteira=True, mes_referencia="2026-09", user_id=semeado
        )

        assert [p.tipo.value for p in cascata.passos] == ["contribution"]


class TestOCdiVemComposto:
    def test_anual_para_mensal_e_por_juros_compostos(self):
        assert cashflow_service._mensal_de_anual(12.0) == pytest.approx(0.9489, abs=1e-4)

    def test_dividir_por_doze_afrouxaria_a_regua(self, semeado):
        cash_store.add_debt(
            Debt(
                kind="credito_pessoal",
                description="Empréstimo",
                balance=3000.0,
                monthly_rate=0.97,
            ),
            user_id=semeado,
        )

        lidas = cashflow_service.dividas(
            referencia_mensal=None, tem_carteira=False, cdi_anual=12.0, user_id=semeado
        )

        assert lidas[0]["reference_source"] == "cdi"
        assert lidas[0]["reference_monthly"] == pytest.approx(0.9489, abs=1e-3)
        assert lidas[0]["class"] == "expensive"
        assert 0.97 < 12.0 / 12, "com a conta ingenua esta divida passaria por administravel"


class TestAPortaUnicaDeEscrita:
    def test_marcar_paga_move_a_conta_para_o_realizado(self, semeado):
        antes = cashflow_service.mes(referencia="2026-09", user_id=semeado)
        assert len(antes.a_vencer) == 2

        cashflow_service.marcar_paga(antes.a_vencer[0].id, "2026-09-22", user_id=semeado)
        depois = cashflow_service.mes(referencia="2026-09", user_id=semeado)

        assert len(depois.a_vencer) == 1
        assert depois.saiu == antes.saiu + Decimal("187.44")
        assert depois.comprometido == antes.comprometido - Decimal("187.44")
        assert depois.livre_agora == antes.livre_agora, (
            "pagar o que ja estava comprometido nao muda o livre: ele ja contava a conta"
        )

    def test_lancamento_de_outro_titular_nao_aparece(self, semeado):
        cashflow_service.registrar(
            entrada("salario", 9999.00, "2026-09-05"), user_id=f"{semeado[:50]}_viz"
        )

        p = cashflow_service.mes(referencia="2026-09", user_id=semeado)

        assert p.entrou == Decimal("6418.73")
