from __future__ import annotations

import pytest

from app.cashflow.entries import CashEntry, CashError, CashKind
from app.cashflow.template import dia_no_mes, montar_molde, repete_todo_mes


def saida(categoria: str, valor: float, dia: str, pago: bool = True) -> CashEntry:
    return CashEntry(
        kind=CashKind.EXPENSE,
        category=categoria,
        description=categoria,
        amount=valor,
        due_on=dia,
        paid_on=dia if pago else None,
    )


def entrada(categoria: str, valor: float, dia: str, descricao: str | None = None) -> CashEntry:
    return CashEntry(
        kind=CashKind.INCOME,
        category=categoria,
        description=descricao or categoria,
        amount=valor,
        due_on=dia,
        paid_on=dia,
    )


def agosto() -> list[CashEntry]:
    return [
        entrada("salario", 6418.73, "2026-08-05"),
        saida("moradia", 2150.00, "2026-08-05"),
        saida("contas_da_casa", 187.44, "2026-08-22"),
        saida("divida", 1099.92, "2026-08-12"),
        saida("mercado", 804.15, "2026-08-14"),
        saida("lazer", 96.00, "2026-08-19"),
    ]


class TestOQueRepeteEOQueNao:
    def test_o_fixo_a_divida_e_o_salario_repetem(self):
        molde = {c.entry.category: c for c in montar_molde(agosto(), "2026-08", "2026-09")}

        assert molde["moradia"].repete is True
        assert molde["contas_da_casa"].repete is True
        assert molde["divida"].repete is True
        assert molde["salario"].repete is True

    def test_gasto_variavel_nao_repete(self):
        molde = {c.entry.category: c for c in montar_molde(agosto(), "2026-08", "2026-09")}

        assert molde["mercado"].repete is False, (
            "copiar mercado inventaria despesa: o valor do mês que passou é fato daquele mês, e "
            "a estimativa de variável já é derivada do histórico"
        )
        assert molde["lazer"].repete is False

    def test_o_variavel_continua_aparecendo_como_candidato(self):
        categorias = [c.entry.category for c in montar_molde(agosto(), "2026-08", "2026-09")]

        assert "mercado" in categorias, (
            "não sugerido não é escondido: quem quer copiar a mensalidade que caiu em 'outros' "
            "precisa vê-la para marcar"
        )

    def test_decimo_terceiro_nao_repete(self):
        entries = [entrada("decimo_terceiro", 6418.73, "2026-12-20")]
        molde = montar_molde(entries, "2026-12", "2027-01")

        assert molde[0].repete is False, "acontece uma vez no ano, não todo mês"

    def test_provento_derivado_nao_entra_no_molde(self):
        entries = agosto() + [
            CashEntry(
                kind=CashKind.INCOME,
                category="provento",
                description="Provento de PETR4",
                amount=340.0,
                due_on="2026-08-15",
                paid_on="2026-08-15",
                derived=True,
            )
        ]
        categorias = [c.entry.category for c in montar_molde(entries, "2026-08", "2026-09")]

        assert "provento" not in categorias, (
            "provento é projeção do razão; copiá-lo gravaria como lançamento o que é derivado"
        )
        assert repete_todo_mes(entries[-1]) is False


class TestADataViajaParaODestino:
    def test_o_dia_se_mantem(self):
        molde = {c.entry.category: c for c in montar_molde(agosto(), "2026-08", "2026-09")}

        assert molde["moradia"].entry.due_on == "2026-09-05"
        assert molde["divida"].entry.due_on == "2026-09-12"

    def test_dia_31_em_mes_de_30_prende_no_ultimo(self):
        assert dia_no_mes("2026-08-31", "2026-09") == "2026-09-30"
        assert dia_no_mes("2026-01-31", "2026-02") == "2026-02-28"
        assert dia_no_mes("2028-01-31", "2028-02") == "2028-02-29", "ano bissexto"

    def test_o_copiado_nasce_a_vencer_e_nao_pago(self):
        for c in montar_molde(agosto(), "2026-08", "2026-09"):
            assert c.entry.paid_on is None, (
                "copiar o pagamento junto diria que o dinheiro se moveu num mês que ainda não "
                "aconteceu — o caixa mede movimento, não intenção"
            )


class TestOMoldeNaoDuplica:
    def test_o_que_ja_esta_no_destino_vem_marcado(self):
        entries = agosto() + [saida("moradia", 2200.00, "2026-09-05")]
        molde = {c.entry.category: c for c in montar_molde(entries, "2026-08", "2026-09")}

        assert molde["moradia"].ja_esta_la is True
        assert molde["contas_da_casa"].ja_esta_la is False

    def test_a_identidade_ignora_o_valor(self):
        entries = agosto() + [saida("contas_da_casa", 129.90, "2026-09-22")]
        molde = {c.entry.category: c for c in montar_molde(entries, "2026-08", "2026-09")}

        assert molde["contas_da_casa"].ja_esta_la is True, (
            "a conta de luz muda de valor todo mês; se o valor entrasse na identidade, o molde "
            "ofereceria a mesma conta de novo"
        )

    def test_descricao_com_caixa_diferente_e_o_mesmo_lancamento(self):
        entries = [
            saida("moradia", 2150.00, "2026-08-05"),
            CashEntry(
                kind=CashKind.EXPENSE,
                category="moradia",
                description="MORADIA",
                amount=2150.00,
                due_on="2026-09-05",
                paid_on=None,
            ),
        ]
        molde = montar_molde(entries, "2026-08", "2026-09")

        assert molde[0].ja_esta_la is True


class TestOMoldeSeRecusa:
    def test_um_mes_nao_e_molde_de_si_mesmo(self):
        with pytest.raises(CashError, match="molde de si mesmo"):
            montar_molde(agosto(), "2026-08", "2026-08")

    def test_mes_mal_formado_e_recusado(self):
        with pytest.raises(CashError, match="YYYY-MM"):
            montar_molde(agosto(), "2026-08-01", "2026-09")

    def test_mes_de_origem_vazio_da_molde_vazio(self):
        assert montar_molde(agosto(), "2026-07", "2026-08") == ()
