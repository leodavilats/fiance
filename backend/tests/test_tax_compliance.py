import time

from app.core.brt import BRT, month_bounds, to_brt
from app.models.enums import AssetCategory
from tests.conftest import make_auth_headers

ACOES = AssetCategory.acoes_br.value
FIIS = AssetCategory.fiis.value


def _dia_do_mes_passado() -> str:
    month_start, _ = month_bounds()
    return to_brt(month_start - 5 * 86400).strftime("%Y-%m-%d")


def _dia_de_hoje() -> str:
    return to_brt(time.time()).strftime("%Y-%m-%d")


def declarar(client, headers, ticker: str, quantidade: float, preco: float, categoria: str):
    return client.post(
        "/api/portfolio/position",
        headers=headers,
        json={
            "ticker": ticker,
            "quantity": quantidade,
            "avg_price": preco,
            "category": categoria,
        },
    )


def lancar_venda(client, headers, ticker: str, quantidade: float, preco: float, dia: str):
    return client.post(
        "/api/transactions",
        headers=headers,
        json={
            "kind": "sell",
            "symbol": ticker,
            "quantity": quantidade,
            "price": preco,
            "traded_on": dia,
        },
    )


def encerradas(client, headers) -> dict:
    return client.get("/api/portfolio/trades", headers=headers).json()


def mes(corpo: dict, chave: str, categoria: str = ACOES) -> dict | None:
    return next(
        (m for m in corpo["months"] if m["month"] == chave and m["category"] == categoria),
        None,
    )


class TestOMesEAUnidadeDaApuracao:
    def test_venda_retroativa_e_apurada_no_mes_dela(self, client):
        headers = make_auth_headers("tax_backdate_user")
        passado = _dia_do_mes_passado()

        declarar(client, headers, "PETR4", 2000, 10.0, ACOES)
        assert lancar_venda(client, headers, "PETR4", 2000, 30.0, passado).status_code in (200, 201)

        corpo = encerradas(client, headers)
        apurado = mes(corpo, passado[:7])

        assert apurado is not None
        assert apurado["exempt"] is False, "R$ 60.000 vendidos passam longe da isenção"
        assert apurado["ir_amount"] > 0, "venda retroativa não pode herdar a isenção de outro mês"

    def test_o_mes_corrente_nao_e_poluido_pelo_mes_passado(self, client):
        headers = make_auth_headers("tax_current_month_user")
        passado = _dia_do_mes_passado()
        hoje = _dia_de_hoje()

        declarar(client, headers, "PETR4", 3000, 10.0, ACOES)
        lancar_venda(client, headers, "PETR4", 2000, 30.0, passado)
        lancar_venda(client, headers, "PETR4", 100, 30.0, hoje)

        corpo = encerradas(client, headers)
        atual = mes(corpo, hoje[:7])

        assert atual["gross_sales"] == 3_000.0
        assert atual["exempt"] is True
        assert atual["ir_amount"] == 0.0

    def test_duas_vendas_do_mesmo_mes_somam_para_a_isencao(self, client):
        headers = make_auth_headers("tax_soma_do_mes")
        hoje = _dia_de_hoje()

        declarar(client, headers, "PETR4", 2000, 10.0, ACOES)
        lancar_venda(client, headers, "PETR4", 1000, 15.0, hoje)
        lancar_venda(client, headers, "PETR4", 1000, 15.0, hoje)

        atual = mes(encerradas(client, headers), hoje[:7])

        assert atual["gross_sales"] == 30_000.0
        assert atual["exempt"] is False


class TestPrejuizoCompensavel:
    def test_prejuizo_em_mes_isento_nao_vira_saldo(self, client):
        headers = make_auth_headers("tax_prejuizo_isento")
        hoje = _dia_de_hoje()

        declarar(client, headers, "PETR4", 100, 10.0, ACOES)
        lancar_venda(client, headers, "PETR4", 100, 8.0, hoje)

        corpo = encerradas(client, headers)

        assert corpo["total_tax_loss_available"] == 0.0, (
            "prejuízo apurado dentro da isenção não compensa ganho futuro"
        )

    def test_prejuizo_acima_da_isencao_vira_saldo(self, client):
        headers = make_auth_headers("tax_prejuizo_compensavel")
        hoje = _dia_de_hoje()

        declarar(client, headers, "PETR4", 3000, 10.0, ACOES)
        lancar_venda(client, headers, "PETR4", 3000, 8.0, hoje)

        corpo = encerradas(client, headers)
        saldo = {b["category"]: b for b in corpo["tax_loss_balances"]}

        assert saldo[ACOES]["available"] == 6_000.0

    def test_prejuizo_de_fii_e_sempre_compensavel_porque_nao_ha_isencao(self, client):
        headers = make_auth_headers("tax_prejuizo_fii")
        hoje = _dia_de_hoje()

        declarar(client, headers, "HGLG11", 10, 100.0, FIIS)
        lancar_venda(client, headers, "HGLG11", 10, 80.0, hoje)

        saldo = {b["category"]: b for b in encerradas(client, headers)["tax_loss_balances"]}

        assert saldo[FIIS]["available"] == 200.0

    def test_o_abatimento_nunca_deixa_o_imposto_negativo(self, client):
        headers = make_auth_headers("tax_abatimento_teto")
        passado = _dia_do_mes_passado()
        hoje = _dia_de_hoje()

        declarar(client, headers, "HGLG11", 100, 100.0, FIIS)
        lancar_venda(client, headers, "HGLG11", 50, 20.0, passado)
        lancar_venda(client, headers, "HGLG11", 50, 110.0, hoje)

        corpo = encerradas(client, headers)
        atual = mes(corpo, hoje[:7], FIIS)

        assert atual["ir_amount"] == 0.0
        assert atual["taxable_profit"] == 0.0
        assert atual["loss_offset_used"] == 500.0, "abate só o ganho, e não o saldo inteiro"


class TestTodaVendaChegaNaApuracao:
    def test_venda_por_transactions_aparece_em_encerradas(self, client):
        headers = make_auth_headers("tax_venda_pelo_razao")
        hoje = _dia_de_hoje()

        declarar(client, headers, "PETR4", 3000, 10.0, ACOES)
        lancar_venda(client, headers, "PETR4", 3000, 20.0, hoje)

        corpo = encerradas(client, headers)

        assert corpo["total_count"] == 1
        assert corpo["trades"][0]["ticker"] == "PETR4"
        assert corpo["total_ir_paid"] == 4_500.0

    def test_venda_por_portfolio_sell_tambem(self, client):
        headers = make_auth_headers("tax_venda_pela_rota_de_venda")

        declarar(client, headers, "HGLG11", 100, 100.0, FIIS)
        resp = client.post(
            "/api/portfolio/sell",
            headers=headers,
            json={"ticker": "HGLG11", "quantity": 100, "sell_price": 150.0},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["ir_amount"] == 1_000.0, "20% sobre R$ 5.000 de lucro"

        corpo = encerradas(client, headers)
        assert corpo["total_count"] == 1


class TestOFusoFiscalEBrasileiro:
    def test_month_bounds_usa_o_mes_calendario_brasileiro(self):
        start, end = month_bounds()
        assert to_brt(start).day == 1
        assert to_brt(start).hour == 0
        assert to_brt(end).day == 1
        assert end > start

    def test_month_bounds_atravessa_o_ano(self):
        december = time.mktime(time.struct_time((2026, 12, 20, 12, 0, 0, 0, 0, 0)))
        start, end = month_bounds(december)
        assert to_brt(start).month == 12
        assert to_brt(end).month == 1
        assert to_brt(end).year == to_brt(start).year + 1

    def test_a_venda_do_dia_primeiro_fica_no_mes_dela_e_nao_no_anterior(self):
        from app.core.brt import day_timestamp

        instante = day_timestamp("2026-03-01")

        assert to_brt(instante).month == 3
        assert to_brt(instante).day == 1
        assert to_brt(instante).tzinfo == BRT or to_brt(instante).utcoffset() == BRT.utcoffset(None)
