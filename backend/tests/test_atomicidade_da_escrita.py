"""A unidade de trabalho da requisição — o buraco que 797 testes não viram.

A sessão de banco nascia e commitava no middleware de observabilidade, e só o
ramo `except BaseException` fazia rollback. Mas os handlers de `DomainError` e
`ValueError` vivem no `ExceptionMiddleware` do Starlette, que é *interno* ao
middleware de usuário: o erro nunca subia, o middleware via uma resposta 4xx
normal e commitava a escrita parcial.

A suíte não pegava porque exercita rotas e confere respostas, não o estado do
banco depois de um erro de domínio no meio de uma escrita composta.
"""

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
    def test_venda_recusada_pelo_razao_nao_grava_trade_encerrado(self, client, como):
        """O cenário exato de F-01, no caminho em que ele corrompe dinheiro.

        `sell_position` valida contra a *posição*, grava o `ClosedTradeDb` —
        com IR apurado — e só depois chama o razão. Quando projeção e posição
        divergem, o razão recusa: o usuário levava 400, o trade encerrado
        ficava gravado com imposto calculado, e a venda não existia no razão.
        A carteira e a apuração fiscal saíam de sincronia para sempre.

        A divergência é semeada apagando o razão por baixo — que é o que uma
        escrita parcial anterior produziria na prática.
        """
        uid = como("u_atomico_venda")
        headers = make_auth_headers(uid)

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 10, "avg_price": 20.0},
            headers=headers,
        )
        ledger_store.delete_symbol_entries("PETR4", user_id=uid)

        antes = len(portfolio_store.list_closed_trades(user_id=uid))

        resposta = client.post(
            "/api/portfolio/sell",
            json={"ticker": "PETR4", "quantity": 5, "sell_price": 30.0},
            headers=headers,
        )

        assert resposta.status_code >= 400, "o razão precisa recusar para o cenário existir"
        assert len(portfolio_store.list_closed_trades(user_id=uid)) == antes
        assert portfolio_store.get_position("PETR4", user_id=uid)["quantity"] == 10

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
        """O contador do teto não pode voltar atrás junto com o 4xx que provocou.

        Ele escreve em transação própria justamente por isso — senão o
        rate limiting seria desarmado pela própria correção de F-01.
        """
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
