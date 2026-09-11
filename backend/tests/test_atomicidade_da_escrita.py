from __future__ import annotations

import pytest

from app.core.context import reset_current_user_id, set_current_user_id
from app.storage import ledger_store, portfolio_store
from tests.conftest import make_auth_headers


@pytest.fixture()
def como():
    tokens = []

    def _enter(user_id: str):
        tokens.append(set_current_user_id(user_id))
        return user_id

    yield _enter

    for token in reversed(tokens):
        reset_current_user_id(token)


class TestVendaRecusadaNaoDeixaRastro:
    def test_venda_recusada_pelo_razao_nao_deixa_apuracao_nem_posicao_reduzida(self, client, como):
        uid = como("u_atomico_venda")
        headers = make_auth_headers(uid)

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 10, "avg_price": 20.0},
            headers=headers,
        )
        ledger_store.delete_symbol_entries("PETR4", user_id=uid)

        resposta = client.post(
            "/api/portfolio/sell",
            json={"ticker": "PETR4", "quantity": 5, "sell_price": 30.0},
            headers=headers,
        )

        assert resposta.status_code >= 400, "o razão precisa recusar para o cenário existir"
        assert ledger_store.list_entries(symbol="PETR4", user_id=uid) == []
        assert portfolio_store.get_position("PETR4", user_id=uid)["quantity"] == 10

        encerradas = client.get("/api/portfolio/trades", headers=headers).json()
        assert encerradas["total_count"] == 0
        assert encerradas["total_ir_paid"] == 0.0

    def test_lancamento_invalido_nao_fica_no_razao(self, client, como):
        uid = como("u_atomico_razao")
        headers = make_auth_headers(uid)

        antes = len(ledger_store.list_entries(user_id=uid))

        resposta = client.post(
            "/api/transactions",
            json={
                "kind": "sell",
                "symbol": "VALE3",
                "traded_on": "2026-01-10",
                "quantity": 50,
                "price": 60.0,
            },
            headers=headers,
        )

        assert resposta.status_code >= 400
        assert len(ledger_store.list_entries(user_id=uid)) == antes


class TestOContadorDoTetoSobreveveAoErro:
    def test_a_recusa_nao_devolve_a_cota(self, client, como):
        from app.core import usage

        uid = como("u_atomico_teto")
        janela = usage.minute_window()

        usage.increment(uid, "prova", janela, ttl_seconds=120)
        antes = usage.current(uid, "prova", janela)

        client.post(
            "/api/portfolio/sell",
            json={"ticker": "NAOEXISTE1", "quantity": 1, "sell_price": 1.0},
            headers=make_auth_headers(uid),
        )

        assert usage.current(uid, "prova", janela) == antes
